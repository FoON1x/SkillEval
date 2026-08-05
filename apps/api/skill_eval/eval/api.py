"""Eval API: run rule + assertion evaluation and persist the run."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from skill_eval.eval.service import EvalOutcome, evaluate
from skill_eval.store.dto import EvalRunCreate
from skill_eval.store.repository import record_to_trace

router = APIRouter(prefix="/api/eval", tags=["eval"])


class EvalRequest(BaseModel):
    test_case_id: str
    trace_id: str


@router.post("/run")
def run_evaluation(req: EvalRequest, request: Request) -> dict[str, Any]:
    store = request.app.state.store
    test_case = store.get_test_case(req.test_case_id)
    if test_case is None:
        raise HTTPException(status_code=404, detail="test case not found")
    trace_record = store.get_trace(req.trace_id)
    if trace_record is None:
        raise HTTPException(status_code=404, detail="trace not found")

    try:
        outcome: EvalOutcome = evaluate(record_to_trace(trace_record), test_case)
        result = "passed" if outcome.passed else "failed"
        details: dict[str, Any] = {
            "rule": outcome.rule.model_dump(),
            "assertions": [a.model_dump() for a in outcome.assertions],
        }
        run = store.save_eval_run(
            EvalRunCreate(
                test_case_id=req.test_case_id,
                trace_id=req.trace_id,
                rule=outcome.rule.rule,  # type: ignore[arg-type]
                result=result,
                score=outcome.score,
                details=details,
            )
        )
    except Exception as exc:
        run = store.save_eval_run(
            EvalRunCreate(
                test_case_id=req.test_case_id,
                trace_id=req.trace_id,
                rule="strict",  # placeholder: rule unknown when evaluation crashes
                result="error",
                details={"error": str(exc)},
            )
        )
        raise HTTPException(status_code=500, detail=f"evaluation failed: {exc}") from exc

    return {
        "run_id": run.id,
        "result": result,
        "score": outcome.score,
        "details": details,
    }
