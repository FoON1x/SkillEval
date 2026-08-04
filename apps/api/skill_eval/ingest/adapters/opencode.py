"""opencode adapter — v1 assumption format (docs/SCHEMA.md §7, pending real samples).

Expected raw JSON:
{
  "version": "0.1",
  "session_id": str,
  "skill_name": str | None,
  "events": [
    {"type": "session.start", "ts": iso8601},
    {"type": "agent.start", "ts": iso8601},
    {"type": "tool.start", "tool": str, "args": {...}, "ts": iso8601},
    {"type": "tool.end",   "tool": str, "result": {...}, "ts": iso8601},
    {"type": "agent.end",  "ts": iso8601},
    {"type": "session.end", "ts": iso8601},
    ...
  ]
}
Unknown event types are ignored (warned).
"""

import datetime as dt
import uuid
import warnings
from typing import Any

from skill_eval.core.schema import (
    AgentName,
    Node,
    NodeStatus,
    NodeType,
    RunState,
    Trace,
    ToolCall,
)
from skill_eval.ingest.errors import ParseError, ParseWarning
from skill_eval.ingest.registry import BaseImporter


def _parse_dt(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _ms(start: dt.datetime | None, end: dt.datetime | None) -> int | None:
    if start and end:
        return max(0, int((end - start).total_seconds() * 1000))
    return None


class OpencodeImporter(BaseImporter):
    agent = AgentName.OPENCODE.value

    def parse(self, raw: dict[str, Any] | bytes | str | None) -> Trace:
        data = self.load_raw(raw)
        events = data.get("events")
        if not isinstance(events, list):
            raise ParseError("missing 'events' list in opencode raw payload")

        node_counter = 0

        def next_id() -> str:
            nonlocal node_counter
            node_counter += 1
            return f"n{node_counter}"

        def parse_ts(ev: dict[str, Any]) -> dt.datetime | None:
            return _parse_dt(ev.get("ts"))

        root = Node(
            id=next_id(),
            type=NodeType.SKILL_START,
            name=data.get("skill_name") or data.get("session_id") or "skill",
            started_at=None,
            extra={"raw_version": data.get("version")},
        )

        step: Node | None = None
        open_tools: dict[str, Node] = {}
        session_ended = False

        def ensure_step() -> Node:
            nonlocal step
            if step is None:
                step = Node(id=next_id(), type=NodeType.AGENT_STEP, name="agent")
                root.children.append(step)
            return step

        for ev in events:
            if not isinstance(ev, dict) or "type" not in ev:
                raise ParseError(f"malformed event (expected object with 'type'): {ev!r}")
            kind = ev["type"]
            ts = parse_ts(ev)

            if kind == "session.start":
                root.started_at = ts
                root.ended_at = ts
            elif kind == "agent.start":
                ensure_step().started_at = ts
            elif kind == "tool.start":
                tool_name = ev.get("tool")
                if not isinstance(tool_name, str) or not tool_name:
                    raise ParseError(f"tool.start without 'tool' name: {ev!r}")
                node = Node(
                    id=next_id(),
                    type=NodeType.TOOL_CALL,
                    name=tool_name,
                    status=NodeStatus.RUNNING,
                    started_at=ts,
                    tool=ToolCall(name=tool_name, args=ev.get("args")),
                )
                ensure_step().children.append(node)
                open_tools[tool_name] = node
            elif kind == "tool.end":
                tool_name = ev.get("tool")
                node = open_tools.pop(tool_name, None) if isinstance(tool_name, str) else None
                if node is None:
                    raise ParseError(f"tool.end without matching tool.start: {tool_name!r}")
                node.status = NodeStatus.COMPLETED
                node.ended_at = ts
                node.duration_ms = _ms(node.started_at, ts)
                assert node.tool is not None
                node.tool.result = ev.get("result")
                node.output = ev.get("result")
            elif kind == "agent.end":
                if step is not None:
                    step.ended_at = ts
                    step.duration_ms = _ms(step.started_at, ts)
            elif kind == "session.end":
                root.ended_at = ts
                root.duration_ms = _ms(root.started_at, ts)
                session_ended = True
            else:
                warnings.warn(f"ignoring unknown opencode event type: {kind}", ParseWarning)

        for node in open_tools.values():
            node.status = NodeStatus.RUNNING

        running = bool(open_tools) or not session_ended
        if not running:
            end = Node(id=next_id(), type=NodeType.SKILL_END, name="skill_end",
                       ended_at=root.ended_at, duration_ms=_ms(root.ended_at, root.started_at))
            root.children.append(end)

        return Trace(
            id=str(uuid.uuid4()),
            agent=AgentName.OPENCODE,
            tool_version=str(data.get("version") or ""),
            skill_name=data.get("skill_name"),
            session_id=data.get("session_id"),
            status=RunState.RUNNING if running else RunState.COMPLETED,
            started_at=root.started_at,
            ended_at=None if running else root.ended_at,
            root=root,
            extra={"source": "opencode", "event_count": len(events)},
        )
