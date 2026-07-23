"""Canonical instructions and client settings must enforce CLI-first tool selection."""

from __future__ import annotations

import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_global_instructions_prefer_structured_cli_over_equivalent_mcp():
    instructions = (ROOT / "agents" / "general.md").read_text().lower()

    assert "cli" in instructions
    assert "mcp" in instructions
    assert "structured" in instructions
    assert "gh" in instructions


def test_global_instructions_enforce_personal_worktree_and_artifact_boundaries():
    instructions = (ROOT / "agents" / "general.md").read_text().lower()

    for requirement in (
        "repository root",
        "current worktree",
        "canonical checkout",
        "generated code",
        "regression test",
        "smallest relevant validation",
        "data classification",
        ".local/share/ai-sync/projects",
        "do not create ai workflow artifacts",
    ):
        assert requirement in instructions


def test_redundant_claude_plugins_are_disabled():
    settings = json.loads((ROOT / "claude" / "settings.json").read_text())
    enabled = settings["enabledPlugins"]

    assert enabled["github@claude-plugins-official"] is False
    assert enabled["playwright@claude-plugins-official"] is False
    assert enabled["security-guidance@claude-plugins-official"] is False
    assert enabled["chrome-devtools-mcp@claude-plugins-official"] is True


def test_notes_skill_uses_native_files_in_opencode():
    skill = (ROOT / "skills" / "personal" / "notes-vault" / "SKILL.md").read_text().lower()

    assert "opencode" in skill
    assert "native file" in skill
    assert "notes mcp" not in skill
