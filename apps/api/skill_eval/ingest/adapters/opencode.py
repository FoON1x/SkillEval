"""opencode adapter — consumes the real `opencode run --format json` JSONL stream.

Real event format (opencode CLI >= 1.18): each JSONL line is
  {"type": <str>, "timestamp": <epoch_ms>, "sessionID": <str>, "part": {...}}
Recognized types: step_start, text, tool_use, step_finish. Unknown types are
ignored with a ParseWarning. The batch `parse()` path accepts a dict wrapping a
list of such lines; the incremental `TraceBuilder` path feeds lines one-by-one
(used by the live runner). Both share one mapping core.

`opencode export <sessionID>` JSON (the `export_info` arg to finalize) provides
authoritative trace-level metadata (title, agent, model, cost, tokens) richer
than the live stream; finalize merges it when available.
"""

import datetime as dt
import uuid
import warnings
from typing import Any

from skill_eval.core.schema import (
    AgentName,
    LlmUsage,
    Node,
    NodeStatus,
    NodeType,
    RunState,
    Trace,
    TraceError,
    ToolCall,
    Usage,
)
from skill_eval.ingest.errors import ParseError, ParseWarning
from skill_eval.ingest.registry import BaseImporter


def _from_ms(ms: int | None) -> dt.datetime | None:
    if ms is None:
        return None
    return dt.datetime.fromtimestamp(ms / 1000, tz=dt.timezone.utc)


def _ms(start: dt.datetime | None, end: dt.datetime | None) -> int | None:
    if start and end:
        return max(0, int((end - start).total_seconds() * 1000))
    return None


class _TraceBuilder:
    """Incremental builder: feed real JSONL lines, finalize into a Trace.

    Shared mapping core for both the batch `parse()` and live runner paths.
    """

    def __init__(self, skill_name: str | None) -> None:
        self._skill_name = skill_name
        self._counter = 0
        self._session_id: str | None = None
        self._root: Node = Node(
            id=self._next_id(),
            type=NodeType.SKILL_START,
            name=skill_name or "skill",
            started_at=None,
            extra={"source": "opencode"},
        )
        self._current_step: Node | None = None
        self._has_skill_end = False

    def _next_id(self) -> str:
        self._counter += 1
        return f"n{self._counter}"

    @property
    def session_id(self) -> str | None:
        return self._session_id

    def feed(self, event: dict[str, Any]) -> dict[str, Any] | None:
        """Feed one JSONL line; return a canonical event dict for SSE, or None."""
        if not isinstance(event, dict) or "type" not in event:
            raise ParseError(f"malformed event (expected object with 'type'): {event!r}")
        if self._session_id is None:
            sid = event.get("sessionID")
            if isinstance(sid, str):
                self._session_id = sid
                if not self._skill_name:
                    self._root.name = sid

        kind = event["type"]
        part = event.get("part") or {}
        ts_ms = event.get("timestamp")
        ts = _from_ms(ts_ms)

        if kind == "step_start":
            step = Node(
                id=self._next_id(),
                type=NodeType.AGENT_STEP,
                name="step",
                status=NodeStatus.RUNNING,
                started_at=ts,
            )
            self._root.children.append(step)
            self._current_step = step
            if self._root.started_at is None:
                self._root.started_at = ts
            return {"node_type": "agent_step", "status": "running", "name": "step", "started_at": ts_ms}

        if kind == "text":
            step = self._ensure_step(ts)
            text = part.get("text", "")
            msg = Node(
                id=self._next_id(),
                type=NodeType.MESSAGE,
                name="message",
                status=NodeStatus.COMPLETED,
                started_at=_from_ms((part.get("time") or {}).get("start")) or ts,
                ended_at=_from_ms((part.get("time") or {}).get("end")),
                output=text,
            )
            msg.duration_ms = _ms(msg.started_at, msg.ended_at)
            step.children.append(msg)
            return {"node_type": "message", "status": "completed", "text": text}

        if kind == "tool_use":
            step = self._ensure_step(ts)
            state = part.get("state") or {}
            tool_name = part.get("tool") or "tool"
            time = state.get("time") or {}
            start = _from_ms(time.get("start")) or ts
            end = _from_ms(time.get("end"))
            meta = state.get("metadata") or {}
            exit_code = meta.get("exit")
            is_error = isinstance(exit_code, int) and exit_code != 0
            status = NodeStatus.ERROR if is_error else _status_from(state.get("status"))
            node = Node(
                id=self._next_id(),
                type=NodeType.TOOL_CALL,
                name=tool_name,
                status=status,
                started_at=start,
                ended_at=end,
                duration_ms=_ms(start, end),
                input=state.get("input"),
                output=state.get("output"),
                tool=ToolCall(
                    name=tool_name,
                    args=state.get("input"),
                    result=state.get("output"),
                    meta=meta,
                ),
                error=TraceError(
                    message=str(state.get("output", ""))[:500],
                    kind=f"exit:{exit_code}",
                ) if is_error else None,
                extra={"title": state.get("title"), "call_id": part.get("callID")},
            )
            step.children.append(node)
            return {
                "node_type": "tool_call", "status": status.value, "name": tool_name,
                "tool": tool_name, "exit": exit_code,
            }

        if kind == "step_finish":
            if self._current_step is not None:
                self._current_step.ended_at = ts
                self._current_step.duration_ms = _ms(self._current_step.started_at, ts)
                self._current_step.status = NodeStatus.COMPLETED
            tokens = part.get("tokens") or {}
            cost = part.get("cost")
            llm = LlmUsage(
                input_tokens=tokens.get("input"),
                output_tokens=tokens.get("output"),
                total_tokens=tokens.get("total"),
                cost_usd=cost,
            )
            if self._current_step is not None and (llm.input_tokens or llm.total_tokens):
                self._current_step.llm = llm
            reason = part.get("reason")
            if reason == "stop":
                self._has_skill_end = True
            return {"node_type": "step_finish", "reason": reason, "cost": cost}

        warnings.warn(f"ignoring unknown opencode event type: {kind}", ParseWarning)
        return None

    def _ensure_step(self, ts: dt.datetime | None) -> Node:
        if self._current_step is None or self._current_step.status == NodeStatus.COMPLETED:
            step = Node(
                id=self._next_id(),
                type=NodeType.AGENT_STEP,
                name="step",
                status=NodeStatus.RUNNING,
                started_at=ts,
            )
            self._root.children.append(step)
            self._current_step = step
        return self._current_step

    def finalize(self, export_info: dict[str, Any] | None = None) -> Trace:
        info = export_info or {}
        started = _from_ms((info.get("time") or {}).get("created")) or self._root.started_at
        ended = _from_ms((info.get("time") or {}).get("updated")) or self._root.ended_at
        if ended is None and self._current_step is not None:
            ended = self._current_step.ended_at
        self._root.started_at = started
        self._root.ended_at = ended
        self._root.duration_ms = _ms(started, ended)

        if self._has_skill_end:
            self._root.children.append(
                Node(
                    id=self._next_id(),
                    type=NodeType.SKILL_END,
                    name="skill_end",
                    ended_at=ended,
                    duration_ms=_ms(started, ended),
                )
            )

        usage: Usage | None = None
        toks = info.get("tokens")
        cost = info.get("cost")
        if toks or cost is not None:
            in_t = (toks or {}).get("input")
            out_t = (toks or {}).get("output")
            total = (int(in_t) if in_t is not None else 0) + (int(out_t) if out_t is not None else 0)
            usage = Usage(
                input_tokens=in_t,
                output_tokens=out_t,
                total_tokens=total or None,
                cost_usd=cost,
                models=[info.get("model", {}).get("id")] if info.get("model") else [],
            )

        return Trace(
            id=str(uuid.uuid4()),
            agent=AgentName.OPENCODE,
            tool_version=str(info.get("version") or ""),
            skill_name=self._skill_name,
            session_id=self._session_id,
            status=RunState.COMPLETED,
            started_at=started,
            ended_at=ended,
            usage=usage,
            root=self._root,
            extra={
                "source": "opencode",
                "event_count": self._counter,
                "title": info.get("title"),
                "agent_name": info.get("agent"),
            },
        )


def _status_from(raw: Any) -> NodeStatus:
    if isinstance(raw, str):
        try:
            return NodeStatus(raw)
        except ValueError:
            return NodeStatus.COMPLETED
    return NodeStatus.COMPLETED


class OpencodeImporter(BaseImporter):
    agent = AgentName.OPENCODE.value

    def parse(self, raw: dict[str, Any] | bytes | str | None) -> Trace:
        data = self.load_raw(raw)
        events = data.get("events")
        if not isinstance(events, list):
            raise ParseError("missing 'events' list in opencode raw payload")
        builder = _TraceBuilder(skill_name=data.get("skill_name"))
        for ev in events:
            builder.feed(ev)
        export_info = data.get("export_info")
        return builder.finalize(export_info=export_info if isinstance(export_info, dict) else None)

    def new_builder(self, skill_name: str | None) -> _TraceBuilder:
        return _TraceBuilder(skill_name=skill_name)
