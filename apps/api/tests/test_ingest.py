"""Ingest layer tests: adapter registry, opencode parser, skeletons and HTTP API.

NOTE: real per-agent formats are not yet confirmed (docs/SCHEMA.md §7).
The opencode raw format below is a documented v1 assumption until real samples land.
"""

import pytest
from fastapi.testclient import TestClient

from skill_eval.core.schema import NodeStatus, NodeType, Trace
from skill_eval.ingest.errors import ParseError
from skill_eval.ingest.registry import get_registry

OPENCODE_RAW: dict = {
    "version": "0.1",
    "session_id": "sess-1",
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
        {"type": "tool.start", "tool": "grep", "args": {"q": "x"}, "ts": "2026-08-04T10:00:08Z"},
        {"type": "tool.end", "tool": "grep", "result": {"ok": True}, "ts": "2026-08-04T10:00:12Z"},
        {"type": "agent.end", "ts": "2026-08-04T10:00:13Z"},
        {"type": "session.end", "ts": "2026-08-04T10:00:15Z"},
    ],
}


class TestRegistry:
    def test_known_agents_registered(self) -> None:
        reg = get_registry()
        for agent in ("opencode", "codex", "claude-code", "pi"):
            assert reg.get(agent) is not None

    def test_unknown_agent_raises(self) -> None:
        with pytest.raises(KeyError):
            get_registry().get("bogus-agent")


class TestOpencodeAdapter:
    def test_parses_basic_session(self) -> None:
        trace = get_registry().parse("opencode", OPENCODE_RAW)
        assert isinstance(trace, Trace)
        assert trace.agent == "opencode"
        assert trace.skill_name == "demo-skill"
        assert trace.session_id == "sess-1"
        assert trace.status == "completed"

    def test_tool_calls_in_order(self) -> None:
        trace = get_registry().parse("opencode", OPENCODE_RAW)
        assert trace.tool_names() == ["read_file", "grep"]

    def test_tree_shape(self) -> None:
        trace = get_registry().parse("opencode", OPENCODE_RAW)
        assert trace.root.type == NodeType.SKILL_START
        step = trace.root.children[0]
        assert step.type == NodeType.AGENT_STEP
        assert len(step.children) == 2
        assert all(c.type == NodeType.TOOL_CALL for c in step.children)
        assert trace.root.children[-1].type == NodeType.SKILL_END

    def test_unpaired_tool_start_marks_running(self) -> None:
        raw = dict(OPENCODE_RAW)
        raw["events"] = [
            e for e in raw["events"] if not (e["type"] == "tool.end" and e["tool"] == "grep")
        ]
        trace = get_registry().parse("opencode", raw)
        assert trace.status == "running"
        assert trace.tool_names() == ["read_file", "grep"]
        grep = trace.tool_names() and [
            n for n in trace.iter_nodes() if n.type == NodeType.TOOL_CALL and n.name == "grep"
        ][0]
        assert grep.status == NodeStatus.RUNNING

    def test_tool_end_without_start_raises(self) -> None:
        raw = dict(OPENCODE_RAW)
        raw["events"] = [
            e for e in raw["events"] if not (e["type"] == "tool.start" and e["tool"] == "grep")
        ]
        with pytest.raises(ParseError):
            get_registry().parse("opencode", raw)

    def test_missing_events_raises(self) -> None:
        with pytest.raises(ParseError):
            get_registry().parse("opencode", {"version": "0.1"})

    def test_unknown_event_type_ignored(self) -> None:
        raw = dict(OPENCODE_RAW)
        raw["events"] = [*raw["events"], {"type": "heartbeat", "ts": "2026-08-04T10:00:14Z"}]
        trace = get_registry().parse("opencode", raw)
        assert trace.status == "completed"

    def test_llm_events_build_llm_call_node(self) -> None:
        raw = dict(OPENCODE_RAW)
        raw["events"] = [
            *raw["events"][:4],
            {
                "type": "llm.start",
                "model": "claude-sonnet",
                "input_tokens": 100,
                "ts": "2026-08-04T10:00:05Z",
            },
            {
                "type": "llm.end",
                "output_tokens": 50,
                "cost_usd": 0.001,
                "latency_ms": 900,
                "ts": "2026-08-04T10:00:06Z",
            },
            *raw["events"][4:],
        ]
        trace = get_registry().parse("opencode", raw)
        llm_nodes = [n for n in trace.iter_nodes() if n.type == NodeType.LLM_CALL]
        assert len(llm_nodes) == 1
        assert llm_nodes[0].status == NodeStatus.COMPLETED
        assert llm_nodes[0].llm is not None
        assert llm_nodes[0].llm.model == "claude-sonnet"
        assert llm_nodes[0].llm.total_tokens == 150
        assert llm_nodes[0].llm.cost_usd == 0.001
        assert llm_nodes[0].llm.latency_ms == 900

    def test_llm_end_without_start_raises(self) -> None:
        raw = dict(OPENCODE_RAW)
        raw["events"] = [
            *raw["events"][:4],
            {"type": "llm.end", "output_tokens": 5, "ts": "2026-08-04T10:00:06Z"},
            *raw["events"][4:],
        ]
        with pytest.raises(ParseError):
            get_registry().parse("opencode", raw)


class TestSkeletonAdapters:
    @pytest.mark.parametrize("agent", ["codex", "claude-code", "pi"])
    def test_not_implemented(self, agent: str) -> None:
        with pytest.raises(ParseError, match="not implemented"):
            get_registry().parse(agent, {"anything": True})


class TestIngestApi:
    def _client(self) -> TestClient:
        from skill_eval.app import create_app
        from skill_eval.store.repository import Store

        return TestClient(create_app(store=Store.in_memory()))

    def test_import_ok(self) -> None:
        resp = self._client().post(
            "/api/ingest/import", json={"agent": "opencode", "raw": OPENCODE_RAW}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "parsed"
        assert body["trace"]["agent"] == "opencode"
        assert body["trace"]["skill_name"] == "demo-skill"

    def test_import_unknown_agent(self) -> None:
        resp = self._client().post(
            "/api/ingest/import", json={"agent": "nope", "raw": {}}
        )
        assert resp.status_code == 404
        assert "agent" in resp.json()["detail"]

    def test_import_malformed_raw(self) -> None:
        resp = self._client().post(
            "/api/ingest/import", json={"agent": "opencode", "raw": {"no": "events"}}
        )
        assert resp.status_code == 400
        assert "detail" in resp.json()

    def test_push_valid_trace(self) -> None:
        trace = Trace(
            id="push-1",
            agent="opencode",
            skill_name="s",
            root={
                "id": "r",
                "type": "skill_start",
                "name": "s",
                "children": [
                    {
                        "id": "t",
                        "type": "tool_call",
                        "name": "bash",
                        "tool": {"name": "bash", "args": {"cmd": "ls"}},
                    }
                ],
            },
        ).model_dump()
        resp = self._client().post("/api/ingest/push", json=trace)
        assert resp.status_code == 200
        assert resp.json() == {"accepted": True, "id": "push-1", "saved": True}

    def test_push_invalid_trace(self) -> None:
        resp = self._client().post("/api/ingest/push", json={"id": 1})
        assert resp.status_code == 422

    def test_import_endpoint_listed_in_openapi(self) -> None:
        schema = self._client().get("/openapi.json").json()
        assert "/api/ingest/import" in schema["paths"]
        assert "/api/ingest/push" in schema["paths"]
