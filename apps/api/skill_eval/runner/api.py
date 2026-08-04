"""Runner HTTP endpoint: trigger headless agent runs."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from skill_eval.core.schema import Trace
from skill_eval.runner.base import RunContext, RunnerUnavailableError
from skill_eval.runner.registry import get_runner_registry

router = APIRouter(prefix="/api/runner", tags=["runner"])


class RunRequest(BaseModel):
    agent: str
    task: str
    session_id: str | None = None


@router.post("/run")
def run_agent(req: RunRequest) -> dict[str, object]:
    try:
        runner = get_runner_registry().get(req.agent)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"unknown agent: {exc}") from exc
    try:
        trace: Trace = runner.run(RunContext(task=req.task, session_id=req.session_id))
    except RunnerUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    return {"status": "started", "trace": trace}
