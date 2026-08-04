"""Skeleton adapters for agents whose real trace format is not yet confirmed."""

from typing import Any

from skill_eval.core.schema import Trace
from skill_eval.ingest.errors import ParseError
from skill_eval.ingest.registry import BaseImporter


class SkeletonImporter(BaseImporter):
    def __init__(self, agent: str) -> None:
        self.agent = agent

    def parse(self, raw: dict[str, Any] | bytes | str | None) -> Trace:
        self.load_raw(raw)
        raise ParseError(f"adapter '{self.agent}' is not implemented yet (pending real trace samples)")
