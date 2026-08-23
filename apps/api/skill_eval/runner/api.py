"""Runner HTTP endpoints: trigger headless agent runs (sync + live SSE stream) + skill list."""

import json
import queue
import threading

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from skill_eval.core.schema import Trace
from skill_eval.runner.base import RunContext, RunnerUnavailableError
from skill_eval.runner.registry import get_runner_registry
from skill_eval.runner.skills import list_skills

router = APIRouter(prefix="/api/runner", tags=["runner"])


class RunRequest(BaseModel):
    agent: str
    task: str
    session_id: str | None = None


class StreamRunRequest(BaseModel):
    agent: str = "opencode"
    task: str
    skill_name: str | None = None
    session_id: str | None = None
    cwd: str | None = None
    auto: bool = True
    timeout: int = 300
    agent_name: str | None = None
    model: str | None = None


@router.post("/run")
def run_agent(req: RunRequest) -> dict[str, object]:
    try:
        runner = get_runner_registry().get(req.agent)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"unknown agent: {exc}") from exc
    try:
        trace: Trace = runner.run_stream(
            RunContext(task=req.task, session_id=req.session_id), emit=lambda _c: None
        )
    except RunnerUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    return {"status": "started", "trace": trace}


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/run/stream")
def run_stream(req: StreamRunRequest, request: Request) -> StreamingResponse:
    try:
        runner = get_runner_registry().get(req.agent)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"unknown agent: {exc}") from exc
    if not runner.available():
        raise HTTPException(status_code=503, detail=f"{req.agent} CLI not available")

    ctx = RunContext(
        task=req.task,
        session_id=req.session_id,
        skill_name=req.skill_name,
        cwd=req.cwd,
        auto=req.auto,
        timeout=req.timeout,
        agent_name=req.agent_name,
        model=req.model,
    )
    store = request.app.state.store

    def event_stream():
        q: queue.Queue[tuple[str, object]] = queue.Queue()

        def emit(canon: dict) -> None:
            q.put(("event", canon))

        def worker() -> None:
            try:
                trace = runner.run_stream(ctx, emit=emit)
                store.save_trace(trace)
                q.put(("done", trace.id))
            except Exception as exc:
                q.put(("error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()
        while True:
            kind, payload = q.get()
            if kind == "event":
                yield _sse({"type": "event", "node": payload})
            elif kind == "done":
                yield _sse({"type": "done", "trace_id": payload})
                break
            else:
                yield _sse({"type": "error", "message": payload})
                break

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/skills")
def get_skills() -> dict[str, object]:
    return {"skills": list_skills()}
