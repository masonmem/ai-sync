"""Personal workflow state stays external and stable across linked worktrees."""

from __future__ import annotations

import os
import pathlib
import subprocess


ROOT = pathlib.Path(__file__).resolve().parent.parent
HELPER = ROOT / "bin" / "ai-project-state"


def git(cwd: pathlib.Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_project_state_is_external_stable_and_private(tmp_path):
    repo = tmp_path / "example-repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Test")
    (repo / "README").write_text("test\n")
    git(repo, "add", "README")
    git(repo, "commit", "-qm", "init")
    git(repo, "remote", "add", "origin", "git@example.invalid:org/example.git")

    linked = tmp_path / "linked"
    git(repo, "worktree", "add", "-q", "-b", "topic", str(linked))
    state_root = tmp_path / "state"
    env = {
        "PATH": os.environ["PATH"],
        "AI_SYNC_STATE_ROOT": str(state_root),
    }

    canonical = subprocess.run(
        [str(HELPER), "--ensure", str(repo)],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    ).stdout.strip()
    from_linked = subprocess.run(
        [str(HELPER), str(linked)],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    ).stdout.strip()

    assert canonical == from_linked
    path = pathlib.Path(canonical)
    assert path.parent == state_root
    assert path.name.startswith("example-repo--")
    assert "example.invalid" not in path.name
    assert path.stat().st_mode & 0o077 == 0
    assert not (repo / ".ai-local").exists()
