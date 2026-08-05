"""Judge API: result-level and process-level LLM judging, persisted as eval runs."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from skill_eval.judge.analyzers import (
    JudgeReport,
    ProcessAnalyzer,
    ResultJudge,
    extract_final_output,
)
from skill_eval.judge.client import LLMClient, LLMError
from skill_eval.store.dto import EvalRunCreate
from skill_eval.store.repository import record_to_trace

router = APIRouter(prefix="/api/judge", tags=["judge"])


class JudgeRequest(BaseModel):
    trace_id: str


def _get_trace(request: Request, trace_id: str):
    record = request.app.state.store.get_trace(trace_id)
    if record is None:
        raise HTTPException(status_code=404, detail="trace not found")
    return record_to_trace(record)


def _report_to_run(report: JudgeReport) -> tuple[str, str, float, dict[str, Any]]:
    verdict_map = {"pass": "passed", "fail": "failed", "review": "review"}
    return (
        verdict_map[report.verdict],
        report.score,
        {"report": report.model_dump()},
    )


def _persist(
    request: Request,
    trace_id: str,
    rule: str,
    report: JudgeReport,
) -> str:
    result, score, details = _report_to_run(report)
    run = request.app.state.store.save_eval_run(
        EvalRunCreate(
            test_case_id="",
            trace_id=trace_id,
            rule=rule,  # type: ignore[arg-type]
            result=result,
            score=score,
            details=details,
        )
    )
    return run.id


@router.post("/result")
def judge_result(req: JudgeRequest, request: Request) -> dict[str, Any]:
    trace = _get_trace(request, req.trace_id)
    final_output = extract_final_output(trace)
    if final_output is None:
        raise HTTPException(status_code=400, detail="trace has no final output")
    task_input = trace.skill_name or trace.root.summary or trace.root.name

    client: LLMClient = request.app.state.judge_client
    try:
        report = ResultJudge(client).judge(task_input, final_output)
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    run_id = _persist(request, req.trace_id, "llm-result", report)
    return {"run_id": run_id, "report": report.model_dump()}


@router.post("/process")
def judge_process(req: JudgeRequest, request: Request) -> dict[str, Any]:
    trace = _get_trace(request, req.trace_id)
    client: LLMClient = request.app.state.judge_client
    try:
        report = ProcessAnalyzer(client).analyze(trace)
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    run_id = _persist(request, req.trace_id, "llm-process", report)
    return {"run_id": run_id, "report": report.model_dump()}
