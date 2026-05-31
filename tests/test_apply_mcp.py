"""apply must register MCP servers in both clients idempotently."""

from __future__ import annotations

import json

from conftest import parse_invocations


SERVERS_TOML = """
[unifi]
command = "${AI_CONFIG}/bin/unifi-wrapper.sh"
secrets_env = "${AI_CONFIG}/secrets/unifi.env"

[weather]
command = "${HOME}/.local/bin/weather-mcp"
"""


def _seed_servers(fake_home, content=SERVERS_TOML):
    (fake_home / ".ai-config" / "mcp" / "servers.toml").write_text(content)


def _seed_wrappers(fake_home):
    ai = fake_home / ".ai-config"
    (ai / "bin" / "unifi-wrapper.sh").write_text("#!/bin/sh\nexit 0\n")
    (ai / "bin" / "unifi-wrapper.sh").chmod(0o755)


def _claude_adds(fake_claude):
    """Return list[argv] of every `claude mcp add` invocation recorded."""
    return [argv for argv in parse_invocations(fake_claude["log"])
            if argv[:2] == ["mcp", "add"]]


# ── claude registration ──

def test_apply_mcp_registers_each_server_in_claude(fake_home, fake_claude, ai_sync):
    _seed_servers(fake_home)
    _seed_wrappers(fake_home)

    ai_sync("apply", expect_success=True)

    adds = _claude_adds(fake_claude)
    names = {argv[4] for argv in adds}  # argv: mcp add --scope user NAME COMMAND
    assert names == {"unifi", "weather"}


def test_apply_mcp_expands_placeholders_in_claude_command(fake_home, fake_claude, ai_sync):
    _seed_servers(fake_home)
    _seed_wrappers(fake_home)

    ai_sync("apply", expect_success=True)

    adds = {argv[4]: argv[5] for argv in _claude_adds(fake_claude)}
    ai = fake_home / ".ai-config"
    assert adds["unifi"]   == f"{ai}/bin/unifi-wrapper.sh"
    assert adds["weather"] == f"{fake_home}/.local/bin/weather-mcp"


def test_apply_mcp_skips_already_registered_in_claude(fake_home, fake_claude, ai_sync):
    _seed_servers(fake_home)
    _seed_wrappers(fake_home)

    ai_sync("apply", expect_success=True)
    adds_before = len(_claude_adds(fake_claude))

    ai_sync("apply", expect_success=True)
    adds_after = len(_claude_adds(fake_claude))

    assert adds_after == adds_before, "second apply must not re-add already-registered servers"


def test_apply_mcp_respects_host_filter(fake_home, fake_claude, ai_sync):
    (fake_home / ".ai-config" / "mcp" / "servers.toml").write_text("""
[only-elsewhere]
command = "/bin/true"
hosts = ["some-other-host-that-doesnt-exist"]

[unifi]
command = "/bin/true"
""")
    ai_sync("apply", expect_success=True)
    names = {argv[4] for argv in _claude_adds(fake_claude)}
    assert names == {"unifi"}


def test_apply_mcp_respects_client_filter_for_claude(fake_home, fake_claude, ai_sync):
    (fake_home / ".ai-config" / "mcp" / "servers.toml").write_text("""
[copilot-only]
command = "/bin/true"
clients = ["copilot"]

[unifi]
command = "/bin/true"
""")
    ai_sync("apply", expect_success=True)
    names = {argv[4] for argv in _claude_adds(fake_claude)}
    assert names == {"unifi"}, "copilot-only must not be registered in claude"


def test_apply_works_without_servers_toml(fake_home, fake_claude, ai_sync):
    """No registry file = no MCP work, but apply still succeeds."""
    ai_sync("apply", expect_success=True)
    assert _claude_adds(fake_claude) == []


def test_apply_without_claude_cli_logs_and_continues(fake_home, monkeypatch, ai_sync):
    """If claude isn't on PATH, MCP registration is skipped but apply still succeeds."""
    _seed_servers(fake_home)
    # Strip claude from PATH (we never install fake_claude in this test).
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    r = ai_sync("apply", expect_success=True)
    assert "claude CLI not installed" in r.stdout


# ── copilot mcp.json generation ──

def test_apply_writes_copilot_mcp_json_from_registry(fake_home, fake_claude, ai_sync):
    _seed_servers(fake_home)
    _seed_wrappers(fake_home)

    ai_sync("apply", expect_success=True)

    mcp_json = json.loads((fake_home / ".ai-config" / "mcp.json").read_text())
    servers = mcp_json["mcpServers"]
    assert set(servers.keys()) == {"unifi", "weather"}
    assert servers["unifi"]["type"] == "local"
    assert servers["unifi"]["command"] == f"{fake_home / '.ai-config'}/bin/unifi-wrapper.sh"
    assert servers["weather"]["command"] == f"{fake_home}/.local/bin/weather-mcp"


def test_apply_copilot_mcp_json_omits_host_filtered(fake_home, fake_claude, ai_sync):
    (fake_home / ".ai-config" / "mcp" / "servers.toml").write_text("""
[unifi]
command = "/bin/true"

[only-elsewhere]
command = "/bin/true"
hosts = ["nope"]
""")
    ai_sync("apply", expect_success=True)
    mcp_json = json.loads((fake_home / ".ai-config" / "mcp.json").read_text())
    assert set(mcp_json["mcpServers"].keys()) == {"unifi"}


def test_apply_copilot_mcp_json_respects_client_filter(fake_home, fake_claude, ai_sync):
    (fake_home / ".ai-config" / "mcp" / "servers.toml").write_text("""
[claude-only]
command = "/bin/true"
clients = ["claude"]

[unifi]
command = "/bin/true"
""")
    ai_sync("apply", expect_success=True)
    mcp_json = json.loads((fake_home / ".ai-config" / "mcp.json").read_text())
    assert set(mcp_json["mcpServers"].keys()) == {"unifi"}


def test_apply_copilot_mcp_json_idempotent(fake_home, fake_claude, ai_sync):
    """If the generated content hasn't changed, mcp.json mtime stays stable."""
    _seed_servers(fake_home)
    ai_sync("apply", expect_success=True)
    mcp_path = fake_home / ".ai-config" / "mcp.json"
    mtime_before = mcp_path.stat().st_mtime_ns

    ai_sync("apply", expect_success=True)
    mtime_after = mcp_path.stat().st_mtime_ns

    assert mtime_before == mtime_after, "regenerating identical mcp.json must not bump mtime"
