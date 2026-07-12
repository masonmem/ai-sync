"""apply must create the canonical symlinks into ~/.claude and ~/.copilot."""

from __future__ import annotations


def _is_link_to(link, target):
    return link.is_symlink() and link.resolve() == target.resolve()


def test_apply_creates_claude_symlinks(fake_home, fake_claude, ai_sync):
    ai_sync("apply", expect_success=True)
    ai = fake_home / ".ai-config"
    # CLAUDE.md and skills are owned by bin/ai-sync-doctor since the 2026-07
    # consolidation (real @-import file + per-skill links); apply manages only:
    assert _is_link_to(fake_home / ".claude" / "bin",           ai / "bin")
    assert _is_link_to(fake_home / ".claude" / "secrets",       ai / "secrets")
    assert _is_link_to(fake_home / ".claude" / "settings.json", ai / "claude" / "settings.json")


def test_apply_creates_copilot_symlinks(fake_home, fake_claude, ai_sync):
    ai_sync("apply", expect_success=True)
    ai = fake_home / ".ai-config"
    assert _is_link_to(fake_home / ".copilot" / "copilot-instructions.md", ai / "agents" / "general.md")
    assert _is_link_to(fake_home / ".copilot" / "mcp-config.json",         ai / "mcp.json")
    assert _is_link_to(fake_home / ".copilot" / "settings.json",           ai / "copilot" / "settings.json")


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
    assert "refuse to clobber" in (r.stdout + r.stderr).lower()
    # The blocker is still there
    assert blocker.is_file() and not blocker.is_symlink()
    assert blocker.read_text() == "important user file, do not nuke"
