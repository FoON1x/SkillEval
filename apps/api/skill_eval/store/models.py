"""SQLAlchemy models for persistence (SQLite; JSON columns hold canonical payloads)."""

import datetime as dt

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

UTC = dt.timezone.utc


class Base(DeclarativeBase):
    pass


class TraceRecord(Base):
    __tablename__ = "traces"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent: Mapped[str] = mapped_column(String(32), index=True)
    skill_name: Mapped[str | None] = mapped_column(String(255), index=True)
    session_id: Mapped[str | None] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(16), index=True)
    started_at: Mapped[dt.datetime | None] = mapped_column(DateTime, index=True)
    ended_at: Mapped[dt.datetime | None] = mapped_column(DateTime)
    cost_usd: Mapped[float | None] = mapped_column(Float)
    total_tokens: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    data: Mapped[str] = mapped_column(Text)  # canonical Trace JSON
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.now(UTC))
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=dt.datetime.now(UTC), onupdate=dt.datetime.now(UTC)
    )


class TestCaseRecord(Base):
    __tablename__ = "test_cases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    agent: Mapped[str] = mapped_column(String(32), index=True)
    rule: Mapped[str] = mapped_column(String(16), index=True)
    input_context: Mapped[str | None] = mapped_column(Text)  # JSON
    expected: Mapped[str] = mapped_column(Text)  # ExpectedPath JSON
    assertions: Mapped[str] = mapped_column(Text)  # Assertion[] JSON
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.now(UTC))
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=dt.datetime.now(UTC), onupdate=dt.datetime.now(UTC)
    )


class EvalRunRecord(Base):
    __tablename__ = "eval_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    test_case_id: Mapped[str] = mapped_column(String(64), index=True)
    trace_id: Mapped[str] = mapped_column(String(64), index=True)
    rule: Mapped[str] = mapped_column(String(16))
    result: Mapped[str] = mapped_column(String(16))  # passed | failed | error
    score: Mapped[float | None] = mapped_column(Float)
    details: Mapped[str] = mapped_column(Text)  # JSON
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.now(UTC))

