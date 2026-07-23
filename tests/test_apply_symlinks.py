"""apply must create the canonical symlinks into ~/.claude and ~/.copilot."""

from __future__ import annotations

import socket


def _is_link_to(link, target):
    return link.is_symlink() and link.resolve() == target.resolve()


def test_apply_creates_claude_symlinks(fake_home, fake_claude, ai_sync):
    ai_sync("apply", expect_success=True)
    ai = fake_home / ".ai-config"
    assert (fake_home / ".claude" / "CLAUDE.md").read_text() == "@~/code/ai-sync/agents/general.md"
    assert _is_link_to(fake_home / ".claude" / "bin",           ai / "bin")
    assert _is_link_to(fake_home / ".claude" / "secrets",       ai / "secrets")
    assert _is_link_to(fake_home / ".claude" / "settings.json", ai / "claude" / "settings.json")


def test_apply_creates_copilot_symlinks(fake_home, fake_claude, ai_sync):
    ai_sync("apply", expect_success=True)
    ai = fake_home / ".ai-config"
    assert _is_link_to(fake_home / ".copilot" / "copilot-instructions.md", ai / "agents" / "general.md")
    assert _is_link_to(fake_home / ".copilot" / "mcp-config.json",         ai / "mcp.json")
    assert _is_link_to(fake_home / ".copilot" / "settings.json",           ai / "copilot" / "settings.json")


def test_apply_creates_independent_skill_hubs(fake_home, fake_claude, ai_sync):
    ai = fake_home / ".ai-config"
    skill = ai / "skills" / "general" / "portable-skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("---\nname: portable-skill\ndescription: test\n---\n")

    ai_sync("apply", expect_success=True)

    for hub in (
        fake_home / ".claude" / "skills",
        fake_home / ".copilot" / "skills",
        fake_home / ".codex" / "skills",
    ):
        assert _is_link_to(hub / "portable-skill", skill)
    assert not (fake_home / ".agents" / "skills").exists()


def test_apply_removes_legacy_agents_skill_alias(fake_home, fake_claude, ai_sync):
    legacy = fake_home / ".agents" / "skills"
    legacy.parent.mkdir()
    legacy.symlink_to(fake_home / ".claude" / "skills")

    ai_sync("apply", expect_success=True)

    assert not legacy.exists()


def test_apply_creates_copilot_agent_and_hook_symlinks(
    fake_home, fake_claude, ai_sync
):
    ai = fake_home / ".ai-config"
    agent = ai / "agents" / "copilot" / "implementation-writer.agent.md"
    hook = ai / "hooks" / "copilot" / "guard.json"
    agent.parent.mkdir()
    hook.parent.mkdir(parents=True)
    agent.write_text("---\ndescription: Writes code\n---\n")
    hook.write_text("{}\n")

    ai_sync("apply", expect_success=True)

    assert _is_link_to(
        fake_home / ".copilot" / "agents" / agent.name,
        agent,
    )
    assert _is_link_to(
        fake_home / ".copilot" / "hooks" / hook.name,
        hook,
    )


def test_general_scope_never_installs_personal_skills(
    fake_home, fake_claude, ai_sync, monkeypatch
):
    ai = fake_home / ".ai-config"
    host = socket.gethostname().split(".", 1)[0].lower()
    (ai / "hosts" / host).mkdir(parents=True)
    personal = ai / "skills" / "personal" / "home-only"
    personal.mkdir()
    (personal / "SKILL.md").write_text("---\nname: home-only\n---\n")
    monkeypatch.setenv("AI_SYNC_SKILL_SCOPE", "general")

    ai_sync("apply", expect_success=True)

    for hub in (
        fake_home / ".claude" / "skills",
        fake_home / ".copilot" / "skills",
        fake_home / ".codex" / "skills",
    ):
        assert not (hub / "home-only").exists()


def test_work_profile_preserves_machine_local_client_configuration(
    fake_home, fake_claude, ai_sync, monkeypatch
):
    ai = fake_home / ".ai-config"
    copilot = fake_home / ".copilot"
    claude = fake_home / ".claude"
    codex = fake_home / ".codex"
    local_files = {
        copilot / "mcp-config.json": '{"mcpServers":{"work":{}}}\n',
        copilot / "settings.json": '{"model":"work-model"}\n',
        claude / "settings.json": '{"workSetting":true}\n',
        codex / "config.toml": 'model = "work-model"\n',
    }
    for path, content in local_files.items():
        path.write_text(content)
    (ai / "codex").mkdir()
    (ai / "codex" / "plugins.toml").write_text(
        '[plugins]\n"github@claude-plugins-official" = false\n'
    )
    monkeypatch.setenv("AI_SYNC_PROFILE", "work")
    monkeypatch.setenv("AI_SYNC_SKILL_SCOPE", "general")

    ai_sync("apply", expect_success=True)
    status = ai_sync("status")

    assert status.returncode == 0, status.stdout + status.stderr
    for path, content in local_files.items():
        assert path.read_text() == content
        assert not path.is_symlink()
    for path in (
        copilot / "bin",
        copilot / "secrets",
        claude / "bin",
        claude / "secrets",
    ):
        assert not path.exists()


def test_apply_skips_tool_homes_that_dont_exist(fake_home, fake_claude, ai_sync):
    # Remove ~/.copilot before apply; the script should silently skip it.
    import shutil
    shutil.rmtree(fake_home / ".copilot")
    ai_sync("apply", expect_success=True)
    assert not (fake_home / ".copilot").exists()
    # Claude links still made
    assert (fake_home / ".claude" / "bin").is_symlink()


def test_apply_idempotent(fake_home, fake_claude, ai_sync):
    """Two consecutive applies produce the same end state and don't churn symlinks."""
    ai_sync("apply", expect_success=True)
    link = fake_home / ".copilot" / "copilot-instructions.md"
    inode_before = link.lstat().st_ino

    ai_sync("apply", expect_success=True)

    inode_after = link.lstat().st_ino
    # ln -sfn semantics: if the link already points at the right target, we
    # don't unlink+create, so the inode should be stable.
    assert inode_before == inode_after, "apply should not churn already-correct symlinks"


def test_apply_replaces_drifted_symlink(fake_home, fake_claude, ai_sync):
    """If a link points at the wrong target, apply must repoint it."""
    ai = fake_home / ".ai-config"
    link = fake_home / ".copilot" / "copilot-instructions.md"
    # Point it at the wrong target
    (ai / "wrong.md").write_text("nope")
    link.symlink_to(ai / "wrong.md")
    assert link.resolve() == (ai / "wrong.md").resolve()

    ai_sync("apply", expect_success=True)

    assert link.resolve() == (ai / "agents" / "general.md").resolve()


def test_apply_refuses_to_clobber_physical_file(fake_home, fake_claude, ai_sync):
    """If a physical (non-symlink) file is in the way, apply must refuse, not silently delete."""
    blocker = fake_home / ".copilot" / "copilot-instructions.md"
    blocker.write_text("important user file, do not nuke")

    r = ai_sync("apply")
    assert r.returncode != 0
    assert "real file/dir in the way" in (r.stdout + r.stderr).lower()
    # The blocker is still there
    assert blocker.is_file() and not blocker.is_symlink()
    assert blocker.read_text() == "important user file, do not nuke"
