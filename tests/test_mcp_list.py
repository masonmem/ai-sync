"""`ai-sync mcp list` prints the canonical registry with placeholders expanded."""

from __future__ import annotations


def test_mcp_list_empty(fake_home, fake_claude, ai_sync):
    r = ai_sync("mcp", "list", expect_success=True)
    assert "no MCP servers" in r.stdout


def test_mcp_list_expands_ai_config_placeholder(fake_home, fake_claude, ai_sync):
    (fake_home / ".ai-config" / "mcp" / "servers.toml").write_text("""
[unifi]
description = "UniFi network"
command = "${AI_CONFIG}/bin/unifi-wrapper.sh"
""")
    r = ai_sync("mcp", "list", expect_success=True)
    ai = fake_home / ".ai-config"
    assert "unifi" in r.stdout
    assert "UniFi network" in r.stdout
    assert f"{ai}/bin/unifi-wrapper.sh" in r.stdout
    assert "${AI_CONFIG}" not in r.stdout
