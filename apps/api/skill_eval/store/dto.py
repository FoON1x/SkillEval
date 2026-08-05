"""API DTOs for persistence layer (evaluation rule names live here until the eval
package lands in Phase 4)."""

import datetime as dt
from typing import Any, Literal

from pydantic import BaseModel, Field

RuleName = Literal["strict", "unordered", "subset", "superset"]
EvalResult = Literal["passed", "failed", "error"]


class ExpectedPath(BaseModel):
    """Expected tool-call path for rule evaluation (tool names in order)."""

    tools: list[str] = Field(default_factory=list)
    description: str | None = None


class Assertion(BaseModel):
    code: str
    label: str | None = None


class TestCaseCreate(BaseModel):
    name: str
    description: str | None = None
    agent: str
    rule: RuleName
    input_context: dict[str, Any] | None = None
    expected: ExpectedPath = Field(default_factory=ExpectedPath)
    assertions: list[Assertion] = Field(default_factory=list)


class TestCaseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    agent: str | None = None
    rule: RuleName | None = None
    input_context: dict[str, Any] | None = None
    expected: ExpectedPath | None = None
    assertions: list[Assertion] | None = None


class EvalRunCreate(BaseModel):
    test_case_id: str
    trace_id: str
    rule: RuleName
    result: EvalResult
    score: float | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class TraceSummaryOut(BaseModel):
    id: str
    agent: str
    skill_name: str | None
    session_id: str | None
    status: str
    started_at: dt.datetime | None
    ended_at: dt.datetime | None
    cost_usd: float | None
    total_tokens: int | None
    latency_ms: int | None
    created_at: dt.datetime


class TestCaseViewOut(BaseModel):
    id: str
    name: str
    description: str | None
    agent: str
    rule: str
    input_context: dict[str, Any] | None
    expected: ExpectedPath
    assertions: list[Assertion]
    created_at: dt.datetime


class EvalRunViewOut(BaseModel):
    id: str
    test_case_id: str
    trace_id: str
    rule: str
    result: str
    score: float | None
    details: dict[str, Any]
    created_at: dt.datetime
