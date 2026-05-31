"""Per-host overlay rendering (Option B: opt-in via overlay file).

By default, settings.json files are symlinks (v1 behaviour — tool runtime
writebacks flow naturally into the canonical tracked file). When a host
overlay file exists at hosts/<hostname>/<overlay-name>, ai-sync switches that
file to render mode: it writes a deep-merged real file. The tradeoff —
runtime writebacks become DRIFT and must be reconciled manually — is the
price of per-host divergence.
"""

from __future__ import annotations

import json
import os


def _hostname():
    return os.uname().nodename.split(".")[0]


def _seed_base(fake_home, theme="dark-ansi", **extra):
    base = {"theme": theme, "advisorModel": "opus", "skipAutoPermissionPrompt": True}
    base.update(extra)
    (fake_home / ".ai-config" / "claude" / "settings.json").write_text(json.dumps(base) + "\n")


def _seed_overlay(fake_home, payload, *, name="claude-settings.json"):
    host = _hostname()
    overlay_dir = fake_home / ".ai-config" / "hosts" / host
    overlay_dir.mkdir(parents=True, exist_ok=True)
    (overlay_dir / name).write_text(json.dumps(payload) + "\n")


# ── default behaviour (no overlay) ──

def test_no_overlay_means_symlink_mode(fake_home, fake_claude, ai_sync):
    """Without an overlay, settings.json must remain a symlink (v1 behaviour)."""
    _seed_base(fake_home)
    ai_sync("apply", expect_success=True)
    settings = fake_home / ".claude" / "settings.json"
    assert settings.is_symlink(), "no overlay → expect symlink, not rendered file"
    assert settings.resolve() == (fake_home / ".ai-config" / "claude" / "settings.json").resolve()


def test_tool_writeback_propagates_through_symlink_with_no_overlay(fake_home, fake_claude, ai_sync):
    """With no overlay, simulated tool writeback to settings.json lands in canonical."""
    _seed_base(fake_home)
    ai_sync("apply", expect_success=True)
    settings = fake_home / ".claude" / "settings.json"
    # Simulate Claude Code toggling a setting via /config:
    settings.write_text(json.dumps({"theme": "dark-ansi", "newKey": "live-edit"}) + "\n")
    # The canonical tracked file should reflect the change (via symlink):
    canonical = json.loads((fake_home / ".ai-config" / "claude" / "settings.json").read_text())
    assert canonical["newKey"] == "live-edit"


# ── opt-in to render mode (overlay exists) ──

def test_overlay_switches_to_render_mode(fake_home, fake_claude, ai_sync):
    _seed_base(fake_home, theme="dark-ansi")
    _seed_overlay(fake_home, {"theme": "dark"})

    ai_sync("apply", expect_success=True)

    settings = fake_home / ".claude" / "settings.json"
    assert settings.is_file() and not settings.is_symlink(), "overlay → expect rendered file"
    rendered = json.loads(settings.read_text())
    assert rendered["theme"] == "dark"
    assert rendered["advisorModel"] == "opus"


def test_apply_replaces_existing_symlink_when_overlay_added(fake_home, fake_claude, ai_sync):
    """User had no overlay, did apply, settings.json is symlink. They add an
    overlay, run apply again — symlink replaced with rendered file."""
    _seed_base(fake_home)
    ai_sync("apply", expect_success=True)
    settings = fake_home / ".claude" / "settings.json"
    assert settings.is_symlink()

    _seed_overlay(fake_home, {"theme": "dark"})
    ai_sync("apply", expect_success=True)

    assert settings.is_file() and not settings.is_symlink()
    assert json.loads(settings.read_text())["theme"] == "dark"


def test_apply_switches_back_to_symlink_when_overlay_removed_clean(fake_home, fake_claude, ai_sync):
    """Overlay deleted + rendered file matches base → safe to swap back to symlink."""
    _seed_base(fake_home)
    _seed_overlay(fake_home, {})  # identity overlay
    ai_sync("apply", expect_success=True)
    settings = fake_home / ".claude" / "settings.json"
    # identity overlay: rendered content == base content (post-roundtrip via json.dumps)

    # Remove overlay
    overlay_path = fake_home / ".ai-config" / "hosts" / _hostname() / "claude-settings.json"
    overlay_path.unlink()
    ai_sync("apply", expect_success=True)

    assert settings.is_symlink(), "no overlay → should be symlink"


def test_apply_refuses_to_swap_render_to_symlink_with_divergent_content(fake_home, fake_claude, ai_sync):
    """Overlay deleted but rendered file has runtime edits → refuse to clobber."""
    _seed_base(fake_home)
    _seed_overlay(fake_home, {"theme": "dark"})
    ai_sync("apply", expect_success=True)

    # Simulate Claude Code writing a new field:
    settings = fake_home / ".claude" / "settings.json"
    data = json.loads(settings.read_text())
    data["newRuntimeField"] = "live-edit"
    settings.write_text(json.dumps(data) + "\n")

    # User removes overlay:
    (fake_home / ".ai-config" / "hosts" / _hostname() / "claude-settings.json").unlink()
    r = ai_sync("apply")
    assert r.returncode != 0
    assert "Reconcile manually" in (r.stdout + r.stderr) or "differs from canonical" in (r.stdout + r.stderr)


# ── deep merge behaviour through apply ──

def test_overlay_merges_nested_dicts(fake_home, fake_claude, ai_sync):
    _seed_base(fake_home, statusLine={"type": "command", "command": "base.sh"})
    _seed_overlay(fake_home, {"statusLine": {"command": "host.sh"}})

    ai_sync("apply", expect_success=True)

    rendered = json.loads((fake_home / ".claude" / "settings.json").read_text())
    assert rendered["statusLine"] == {"type": "command", "command": "host.sh"}


def test_overlay_replaces_lists_wholesale(fake_home, fake_claude, ai_sync):
    _seed_base(fake_home, allowedTools=["Bash", "Read"])
    _seed_overlay(fake_home, {"allowedTools": ["Read"]})

    ai_sync("apply", expect_success=True)

    rendered = json.loads((fake_home / ".claude" / "settings.json").read_text())
    assert rendered["allowedTools"] == ["Read"]


# ── idempotency in render mode ──

def test_render_mode_apply_is_idempotent(fake_home, fake_claude, ai_sync):
    _seed_base(fake_home)
    _seed_overlay(fake_home, {"theme": "dark"})
    ai_sync("apply", expect_success=True)
    settings = fake_home / ".claude" / "settings.json"
    mtime_before = settings.stat().st_mtime_ns

    ai_sync("apply", expect_success=True)
    mtime_after = settings.stat().st_mtime_ns

    assert mtime_before == mtime_after, "second apply must not rewrite identical rendered file"


# ── the writeback trap ──

def test_apply_refuses_to_clobber_drifted_render(fake_home, fake_claude, ai_sync):
    """Tool wrote back to rendered file → apply refuses without --force."""
    _seed_base(fake_home)
    _seed_overlay(fake_home, {"theme": "dark"})
    ai_sync("apply", expect_success=True)

    settings = fake_home / ".claude" / "settings.json"
    data = json.loads(settings.read_text())
    data["newKeyFromTool"] = "would-be-lost"
    settings.write_text(json.dumps(data) + "\n")

    r = ai_sync("apply")
    assert r.returncode != 0
    assert "drifted" in (r.stdout + r.stderr).lower()
    # The drifted content is preserved on disk:
    assert json.loads(settings.read_text())["newKeyFromTool"] == "would-be-lost"


def test_apply_force_overwrites_drifted_render(fake_home, fake_claude, ai_sync):
    _seed_base(fake_home)
    _seed_overlay(fake_home, {"theme": "dark"})
    ai_sync("apply", expect_success=True)

    settings = fake_home / ".claude" / "settings.json"
    data = json.loads(settings.read_text())
    data["newKeyFromTool"] = "discard-me"
    settings.write_text(json.dumps(data) + "\n")

    ai_sync("apply", "--force", expect_success=True)

    rendered = json.loads(settings.read_text())
    assert "newKeyFromTool" not in rendered
    assert rendered["theme"] == "dark"


# ── status drift detection in render mode ──

def test_status_clean_with_overlay(fake_home, fake_claude, ai_sync):
    _seed_base(fake_home)
    _seed_overlay(fake_home, {"theme": "dark"})
    ai_sync("apply", expect_success=True)

    r = ai_sync("status")
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"hosts/{_hostname()}/claude-settings.json" in r.stdout


def test_status_detects_runtime_writeback(fake_home, fake_claude, ai_sync):
    _seed_base(fake_home)
    _seed_overlay(fake_home, {"theme": "dark"})
    ai_sync("apply", expect_success=True)

    settings = fake_home / ".claude" / "settings.json"
    data = json.loads(settings.read_text())
    data["wroteBack"] = True
    settings.write_text(json.dumps(data) + "\n")

    r = ai_sync("status")
    assert r.returncode == 1
    assert "DRIFTED" in r.stdout


def test_status_detects_symlink_when_overlay_exists(fake_home, fake_claude, ai_sync):
    """If user adds overlay but doesn't run apply, status nudges them to."""
    _seed_base(fake_home)
    # Make settings.json a symlink manually (simulating pre-overlay state)
    (fake_home / ".claude" / "settings.json").symlink_to(
        fake_home / ".ai-config" / "claude" / "settings.json"
    )
    _seed_overlay(fake_home, {"theme": "dark"})

    r = ai_sync("status")
    assert r.returncode == 1
    assert "STILL A SYMLINK" in r.stdout


# ── invalid overlay ──

def test_apply_rejects_invalid_overlay_json(fake_home, fake_claude, ai_sync):
    _seed_base(fake_home)
    host = _hostname()
    overlay_dir = fake_home / ".ai-config" / "hosts" / host
    overlay_dir.mkdir(parents=True)
    (overlay_dir / "claude-settings.json").write_text("{this is not json")

    r = ai_sync("apply")
    assert r.returncode != 0
    assert "invalid JSON" in (r.stdout + r.stderr)
