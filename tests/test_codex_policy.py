"""Codex MCP and plugin policy must be reconciled from ai-sync."""

from __future__ import annotations

import json
import tomllib

from conftest import parse_invocations


def _seed_servers(fake_home):
    (fake_home / ".ai-config" / "mcp" / "servers.toml").write_text("""
[context7]
command = "${AI_CONFIG}/bin/context7-wrapper.sh"
args = ["--stdio"]

[claude-only]
command = "/bin/true"
clients = ["claude"]
""")


def _codex_invocations(fake_codex):
    return parse_invocations(fake_codex["log"])


def test_apply_registers_selected_mcp_servers_in_codex(fake_home, fake_claude, fake_codex, ai_sync):
    _seed_servers(fake_home)

    ai_sync("apply", expect_success=True)

    state = json.loads(fake_codex["state"].read_text())
    assert state == {
        "context7": {
            "command": str(fake_home / ".ai-config" / "bin" / "context7-wrapper.sh"),
            "args": ["--stdio"],
        }
    }


def test_apply_replaces_drifted_codex_mcp_registration(fake_home, fake_claude, fake_codex, ai_sync):
    _seed_servers(fake_home)
    fake_codex["state"].write_text(json.dumps({
        "context7": {"command": "/old/context7", "args": []},
    }) + "\n")

    ai_sync("apply", expect_success=True)

    calls = _codex_invocations(fake_codex)
    assert ["mcp", "remove", "context7"] in calls
    assert [
        "mcp", "add", "context7", "--",
        str(fake_home / ".ai-config" / "bin" / "context7-wrapper.sh"),
        "--stdio",
    ] in calls


def test_apply_enforces_codex_plugin_policy_without_clobbering_other_config(
    fake_home, fake_claude, fake_codex, ai_sync
):
    policy_dir = fake_home / ".ai-config" / "codex"
    policy_dir.mkdir()
    (policy_dir / "plugins.toml").write_text("""
[plugins]
"github@claude-plugins-official" = false
"playwright@claude-plugins-official" = false
""")
    config = fake_home / ".codex" / "config.toml"
    config.write_text("""model = "gpt-test"

[plugins."github@claude-plugins-official"]
enabled = true
""")

    ai_sync("apply", expect_success=True)

    parsed = tomllib.loads(config.read_text())
    assert parsed["model"] == "gpt-test"
    assert parsed["plugins"]["github@claude-plugins-official"]["enabled"] is False
    assert parsed["plugins"]["playwright@claude-plugins-official"]["enabled"] is False


def test_codex_plugin_policy_apply_is_idempotent(fake_home, fake_claude, fake_codex, ai_sync):
    policy_dir = fake_home / ".ai-config" / "codex"
    policy_dir.mkdir()
    (policy_dir / "plugins.toml").write_text("""
[plugins]
"github@claude-plugins-official" = false
""")

    ai_sync("apply", expect_success=True)
    config = fake_home / ".codex" / "config.toml"
    before = config.stat().st_mtime_ns

    ai_sync("apply", expect_success=True)

    assert config.stat().st_mtime_ns == before


def test_status_detects_codex_plugin_policy_drift(fake_home, fake_claude, fake_codex, ai_sync):
    policy_dir = fake_home / ".ai-config" / "codex"
    policy_dir.mkdir()
    (policy_dir / "plugins.toml").write_text("""
[plugins]
"github@claude-plugins-official" = false
""")
    (fake_home / ".codex" / "config.toml").write_text("""
[plugins."github@claude-plugins-official"]
enabled = true
""")

    result = ai_sync("status")

    assert result.returncode == 1
    assert "github@claude-plugins-official" in result.stdout
    assert "DRIFTED" in result.stdout
