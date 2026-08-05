"""Restricted Python assertion sandbox (subprocess + timeout + builtin whitelist).

User code sees a small dict context: trace (dict), projection (list of tools with
attribute access), actual / expected (lists of tool names). Code may be an
expression (auto-bool) or statements assigning `result`.
"""

import json
import subprocess
import sys
from typing import Any

from pydantic import BaseModel

SANDBOX_SCRIPT = r"""
import builtins
import json
import sys

SAFE_BUILTINS = (
    "len any all sum sorted min max abs round str int float bool dict list set tuple "
    "zip enumerate range filter map isinstance type"
).split()

class Tool:
    def __init__(self, d):
        self.node_id = d.get("node_id")
        self.name = d.get("name")
        self.args = d.get("args")
        self.result = d.get("result")

def main():
    payload = json.loads(sys.stdin.read())
    ctx = payload["ctx"]
    code = payload["code"]
    env = {"__builtins__": {k: getattr(builtins, k) for k in SAFE_BUILTINS}}
    ctx = dict(ctx)
    ctx["projection"] = [Tool(d) for d in ctx.get("projection", [])]
    env.update(ctx)
    env["result"] = None

    def finish(passed, message=None):
        print(json.dumps({"passed": bool(passed), "message": message}))
        sys.exit(0)

    try:
        compiled = compile(code, "<assertion>", "eval")
    except SyntaxError:
        try:
            compiled = compile(code, "<assertion>", "exec")
        except SyntaxError as exc:
            finish(False, f"SyntaxError: {exc}")
        try:
            exec(compiled, env)
        except Exception as exc:
            finish(False, f"{type(exc).__name__}: {exc}")
        result = env.get("result")
        if result is None:
            finish(False, "no `result` variable assigned")
        finish(result)
    else:
        try:
            value = eval(compiled, env)
        except Exception as exc:
            finish(False, f"{type(exc).__name__}: {exc}")
        finish(value)

main()
"""


class AssertionOutcome(BaseModel):
    passed: bool
    message: str | None = None
    label: str | None = None


def run_assertion(
    code: str,
    ctx: dict[str, Any],
    label: str | None = None,
    timeout_seconds: float = 5.0,
) -> AssertionOutcome:
    payload = json.dumps({"code": code, "ctx": ctx})
    try:
        proc = subprocess.run(
            [sys.executable, "-c", SANDBOX_SCRIPT],
            input=payload,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return AssertionOutcome(passed=False, label=label, message="assertion timed out")

    stdout = (proc.stdout or "").strip()
    try:
        result = json.loads(stdout)
    except json.JSONDecodeError:
        stderr = (proc.stderr or "").strip()
        return AssertionOutcome(
            passed=False,
            label=label,
            message=f"sandbox crashed: {stderr or stdout}",
        )
    return AssertionOutcome(
        passed=bool(result.get("passed")),
        label=label,
        message=result.get("message"),
    )
