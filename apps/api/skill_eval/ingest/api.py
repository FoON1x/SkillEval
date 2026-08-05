"""Ingest HTTP endpoints: import (adapter parse + persist) and push (canonical trace)."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from skill_eval.core.schema import Trace
from skill_eval.ingest.errors import ParseError
from skill_eval.ingest.registry import get_registry

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


class ImportRequest(BaseModel):
    agent: str
    raw: dict[str, Any] | list[Any] | None = None


@router.post("/import")
def import_trace(req: ImportRequest, request: Request) -> dict[str, Any]:
    try:
        trace = get_registry().parse(req.agent, req.raw)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"unknown agent: {exc}") from exc
    except ParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    request.app.state.store.save_trace(trace)
    return {"status": "parsed", "trace": trace, "id": trace.id, "saved": True}


@router.post("/push")
def push_trace(trace: Trace, request: Request) -> dict[str, Any]:
    request.app.state.store.save_trace(trace)
    return {"accepted": True, "id": trace.id, "saved": True}
