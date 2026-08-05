"""Assertion sandbox tests: expression/block forms, failures, restrictions, timeout."""

from skill_eval.core.schema import Trace, Node
from skill_eval.eval.sandbox import run_assertion
from skill_eval.mock.generator import make_trace


def _ctx(trace: Trace | None = None) -> dict:
    t = trace or make_trace(kind="simple_ok", tool_count=2)
    return {
        "trace": t.model_dump(mode="json"),
        "projection": [{"node_id": "n1", "name": "read_file"}, {"node_id": "n2", "name": "grep"}],
        "actual": ["read_file", "grep"],
        "expected": ["read_file", "grep"],
    }


class TestExpressionForm:
    def test_true_expression(self) -> None:
        out = run_assertion("len(projection) >= 2", _ctx())
        assert out.passed is True
        assert out.message is None

    def test_false_expression(self) -> None:
        out = run_assertion("len(projection) >= 5", _ctx())
        assert out.passed is False

    def test_attribute_access_on_tool(self) -> None:
        out = run_assertion("all(t.name in expected for t in projection)", _ctx())
        assert out.passed is True

    def test_exception_becomes_failure(self) -> None:
        out = run_assertion("projection[0].missing_attr == 1", _ctx())
        assert out.passed is False
        assert "Error" in (out.message or "")


class TestBlockForm:
    def test_result_variable(self) -> None:
        code = "result = len(actual) == len(expected)"
        assert run_assertion(code, _ctx()).passed is True

    def test_multi_statement(self) -> None:
        code = "names = [t.name for t in projection]\nresult = 'grep' in names"
        assert run_assertion(code, _ctx()).passed is True

    def test_no_result_assigned(self) -> None:
        out = run_assertion("x = 1", _ctx())
        assert out.passed is False
        assert out.message is not None

    def test_rule_driven_logic(self) -> None:
        out = run_assertion(
            "result = set(actual) == set(expected)", _ctx()
        )
        assert out.passed is True


class TestRestrictions:
    def test_open_blocked(self) -> None:
        out = run_assertion("open('C:/x').read()", _ctx())
        assert out.passed is False
        assert out.message is not None

    def test_import_blocked(self) -> None:
        out = run_assertion("__import__('os').system('echo hi')", _ctx())
        assert out.passed is False

    def test_syntax_error(self) -> None:
        out = run_assertion("def broken(:", _ctx())
        assert out.passed is False
        assert "Error" in (out.message or "")


class TestTimeout:
    def test_infinite_loop_times_out(self) -> None:
        out = run_assertion("while True: pass", _ctx(), timeout_seconds=2)
        assert out.passed is False
        assert "timed out" in (out.message or "")
