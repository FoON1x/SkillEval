"""opencode headless runner: spawns `opencode run --format json`, streams JSONL,
runs `opencode export` for authoritative metadata, returns a canonical Trace."""

import json
import shutil
import subprocess
import threading
from collections.abc import Callable
from typing import Any

from skill_eval.core.schema import RunState, Trace, TraceError
from skill_eval.runner.base import BaseRunner, RunContext, RunnerUnavailableError

_MAX_TIMEOUT = 3600


def _run_export(session_id: str | None) -> dict | None:
    """Run `opencode export <sessionID>` and return parsed JSON info, or None on failure."""
    if not session_id:
        return None
    try:
        proc = subprocess.run(
            ["opencode", "export", session_id],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode != 0:
            return None
        data = json.loads(proc.stdout)
        return data.get("info") if isinstance(data, dict) else None
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return None


class OpencodeRunner(BaseRunner):
    agent = "opencode"
    binary = "opencode"

    def available(self) -> bool:
        return shutil.which(self.binary) is not None

    def run_stream(self, context: RunContext, emit: Callable[[dict[str, Any]], None]) -> Trace:
        if not self.available():
            raise RunnerUnavailableError("opencode CLI not found on PATH")

        cmd = ["opencode", "run", context.task, "--format", "json"]
        if context.agent_name:
            cmd += ["--agent", context.agent_name]
        if context.session_id:
            cmd += ["--session", context.session_id]
        if context.cwd:
            cmd += ["--dir", context.cwd]
        if context.model:
            cmd += ["--model", context.model]
        if context.auto:
            cmd += ["--auto"]

        from skill_eval.ingest.registry import get_registry  # noqa: F401 (forces registry module
        # to fully load — and register adapter defaults — before we import OpencodeImporter below,
        # avoiding a circular import: adapter -> registry._register_defaults -> adapter)
        from skill_eval.ingest.adapters.opencode import OpencodeImporter

        builder = OpencodeImporter().new_builder(skill_name=context.skill_name)
        error: TraceError | None = None
        timeout = min(max(context.timeout, 1), _MAX_TIMEOUT)
        proc: subprocess.Popen | None = None
        timed_out = False

        def watchdog() -> None:
            nonlocal timed_out
            if proc is not None:
                timed_out = True
                proc.kill()

        timer = threading.Timer(timeout, watchdog)

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                cwd=context.cwd,
            )
            timer.start()
            if proc.stdout is None:
                raise OSError("subprocess stdout pipe was not opened")
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    emit({"node_type": "warning", "message": "unparseable JSONL line"})
                    continue
                canonical = builder.feed(event)
                if canonical is not None:
                    emit(canonical)
            returncode = proc.wait(timeout=10)
            if returncode != 0 and not timed_out:
                error = TraceError(
                    message=f"opencode exited with code {returncode}",
                    kind="cli_exit",
                )
        except subprocess.TimeoutExpired:
            if proc is not None:
                proc.kill()
            error = TraceError(message=f"opencode timed out after {timeout}s", kind="timeout")
        except OSError as exc:
            error = TraceError(message=str(exc), kind="spawn_error")
        finally:
            timer.cancel()
            if proc is not None and proc.stdout is not None and hasattr(proc.stdout, "close"):
                proc.stdout.close()

        if timed_out:
            error = TraceError(message=f"opencode timed out after {timeout}s", kind="timeout")

        export_info = _run_export(builder.session_id)
        trace = builder.finalize(export_info=export_info)
        if error is not None:
            trace.status = RunState.ERROR
            trace.error = error
        return trace
