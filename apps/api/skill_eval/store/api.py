"""Data API: traces / test-cases / eval-runs CRUD + history queries."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from skill_eval.core.schema import Trace
from skill_eval.store.dto import (
    EvalRunCreate,
    EvalRunViewOut,
    TestCaseCreate,
    TestCaseUpdate,
    TestCaseViewOut,
    TraceSummaryOut,
)
from skill_eval.store.repository import Store, record_to_trace

router = APIRouter(prefix="/api", tags=["data"])


def _store(request: Request) -> Store:
    return request.app.state.store


class TraceListOut(BaseModel):
    items: list[TraceSummaryOut]
    total: int


class TestCaseListOut(BaseModel):
    items: list[TestCaseViewOut]
    total: int


class EvalRunListOut(BaseModel):
    items: list[EvalRunViewOut]
    total: int


@router.get("/traces", response_model=TraceListOut)
def list_traces(
    request: Request,
    agent: str | None = None,
    skill_name: str | None = None,
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    filters = {
        "agent": agent or "",
        "skill_name": skill_name or "",
        "status": status or "",
    }
    items, total = _store(request).list_traces(filters, limit=limit, offset=offset)
    return {
        "items": [TraceSummaryOut(**vars(i)) for i in items],
        "total": total,
    }


@router.get("/traces/{trace_id}", response_model=Trace)
def get_trace(trace_id: str, request: Request) -> Trace:
    record = _store(request).get_trace(trace_id)
    if record is None:
        raise HTTPException(status_code=404, detail="trace not found")
    return record_to_trace(record)


@router.delete("/traces/{trace_id}", status_code=204)
def delete_trace(trace_id: str, request: Request) -> None:
    if not _store(request).delete_trace(trace_id):
        raise HTTPException(status_code=404, detail="trace not found")


@router.get("/test-cases", response_model=TestCaseListOut)
def list_test_cases(
    request: Request,
    agent: str | None = None,
    rule: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    filters = {"agent": agent or "", "rule": rule or ""}
    items, total = _store(request).list_test_cases(filters, limit=limit, offset=offset)
    return {"items": [TestCaseViewOut(**vars(i)) for i in items], "total": total}


@router.post("/test-cases", response_model=TestCaseViewOut)
def create_test_case(create: TestCaseCreate, request: Request) -> TestCaseViewOut:
    view = _store(request).save_test_case(create)
    return TestCaseViewOut(**vars(view))


@router.get("/test-cases/{test_case_id}", response_model=TestCaseViewOut)
def get_test_case(test_case_id: str, request: Request) -> TestCaseViewOut:
    view = _store(request).get_test_case(test_case_id)
    if view is None:
        raise HTTPException(status_code=404, detail="test case not found")
    return TestCaseViewOut(**vars(view))


@router.put("/test-cases/{test_case_id}", response_model=TestCaseViewOut)
def update_test_case(
    test_case_id: str, update: TestCaseUpdate, request: Request
) -> TestCaseViewOut:
    view = _store(request).update_test_case(test_case_id, update)
    if view is None:
        raise HTTPException(status_code=404, detail="test case not found")
    return TestCaseViewOut(**vars(view))


@router.delete("/test-cases/{test_case_id}", status_code=204)
def delete_test_case(test_case_id: str, request: Request) -> None:
    if not _store(request).delete_test_case(test_case_id):
        raise HTTPException(status_code=404, detail="test case not found")


@router.get("/eval-runs", response_model=EvalRunListOut)
def list_eval_runs(
    request: Request,
    trace_id: str | None = None,
    test_case_id: str | None = None,
    result: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    filters = {
        "trace_id": trace_id or "",
        "test_case_id": test_case_id or "",
        "result": result or "",
    }
    items, total = _store(request).list_eval_runs(filters, limit=limit, offset=offset)
    return {"items": [EvalRunViewOut(**vars(i)) for i in items], "total": total}


@router.post("/eval-runs", response_model=EvalRunViewOut)
def create_eval_run(create: EvalRunCreate, request: Request) -> EvalRunViewOut:
    view = _store(request).save_eval_run(create)
    return EvalRunViewOut(**vars(view))


@router.get("/eval-runs/{eval_run_id}", response_model=EvalRunViewOut)
def get_eval_run(eval_run_id: str, request: Request) -> EvalRunViewOut:
    view = _store(request).get_eval_run(eval_run_id)
    if view is None:
        raise HTTPException(status_code=404, detail="eval run not found")
    return EvalRunViewOut(**vars(view))


@router.delete("/eval-runs/{eval_run_id}", status_code=204)
def delete_eval_run(eval_run_id: str, request: Request) -> None:
    if not _store(request).delete_eval_run(eval_run_id):
        raise HTTPException(status_code=404, detail="eval run not found")
