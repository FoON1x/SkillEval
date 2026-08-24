"""Ingest layer tests: adapter registry, opencode parser (real JSONL), skeletons and HTTP API.

The opencode raw format mirrors `opencode run --format json` JSONL output (v1.18+).
Each event is a parsed JSONL line: {"type","timestamp","sessionID","part"}.
"""

import json
import warnings

import pytest
from fastapi.testclient import TestClient

from skill_eval.core.schema import NodeStatus, NodeType, RunState, Trace
from skill_eval.ingest.errors import ParseError, ParseWarning
from skill_eval.ingest.registry import get_registry

SID = "ses_fd0e2fbe7ffea507EbQjAfZ7Ef"

STEP_START_1 = {
    "type": "step_start", "timestamp": 1787496829616, "sessionID": SID,
    "part": {"id": "prt1", "messageID": "msg1", "sessionID": SID, "type": "step-start"},
}
TOOL_USE_BASH = {
    "type": "tool_use", "timestamp": 1787496843497, "sessionID": SID,
    "part": {
        "type": "tool", "tool": "bash", "callID": "call_1",
        "state": {
            "status": "completed", "input": {"command": "ls"},
            "output": "file_a.txt\nfile_b.txt",
            "metadata": {"output": "file_a.txt\nfile_b.txt", "exit": 0, "truncated": False},
            "title": "ls", "time": {"start": 1787496843223, "end": 1787496843469},
        },
        "id": "prt2", "sessionID": SID, "messageID": "msg1",
    },
}
STEP_FINISH_1 = {
    "type": "step_finish", "timestamp": 1787496843497, "sessionID": SID,
    "part": {
        "id": "prt3", "reason": "tool-calls", "messageID": "msg1",
        "sessionID": SID, "type": "step-finish",
        "tokens": {"total": 12830, "input": 4420, "output": 11, "reasoning": 975,
                   "cache": {"write": 0, "read": 7424}},
        "cost": 0.01245664,
    },
}
STEP_START_2 = {
    "type": "step_start", "timestamp": 1787496845390, "sessionID": SID,
    "part": {"id": "prt4", "messageID": "msg2", "sessionID": SID, "type": "step-start"},
}
TEXT_REPLY = {
    "type": "text", "timestamp": 1787496846198, "sessionID": SID,
    "part": {
        "id": "prt5", "messageID": "msg2", "sessionID": SID, "type": "text",
        "text": "The current directory is empty.",
        "time": {"start": 1787496845582, "end": 1787496846185},
    },
}
STEP_FINISH_2 = {
    "type": "step_finish", "timestamp": 1787496846198, "sessionID": SID,
    "part": {
        "id": "prt6", "reason": "stop", "messageID": "msg2",
        "sessionID": SID, "type": "step-finish",
        "tokens": {"total": 12874, "input": 1061, "output": 24, "reasoning": 13,
                   "cache": {"write": 0, "read": 11776}},
        "cost": 0.00470996,
    },
}

EVENTS = [STEP_START_1, TOOL_USE_BASH, STEP_FINISH_1, STEP_START_2, TEXT_REPLY, STEP_FINISH_2]

OPENCODE_RAW: dict = {
    "session_id": SID,
    "skill_name": "demo-skill",
    "events": EVENTS,
}

EXPORT_INFO: dict = {
    "id": SID, "title": "ls and reply", "agent": "build",
    "model": {"id": "glm-5.2", "providerID": "opencode-go", "variant": "default"},
    "version": "1.18.21", "cost": 0.0171666,
    "tokens": {"input": 5481, "output": 35, "reasoning": 988,
               "cache": {"read": 19200, "write": 0}},
    "time": {"created": 1787496828749, "updated": 1787496847431},
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
        assert trace.session_id == SID
        assert trace.status == RunState.COMPLETED

    def test_tool_calls_in_order(self) -> None:
        trace = get_registry().parse("opencode", OPENCODE_RAW)
        assert trace.tool_names() == ["bash"]

    def test_tree_shape(self) -> None:
        trace = get_registry().parse("opencode", OPENCODE_RAW)
        assert trace.root.type == NodeType.SKILL_START
        assert trace.root.name == "demo-skill"
        steps = [c for c in trace.root.children if c.type == NodeType.AGENT_STEP]
        assert len(steps) == 2
        assert steps[0].children[0].type == NodeType.TOOL_CALL
        assert steps[1].children[0].type == NodeType.MESSAGE
        assert trace.root.children[-1].type == NodeType.SKILL_END

    def test_tool_node_has_args_result_and_timing(self) -> None:
        trace = get_registry().parse("opencode", OPENCODE_RAW)
        tool = [n for n in trace.iter_nodes() if n.type == NodeType.TOOL_CALL][0]
        assert tool.status == NodeStatus.COMPLETED
        assert tool.tool is not None
        assert tool.tool.name == "bash"
        assert tool.tool.args == {"command": "ls"}
        assert tool.tool.result == "file_a.txt\nfile_b.txt"
        assert tool.output == "file_a.txt\nfile_b.txt"
        assert tool.duration_ms == 246

    def test_failed_tool_marks_error(self) -> None:
        raw = {
            "session_id": SID, "skill_name": "s",
            "events": [
                STEP_START_1,
                {
                    "type": "tool_use", "timestamp": 1787496843497, "sessionID": SID,
                    "part": {
                        "type": "tool", "tool": "bash", "callID": "call_e",
                        "state": {
                            "status": "completed", "input": {"command": "rm x"},
                            "output": "path not found",
                            "metadata": {"output": "path not found", "exit": 1, "truncated": False},
                            "title": "rm x", "time": {"start": 1787496843223, "end": 1787496843265},
                        },
                        "id": "prt_e", "sessionID": SID, "messageID": "msg1",
                    },
                },
                STEP_FINISH_1, STEP_FINISH_2,
            ],
        }
        trace = get_registry().parse("opencode", raw)
        tool = [n for n in trace.iter_nodes() if n.type == NodeType.TOOL_CALL][0]
        assert tool.status == NodeStatus.ERROR
        assert tool.error is not None
        assert "exit" in (tool.error.kind or "")

    def test_message_node_captures_text(self) -> None:
        trace = get_registry().parse("opencode", OPENCODE_RAW)
        msgs = [n for n in trace.iter_nodes() if n.type == NodeType.MESSAGE]
        assert len(msgs) == 1
        assert msgs[0].output == "The current directory is empty."

    def test_missing_events_raises(self) -> None:
        with pytest.raises(ParseError):
            get_registry().parse("opencode", {"session_id": "x"})

    def test_unknown_event_type_ignored(self) -> None:
        raw = dict(OPENCODE_RAW)
        raw["events"] = [*EVENTS, {"type": "heartbeat", "timestamp": 1, "sessionID": SID, "part": {}}]
        with warnings.catch_warnings():
            warnings.simplefilter("error", ParseWarning)
            with pytest.warns(ParseWarning):
                trace = get_registry().parse("opencode", raw)
        assert trace.status == RunState.COMPLETED

    def test_session_id_inferred_from_first_event(self) -> None:
        raw = {"skill_name": "s", "events": EVENTS}
        trace = get_registry().parse("opencode", raw)
        assert trace.session_id == SID


class TestOpencodeTraceBuilder:
    def test_feed_returns_canonical_event_and_finalize_builds_trace(self) -> None:
        from skill_eval.ingest.adapters.opencode import OpencodeImporter

        builder = OpencodeImporter().new_builder(skill_name="demo-skill")
        canonical_events = []
        for ev in EVENTS:
            canon = builder.feed(ev)
            if canon is not None:
                canonical_events.append(canon)
        trace = builder.finalize(export_info=EXPORT_INFO)

        assert isinstance(trace, Trace)
        assert trace.session_id == SID
        assert trace.status == RunState.COMPLETED
        assert trace.tool_names() == ["bash"]
        assert trace.usage is not None
        assert trace.usage.cost_usd == pytest.approx(0.0171666)
        assert trace.usage.input_tokens == 5481
        assert trace.usage.output_tokens == 35
        assert "glm-5.2" in trace.usage.models
        assert trace.skill_name == "demo-skill"

    def test_feed_step_start_returns_node_event(self) -> None:
        from skill_eval.ingest.adapters.opencode import OpencodeImporter

        builder = OpencodeImporter().new_builder(skill_name="s")
        canon = builder.feed(STEP_START_1)
        assert canon is not None
        assert canon["node_type"] == "agent_step"
        assert canon["status"] == "running"

    def test_finalize_without_export_still_builds_trace(self) -> None:
        from skill_eval.ingest.adapters.opencode import OpencodeImporter

        builder = OpencodeImporter().new_builder(skill_name="s")
        for ev in EVENTS:
            builder.feed(ev)
        trace = builder.finalize()
        assert trace.usage is None or trace.usage.cost_usd is None
        assert trace.tool_names() == ["bash"]

    def test_finalize_with_null_token_fields_does_not_crash(self) -> None:
        from skill_eval.ingest.adapters.opencode import OpencodeImporter

        builder = OpencodeImporter().new_builder(skill_name="s")
        for ev in EVENTS:
            builder.feed(ev)
        trace = builder.finalize(
            export_info={
                "id": SID, "cost": 0.001,
                "tokens": {"input": None, "output": None, "reasoning": None,
                           "cache": {"read": None, "write": None}},
                "model": {"id": "glm-5.2", "providerID": "opencode-go"},
            }
        )
        assert trace.usage is not None
        assert trace.usage.cost_usd == pytest.approx(0.001)
        assert trace.usage.total_tokens is None
        assert trace.usage.input_tokens is None
        assert trace.usage.models == ["glm-5.2"]

    def test_finalize_synthetic_step_for_tool_after_step_finish(self) -> None:
        from skill_eval.ingest.adapters.opencode import OpencodeImporter
        from skill_eval.core.schema import NodeType

        builder = OpencodeImporter().new_builder(skill_name="s")
        builder.feed(STEP_START_1)
        builder.feed(STEP_FINISH_1)
        builder.feed(TOOL_USE_BASH)
        trace = builder.finalize()
        steps = [c for c in trace.root.children if c.type == NodeType.AGENT_STEP]
        assert len(steps) == 2
        assert steps[1].children[0].type == NodeType.TOOL_CALL


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
        assert body["trace"]["session_id"] == SID

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
