"""Runner abstraction: headless agent execution -> canonical Trace."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from skill_eval.core.schema import Trace


class RunnerUnavailableError(RuntimeError):
    """Raised when the agent CLI is not installed / not on PATH."""


class RunContext(BaseModel):
    task: str
    session_id: str | None = None
    cwd: str | None = None
    skill_name: str | None = None
    auto: bool = True
    timeout: int = 300
    agent_name: str | None = None
    model: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class BaseRunner(ABC):
    agent: str
    binary: str = ""

    @abstractmethod
    def run_stream(self, context: RunContext, emit: Callable[[dict[str, Any]], None]) -> Trace:
        """Execute the agent headless for the given task, emitting live events, return its Trace."""

    def available(self) -> bool:
        """Whether the agent CLI is available on this machine (overridable)."""
        return True
