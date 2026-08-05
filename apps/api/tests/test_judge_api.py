"""Judge API tests: result-level / process-level endpoints, persistence, errors."""

import json

from fastapi.testclient import TestClient

from skill_eval.app import create_app
from skill_eval.core.schema import Trace, Node
from skill_eval.judge.client import LLMError
from skill_eval.mock.generator import make_trace
from skill_eval.store.repository import Store

VALID_REPORT = json.dumps(
    {"score": 0.9, "verdict": "pass", "summary": "good", "findings": ["ok"]}
)


class FakeLLM:
    def __init__(self, content: str = VALID_REPORT) -> None:
        self.content = content

    def configured(self) -> bool:
        return True

    def complete(self, messages: list[dict]) -> str:
        return self.content


class BrokenLLM:
    def configured(self) -> bool:
        return False

    def complete(self, messages: list[dict]) -> str:
        raise LLMError("LLM provider not configured (SKILLEVAL_LLM_API_KEY)")


def client_with(llm: object) -> TestClient:
    return TestClient(create_app(store=Store.in_memory(), judge_client=llm))  # type: ignore[arg-type]


def _seed_trace_with_output(c: TestClient) -> str:
    trace = make_trace(tool_count=2)
    last = [n for n in trace.iter_nodes()][-1]
    last.output = "final: 3 files written"
    c.post("/api/ingest/push", json=trace.model_dump(mode="json"))
    return trace.id


class TestJudgeApi:
    def test_result_level_run_and_persist(self) -> None:
        c = client_with(FakeLLM())
        trace_id = _seed_trace_with_output(c)
        resp = c.post("/api/judge/result", json={"trace_id": trace_id})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["report"]["verdict"] == "pass"
        assert body["report"]["score"] == 0.9
        assert body["run_id"]

        runs = c.get("/api/eval-runs", params={"trace_id": trace_id}).json()
        assert runs["total"] == 1
        assert runs["items"][0]["rule"] == "llm-result"
        assert runs["items"][0]["result"] == "passed"

    def test_process_level_run_and_persist(self) -> None:
        c = client_with(FakeLLM())
        trace_id = _seed_trace_with_output(c)
        resp = c.post("/api/judge/process", json={"trace_id": trace_id})
        assert resp.status_code == 200
        runs = c.get("/api/eval-runs", params={"trace_id": trace_id}).json()
        assert runs["items"][0]["rule"] == "llm-process"

    def test_unknown_trace_404(self) -> None:
        resp = client_with(FakeLLM()).post("/api/judge/result", json={"trace_id": "nope"})
        assert resp.status_code == 404

    def test_no_final_output_400(self) -> None:
        c = client_with(FakeLLM())
        trace = make_trace(tool_count=2)  # no node outputs
        c.post("/api/ingest/push", json=trace.model_dump(mode="json"))
        resp = c.post("/api/judge/result", json={"trace_id": trace.id})
        assert resp.status_code == 400

    def test_unconfigured_provider_503(self) -> None:
        c = client_with(BrokenLLM())
        trace_id = _seed_trace_with_output(c)
        resp = c.post("/api/judge/result", json={"trace_id": trace_id})
        assert resp.status_code == 503

    def test_review_verdict_maps_to_review_result(self) -> None:
        c = client_with(FakeLLM(content=json.dumps(
            {"score": 0.5, "verdict": "review", "summary": "?", "findings": []}
        )))
        trace_id = _seed_trace_with_output(c)
        resp = c.post("/api/judge/result", json={"trace_id": trace_id})
        assert resp.json()["report"]["verdict"] == "review"
        runs = c.get("/api/eval-runs", params={"trace_id": trace_id}).json()
        assert runs["items"][0]["result"] == "review"
