"""Runner tests: registry, opencode run_stream (subprocess + export), and HTTP API.

Subprocess and `opencode export` are monkeypatched so tests run without the CLI.
"""

import json
import shutil

import pytest
from fastapi.testclient import TestClient

from skill_eval.core.schema import RunState, Trace
from skill_eval.runner.base import RunContext, RunnerUnavailableError
from skill_eval.runner.opencode import OpencodeRunner
from skill_eval.runner.registry import get_runner_registry

SID = "ses_fd0e2fbe7ffea507EbQjAfZ7Ef"

JSONL_LINES = [
    json.dumps({
        "type": "step_start", "timestamp": 1787496829616, "sessionID": SID,
        "part": {"id": "p1", "messageID": "m1", "sessionID": SID, "type": "step-start"},
    }),
    json.dumps({
        "type": "tool_use", "timestamp": 1787496843497, "sessionID": SID,
        "part": {
            "type": "tool", "tool": "bash", "callID": "c1",
            "state": {"status": "completed", "input": {"command": "ls"},
                      "output": "a.txt", "metadata": {"exit": 0, "truncated": False},
                      "title": "ls", "time": {"start": 1787496843223, "end": 1787496843469}},
            "id": "p2", "sessionID": SID, "messageID": "m1",
        },
    }),
    json.dumps({
        "type": "step_finish", "timestamp": 1787496843497, "sessionID": SID,
        "part": {"id": "p3", "reason": "stop", "messageID": "m1", "sessionID": SID,
                 "type": "step-finish", "tokens": {"total": 100, "input": 80, "output": 20},
                 "cost": 0.001},
    }),
]

EXPORT_JSON = {
    "info": {
        "id": SID, "title": "test run", "agent": "build",
        "model": {"id": "glm-5.2", "providerID": "opencode-go", "variant": "default"},
        "version": "1.18.21", "cost": 0.001,
        "tokens": {"input": 80, "output": 20, "reasoning": 0,
                   "cache": {"read": 0, "write": 0}},
        "time": {"created": 1787496829616, "updated": 1787496843497},
    }
}


class _FakeProc:
    def __init__(self, lines: list[str], returncode: int = 0) -> None:
        self.stdout = iter(lines)
        self._returncode = returncode

    def wait(self, timeout: float | None = None) -> int:
        return self._returncode


def _patch_run(monkeypatch: pytest.MonkeyPatch, lines: list[str], returncode: int = 0) -> None:
    monkeypatch.setattr(shutil, "which", lambda b: "/fake/opencode")
    monkeypatch.setattr(
        "skill_eval.runner.opencode.subprocess.Popen",
        lambda *a, **kw: _FakeProc(lines, returncode),
    )
    monkeypatch.setattr(
        "skill_eval.runner.opencode._run_export", lambda sid: EXPORT_JSON["info"] if sid else None
    )


class TestRunnerRegistry:
    def test_opencode_registered(self) -> None:
        assert get_runner_registry().get("opencode") is not None

    def test_unknown_agent_raises(self) -> None:
        with pytest.raises(KeyError):
            get_runner_registry().get("bogus")


class TestOpencodeRunner:
    def test_unavailable_when_cli_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(shutil, "which", lambda _: None)
        assert not OpencodeRunner().available()
        with pytest.raises(RunnerUnavailableError):
            OpencodeRunner().run_stream(RunContext(task="hello"), emit=lambda c: None)

    def test_context_defaults(self) -> None:
        ctx = RunContext(task="hi")
        assert ctx.session_id is None
        assert ctx.cwd is None
        assert ctx.auto is True
        assert ctx.timeout == 300
        assert ctx.skill_name is None

    def test_run_stream_emits_events_and_returns_trace(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_run(monkeypatch, JSONL_LINES)
        emitted: list[dict] = []
        runner = OpencodeRunner()
        ctx = RunContext(task="list files", skill_name="demo-skill", auto=True)

        trace = runner.run_stream(ctx, emit=emitted.append)

        assert isinstance(trace, Trace)
        assert trace.agent == "opencode"
        assert trace.skill_name == "demo-skill"
        assert trace.session_id == SID
        assert trace.status == RunState.COMPLETED
        assert trace.tool_names() == ["bash"]
        assert trace.usage is not None
        assert trace.usage.cost_usd == pytest.approx(0.001)
        assert trace.usage.models == ["glm-5.2"]
        assert len(emitted) >= 2
        assert any(e.get("node_type") == "tool_call" for e in emitted)

    def test_run_stream_cli_failure_marks_error_status(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_run(monkeypatch, JSONL_LINES, returncode=2)
        runner = OpencodeRunner()
        ctx = RunContext(task="boom")
        trace = runner.run_stream(ctx, emit=lambda c: None)
        assert trace.status == RunState.ERROR
        assert trace.error is not None

    def test_run_stream_no_export_still_builds_trace(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(shutil, "which", lambda b: "/fake/opencode")
        monkeypatch.setattr(
            "skill_eval.runner.opencode.subprocess.Popen",
            lambda *a, **kw: _FakeProc(JSONL_LINES),
        )
        monkeypatch.setattr("skill_eval.runner.opencode._run_export", lambda sid: None)
        trace = OpencodeRunner().run_stream(RunContext(task="x"), emit=lambda c: None)
        assert trace.tool_names() == ["bash"]
        assert trace.usage is None or trace.usage.cost_usd is None


class TestRunnerApi:
    def _client(self) -> TestClient:
        from skill_eval.app import create_app
        from skill_eval.store.repository import Store

        return TestClient(create_app(store=Store.in_memory()))

    def test_unknown_agent_404(self) -> None:
        resp = self._client().post("/api/runner/run", json={"agent": "nope", "task": "x"})
        assert resp.status_code == 404

    def test_cli_missing_503(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(shutil, "which", lambda _: None)
        resp = self._client().post("/api/runner/run", json={"agent": "opencode", "task": "x"})
        assert resp.status_code == 503
