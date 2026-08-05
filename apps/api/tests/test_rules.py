"""Rule evaluator tests: strict / unordered / subset / superset."""

import pytest

from skill_eval.eval.rules import RuleOutcome, evaluate_rule


class TestStrict:
    def test_exact_sequence_passes(self) -> None:
        out = evaluate_rule("strict", ["a", "b", "c"], ["a", "b", "c"])
        assert out.passed and out.mismatches == []

    def test_order_change_fails(self) -> None:
        out = evaluate_rule("strict", ["a", "b", "c"], ["a", "c", "b"])
        assert not out.passed
        assert len(out.mismatches) > 0
        assert out.mismatches[0]["expected"] == "b"

    def test_missing_tool_fails(self) -> None:
        out = evaluate_rule("strict", ["a", "b"], ["a"])
        assert not out.passed
        assert out.missing == ["b"]

    def test_extra_tool_fails(self) -> None:
        out = evaluate_rule("strict", ["a"], ["a", "x"])
        assert not out.passed
        assert out.unexpected == ["x"]

    def test_duplicate_sequence_passes(self) -> None:
        assert evaluate_rule("strict", ["a", "a"], ["a", "a"]).passed


class TestUnordered:
    def test_same_multiset_any_order_passes(self) -> None:
        assert evaluate_rule("unordered", ["a", "b"], ["b", "a"]).passed

    def test_duplicates_respected(self) -> None:
        assert not evaluate_rule("unordered", ["a", "a"], ["a"]).passed

    def test_missing_fails(self) -> None:
        out = evaluate_rule("unordered", ["a", "b"], ["a"])
        assert not out.passed and out.missing == ["b"]

    def test_extra_fails(self) -> None:
        out = evaluate_rule("unordered", ["a"], ["a", "x"])
        assert not out.passed and out.unexpected == ["x"]


class TestSubset:
    def test_exact_set_passes(self) -> None:
        assert evaluate_rule("subset", ["a", "b"], ["b", "a"]).passed

    def test_strict_subset_passes(self) -> None:
        assert evaluate_rule("subset", ["a", "b", "c"], ["a", "b"]).passed

    def test_extra_tool_fails(self) -> None:
        out = evaluate_rule("subset", ["a"], ["a", "x"])
        assert not out.passed and out.unexpected == ["x"]


class TestSuperset:
    def test_exact_set_passes(self) -> None:
        assert evaluate_rule("superset", ["a", "b"], ["b", "a"]).passed

    def test_covers_required_passes(self) -> None:
        assert evaluate_rule("superset", ["a", "b"], ["a", "b", "c"]).passed

    def test_missing_required_fails(self) -> None:
        out = evaluate_rule("superset", ["a", "b"], ["a"])
        assert not out.passed and out.missing == ["b"]


class TestMisc:
    def test_unknown_rule_raises(self) -> None:
        with pytest.raises(ValueError):
            evaluate_rule("bogus", [], [])  # type: ignore[arg-type]

    def test_outcome_fields(self) -> None:
        out = evaluate_rule("strict", ["a"], ["b"])
        assert isinstance(out, RuleOutcome)
        assert out.expected == ["a"] and out.actual == ["b"]

    def test_empty_expected_passes_for_subset(self) -> None:
        assert evaluate_rule("subset", [], []).passed
