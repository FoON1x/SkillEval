"""Deterministic reference Trace generator for development, tests and UI demos.

Kinds: simple_ok / nested / error_mid / running / long_chain
"""

import datetime as dt

from skill_eval.core.schema import (
    AgentName,
    LlmUsage,
    Node,
    NodeStatus,
    NodeType,
    RunState,
    Trace,
    TraceError,
    Usage,
)

MOCK_KINDS = ("simple_ok", "nested", "error_mid", "running", "long_chain")

TOOL_POOL = [
    "read_file",
    "grep",
    "bash",
    "edit_file",
    "web_fetch",
    "list_dir",
    "search",
    "browser",
    "memory",
    "database_query",
]

_BASE = dt.datetime(2026, 8, 4, 10, 0, 0)


def _tool_name(i: int) -> str:
    return TOOL_POOL[i % len(TOOL_POOL)]


class _Builder:
    def __init__(self) -> None:
        self._counter = 0
        self._cursor = _BASE

    def _next_id(self) -> str:
        self._counter += 1
        return f"n{self._counter}"

    def _tick(self, seconds: int = 5) -> tuple[dt.datetime, dt.datetime]:
        start = self._cursor
        end = start + dt.timedelta(seconds=seconds)
        self._cursor = end
        return start, end

    def tool(
        self,
        name: str | None = None,
        status: NodeStatus = NodeStatus.COMPLETED,
        args: object | None = None,
        result: object | None = None,
    ) -> Node:
        start, end = self._tick()
        if name is None:
            name = _tool_name(self._counter)
        return Node(
            id=self._next_id(),
            type=NodeType.TOOL_CALL,
            name=name,
            status=status,
            started_at=start,
            ended_at=end,
            duration_ms=5000,
            tool={
                "name": name,
                "args": args if args is not None else {"query": name},
                "result": result if result is not None else {"ok": True},
            },
        )

    def step(self, children: list[Node], name: str = "agent step") -> Node:
        start, end = self._tick()
        return Node(
            id=self._next_id(),
            type=NodeType.AGENT_STEP,
            name=name,
            status=NodeStatus.COMPLETED,
            started_at=start,
            ended_at=end,
            duration_ms=5000,
            children=children,
        )

    def skill_start(self, skill_name: str) -> Node:
        return Node(
            id=self._next_id(),
            type=NodeType.SKILL_START,
            name=skill_name,
            status=NodeStatus.COMPLETED,
            started_at=self._cursor,
        )

    def skill_end(self, status: NodeStatus = NodeStatus.COMPLETED) -> Node:
        start, end = self._tick()
        return Node(
            id=self._next_id(),
            type=NodeType.SKILL_END,
            name="skill_end",
            status=status,
            started_at=start,
            ended_at=end,
            duration_ms=5000,
        )


def _usage(tool_count: int, running: bool = False) -> Usage:
    input_tokens = 1000
    output_tokens = 200 * tool_count
    total = input_tokens + output_tokens
    return Usage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total,
        cost_usd=0.00005 * total if not running else None,
        latency_ms=sum(5000 for _ in range(tool_count)) + 1000,
        models=["demo-model"],
    )


def make_trace(
    agent: AgentName | str = "opencode",
    kind: str = "simple_ok",
    skill_name: str = "demo-skill",
    tool_count: int = 3,
) -> Trace:
    """Build a deterministic Trace of the given kind."""

    if kind not in MOCK_KINDS:
        raise ValueError(f"unknown kind: {kind!r} (expected one of {MOCK_KINDS})")

    b = _Builder()
    root = b.skill_start(skill_name)
    children: list[Node] = []

    if kind == "simple_ok":
        children.append(b.step([b.tool() for _ in range(tool_count)]))
        children.append(b.skill_end())

    elif kind == "nested":
        children.append(b.step([b.tool() for _ in range(2)]))
        sub = Node(
            id=b._next_id(),
            type=NodeType.SUB_AGENT,
            name="sub_agent",
            status=NodeStatus.COMPLETED,
            started_at=b._cursor,
            children=[b.step([b.tool() for _ in range(tool_count)], name="sub step")],
        )
        children.append(sub)
        children.append(b.skill_end())

    elif kind == "error_mid":
        tools = [b.tool() for _ in range(2)]
        start, _ = b._tick()
        err = Node(
            id=b._next_id(),
            type=NodeType.ERROR,
            name="bash failed",
            status=NodeStatus.ERROR,
            started_at=start,
            error=TraceError(message="command exited with code 2", kind="runtime"),
        )
        children.append(b.step([*tools, err]))
        children.append(b.skill_end(status=NodeStatus.SKIPPED))

    elif kind == "running":
        children.append(b.step([b.tool() for _ in range(tool_count)]))

    elif kind == "long_chain":
        children.append(b.step([b.tool() for _ in range(tool_count)]))
        children.append(b.skill_end())

    root.children = children

    running = kind == "running"
    status = RunState.ERROR if kind == "error_mid" else RunState.RUNNING if running else RunState.COMPLETED
    return Trace(
        id=f"{agent}-{kind}-{tool_count}",
        agent=agent,
        tool_version="1.0.0",
        skill_name=skill_name,
        session_id=f"sess-{kind}",
        status=status,
        started_at=_BASE,
        ended_at=None if running else b._cursor,
        usage=None if running else _usage(tool_count),
        error=TraceError(message="skill failed", kind="tool_error") if kind == "error_mid" else None,
        root=root,
    )
