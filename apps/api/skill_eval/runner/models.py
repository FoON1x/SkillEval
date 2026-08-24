"""List models available to the opencode CLI by shelling out to `opencode models`."""

import shutil
import subprocess
from typing import Any


def list_models() -> list[dict[str, Any]]:
    if shutil.which("opencode") is None:
        return []
    try:
        proc = subprocess.run(
            ["opencode", "models", "--verbose"],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if proc.returncode != 0:
        return []
    out: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line or "/" not in line:
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
