"""The read-only health check catches version-control and permission hazards."""

from __future__ import annotations

import os
import pathlib
import subprocess


ROOT = pathlib.Path(__file__).resolve().parent.parent
HEALTH = ROOT / "bin" / "ai-health"
PERMISSIONS = ROOT / "bin" / "ai-runtime-permissions"


def git(cwd: pathlib.Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def test_repo_check_rejects_tracked_copilot_runtime_state(tmp_path):
    repo = tmp_path / "ai-sync"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    runtime = repo / "copilot" / "session-state"
    runtime.mkdir(parents=True)
    (runtime / "session.json").write_text("{}\n")
    git(repo, "add", ".")

    result = subprocess.run(
        [str(HEALTH), "--repo", str(repo), "--repo-only"],
        capture_output=True,
        text=True,
        env={"PATH": os.environ["PATH"]},
    )

    assert result.returncode == 1
    assert "tracked copilot runtime state" in result.stdout.lower()


def test_permission_check_rejects_world_readable_runtime_file(tmp_path):
    home = tmp_path / "home"
    runtime = home / ".copilot" / "session-state"
    runtime.mkdir(parents=True)
    runtime.chmod(0o700)
    state = runtime / "session.json"
    state.write_text("{}\n")
    state.chmod(0o644)

    result = subprocess.run(
        [str(HEALTH), "--home", str(home), "--permissions-only"],
        capture_output=True,
        text=True,
        env={"PATH": os.environ["PATH"]},
    )

    assert result.returncode == 1
    assert "unsafe copilot runtime permissions" in result.stdout.lower()


def test_permission_repair_is_scoped_to_runtime_state(tmp_path):
    home = tmp_path / "home"
    runtime = home / ".copilot" / "session-state"
    runtime.mkdir(parents=True)
    state = runtime / "session.json"
    state.write_text("{}\n")
    state.chmod(0o644)
    curated = home / ".copilot" / "settings.json"
    curated.write_text("{}\n")
    curated.chmod(0o644)

    subprocess.run(
        [str(PERMISSIONS)],
        check=True,
        capture_output=True,
        text=True,
        env={"HOME": str(home), "PATH": os.environ["PATH"]},
    )

    assert state.stat().st_mode & 0o077 == 0
    assert runtime.stat().st_mode & 0o077 == 0
    assert curated.stat().st_mode & 0o077 == 0o044
