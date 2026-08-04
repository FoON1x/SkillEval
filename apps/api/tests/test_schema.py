import datetime as dt

import pytest
from pydantic import ValidationError

from skill_eval.core.schema import (
    AgentName,
    LlmUsage,
    Node,
    NodeStatus,
    NodeType,
    Trace,
    TraceError,
    Usage,
)


def make_node(**overrides: object) -> Node:
    base: dict[str, object] = {"id": "n1", "type": "tool_call", "name": "read_file"}
    base.update(overrides)
    return Node(**base)


class TestNode:
    def test_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            Node(id="n1", type="tool_call")  # type: ignore[call-arg]

    def test_defaults(self) -> None:
        node = make_node()
        assert node.status == NodeStatus.COMPLETED
        assert node.parent_id is None
        assert node.children == []
        assert node.extra == {}

    def test_invalid_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_node(type="bogus")  # type: ignore[arg-type]

    def test_invalid_status_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_node(status="bogus")  # type: ignore[arg-type]


class TestTrace:
    def test_agent_literal(self) -> None:
        trace = Trace(
            id="t1",
            agent="opencode",
            root=make_node(type="skill_start", name="s"),
        )
        assert trace.agent == AgentName.OPENCODE

    def test_unknown_agent_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Trace(id="t1", agent="unknown", root=make_node())  # type: ignore[arg-type]

    def test_requires_root(self) -> None:
        with pytest.raises(ValidationError):
            Trace(id="t1", agent="codex")  # type: ignore[call-arg]

    def test_roundtrip_json(self) -> None:
        trace = Trace(
            id="t1",
            agent="codex",
            skill_name="demo",
            status="error",
            started_at=dt.datetime(2026, 8, 4, 10, 0, 0),
            error=TraceError(message="boom", kind="runtime"),
            usage=Usage(
                total_tokens=100,
                cost_usd=0.01,
                models=["gpt-x"],
            ),
            root=make_node(
                type="agent_step",
                name="step",
                children=[
                    make_node(
                        tool={"name": "read_file", "args": {"path": "/a"}, "result": "content"}
                    )
                ],
            ),
        )
        restored = Trace.model_validate_json(trace.model_dump_json())
        assert restored == trace
        assert restored.root.children[0].tool.name == "read_file"  # type: ignore[union-attr]

    def test_nested_children_validated(self) -> None:
        trace = Trace(id="t1", agent="pi", root=make_node(children=[make_node(id="c1")]))
        assert trace.root.children[0].id == "c1"


class TestLlmUsage:
    def test_all_optional(self) -> None:
        usage = LlmUsage()
        assert usage.model is None
        assert usage.cost_usd is None
