"""Eval API tests: run evaluation, persistence, error paths."""

from fastapi.testclient import TestClient

from skill_eval.app import create_app
from skill_eval.mock.generator import make_trace
from skill_eval.store.repository import Store


def client() -> TestClient:
    return TestClient(create_app(store=Store.in_memory()))


def _seed(c: TestClient) -> tuple[str, str]:
    trace = make_trace(tool_count=2)
    c.post("/api/ingest/push", json=trace.model_dump(mode="json"))
    tc = c.post(
        "/api/test-cases",
        json={
            "name": "demo",
            "agent": "opencode",
            "rule": "strict",
            "expected": {"tools": trace.tool_names()},
            "assertions": [{"code": "len(projection) >= 1", "label": "at least one tool"}],
        },
    ).json()
    return tc["id"], trace.id


class TestEvalApi:
    def test_run_passes_and_persists(self) -> None:
        c = client()
        tc_id, trace_id = _seed(c)
        resp = c.post("/api/eval/run", json={"test_case_id": tc_id, "trace_id": trace_id})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["result"] == "passed"
        assert body["score"] == 1.0
        assert body["details"]["assertions"][0]["passed"] is True

        runs = c.get("/api/eval-runs", params={"trace_id": trace_id}).json()
        assert runs["total"] == 1
        assert runs["items"][0]["result"] == "passed"
        assert runs["items"][0]["id"] == body["run_id"]

    def test_run_fails_on_rule_mismatch(self) -> None:
        c = client()
        tc_id, trace_id = _seed(c)
        trace = make_trace(tool_count=2)
        resp = c.post(
            "/api/test-cases",
            json={
                "name": "bad",
                "agent": "opencode",
                "rule": "strict",
                "expected": {"tools": list(reversed(trace.tool_names()))},
            },
        ).json()
        body = c.post("/api/eval/run", json={"test_case_id": resp["id"], "trace_id": trace_id}).json()
        assert body["result"] == "failed"
        assert body["score"] < 1.0

    def test_unknown_test_case_404(self) -> None:
        c = client()
        _, trace_id = _seed(c)
        resp = c.post("/api/eval/run", json={"test_case_id": "nope", "trace_id": trace_id})
        assert resp.status_code == 404

    def test_unknown_trace_404(self) -> None:
        c = client()
        tc_id, _ = _seed(c)
        resp = c.post("/api/eval/run", json={"test_case_id": tc_id, "trace_id": "nope"})
        assert resp.status_code == 404

    def test_assertion_sandbox_error_persisted_as_failed(self) -> None:
        c = client()
        tc_id, trace_id = _seed(c)
        trace = make_trace(tool_count=2)
        tc = c.post(
            "/api/test-cases",
            json={
                "name": "boom",
                "agent": "opencode",
                "rule": "strict",
                "expected": {"tools": trace.tool_names()},
                "assertions": [{"code": "1/0"}],
            },
        ).json()
        body = c.post(
            "/api/eval/run", json={"test_case_id": tc["id"], "trace_id": trace_id}
        ).json()
        assert body["result"] == "failed"
        assert body["details"]["assertions"][0]["passed"] is False
