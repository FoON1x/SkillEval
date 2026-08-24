"""Runner tests: registry, opencode run_stream (subprocess + export), and HTTP API.

Subprocess and `opencode export` are monkeypatched so tests run without the CLI.
"""

import json
import shutil
import subprocess

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
        self._stdout = iter(lines)
        self._returncode = returncode
        self.killed = False

    @property
    def stdout(self):
        return self._stdout

    def wait(self, timeout: float | None = None) -> int:
        return self._returncode

    def kill(self) -> None:
        self.killed = True
        self._returncode = -9

    def terminate(self) -> None:
        self.killed = True


class _StubOut:
    def __init__(self, stdout: str = "", returncode: int = 0) -> None:
        self.stdout = stdout
        self.returncode = returncode


class _SlowFakeProc(_FakeProc):
    """A proc whose stdout never ends — simulates an ever-streaming runaway process."""

    def __init__(self, lines: list[str]) -> None:
        super().__init__(lines)
        import itertools
        self._slow = itertools.chain(lines, itertools.repeat(None))

    @property
    def stdout(self):
        return self._slow


class _FakeProcTimeout(_FakeProc):
    """A proc whose wait() raises TimeoutExpired (legacy post-stream timeout path)."""

    def __init__(self, lines: list[str]) -> None:
        super().__init__(lines)

    def wait(self, timeout: float | None = None) -> int:
        raise subprocess.TimeoutExpired(cmd="opencode", timeout=timeout or 0)


class _BlockingFakeProc(_FakeProc):
    """A proc that streams lines then blocks on the next read until kill() unblocks it."""

    def __init__(self, lines: list[str]) -> None:
        super().__init__(lines)
        import threading
        self._kill = threading.Event()

        class _Stdout:
            def __init__(self, owner: "_BlockingFakeProc") -> None:
                self._owner = owner
                self._idx = 0

            def __iter__(self):
                return self

            def __next__(self):
                if self._idx < len(lines):
                    line = lines[self._idx]
                    self._idx += 1
                    return line
                self._owner._kill.wait(timeout=30)
                raise StopIteration

        self._stdout = _Stdout(self)

    @property
    def stdout(self):
        return self._stdout

    def kill(self) -> None:
        self.killed = True
        self._kill.set()
        self._returncode = -9

    def terminate(self) -> None:
        self.kill()


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

    def test_run_stream_timeout_kills_proc_and_marks_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        proc = _FakeProcTimeout(JSONL_LINES)
        monkeypatch.setattr(shutil, "which", lambda b: "/fake/opencode")
        monkeypatch.setattr("skill_eval.runner.opencode.subprocess.Popen", lambda *a, **kw: proc)
        monkeypatch.setattr("skill_eval.runner.opencode._run_export", lambda sid: None)
        ctx = RunContext(task="hang", timeout=1)
        trace = OpencodeRunner().run_stream(ctx, emit=lambda c: None)
        assert trace.status == RunState.ERROR
        assert trace.error is not None
        assert trace.error.kind == "timeout"
        assert proc.killed is True

    def test_run_stream_watchdog_kills_ever_streaming_proc(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        proc = _BlockingFakeProc(JSONL_LINES)
        monkeypatch.setattr(shutil, "which", lambda b: "/fake/opencode")
        monkeypatch.setattr("skill_eval.runner.opencode.subprocess.Popen", lambda *a, **kw: proc)
        monkeypatch.setattr("skill_eval.runner.opencode._run_export", lambda sid: None)
        ctx = RunContext(task="runaway", timeout=1)
        trace = OpencodeRunner().run_stream(ctx, emit=lambda c: None)
        assert trace.status == RunState.ERROR
        assert proc.killed is True

    def test_run_stream_unparseable_jsonl_emits_warning(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        lines = [JSONL_LINES[0], "{not valid json", JSONL_LINES[1], JSONL_LINES[2]]
        monkeypatch.setattr(shutil, "which", lambda b: "/fake/opencode")
        monkeypatch.setattr(
            "skill_eval.runner.opencode.subprocess.Popen",
            lambda *a, **kw: _FakeProc(lines),
        )
        monkeypatch.setattr("skill_eval.runner.opencode._run_export", lambda sid: None)
        emitted: list[dict] = []
        trace = OpencodeRunner().run_stream(RunContext(task="x"), emit=emitted.append)
        assert any(e.get("node_type") == "warning" for e in emitted)
        assert trace.tool_names() == ["bash"]

    def test_run_stream_forwards_model_flag_into_cmd(self, monkeypatch: pytest.MonkeyPatch):
        captured: list[list[str]] = []

        class _CmdCaptureProc(_FakeProc):
            def __init__(self, lines: list[str]) -> None:
                super().__init__(lines)

        def _capture_popen(cmd, *a, **kw):
            captured.append(cmd)
            return _CmdCaptureProc(JSONL_LINES)

        monkeypatch.setattr(shutil, "which", lambda b: "/fake/opencode")
        monkeypatch.setattr("skill_eval.runner.opencode.subprocess.Popen", _capture_popen)
        monkeypatch.setattr("skill_eval.runner.opencode._run_export", lambda sid: EXPORT_JSON["info"])
        runner = OpencodeRunner()
        ctx = RunContext(task="hi", model="opencode-go/glm-5.2")
        runner.run_stream(ctx, emit=lambda _c: None)
        assert "--model" in captured[0]
        assert "opencode-go/glm-5.2" in captured[0]


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


class TestRunnerStreamApi:
    def _client(self) -> TestClient:
        from skill_eval.app import create_app
        from skill_eval.store.repository import Store

        return TestClient(create_app(store=Store.in_memory()))

    def _patch_runner(self, monkeypatch: pytest.MonkeyPatch, trace_id: str = "tr-1") -> None:
        from skill_eval.core.schema import NodeType, RunState, Trace, Node
        from skill_eval.runner.base import RunContext

        canned_trace = Trace(
            id=trace_id, agent="opencode", skill_name="s", status=RunState.COMPLETED,
            root=Node(id="r", type=NodeType.SKILL_START, name="s"),
        )

        def fake_run_stream(self, ctx: RunContext, emit) -> Trace:
            emit({"node_type": "agent_step", "status": "running"})
            emit({"node_type": "tool_call", "status": "completed", "name": "bash"})
            return canned_trace

        monkeypatch.setattr(shutil, "which", lambda b: "/fake/opencode")
        monkeypatch.setattr(
            "skill_eval.runner.opencode.OpencodeRunner.run_stream", fake_run_stream
        )

    def test_stream_emits_events_then_done(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._patch_runner(monkeypatch)
        resp = self._client().post(
            "/api/runner/run/stream",
            json={"agent": "opencode", "task": "hi", "skill_name": "s", "cwd": "C:/tmp"},
        )
        assert resp.status_code == 200
        text = resp.text
        assert 'data: {"type": "event"' in text
        assert "agent_step" in text
        assert "bash" in text
        assert 'data: {"type": "done", "trace_id": "tr-1"}' in text

    def test_stream_persists_trace(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._patch_runner(monkeypatch, trace_id="tr-persist")
        c = self._client()
        c.post("/api/runner/run/stream", json={"agent": "opencode", "task": "hi"})
        got = c.get("/api/traces/tr-persist")
        assert got.status_code == 200
        assert got.json()["id"] == "tr-persist"

    def test_stream_unknown_agent_404(self) -> None:
        resp = self._client().post(
            "/api/runner/run/stream", json={"agent": "nope", "task": "x"}
        )
        assert resp.status_code == 404

    def test_stream_cli_missing_503(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(shutil, "which", lambda _: None)
        resp = self._client().post(
            "/api/runner/run/stream", json={"agent": "opencode", "task": "x"}
        )
        assert resp.status_code == 503


class TestSkillsApi:
    def _client(self) -> TestClient:
        from skill_eval.app import create_app
        from skill_eval.store.repository import Store

        return TestClient(create_app(store=Store.in_memory()))

    def test_lists_skills_from_dirs(self, monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
        skills_dir = tmp_path / "skills"
        for name, desc in [("xlsx", "spreadsheet skill"), ("pdf", "pdf skill")]:
            d = skills_dir / name
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text(
                f'---\nname: {name}\ndescription: "{desc}"\n---\nbody\n', encoding="utf-8"
            )
        monkeypatch.setattr(
            "skill_eval.runner.skills.default_skill_dirs", lambda: [skills_dir]
        )
        resp = self._client().get("/api/runner/skills")
        assert resp.status_code == 200
        names = [s["name"] for s in resp.json()["skills"]]
        assert "xlsx" in names and "pdf" in names
        xlsx = [s for s in resp.json()["skills"] if s["name"] == "xlsx"][0]
        assert xlsx["description"] == "spreadsheet skill"

    def test_skills_handles_missing_dir(self, monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
        monkeypatch.setattr(
            "skill_eval.runner.skills.default_skill_dirs",
            lambda: [tmp_path / "nonexistent"],
        )
        resp = self._client().get("/api/runner/skills")
        assert resp.status_code == 200
        assert resp.json()["skills"] == []


class TestModelsApi:
    def _client(self) -> TestClient:
        from skill_eval.app import create_app
        from skill_eval.store.repository import Store

        return TestClient(create_app(store=Store.in_memory()))

    def test_lists_models_from_cli(self, monkeypatch: pytest.MonkeyPatch) -> None:
        sample = "opencode-go/glm-5.2\nanthropic/claude-opus-4-6\n"
        import skill_eval.runner.models as m

        monkeypatch.setattr(shutil, "which", lambda b: "/fake/opencode")
        monkeypatch.setattr(m.subprocess, "run", lambda *a, **kw: _StubOut(stdout=sample))
        from skill_eval.runner.models import list_models

        out = list_models()
        assert out[0]["provider"] == "opencode-go"
        assert out[0]["model"] == "glm-5.2"
        assert out[0]["id"] == "opencode-go/glm-5.2"
        assert out[1]["provider"] == "anthropic"

    def test_models_empty_when_cli_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(shutil, "which", lambda b: None)
        from skill_eval.runner.models import list_models

        assert list_models() == []

    def test_models_empty_when_cli_times_out(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import skill_eval.runner.models as m

        monkeypatch.setattr(shutil, "which", lambda b: "/fake/opencode")

        def _timeout(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="opencode", timeout=30)

        monkeypatch.setattr(m.subprocess, "run", _timeout)
        from skill_eval.runner.models import list_models

        assert list_models() == []

    def test_models_endpoint(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import skill_eval.runner.models as m

        monkeypatch.setattr(shutil, "which", lambda b: "/fake/opencode")
        monkeypatch.setattr(m.subprocess, "run", lambda *a, **kw: _StubOut(stdout="opencode-go/glm-5.2\n"))
        r = self._client().get("/api/runner/models")
        assert r.status_code == 200
        body = r.json()
        assert body["models"][0]["id"] == "opencode-go/glm-5.2"


class TestModelsParsing:
    def test_parses_clean_model_lines(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import skill_eval.runner.models as m

        sample = "opencode-go/glm-5.2\nanthropic/claude-opus-4-6\n"
        monkeypatch.setattr(shutil, "which", lambda b: "/fake/opencode")
        monkeypatch.setattr(m.subprocess, "run", lambda *a, **kw: _StubOut(stdout=sample))
        out = m.list_models()
        assert [x["id"] for x in out] == [
            "opencode-go/glm-5.2", "anthropic/claude-opus-4-6",
        ]
        assert [x["provider"] for x in out] == ["opencode-go", "anthropic"]
        assert all(x["context_window"] is None for x in out)
        assert all(x["input_cost"] is None for x in out)
        assert all(x["output_cost"] is None for x in out)

    def test_rejects_verbose_json_block_garbage(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import skill_eval.runner.models as m

        sample = (
            "opencode-go/glm-5.2\n"
            '{\n'
            '  "id": "opencode-go/glm-5.2",\n'
            '  "providerID": "opencode-go",\n'
            '  "name": "GLM-5.2",\n'
            '  "inputCost": 0.1,\n'
            '  "outputCost": 0.2\n'
            '}\n'
            "anthropic/claude-opus-4-6\n"
            '{"id": "nested/other", "name": "other"}\n'
        )
        monkeypatch.setattr(shutil, "which", lambda b: "/fake/opencode")
        monkeypatch.setattr(m.subprocess, "run", lambda *a, **kw: _StubOut(stdout=sample))
        out = m.list_models()
        assert [x["id"] for x in out] == [
            "opencode-go/glm-5.2", "anthropic/claude-opus-4-6",
        ]

    def test_build_cmd_windows_cmd_shim(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import skill_eval.runner.models as m

        monkeypatch.setattr(
            shutil, "which",
            lambda b: "C:\\Users\\eric3\\AppData\\Roaming\\npm\\opencode.CMD",
        )
        monkeypatch.setattr(m.os, "name", "nt")
        assert m._build_cmd() == ["cmd", "/c", "opencode", "models"]

    def test_build_cmd_windows_non_cmd_plain(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import skill_eval.runner.models as m

        monkeypatch.setattr(shutil, "which", lambda b: "C:\\bin\\opencode.exe")
        monkeypatch.setattr(m.os, "name", "nt")
        assert m._build_cmd() == ["opencode", "models"]

    def test_build_cmd_posix_plain(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import skill_eval.runner.models as m

        monkeypatch.setattr(shutil, "which", lambda b: "/usr/bin/opencode")
        monkeypatch.setattr(m.os, "name", "posix")
        assert m._build_cmd() == ["opencode", "models"]

    def test_models_empty_when_returncode_nonzero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import skill_eval.runner.models as m

        monkeypatch.setattr(shutil, "which", lambda b: "/fake/opencode")
        monkeypatch.setattr(
            m.subprocess, "run",
            lambda *a, **kw: _StubOut(stdout="opencode-go/glm-5.2\n", returncode=1),
        )
        assert m.list_models() == []

    def test_models_empty_when_oserror(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import skill_eval.runner.models as m

        monkeypatch.setattr(shutil, "which", lambda b: "/fake/opencode")

        def _raise(*args, **kwargs):
            raise OSError("boom")

        monkeypatch.setattr(m.subprocess, "run", _raise)
        assert m.list_models() == []
