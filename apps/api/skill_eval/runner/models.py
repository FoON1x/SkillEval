"""List models available to the opencode CLI by shelling out to `opencode models`."""

import os
import re
import shutil
import subprocess
from typing import Any

_MODEL_LINE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.:+-]+$")


def _build_cmd() -> list[str]:
    exe = shutil.which("opencode")
    cmd = ["opencode", "models"]
    if os.name == "nt" and exe and exe.lower().endswith((".cmd", ".bat")):
        return ["cmd", "/c", *cmd]
    return cmd


def list_models() -> list[dict[str, Any]]:
    if shutil.which("opencode") is None:
        return []
    try:
        proc = subprocess.run(_build_cmd(), capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return []
    if proc.returncode != 0:
        return []
    out: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not _MODEL_LINE.match(line):
            continue
        provider, _, model = line.partition("/")
        out.append({
            "provider": provider,
            "model": model,
            "id": line,
            "context_window": None,
            "input_cost": None,
            "output_cost": None,
        })
    return out
