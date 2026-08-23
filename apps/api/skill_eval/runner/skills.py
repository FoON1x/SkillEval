"""Scan opencode skill directories and parse SKILL.md frontmatter for the UI dropdown."""

import re
from pathlib import Path
from typing import Any


def default_skill_dirs() -> list[Path]:
    home = Path.home()
    return [
        home / ".agents" / "skills",
        home / ".config" / "opencode" / "node_modules" / "superpowers" / "skills",
    ]


_FRONT_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_frontmatter(text: str) -> dict[str, str]:
    m = _FRONT_RE.match(text)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        val = val.strip()
        if len(val) >= 2 and val[0] in "\"'" and val[-1] == val[0]:
            val = val[1:-1]
        out[key.strip()] = val
    return out


def list_skills(dirs: list[Path] | None = None) -> list[dict[str, Any]]:
    bases = dirs if dirs is not None else default_skill_dirs()
    skills: list[dict[str, Any]] = []
    for base in bases:
        if not base.is_dir():
            continue
        for d in sorted(base.iterdir()):
            if not d.is_dir():
                continue
            skill_md = d / "SKILL.md"
            if not skill_md.is_file():
                continue
            try:
                fm = _parse_frontmatter(skill_md.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
            skills.append(
                {
                    "name": fm.get("name", d.name),
                    "description": fm.get("description", ""),
                    "source": str(base),
                }
            )
    return skills
