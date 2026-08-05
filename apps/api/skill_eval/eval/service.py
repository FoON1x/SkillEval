"""Evaluation service: rule evaluation + assertion sandbox + scoring."""

from pydantic import BaseModel

from skill_eval.core.projection import tool_projection
from skill_eval.core.schema import Trace
from skill_eval.eval.rules import RuleOutcome, evaluate_rule
from skill_eval.eval.sandbox import AssertionOutcome, run_assertion
from skill_eval.store.repository import TestCaseView


class EvalOutcome(BaseModel):
    passed: bool
    score: float
    rule: RuleOutcome
    assertions: list[AssertionOutcome]


def evaluate(trace: Trace, test_case: TestCaseView) -> EvalOutcome:
    projection = tool_projection(trace)
    actual = [ref.name for ref in projection]
    rule_outcome = evaluate_rule(test_case.rule, test_case.expected.tools, actual)

    ctx: dict = {
        "trace": trace.model_dump(mode="json"),
        "projection": [ref.model_dump(mode="json") for ref in projection],
        "actual": actual,
        "expected": test_case.expected.tools,
    }
    assertion_outcomes = [
        run_assertion(a.code, ctx, label=a.label) for a in test_case.assertions
    ]

    passed = rule_outcome.passed and all(a.passed for a in assertion_outcomes)
    score = (
        int(rule_outcome.passed) + sum(int(a.passed) for a in assertion_outcomes)
    ) / (1 + len(assertion_outcomes))

    return EvalOutcome(passed=passed, score=score, rule=rule_outcome, assertions=assertion_outcomes)
