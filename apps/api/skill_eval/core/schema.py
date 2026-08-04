"""Canonical Trace Schema — the single source of truth (see docs/SCHEMA.md).

Cross-language: FastAPI exposes this via OpenAPI; frontend consumes generated TS types.
"""

import datetime as dt
from enum import StrEnum
from typing import Any, Iterator

from pydantic import BaseModel, Field


class AgentName(StrEnum):
    OPENCODE = "opencode"
    CODEX = "codex"
    CLAUDE_CODE = "claude-code"
    PI = "pi"


class RunState(StrEnum):
    COMPLETED = "completed"
    RUNNING = "running"
    ERROR = "error"
    CANCELLED = "cancelled"


class NodeStatus(StrEnum):
    COMPLETED = "completed"
    RUNNING = "running"
    ERROR = "error"
    SKIPPED = "skipped"


class NodeType(StrEnum):
    SKILL_START = "skill_start"
    SKILL_END = "skill_end"
    AGENT_STEP = "agent_step"
    TOOL_CALL = "tool_call"
    LLM_CALL = "llm_call"
    SUB_AGENT = "sub_agent"
    MESSAGE = "message"
    ERROR = "error"
    CUSTOM = "custom"


class ToolCall(BaseModel):
    name: str
    args: Any = None
    result: Any = None
    meta: dict[str, Any] = Field(default_factory=dict)


class LlmUsage(BaseModel):
    model: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    cost_usd: float | None = None
    latency_ms: int | None = None


class Usage(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    cost_usd: float | None = None
    latency_ms: int | None = None
    models: list[str] = Field(default_factory=list)


class TraceError(BaseModel):
    message: str
    kind: str | None = None
    trace: str | None = None


class Node(BaseModel):
    """A recursive observable event node (OTel-span-like)."""

    id: str
    parent_id: str | None = None
    type: NodeType
    name: str
    summary: str | None = None
    status: NodeStatus = NodeStatus.COMPLETED
    started_at: dt.datetime | None = None
    ended_at: dt.datetime | None = None
    duration_ms: int | None = None
    input: Any = None
    output: Any = None
    tool: ToolCall | None = None
    llm: LlmUsage | None = None
    error: TraceError | None = None
    children: list["Node"] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class Trace(BaseModel):
    id: str
    agent: AgentName
    tool_version: str | None = None
    skill_name: str | None = None
    session_id: str | None = None
    status: RunState = RunState.COMPLETED
    started_at: dt.datetime | None = None
    ended_at: dt.datetime | None = None
    usage: Usage | None = None
    error: TraceError | None = None
    root: Node
    extra: dict[str, Any] = Field(default_factory=dict)

    def iter_nodes(self) -> Iterator[Node]:
        """Depth-first pre-order traversal including root."""

        def walk(n: Node) -> Iterator[Node]:
            yield n
            for child in n.children:
                yield from walk(child)

        yield from walk(self.root)

    def tool_names(self) -> list[str]:
        """Names of tool_call nodes in DFS order (incl. skipped)."""
        return [n.name for n in self.iter_nodes() if n.type == NodeType.TOOL_CALL]
