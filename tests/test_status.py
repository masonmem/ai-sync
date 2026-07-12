"""status must report drift accurately and exit non-zero on drift."""

from __future__ import annotations


def test_status_after_apply_is_clean(fake_home, fake_claude, ai_sync):
    ai_sync("apply", expect_success=True)
    r = ai_sync("status")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "MISSING" not in r.stdout
    assert "DRIFTED" not in r.stdout


def test_status_detects_missing_link(fake_home, fake_claude, ai_sync):
    # Don't apply — the managed links don't exist yet.
    r = ai_sync("status")
    assert r.returncode == 1
    assert "MISSING" in r.stdout


def test_status_detects_drifted_symlink(fake_home, fake_claude, ai_sync):
    ai_sync("apply", expect_success=True)
    link = fake_home / ".copilot" / "copilot-instructions.md"
    link.unlink()
    # Point at a different (valid) target
    (fake_home / ".ai-config" / "wrong.md").write_text("nope")
    link.symlink_to(fake_home / ".ai-config" / "wrong.md")

    r = ai_sync("status")
    assert r.returncode == 1
    assert "DRIFTED" in r.stdout


def test_status_warns_loose_secret_perms(fake_home, fake_claude, ai_sync):
    (fake_home / ".ai-config" / "mcp" / "servers.toml").write_text("""
[unifi]
command = "/bin/true"
secrets_env = "${AI_CONFIG}/secrets/unifi.env"
""")
    secrets = fake_home / ".ai-config" / "secrets" / "unifi.env"
    secrets.write_text("UNIFI_API_KEY=fake\n")
    secrets.chmod(0o644)  # loose

    ai_sync("apply", expect_success=True)
    r = ai_sync("status")
    assert r.returncode == 1
    assert "loose perms" in r.stdout


def test_status_passes_with_tight_secret_perms(fake_home, fake_claude, ai_sync):
    (fake_home / ".ai-config" / "mcp" / "servers.toml").write_text("""
[unifi]
command = "/bin/true"
secrets_env = "${AI_CONFIG}/secrets/unifi.env"
""")
    secrets = fake_home / ".ai-config" / "secrets" / "unifi.env"
    secrets.write_text("UNIFI_API_KEY=fake\n")
    secrets.chmod(0o600)

    ai_sync("apply", expect_success=True)
    r = ai_sync("status")
    assert r.returncode == 0, r.stdout + r.stderr


def test_status_reports_mcp_not_registered_in_claude(fake_home, fake_claude, ai_sync):
    """If servers.toml lists a server but claude doesn't have it registered, status flags it."""
    (fake_home / ".ai-config" / "mcp" / "servers.toml").write_text("""
[unifi]
command = "/bin/true"
""")
    # Don't apply — just status. claude has nothing registered.
    r = ai_sync("status")
    assert r.returncode == 1
    assert "NOT REGISTERED" in r.stdout


def test_status_reports_mcp_not_in_copilot_json(fake_home, fake_claude, ai_sync):
    """status flags a server present in servers.toml but missing from mcp.json."""
    (fake_home / ".ai-config" / "mcp" / "servers.toml").write_text("""
[unifi]
command = "/bin/true"
""")
    # Pre-register in claude (so claude side is OK).
    fake_claude["state"].write_text("unifi\n")
    # Wipe Copilot's mcp.json so its mcpServers block is empty.
    (fake_home / ".ai-config" / "mcp.json").write_text('{"mcpServers": {}}')
    r = ai_sync("status")
    assert r.returncode == 1
    assert "NOT in mcp.json" in r.stdout
