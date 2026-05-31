"""`ai-sync promote --to base|overlay` moves render drift into the chosen file."""

from __future__ import annotations

import json
import os


def _hostname():
    return os.uname().nodename.split(".")[0]


def _setup_drift(fake_home, ai_sync, base=None, overlay=None, drift=None):
    """Set up render mode + add drift to the rendered file. Returns (overlay_path, settings_path)."""
    base = base or {"theme": "dark-ansi", "advisorModel": "opus"}
    overlay = overlay if overlay is not None else {"theme": "dark"}
    drift = drift or {"newField": "tool-writeback"}

    (fake_home / ".ai-config" / "claude" / "settings.json").write_text(json.dumps(base) + "\n")
    overlay_dir = fake_home / ".ai-config" / "hosts" / _hostname()
    overlay_dir.mkdir(parents=True)
    overlay_path = overlay_dir / "claude-settings.json"
    overlay_path.write_text(json.dumps(overlay) + "\n")
    ai_sync("apply", expect_success=True)

    settings = fake_home / ".claude" / "settings.json"
    data = json.loads(settings.read_text())
    data.update(drift)
    settings.write_text(json.dumps(data) + "\n")
    return overlay_path, settings


def test_promote_to_overlay_adds_drift_keys_to_overlay(fake_home, fake_claude, ai_sync):
    overlay_path, _ = _setup_drift(fake_home, ai_sync)

    ai_sync("promote", "--to", "overlay", "claude", expect_success=True)

    overlay = json.loads(overlay_path.read_text())
    assert overlay["newField"] == "tool-writeback"
    assert overlay["theme"] == "dark"  # original overlay key preserved


def test_promote_to_overlay_clears_drift(fake_home, fake_claude, ai_sync):
    _, settings = _setup_drift(fake_home, ai_sync)

    ai_sync("promote", "--to", "overlay", "claude", expect_success=True)

    # After promote + automatic re-apply, status should be clean
    r = ai_sync("status")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "DRIFTED" not in r.stdout
    # The drift field is now in the rendered output too
    rendered = json.loads(settings.read_text())
    assert rendered["newField"] == "tool-writeback"


def test_promote_to_base_adds_drift_keys_to_base(fake_home, fake_claude, ai_sync):
    _setup_drift(fake_home, ai_sync)

    ai_sync("promote", "--to", "base", "claude", expect_success=True)

    base = json.loads((fake_home / ".ai-config" / "claude" / "settings.json").read_text())
    assert base["newField"] == "tool-writeback"
    assert base["advisorModel"] == "opus"  # original base key preserved


def test_promote_to_base_warns_about_overlay_shadow(fake_home, fake_claude, ai_sync):
    """If a promoted-to-base key is also in the overlay, the overlay still wins
    on this host — promote must warn so the user knows the change won't take
    effect locally."""
    _setup_drift(fake_home, ai_sync,
                 base={"theme": "dark-ansi"},
                 overlay={"theme": "dark"},
                 drift={"theme": "light"})  # tool toggled to light

    r = ai_sync("promote", "--to", "base", "claude")
    # exit code 1 because the warning fires
    assert r.returncode == 1
    assert "still win" in (r.stdout + r.stderr).lower() or "shadow" in (r.stdout + r.stderr).lower()


def test_promote_no_drift_noop(fake_home, fake_claude, ai_sync):
    (fake_home / ".ai-config" / "claude" / "settings.json").write_text(
        json.dumps({"theme": "dark-ansi"}) + "\n"
    )
    overlay_dir = fake_home / ".ai-config" / "hosts" / _hostname()
    overlay_dir.mkdir(parents=True)
    (overlay_dir / "claude-settings.json").write_text(json.dumps({"theme": "dark"}) + "\n")
    ai_sync("apply", expect_success=True)

    r = ai_sync("promote", "--to", "overlay", "claude", expect_success=True)
    assert "no drift" in r.stdout.lower() or "nothing to promote" in r.stdout.lower()


def test_promote_requires_to_arg(fake_home, fake_claude, ai_sync):
    r = ai_sync("promote", "claude")
    assert r.returncode != 0
    assert "--to" in (r.stdout + r.stderr)


def test_promote_to_overlay_no_overlay_says_noop(fake_home, fake_claude, ai_sync):
    """promote with no overlay (symlink mode) should report and exit cleanly."""
    ai_sync("apply", expect_success=True)
    r = ai_sync("promote", "--to", "overlay", "claude", expect_success=True)
    assert "symlink mode" in r.stdout or "nothing to promote" in r.stdout


def test_promote_deletion_only_drift_reports_unsupported(fake_home, fake_claude, ai_sync):
    """If the tool DELETED a key from the rendered file (instead of adding or
    changing one), there's no positive changeset to promote. Promote should
    report this case clearly rather than silently no-op."""
    base = {"theme": "dark-ansi", "advisorModel": "opus"}
    overlay = {"theme": "dark"}
    (fake_home / ".ai-config" / "claude" / "settings.json").write_text(json.dumps(base) + "\n")
    overlay_dir = fake_home / ".ai-config" / "hosts" / _hostname()
    overlay_dir.mkdir(parents=True)
    (overlay_dir / "claude-settings.json").write_text(json.dumps(overlay) + "\n")
    ai_sync("apply", expect_success=True)

    # Simulate the tool removing a key:
    settings = fake_home / ".claude" / "settings.json"
    data = json.loads(settings.read_text())
    del data["advisorModel"]
    settings.write_text(json.dumps(data) + "\n")

    r = ai_sync("promote", "--to", "overlay", "claude", expect_success=True)
    assert "removed keys" in r.stdout or "deletions" in r.stdout


def test_apply_silently_recanonicalizes_formatting_only_changes(fake_home, fake_claude, ai_sync):
    """Hand-formatted rendered file (same JSON content, different whitespace)
    should be re-canonicalized silently, NOT treated as drift."""
    base = {"theme": "dark-ansi"}
    overlay = {"theme": "dark"}
    (fake_home / ".ai-config" / "claude" / "settings.json").write_text(json.dumps(base) + "\n")
    overlay_dir = fake_home / ".ai-config" / "hosts" / _hostname()
    overlay_dir.mkdir(parents=True)
    (overlay_dir / "claude-settings.json").write_text(json.dumps(overlay) + "\n")
    ai_sync("apply", expect_success=True)

    # Reformat the file with different whitespace but same data
    settings = fake_home / ".claude" / "settings.json"
    data = json.loads(settings.read_text())
    settings.write_text(json.dumps(data))  # no trailing newline, no indent

    r = ai_sync("apply", expect_success=True)
    # apply succeeded (didn't refuse with "drifted"); status is clean
    r2 = ai_sync("status")
    assert r2.returncode == 0, r2.stdout + r2.stderr
