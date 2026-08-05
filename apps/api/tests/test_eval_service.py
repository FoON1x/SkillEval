"""Eval service tests: rule + assertions integration, scoring."""

from skill_eval.core.schema import Trace
from skill_eval.eval.service import evaluate
from skill_eval.mock.generator import make_trace
from skill_eval.store.dto import Assertion, ExpectedPath, TestCaseCreate
from skill_eval.store.repository import Store, TestCaseView


def _trace_and_names(kind: str = "simple_ok", tool_count: int = 3) -> tuple[Trace, list[str]]:
    trace = make_trace(kind=kind, tool_count=tool_count)
    return trace, trace.tool_names()


def _case(
    rule: str = "strict",
    tools: list[str] | None = None,
    assertions: list[Assertion] | None = None,
) -> TestCaseView:
    store = Store.in_memory()
    return store.save_test_case(
        TestCaseCreate(
            name="c",
            agent="opencode",
            rule=rule,
            expected=ExpectedPath(tools=tools or []),
            assertions=assertions or [],
        )
    )


class TestEvaluate:
    def test_strict_pass(self) -> None:
        trace, names = _trace_and_names()
        outcome = evaluate(trace, _case(tools=names))
        assert outcome.passed is True
        assert outcome.score == 1.0
        assert outcome.rule.passed

    def test_strict_order_fail(self) -> None:
        trace, names = _trace_and_names()
        outcome = evaluate(trace, _case(tools=list(reversed(names))))
        assert outcome.passed is False
        assert outcome.rule.mismatches
        assert outcome.score < 1.0

    def test_subset_rule_extra_tool_fails(self) -> None:
        trace, names = _trace_and_names()
        outcome = evaluate(trace, _case(rule="subset", tools=[names[0]]))
        assert outcome.passed is False
        assert outcome.rule.unexpected == names[1:]

    def test_assertions_included(self) -> None:
        trace, names = _trace_and_names()
        case = _case(
            tools=names,
            assertions=[Assertion(code="len(projection) >= 3", label="many tools")],
        )
        outcome = evaluate(trace, case)
        assert outcome.passed is True
        assert outcome.assertions[0].passed is True

    def test_failing_assertion_fails_overall(self) -> None:
        trace, names = _trace_and_names()
        case = _case(
            tools=names,
            assertions=[Assertion(code="len(projection) >= 10", label="impossible")],
        )
        outcome = evaluate(trace, case)
        assert outcome.passed is False
        assert outcome.score == 0.5  # rule ok (1) + 0 assertions ok, out of 2 items

    def test_projection_skips_skipped_nodes(self) -> None:
        trace, names = _trace_and_names()
        case = _case(tools=names)
        last = [n for n in trace.iter_nodes() if n.type.value == "tool_call"][-1]
        last.status = "skipped"
        outcome = evaluate(trace, case)
        assert outcome.passed is False
