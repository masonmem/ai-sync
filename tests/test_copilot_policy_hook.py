"""The Copilot writer/reviewer boundary must fail closed on unsafe tool calls."""

from __future__ import annotations

import json
import os
import pathlib
import subprocess


ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK = ROOT / "bin" / "copilot-policy-hook"


def run_hook(payload: dict, *, boundary: str | None = "writer"):
    env = {"PATH": os.environ["PATH"]}
    if boundary is None:
        env.pop("AI_SYNC_AGENT_BOUNDARY", None)
    else:
        env["AI_SYNC_AGENT_BOUNDARY"] = boundary
    return subprocess.run(
        [str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )


def bash(command: str, cwd: pathlib.Path) -> dict:
    return {
        "cwd": str(cwd),
        "toolName": "bash",
        "toolArgs": {"command": command},
    }


def decision(result: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(result.stdout) if result.stdout.strip() else {}


def test_unscoped_session_is_not_restricted(tmp_path):
    result = run_hook(bash("git push", tmp_path), boundary=None)
    assert result.returncode == 0
    assert decision(result) == {}


def test_writer_allows_read_only_git_status(tmp_path):
    result = run_hook(bash("git status --short", tmp_path))
    assert result.returncode == 0
    assert decision(result) == {}


def test_writer_denies_git_and_filesystem_mutations(tmp_path):
    for command in (
        "git push",
        "git -C repo rebase main",
        "git branch new-branch",
        "git worktree add elsewhere topic",
        "echo ok && git update-ref refs/heads/x HEAD",
        "rm -rf build",
    ):
        result = run_hook(bash(command, tmp_path))
        assert result.returncode == 0
        assert decision(result)["permissionDecision"] == "deny", command


def test_writer_refuses_file_edit_outside_session_worktree(tmp_path):
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    payload = {
        "cwd": str(worktree),
        "toolName": "edit",
        "toolArgs": {"path": str(tmp_path / "elsewhere.txt")},
    }
    result = run_hook(payload)
    assert decision(result)["permissionDecision"] == "deny"


def test_writer_allows_file_edit_inside_session_worktree(tmp_path):
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    payload = {
        "cwd": str(worktree),
        "toolName": "edit",
        "toolArgs": {"path": str(worktree / "inside.txt")},
    }
    result = run_hook(payload)
    assert decision(result) == {}


def test_reviewer_refuses_all_edit_and_create_tools(tmp_path):
    for tool in ("edit", "create"):
        result = run_hook(
            {"cwd": str(tmp_path), "toolName": tool, "toolArgs": {"path": "x"}},
            boundary="reviewer",
        )
        assert decision(result)["permissionDecision"] == "deny"
