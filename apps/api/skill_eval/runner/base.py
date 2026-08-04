"""Runner abstraction: headless agent execution -> canonical Trace."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from skill_eval.core.schema import Trace


class RunnerUnavailableError(RuntimeError):
    """Raised when the agent CLI is not installed / not on PATH."""


class RunContext(BaseModel):
    task: str
    session_id: str | None = None
    cwd: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class BaseRunner(ABC):
    agent: str
    binary: str = ""

    @abstractmethod
    def run(self, context: RunContext) -> Trace:
        """Execute the agent headless for the given task and return its Trace."""

    def available(self) -> bool:
        """Whether the agent CLI is available on this machine (overridable)."""
        return True
