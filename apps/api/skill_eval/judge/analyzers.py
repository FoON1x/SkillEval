"""LLM-as-a-Judge analyzers: result-level and process-level, fixed JSON reports."""

import json
import re
from typing import Any, Literal

from pydantic import BaseModel

from skill_eval.core.schema import Trace
from skill_eval.judge.client import LLMClient

RESULT_SYSTEM_PROMPT = """\
You are an expert evaluator for AI agent skill outputs. Judge whether the final
output satisfies the task, considering correctness, completeness and quality.
Respond ONLY with a JSON object of this exact shape:
{"score": <float 0..1>, "verdict": "pass"|"fail"|"review", "summary": <str>, "findings": [<str>]}
Use verdict "review" when you cannot decide confidently."""

PROCESS_SYSTEM_PROMPT = """\
You are an expert evaluator for AI agent execution traces. Analyze the whole
process: whether the tool path was reasonable, efficient, error handling,
and whether the outcome matches the task. Respond ONLY with a JSON object of
this exact shape:
{"score": <float 0..1>, "verdict": "pass"|"fail"|"review", "summary": <str>, "findings": [<str>]}
Use verdict "review" when you cannot decide confidently."""


class JudgeReport(BaseModel):
    score: float = 0.0
    verdict: Literal["pass", "fail", "review"] = "review"
    summary: str = ""
    findings: list[str] = []
    raw: str | None = None


def _parse_report(content: str) -> JudgeReport:
    text = content.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        data = json.loads(text)
        return JudgeReport(
            score=float(data.get("score", 0.0)),
            verdict=data.get("verdict", "review"),
            summary=str(data.get("summary", "")),
            findings=[str(f) for f in data.get("findings", [])],
        )
    except (json.JSONDecodeError, TypeError, ValueError):
        return JudgeReport(verdict="review", raw=content)


def extract_final_output(trace: Trace) -> str | None:
    for node in reversed(list(trace.iter_nodes())):
        if node.output is not None:
            return node.output if isinstance(node.output, str) else json.dumps(node.output, ensure_ascii=False)
    return None


def _digest(trace: Trace) -> dict[str, Any]:
    tools = [
        {
            "name": n.tool.name if n.tool else n.name,
            "status": n.status.value,
            "summary": n.summary or n.name,
        }
        for n in trace.iter_nodes()
        if n.type.value == "tool_call"
    ]
    usage = trace.usage
    return {
        "skill": trace.skill_name,
        "status": trace.status.value,
        "tools": tools,
        "error": trace.error.model_dump() if trace.error else None,
        "usage": usage.model_dump() if usage else None,
        "root": {
            "name": trace.root.name,
            "status": trace.root.status.value,
            "summary": trace.root.summary,
        },
    }


class ResultJudge:
    """Result-level judgment: task input + final output only."""

    def __init__(self, client: LLMClient) -> None:
        self._client = client

    def judge(self, task_input: str, final_output: str) -> JudgeReport:
        messages = [
            {"role": "system", "content": RESULT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps({"task": task_input, "final_output": final_output}, ensure_ascii=False),
            },
        ]
        return _parse_report(self._client.complete(messages))


class ProcessAnalyzer:
    """Process-level analysis: full trace digest."""

    def __init__(self, client: LLMClient) -> None:
        self._client = client

    def analyze(self, trace: Trace) -> JudgeReport:
        messages = [
            {"role": "system", "content": PROCESS_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(_digest(trace), ensure_ascii=False),
            },
        ]
        return _parse_report(self._client.complete(messages))
