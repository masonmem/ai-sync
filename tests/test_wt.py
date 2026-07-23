"""The personal worktree helper is conservative and branch-name preserving."""

from __future__ import annotations

import os
import pathlib
import subprocess


ROOT = pathlib.Path(__file__).resolve().parent.parent
WT = ROOT / "bin" / "wt"


def run(cwd: pathlib.Path, *args: str, check: bool = True, env=None):
    result = subprocess.run(
        [str(WT), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )
    if check and result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return result


def git(cwd: pathlib.Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def repository(tmp_path: pathlib.Path) -> pathlib.Path:
    repo = tmp_path / "canonical"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Test")
    (repo / "README").write_text("test\n")
    git(repo, "add", "README")
    git(repo, "commit", "-qm", "init")
    return repo


def test_create_list_path_dirty_refusal_remove_and_delete_branch(tmp_path):
    repo = repository(tmp_path)

    created = pathlib.Path(run(repo, "new", "feature/example").stdout.strip())
    assert created == repo / ".worktrees" / "feature--example"
    assert git(created, "branch", "--show-current") == "feature/example"
    assert "feature/example" in run(repo, "ls").stdout
    assert run(repo, "path", "feature/example").stdout.strip() == str(created)

    dirty = created / "untracked.txt"
    dirty.write_text("dirty\n")
    refused = run(repo, "rm", "feature/example", check=False)
    assert refused.returncode != 0
    assert "dirty" in (refused.stdout + refused.stderr).lower()
    assert created.exists()

    dirty.unlink()
    run(repo, "rm", "feature/example")
    assert not created.exists()
    assert git(repo, "show-ref", "--verify", "refs/heads/feature/example")
    run(repo, "delete-branch", "feature/example")
    missing = subprocess.run(
        ["git", "show-ref", "--verify", "refs/heads/feature/example"],
        cwd=repo,
    )
    assert missing.returncode != 0


def test_linked_invocation_uses_canonical_worktrees_directory(tmp_path):
    repo = repository(tmp_path)
    first = pathlib.Path(run(repo, "new", "first/topic").stdout.strip())
    second = pathlib.Path(run(first, "new", "second/topic").stdout.strip())

    assert second == repo / ".worktrees" / "second--topic"


def test_new_refuses_ambiguous_slug_collision(tmp_path):
    repo = repository(tmp_path)
    run(repo, "new", "feature/a+b")

    result = run(repo, "new", "feature/a@b", check=False)

    assert result.returncode != 0
    assert "slug collision" in (result.stdout + result.stderr).lower()


def test_prune_shows_dry_run_before_pruning(tmp_path):
    repo = repository(tmp_path)
    env = os.environ | {"WT_PRUNE_CONFIRM": "yes"}

    result = run(repo, "prune", env=env)

    assert "dry run" in result.stdout.lower()
