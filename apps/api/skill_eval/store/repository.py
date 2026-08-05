"""Store: persistence repository over SQLAlchemy (SQLite)."""

import datetime as dt
import json
import uuid
from contextlib import contextmanager
from typing import Any, Iterator

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from skill_eval.core.schema import Trace
from skill_eval.store.db import make_engine, make_session_factory
from skill_eval.store.dto import (
    Assertion,
    EvalRunCreate,
    ExpectedPath,
    TestCaseCreate,
    TestCaseUpdate,
)
from skill_eval.store.models import Base, EvalRunRecord, TestCaseRecord, TraceRecord


class TraceSummary:
    def __init__(
        self,
        id: str,
        agent: str,
        skill_name: str | None,
        session_id: str | None,
        status: str,
        started_at: dt.datetime | None,
        ended_at: dt.datetime | None,
        cost_usd: float | None,
        total_tokens: int | None,
        latency_ms: int | None,
        created_at: dt.datetime,
    ) -> None:
        self.id = id
        self.agent = agent
        self.skill_name = skill_name
        self.session_id = session_id
        self.status = status
        self.started_at = started_at
        self.ended_at = ended_at
        self.cost_usd = cost_usd
        self.total_tokens = total_tokens
        self.latency_ms = latency_ms
        self.created_at = created_at


class TestCaseView:
    def __init__(
        self,
        id: str,
        name: str,
        description: str | None,
        agent: str,
        rule: str,
        input_context: dict[str, Any] | None,
        expected: ExpectedPath,
        assertions: list[Assertion],
        created_at: dt.datetime,
    ) -> None:
        self.id = id
        self.name = name
        self.description = description
        self.agent = agent
        self.rule = rule
        self.input_context = input_context
        self.expected = expected
        self.assertions = assertions
        self.created_at = created_at


class EvalRunView:
    def __init__(
        self,
        id: str,
        test_case_id: str,
        trace_id: str,
        rule: str,
        result: str,
        score: float | None,
        details: dict[str, Any],
        created_at: dt.datetime,
    ) -> None:
        self.id = id
        self.test_case_id = test_case_id
        self.trace_id = trace_id
        self.rule = rule
        self.result = result
        self.score = score
        self.details = details
        self.created_at = created_at


class Store:
    def __init__(self, engine: Engine) -> None:
        Base.metadata.create_all(engine)
        self._sf = make_session_factory(engine)

    @classmethod
    def default(cls) -> "Store":
        return cls(make_engine())

    @classmethod
    def in_memory(cls) -> "Store":
        return cls(make_engine(in_memory=True))

    @contextmanager
    def _session(self) -> Iterator[Session]:
        with self._sf() as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    # ---- traces ----

    def save_trace(self, trace: Trace) -> TraceRecord:
        payload = trace.model_dump_json()
        usage = trace.usage
        with self._session() as session:
            record = session.get(TraceRecord, trace.id)
            if record is None:
                record = TraceRecord(id=trace.id)
                session.add(record)
            record.agent = trace.agent.value
            record.skill_name = trace.skill_name
            record.session_id = trace.session_id
            record.status = trace.status.value
            record.started_at = trace.started_at
            record.ended_at = trace.ended_at
            record.cost_usd = usage.cost_usd if usage else None
            record.total_tokens = usage.total_tokens if usage else None
            record.latency_ms = usage.latency_ms if usage else None
            record.data = payload
            session.flush()
            return record

    def get_trace(self, trace_id: str) -> TraceRecord | None:
        with self._session() as session:
            return session.get(TraceRecord, trace_id)

    def list_traces(
        self,
        filters: dict[str, str],
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[TraceSummary], int]:
        with self._session() as session:
            query = session.query(TraceRecord)
            if filters.get("agent"):
                query = query.filter(TraceRecord.agent == filters["agent"])
            if filters.get("skill_name"):
                query = query.filter(TraceRecord.skill_name == filters["skill_name"])
            if filters.get("status"):
                query = query.filter(TraceRecord.status == filters["status"])
            total = query.count()
            rows = (
                query.order_by(TraceRecord.started_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [self._summary(r) for r in rows], total

    def delete_trace(self, trace_id: str) -> bool:
        with self._session() as session:
            record = session.get(TraceRecord, trace_id)
            if record is None:
                return False
            session.delete(record)
            return True

    @staticmethod
    def _summary(r: TraceRecord) -> TraceSummary:
        return TraceSummary(
            id=r.id,
            agent=r.agent,
            skill_name=r.skill_name,
            session_id=r.session_id,
            status=r.status,
            started_at=r.started_at,
            ended_at=r.ended_at,
            cost_usd=r.cost_usd,
            total_tokens=r.total_tokens,
            latency_ms=r.latency_ms,
            created_at=r.created_at,
        )

    # ---- test cases ----

    def save_test_case(self, create: TestCaseCreate, id: str | None = None) -> TestCaseView:
        with self._session() as session:
            record = TestCaseRecord(
                id=id or f"tc-{uuid.uuid4().hex[:12]}",
                name=create.name,
                description=create.description,
                agent=create.agent,
                rule=create.rule,
                input_context=json.dumps(create.input_context) if create.input_context else None,
                expected=create.expected.model_dump_json(),
                assertions=json.dumps([a.model_dump() for a in create.assertions]),
            )
            session.add(record)
            session.flush()
            return self._test_case_view(record)

    def get_test_case(self, test_case_id: str) -> TestCaseView | None:
        with self._session() as session:
            record = session.get(TestCaseRecord, test_case_id)
            return self._test_case_view(record) if record else None

    def update_test_case(self, test_case_id: str, update: TestCaseUpdate) -> TestCaseView | None:
        with self._session() as session:
            record = session.get(TestCaseRecord, test_case_id)
            if record is None:
                return None
            if update.name is not None:
                record.name = update.name
            if update.description is not None:
                record.description = update.description
            if update.agent is not None:
                record.agent = update.agent
            if update.rule is not None:
                record.rule = update.rule
            if update.input_context is not None:
                record.input_context = json.dumps(update.input_context)
            if update.expected is not None:
                record.expected = update.expected.model_dump_json()
            if update.assertions is not None:
                record.assertions = json.dumps([a.model_dump() for a in update.assertions])
            session.flush()
            return self._test_case_view(record)

    def list_test_cases(
        self, filters: dict[str, str], limit: int = 50, offset: int = 0
    ) -> tuple[list[TestCaseView], int]:
        with self._session() as session:
            query = session.query(TestCaseRecord)
            if filters.get("agent"):
                query = query.filter(TestCaseRecord.agent == filters["agent"])
            if filters.get("rule"):
                query = query.filter(TestCaseRecord.rule == filters["rule"])
            total = query.count()
            rows = query.order_by(TestCaseRecord.created_at.desc()).offset(offset).limit(limit).all()
            return [self._test_case_view(r) for r in rows], total

    def delete_test_case(self, test_case_id: str) -> bool:
        with self._session() as session:
            record = session.get(TestCaseRecord, test_case_id)
            if record is None:
                return False
            session.delete(record)
            return True

    @staticmethod
    def _test_case_view(r: TestCaseRecord) -> TestCaseView:
        return TestCaseView(
            id=r.id,
            name=r.name,
            description=r.description,
            agent=r.agent,
            rule=r.rule,
            input_context=json.loads(r.input_context) if r.input_context else None,
            expected=ExpectedPath.model_validate_json(r.expected),
            assertions=[
                Assertion.model_validate(a) for a in json.loads(r.assertions)
            ],
            created_at=r.created_at,
        )

    # ---- eval runs ----

    def save_eval_run(self, create: EvalRunCreate, id: str | None = None) -> EvalRunView:
        with self._session() as session:
            record = EvalRunRecord(
                id=id or f"ev-{uuid.uuid4().hex[:12]}",
                test_case_id=create.test_case_id,
                trace_id=create.trace_id,
                rule=create.rule,
                result=create.result,
                score=create.score,
                details=json.dumps(create.details),
            )
            session.add(record)
            session.flush()
            return self._eval_run_view(record)

    def get_eval_run(self, eval_run_id: str) -> EvalRunView | None:
        with self._session() as session:
            record = session.get(EvalRunRecord, eval_run_id)
            return self._eval_run_view(record) if record else None

    def list_eval_runs(
        self, filters: dict[str, str], limit: int = 50, offset: int = 0
    ) -> tuple[list[EvalRunView], int]:
        with self._session() as session:
            query = session.query(EvalRunRecord)
            if filters.get("trace_id"):
                query = query.filter(EvalRunRecord.trace_id == filters["trace_id"])
            if filters.get("test_case_id"):
                query = query.filter(EvalRunRecord.test_case_id == filters["test_case_id"])
            if filters.get("result"):
                query = query.filter(EvalRunRecord.result == filters["result"])
            total = query.count()
            rows = query.order_by(EvalRunRecord.created_at.desc()).offset(offset).limit(limit).all()
            return [self._eval_run_view(r) for r in rows], total

    def delete_eval_run(self, eval_run_id: str) -> bool:
        with self._session() as session:
            record = session.get(EvalRunRecord, eval_run_id)
            if record is None:
                return False
            session.delete(record)
            return True

    @staticmethod
    def _eval_run_view(r: EvalRunRecord) -> EvalRunView:
        return EvalRunView(
            id=r.id,
            test_case_id=r.test_case_id,
            trace_id=r.trace_id,
            rule=r.rule,
            result=r.result,
            score=r.score,
            details=json.loads(r.details),
            created_at=r.created_at,
        )


def record_to_trace(record: TraceRecord) -> Trace:
    return Trace.model_validate_json(record.data)
