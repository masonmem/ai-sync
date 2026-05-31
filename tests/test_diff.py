"""`ai-sync diff` compares render-mode files to their expected render."""

from __future__ import annotations

import json
import os


def _hostname():
    return os.uname().nodename.split(".")[0]


def _seed_render_mode(fake_home, base=None, overlay=None):
    base = base or {"theme": "dark-ansi", "advisorModel": "opus"}
    overlay = overlay if overlay is not None else {"theme": "dark"}
    (fake_home / ".ai-config" / "claude" / "settings.json").write_text(json.dumps(base) + "\n")
    overlay_dir = fake_home / ".ai-config" / "hosts" / _hostname()
    overlay_dir.mkdir(parents=True)
    (overlay_dir / "claude-settings.json").write_text(json.dumps(overlay) + "\n")


def test_diff_no_overlay_reports_symlink_mode(fake_home, fake_claude, ai_sync):
    """Without an overlay, the target is in symlink mode — nothing to diff."""
    ai_sync("apply", expect_success=True)
    r = ai_sync("diff", "claude", expect_success=True)
    assert "symlink mode" in r.stdout
    assert "nothing to diff" in r.stdout


def test_diff_clean_render_says_clean(fake_home, fake_claude, ai_sync):
    _seed_render_mode(fake_home)
    ai_sync("apply", expect_success=True)
    r = ai_sync("diff", "claude", expect_success=True)
    assert "clean" in r.stdout


def test_diff_drifted_render_shows_unified_diff(fake_home, fake_claude, ai_sync):
    _seed_render_mode(fake_home)
    ai_sync("apply", expect_success=True)

    settings = fake_home / ".claude" / "settings.json"
    data = json.loads(settings.read_text())
    data["newField"] = "tool-wrote-this"
    settings.write_text(json.dumps(data) + "\n")

    r = ai_sync("diff", "claude")
    assert r.returncode == 1  # drift = exit 1
    assert "newField" in r.stdout
    assert "tool-wrote-this" in r.stdout


def test_diff_unknown_target_errors(fake_home, fake_claude, ai_sync):
    r = ai_sync("diff", "totally-not-a-target")
    assert r.returncode == 1
    assert "unknown target" in (r.stdout + r.stderr).lower()


def test_diff_all_targets_when_no_arg(fake_home, fake_claude, ai_sync):
    """`ai-sync diff` (no arg) should look at both claude and copilot."""
    _seed_render_mode(fake_home)  # only claude has an overlay
    ai_sync("apply", expect_success=True)
    r = ai_sync("diff", expect_success=True)
    # claude reports clean, copilot reports symlink-mode
    assert "claude" in r.stdout
    assert "copilot" in r.stdout
