"""opencode headless runner. Wiring lands with real CLI integration; stub for now."""

import shutil

from skill_eval.core.schema import Trace
from skill_eval.runner.base import BaseRunner, RunContext, RunnerUnavailableError


class OpencodeRunner(BaseRunner):
    agent = "opencode"
    binary = "opencode"

    def available(self) -> bool:
        return shutil.which(self.binary) is not None

    def run(self, context: RunContext) -> Trace:
        if not self.available():
            raise RunnerUnavailableError("opencode CLI not found on PATH")
        raise NotImplementedError("opencode headless execution wiring lands with real CLI integration")
