"""Analyzer tests: result-level and process-level LLM judging with fake clients."""

import json

from skill_eval.judge.analyzers import ProcessAnalyzer, ResultJudge, _parse_report
from skill_eval.judge.client import LLMClient
from skill_eval.mock.generator import make_trace


class FakeLLM:
    """Minimal fake of LLMClient interface."""

    def __init__(self, content: str) -> None:
        self.content = content
        self.messages: list[dict] = []

    def configured(self) -> bool:
        return True

    def complete(self, messages: list[dict]) -> str:
        self.messages = messages
        return self.content


VALID_REPORT = json.dumps(
    {
        "score": 0.85,
        "verdict": "pass",
        "summary": "well done",
        "findings": ["used right tools", "order ok"],
    }
)


class TestParseReport:
    def test_valid_json(self) -> None:
        report = _parse_report(VALID_REPORT)
        assert report.score == 0.85
        assert report.verdict == "pass"
        assert report.raw is None

    def test_invalid_json_falls_back_to_review(self) -> None:
        report = _parse_report("the output is fine")
        assert report.verdict == "review"
        assert report.score == 0.0
        assert report.raw == "the output is fine"

    def test_json_embedded_in_code_fence(self) -> None:
        report = _parse_report(f"```json\n{VALID_REPORT}\n```")
        assert report.verdict == "pass"


class TestResultJudge:
    def test_judge_sends_task_and_output(self) -> None:
        fake = FakeLLM(VALID_REPORT)
        ResultJudge(fake).judge(task_input="build a demo", final_output="done, 3 files")
        system_prompt = fake.messages[0]["content"]
        user_payload = json.loads(fake.messages[1]["content"])
        assert "task" in user_payload and "final_output" in user_payload
        assert "final output" in system_prompt.lower().replace("\n", " ")

    def test_judge_parses_report(self) -> None:
        fake = FakeLLM(VALID_REPORT)
        report = ResultJudge(fake).judge(task_input="x", final_output="y")
        assert report.verdict == "pass"


class TestProcessAnalyzer:
    def test_analyze_includes_trace_digest(self) -> None:
        fake = FakeLLM(VALID_REPORT)
        trace = make_trace(kind="simple_ok", tool_count=3)
        ProcessAnalyzer(fake).analyze(trace)
        user_payload = json.loads(fake.messages[1]["content"])
        assert "tools" in user_payload
        names = [t["name"] for t in user_payload["tools"]]
        assert names == trace.tool_names()

    def test_analyze_error_trace_flagged(self) -> None:
        fake = FakeLLM(VALID_REPORT)
        trace = make_trace(kind="error_mid", tool_count=2)
        ProcessAnalyzer(fake).analyze(trace)
        user_payload = json.loads(fake.messages[1]["content"])
        assert user_payload["status"] == "error"
        assert user_payload["error"] is not None


class TestTypes:
    def test_client_type_hint_compatible(self) -> None:
        # FakeLLM must be usable anywhere an LLMClient is expected at runtime
        assert isinstance(FakeLLM("{}").complete([{"role": "user", "content": "x"}]), str)
