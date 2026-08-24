"""Filesystem browse endpoint: list directory entries for the path picker modal."""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/fs", tags=["fs"])


def browse_directory(path: str | None) -> dict[str, Any]:
    target = Path(path).expanduser().resolve() if path else Path.home().resolve()
    if not target.is_dir():
        raise HTTPException(status_code=404, detail=f"not a directory: {target}")
    entries: list[dict[str, str]] = []
    try:
        for d in sorted(target.iterdir()):
            if d.name.startswith("."):
                continue
            entries.append({
                "name": d.name,
                "type": "dir" if d.is_dir() else "file",
                "path": str(d.resolve()),
            })
    except PermissionError:
        pass
    except OSError:
        entries = []
    return {"path": str(target), "entries": entries}


@router.get("/browse")
def get_browse(path: str | None = Query(default=None)) -> dict[str, Any]:
    return browse_directory(path)
