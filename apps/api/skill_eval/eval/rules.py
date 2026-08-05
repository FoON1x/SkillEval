"""Rule evaluators for the four built-in evaluation rules.

Operates on tool-name projections (lists of strings, execution order preserved).
"""

from typing import Literal

from pydantic import BaseModel, Field

RuleName = Literal["strict", "unordered", "subset", "superset"]


class RuleOutcome(BaseModel):
    rule: str
    expected: list[str]
    actual: list[str]
    passed: bool
    missing: list[str] = Field(default_factory=list)
    unexpected: list[str] = Field(default_factory=list)
    mismatches: list[dict[str, object]] = Field(default_factory=list)


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def evaluate_rule(rule: RuleName, expected: list[str], actual: list[str]) -> RuleOutcome:
    if rule not in ("strict", "unordered", "subset", "superset"):
        raise ValueError(f"unknown rule: {rule!r}")

    missing = [t for t in _dedupe_preserve_order(expected) if t not in actual]
    unexpected = [t for t in _dedupe_preserve_order(actual) if t not in expected]
    mismatches: list[dict[str, object]] = []

    if rule == "strict":
        passed = expected == actual
        if not passed:
            for i, (exp, act) in enumerate(zip(expected, actual)):
                if exp != act:
                    mismatches.append({"index": i, "expected": exp, "actual": act})
    elif rule == "unordered":
        passed = sorted(expected) == sorted(actual)
    elif rule == "subset":
        passed = not unexpected
    elif rule == "superset":
        passed = not missing

    return RuleOutcome(
        rule=rule,
        expected=expected,
        actual=actual,
        passed=passed,
        missing=missing,
        unexpected=unexpected,
        mismatches=mismatches,
    )
