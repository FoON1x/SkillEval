"""Runner registry: runners register by agent name."""

from skill_eval.runner.base import BaseRunner


class RunnerRegistry:
    def __init__(self) -> None:
        self._runners: dict[str, BaseRunner] = {}

    def register(self, runner: BaseRunner) -> None:
        self._runners[runner.agent] = runner

    def get(self, agent: str) -> BaseRunner:
        try:
            return self._runners[agent]
        except KeyError as exc:
            raise KeyError(f"no runner registered for agent: {agent}") from exc

    def agents(self) -> list[str]:
        return sorted(self._runners)


_registry = RunnerRegistry()


def get_runner_registry() -> RunnerRegistry:
    return _registry


def _register_defaults() -> None:
    from skill_eval.runner.opencode import OpencodeRunner

    _registry.register(OpencodeRunner())


_register_defaults()
