"""Store layer tests: Trace / TestCase / EvalRun persistence (in-memory SQLite)."""

import pytest

from skill_eval.mock.generator import make_trace
from skill_eval.store.dto import Assertion, EvalRunCreate, ExpectedPath, TestCaseCreate
from skill_eval.store.repository import Store, record_to_trace


@pytest.fixture()
def store() -> Store:
    return Store.in_memory()


@pytest.fixture()
def saved_trace(store: Store):
    trace = make_trace(kind="simple_ok", tool_count=3)
    store.save_trace(trace)
    return trace


class TestTraceStore:
    def test_save_and_get_roundtrip(self, store: Store, saved_trace) -> None:
        rec = store.get_trace(saved_trace.id)
        assert rec is not None
        restored = record_to_trace(rec)
        assert restored == saved_trace

    def test_upsert_no_duplicates(self, store: Store, saved_trace) -> None:
        store.save_trace(saved_trace)
        items, total = store.list_traces({})
        assert total == 1
        assert len(items) == 1

    def test_list_filters(self, store: Store) -> None:
        a = make_trace(agent="opencode", kind="simple_ok", tool_count=2)
        b = make_trace(agent="codex", kind="simple_ok", tool_count=2)
        store.save_trace(a)
        store.save_trace(b)

        items, total = store.list_traces({"agent": "opencode"})
        assert total == 1 and items[0].id == a.id

        err = make_trace(kind="error_mid", tool_count=1)
        store.save_trace(err)
        items, total = store.list_traces({"status": "error"})
        assert total == 1 and items[0].id == err.id

    def test_pagination(self, store: Store) -> None:
        for i in range(5):
            t = make_trace(tool_count=i + 1)
            t.id = f"t{i}"
            store.save_trace(t)
        items, total = store.list_traces({}, limit=2, offset=0)
        assert total == 5 and len(items) == 2
        items2, _ = store.list_traces({}, limit=2, offset=2)
        assert len(items2) == 2
        assert items[0].id != items2[0].id

    def test_delete(self, store: Store, saved_trace) -> None:
        assert store.delete_trace(saved_trace.id) is True
        assert store.get_trace(saved_trace.id) is None
        assert store.delete_trace(saved_trace.id) is False


class TestTestCaseStore:
    def test_crud(self, store: Store) -> None:
        tc = TestCaseCreate(
            name="demo",
            description="demo case",
            agent="opencode",
            rule="strict",
            input_context={"task": "hello"},
            expected=ExpectedPath(tools=["read_file", "grep"]),
            assertions=[Assertion(code="len(projection) >= 1", label="at least one tool")],
        )
        saved = store.save_test_case(tc)
        assert saved.id
        fetched = store.get_test_case(saved.id)
        assert fetched is not None and fetched.name == "demo"
        assert fetched.expected.tools == ["read_file", "grep"]

        items, total = store.list_test_cases({"agent": "opencode"})
        assert total == 1

        assert store.delete_test_case(saved.id) is True
        assert store.get_test_case(saved.id) is None

    def test_rule_filter(self, store: Store) -> None:
        for rule in ("strict", "unordered"):
            store.save_test_case(TestCaseCreate(name=f"c-{rule}", agent="opencode", rule=rule))
        items, total = store.list_test_cases({"rule": "strict"})
        assert total == 1


class TestEvalRunStore:
    def test_crud(self, store: Store, saved_trace) -> None:
        tc = store.save_test_case(
            TestCaseCreate(name="c", agent="opencode", rule="subset")
        )
        run = store.save_eval_run(
            EvalRunCreate(
                test_case_id=tc.id,
                trace_id=saved_trace.id,
                rule="subset",
                result="passed",
                score=1.0,
                details={"diff": []},
            )
        )
        assert run.id
        fetched = store.get_eval_run(run.id)
        assert fetched is not None and fetched.result == "passed"

        items, total = store.list_eval_runs({"trace_id": saved_trace.id})
        assert total == 1

        assert store.delete_eval_run(run.id) is True


class TestTraceSummary:
    def test_summary_fields(self, store: Store, saved_trace) -> None:
        items, _ = store.list_traces({})
        s = items[0]
        assert s.id == saved_trace.id
        assert s.agent == "opencode"
        assert s.skill_name == "demo-skill"
        assert s.status == "completed"
        assert s.cost_usd is not None
        assert s.total_tokens is not None
