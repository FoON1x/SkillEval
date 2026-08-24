"""Tests for filesystem browse endpoint."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from skill_eval.app import create_app


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    (tmp_path / "sub1").mkdir()
    (tmp_path / "sub2").mkdir()
    (tmp_path / "hidden").mkdir()
    (tmp_path / "a.txt").write_text("x")
    (tmp_path / "sub1" / "inner.txt").write_text("y")
    return TestClient(create_app())


def test_browse_lists_dirs_and_files(client: TestClient, tmp_path: Path):
    r = client.get("/api/fs/browse", params={"path": str(tmp_path)})
    assert r.status_code == 200
    body = r.json()
    assert body["path"] == str(tmp_path.resolve())
    names = {e["name"] for e in body["entries"]}
    assert "sub1" in names and "sub2" in names and "a.txt" in names
    types = {e["name"]: e["type"] for e in body["entries"]}
    assert types["sub1"] == "dir" and types["a.txt"] == "file"


def test_browse_skips_hidden(client: TestClient, tmp_path: Path):
    r = client.get("/api/fs/browse", params={"path": str(tmp_path)})
    names = {e["name"] for e in r.json()["entries"]}
    assert "hidden" in names
    (tmp_path / ".secret").mkdir()
    r2 = client.get("/api/fs/browse", params={"path": str(tmp_path)})
    assert ".secret" not in {e["name"] for e in r2.json()["entries"]}


def test_browse_missing_path_returns_404(client: TestClient, tmp_path: Path):
    r = client.get("/api/fs/browse", params={"path": str(tmp_path / "nope")})
    assert r.status_code == 404


def test_browse_empty_path_uses_home(client: TestClient):
    r = client.get("/api/fs/browse")
    assert r.status_code == 200
    from pathlib import Path as P
    assert r.json()["path"] == str(P.home().resolve())
