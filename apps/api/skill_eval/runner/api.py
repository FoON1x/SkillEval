"""Runner HTTP endpoints: trigger headless agent runs (sync + live SSE stream) + skill list."""

import asyncio
import json
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
        timeout=min(max(req.timeout, 1), 3600),
        agent_name=req.agent_name,
        model=req.model,
    )
    store = request.app.state.store

    async def event_stream():
        q: asyncio.Queue[tuple[str, object]] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def emit(canon: dict) -> None:
            loop.call_soon_threadsafe(q.put_nowait, ("event", canon))

        def worker() -> None:
            try:
                trace = runner.run_stream(ctx, emit=emit)
                store.save_trace(trace)
                loop.call_soon_threadsafe(q.put_nowait, ("done", trace.id))
            except Exception as exc:
                loop.call_soon_threadsafe(q.put_nowait, ("error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()
        while True:
            try:
                kind, payload = await asyncio.wait_for(q.get(), timeout=1.0)
            except asyncio.TimeoutError:
                if await request.is_disconnected():
                    break
                continue
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
