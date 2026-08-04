import pytest

from skill_eval.core.schema import Trace
from skill_eval.mock.generator import MOCK_KINDS, make_trace


class TestMockGenerator:
    @pytest.mark.parametrize("kind", MOCK_KINDS)
    def test_kinds_validate(self, kind: str) -> None:
        trace = make_trace(kind=kind, tool_count=5)
        Trace.model_validate(trace.model_dump())
        assert trace.root.children

    def test_deterministic(self) -> None:
        a = make_trace(kind="simple_ok", tool_count=3)
        b = make_trace(kind="simple_ok", tool_count=3)
        assert a == b

    def test_tool_count_respected(self) -> None:
        trace = make_trace(kind="simple_ok", tool_count=7)
        assert len(trace.tool_names()) == 7

    def test_simple_ok_shape(self) -> None:
        trace = make_trace(kind="simple_ok", tool_count=2)
        assert trace.status == "completed"
        assert trace.ended_at is not None
        types = [c.type for c in trace.root.children]
        assert types == ["agent_step", "skill_end"]

    def test_error_kind(self) -> None:
        trace = make_trace(kind="error_mid")
        assert trace.status == "error"
        assert trace.error is not None
        assert any(n.error for n in trace.iter_nodes())

    def test_running_kind(self) -> None:
        trace = make_trace(kind="running")
        assert trace.status == "running"
        assert trace.ended_at is None

    def test_long_chain(self) -> None:
        trace = make_trace(kind="long_chain", tool_count=120)
        assert len(trace.tool_names()) == 120

    def test_node_ids_unique(self) -> None:
        trace = make_trace(kind="nested", tool_count=4)
        ids = [n.id for n in trace.iter_nodes()]
        assert len(ids) == len(set(ids))

    def test_invalid_kind_raises(self) -> None:
        with pytest.raises(ValueError):
            make_trace(kind="nope")

    def test_usage_present_for_completed(self) -> None:
        trace = make_trace(kind="simple_ok", tool_count=3)
        assert trace.usage is not None
        assert trace.usage.total_tokens is not None
