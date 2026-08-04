"""Pluggable ingest registry: adapters register by agent name; dispatch parse()."""

import json
from abc import ABC, abstractmethod
from typing import Any

from skill_eval.core.schema import Trace
from skill_eval.ingest.errors import ParseError


class BaseImporter(ABC):
    """Adapter contract: translate raw agent data into a canonical Trace."""

    agent: str

    @abstractmethod
    def parse(self, raw: dict[str, Any] | bytes | str | None) -> Trace:
        """Parse raw data into a canonical Trace; raise ParseError on failure."""

    def load_raw(self, raw: dict[str, Any] | bytes | str | None) -> dict[str, Any]:
        """Normalize raw input to a dict, raising ParseError for unreadable input."""

        if isinstance(raw, dict):
            return raw
        if isinstance(raw, (bytes, str)):
            try:
                loaded = json.loads(raw)
            except (json.JSONDecodeError, TypeError) as exc:
                raise ParseError(f"invalid JSON payload: {exc}") from exc
            if not isinstance(loaded, dict):
                raise ParseError("raw payload must be a JSON object")
            return loaded
        raise ParseError("raw payload missing")


class IngestRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, BaseImporter] = {}

    def register(self, importer: BaseImporter) -> None:
        self._adapters[importer.agent] = importer

    def get(self, agent: str) -> BaseImporter:
        try:
            return self._adapters[agent]
        except KeyError as exc:
            raise KeyError(f"no importer registered for agent: {agent}") from exc

    def parse(self, agent: str, raw: dict[str, Any] | bytes | str | None) -> Trace:
        return self.get(agent).parse(raw)

    def agents(self) -> list[str]:
        return sorted(self._adapters)


_registry = IngestRegistry()


def get_registry() -> IngestRegistry:
    return _registry


def _register_defaults() -> None:
    from skill_eval.ingest.adapters.opencode import OpencodeImporter
    from skill_eval.ingest.adapters.skeletons import SkeletonImporter

    _registry.register(OpencodeImporter())
    for agent in ("codex", "claude-code", "pi"):
        _registry.register(SkeletonImporter(agent))


_register_defaults()
