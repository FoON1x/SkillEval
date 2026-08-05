"""Data API tests: traces / test-cases / eval-runs CRUD + ingest persistence."""

from fastapi.testclient import TestClient

from skill_eval.app import create_app
from skill_eval.mock.generator import make_trace
from skill_eval.store.repository import Store


def client() -> TestClient:
    return TestClient(create_app(store=Store.in_memory()))


def import_raw(client: TestClient, agent: str = "opencode") -> str:
    resp = client.post(
        "/api/ingest/import",
        json={
            "agent": agent,
            "raw": {
                "version": "0.1",
                "session_id": "s1",
                "skill_name": "demo-skill",
                "events": [
                    {"type": "session.start", "ts": "2026-08-04T10:00:00Z"},
                    {"type": "agent.start", "ts": "2026-08-04T10:00:01Z"},
                    {
                        "type": "tool.start",
                        "tool": "read_file",
                        "args": {"path": "/a"},
                        "ts": "2026-08-04T10:00:02Z",
                    },
                    {
                        "type": "tool.end",
                        "tool": "read_file",
                        "result": {"ok": True},
                        "ts": "2026-08-04T10:00:07Z",
                    },
                    {"type": "agent.end", "ts": "2026-08-04T10:00:08Z"},
                    {"type": "session.end", "ts": "2026-08-04T10:00:10Z"},
                ],
            },
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["trace"]["id"]


class TestTraceEndpoints:
    def test_import_persists(self) -> None:
        c = client()
        trace_id = import_raw(c)
        resp = c.get(f"/api/traces/{trace_id}")
        assert resp.status_code == 200
        assert resp.json()["agent"] == "opencode"
        assert resp.json()["skill_name"] == "demo-skill"

    def test_push_persists(self) -> None:
        c = client()
        trace = make_trace(tool_count=2)
        resp = c.post("/api/ingest/push", json=trace.model_dump(mode="json"))
        assert resp.status_code == 200
        got = c.get(f"/api/traces/{trace.id}")
        assert got.status_code == 200
        assert got.json()["id"] == trace.id

    def test_list_with_filters_and_pagination(self) -> None:
        c = client()
        for i in range(3):
            t = make_trace(tool_count=i + 1)
            t.id = f"t-{i}"
            t.skill_name = f"skill-{i}"
            c.post("/api/ingest/push", json=t.model_dump(mode="json"))

        resp = c.get("/api/traces", params={"limit": 2})
        body = resp.json()
        assert body["total"] == 3
        assert len(body["items"]) == 2

        resp = c.get("/api/traces", params={"skill_name": "skill-1"})
        assert resp.json()["total"] == 1

        resp = c.get("/api/traces", params={"agent": "opencode", "status": "completed"})
        assert resp.json()["total"] == 3

    def test_list_summary_shape(self) -> None:
        c = client()
        import_raw(c)
        item = c.get("/api/traces").json()["items"][0]
        for key in (
            "id",
            "agent",
            "skill_name",
            "session_id",
            "status",
            "started_at",
            "ended_at",
            "cost_usd",
            "total_tokens",
            "latency_ms",
            "created_at",
        ):
            assert key in item

    def test_get_missing_404(self) -> None:
        assert client().get("/api/traces/nope").status_code == 404

    def test_delete(self) -> None:
        c = client()
        trace_id = import_raw(c)
        assert c.delete(f"/api/traces/{trace_id}").status_code == 204
        assert c.get(f"/api/traces/{trace_id}").status_code == 404
        assert c.delete("/api/traces/nope").status_code == 404


class TestTestCaseEndpoints:
    def _create(self, c: TestClient, name: str = "demo") -> str:
        resp = c.post(
            "/api/test-cases",
            json={
                "name": name,
                "description": "d",
                "agent": "opencode",
                "rule": "strict",
                "input_context": {"task": "hello"},
                "expected": {"tools": ["read_file", "grep"]},
                "assertions": [{"code": "len(projection) >= 1", "label": "at least one"}],
            },
        )
        assert resp.status_code == 200, resp.text
        return resp.json()["id"]

    def test_crud(self) -> None:
        c = client()
        tc_id = self._create(c)
        got = c.get(f"/api/test-cases/{tc_id}").json()
        assert got["name"] == "demo"
        assert got["expected"]["tools"] == ["read_file", "grep"]

        upd = c.put(f"/api/test-cases/{tc_id}", json={"name": "renamed"})
        assert upd.status_code == 200
        assert upd.json()["name"] == "renamed"

        items = c.get("/api/test-cases", params={"rule": "strict"}).json()
        assert items["total"] == 1
        assert items["items"][0]["name"] == "renamed"

        assert c.delete(f"/api/test-cases/{tc_id}").status_code == 204
        assert c.get(f"/api/test-cases/{tc_id}").status_code == 404

    def test_invalid_rule_422(self) -> None:
        resp = client().post(
            "/api/test-cases",
            json={"name": "x", "agent": "opencode", "rule": "bogus"},
        )
        assert resp.status_code == 422

    def test_update_missing_404(self) -> None:
        assert client().put("/api/test-cases/nope", json={"name": "x"}).status_code == 404


class TestEvalRunEndpoints:
    def test_crud(self) -> None:
        c = client()
        trace_id = import_raw(c)
        tc_id = c.post(
            "/api/test-cases",
            json={"name": "c", "agent": "opencode", "rule": "subset"},
        ).json()["id"]

        resp = c.post(
            "/api/eval-runs",
            json={
                "test_case_id": tc_id,
                "trace_id": trace_id,
                "rule": "subset",
                "result": "passed",
                "score": 1.0,
                "details": {"diff": []},
            },
        )
        assert resp.status_code == 200, resp.text
        run_id = resp.json()["id"]

        items = c.get("/api/eval-runs", params={"trace_id": trace_id}).json()
        assert items["total"] == 1
        assert items["items"][0]["result"] == "passed"

        assert c.get(f"/api/eval-runs/{run_id}").status_code == 200
        assert c.delete(f"/api/eval-runs/{run_id}").status_code == 204

    def test_invalid_result_422(self) -> None:
        resp = client().post(
            "/api/eval-runs",
            json={
                "test_case_id": "a",
                "trace_id": "b",
                "rule": "strict",
                "result": "maybe",
            },
        )
        assert resp.status_code == 422

