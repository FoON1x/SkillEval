import shutil

import pytest
from fastapi.testclient import TestClient

from skill_eval.runner.base import RunContext, RunnerUnavailableError
from skill_eval.runner.opencode import OpencodeRunner
from skill_eval.runner.registry import get_runner_registry


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
            OpencodeRunner().run(RunContext(task="hello"))

    def test_context_defaults(self) -> None:
        ctx = RunContext(task="hi")
        assert ctx.session_id is None
        assert ctx.cwd is None
        assert ctx.extra == {}


class TestRunnerApi:
    def _client(self) -> TestClient:
        from skill_eval.app import create_app

        return TestClient(create_app())

    def test_unknown_agent_404(self) -> None:
        resp = self._client().post("/api/runner/run", json={"agent": "nope", "task": "x"})
        assert resp.status_code == 404

    def test_cli_missing_503(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(shutil, "which", lambda _: None)
        resp = self._client().post("/api/runner/run", json={"agent": "opencode", "task": "x"})
        assert resp.status_code == 503

    def test_cli_present_501_wiring_pending(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(shutil, "which", lambda _: "opencode")
        resp = self._client().post("/api/runner/run", json={"agent": "opencode", "task": "x"})
        assert resp.status_code == 501
