"""`ai-sync doctor` prints a fix-hint line for each failure from status."""

from __future__ import annotations

import json
import os


def _hostname():
    return os.uname().nodename.split(".")[0].lower()


def test_doctor_clean_state_says_nothing_to_fix(fake_home, fake_claude, ai_sync):
    ai_sync("apply", expect_success=True)
    r = ai_sync("doctor")
    assert r.returncode == 0
    assert "Everything looks good" in r.stdout


def test_doctor_suggests_apply_for_missing_symlinks(fake_home, fake_claude, ai_sync):
    # Don't apply: symlinks are missing.
    r = ai_sync("doctor")
    assert r.returncode == 1
    assert "MISSING" in r.stdout
    assert "ai-sync apply" in r.stdout


def test_doctor_suggests_chmod_for_loose_secret_perms(fake_home, fake_claude, ai_sync):
    (fake_home / ".ai-config" / "mcp" / "servers.toml").write_text("""
[unifi]
command = "/bin/true"
secrets_env = "${AI_CONFIG}/secrets/unifi.env"
""")
    secrets = fake_home / ".ai-config" / "secrets" / "unifi.env"
    secrets.write_text("X=1\n")
    secrets.chmod(0o644)
    ai_sync("apply", expect_success=True)

    r = ai_sync("doctor")
    assert r.returncode == 1
    assert "loose perms" in r.stdout
    assert f"chmod 600 {secrets}" in r.stdout


def test_doctor_suggests_diff_and_promote_for_drifted_render(fake_home, fake_claude, ai_sync):
    (fake_home / ".ai-config" / "claude" / "settings.json").write_text(
        json.dumps({"theme": "dark-ansi"}) + "\n"
    )
    overlay_dir = fake_home / ".ai-config" / "hosts" / _hostname()
    overlay_dir.mkdir(parents=True)
    (overlay_dir / "claude-settings.json").write_text(json.dumps({"theme": "dark"}) + "\n")
    ai_sync("apply", expect_success=True)

    # Simulate tool writeback
    settings = fake_home / ".claude" / "settings.json"
    data = json.loads(settings.read_text())
    data["newPluginEnabled"] = True
    settings.write_text(json.dumps(data) + "\n")

    r = ai_sync("doctor")
    assert r.returncode == 1
    assert "DRIFTED" in r.stdout
    assert "ai-sync diff claude" in r.stdout
    assert "ai-sync promote --to overlay claude" in r.stdout
    assert "ai-sync promote --to base claude" in r.stdout
