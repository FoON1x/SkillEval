"""Engine/session factory helpers."""

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

DEFAULT_DB_PATH = Path("data/skilleval.db")


def make_engine(url: str | None = None, in_memory: bool = False) -> Engine:
    if in_memory:
        return create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    resolved = url or os.environ.get("SKILLEVAL_DB_URL") or f"sqlite:///{DEFAULT_DB_PATH}"
    if resolved.startswith("sqlite:///"):
        db_path = Path(resolved.removeprefix("sqlite:///"))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return create_engine(resolved, connect_args={"check_same_thread": False})
    return create_engine(resolved)


def make_session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, expire_on_commit=False)
