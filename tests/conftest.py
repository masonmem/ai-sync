"""Shared pytest fixtures for ai-sync tests.

Every test runs against an isolated $HOME / $AI_CONFIG tree under tmp_path and
a fake `claude` binary on PATH that records argv and simulates the registration
state. No real network, no real `claude` invocation, no touching the user's
actual ~/.ai-config.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import textwrap

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
AI_SYNC = REPO_ROOT / "bin" / "ai-sync"


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """Build an isolated ~/.ai-config with the minimum file tree ai-sync expects.

    Returns the fake HOME path. Sets HOME and AI_CONFIG env vars and seeds an
    initial git commit so `git diff --quiet` succeeds.
    """
    home = tmp_path / "home"
    ai = home / ".ai-config"
    ai.mkdir(parents=True)
    (ai / "skills").mkdir()
    (ai / "bin").mkdir()
    (ai / "secrets").mkdir()
    (ai / "claude").mkdir()
    (ai / "copilot").mkdir()
    (ai / "mcp").mkdir()
    (ai / "instructions.md").write_text("# test instructions\n")
    (ai / "claude" / "settings.json").write_text("{}\n")
    (ai / "copilot" / "settings.json").write_text("{}\n")
    (ai / "mcp.json").write_text('{"mcpServers": {}}\n')

    (home / ".claude").mkdir()
    (home / ".copilot").mkdir()

    # Seed a git repo so the dirty-tree check has something to compare against.
    env = os.environ | {
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
    }
    run = lambda *a: subprocess.run(a, cwd=ai, check=True, env=env, capture_output=True)
    run("git", "init", "-q", "-b", "main")
    run("git", "config", "user.email", "test@example.invalid")
    run("git", "config", "user.name", "test")
    run("git", "add", ".")
    run("git", "commit", "-q", "-m", "init")

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("AI_CONFIG", str(ai))
    monkeypatch.delenv("NO_COLOR", raising=False)
    return home


@pytest.fixture
def fake_claude(tmp_path, monkeypatch):
    """Install a stub `claude` binary that records argv and tracks registrations.

    State files (all under tmp_path):
        log    — each invocation written as: one argv per line, terminated by `---`
        state  — list of currently-registered MCP server names (one per line)

    Behaviour:
        `claude mcp get NAME`           exits 0 iff NAME is in state.
        `claude mcp add ... NAME CMD`   appends NAME to state, exits 0.
        anything else                   exits 0 (we don't model it).

    ASCII-only delimiters so we don't trip macOS bash's C-locale single-byte
    handling — early versions of this fixture used U+00A6 and lost the lead byte.
    """
    bindir = tmp_path / "fakebin"
    bindir.mkdir()
    log = tmp_path / "claude.log"
    state = tmp_path / "claude.state"
    log.write_text("")
    state.write_text("")

    script = textwrap.dedent(f"""\
        #!/usr/bin/env bash
        for a in "$@"; do printf '%s\\n' "$a"; done >> "{log}"
        printf -- '---\\n' >> "{log}"

        if [[ "$1" == "mcp" && "$2" == "get" ]]; then
          grep -qx "$3" "{state}" && exit 0 || exit 1
        fi
        if [[ "$1" == "mcp" && "$2" == "add" ]]; then
          # argv: mcp add --scope user NAME COMMAND [ARGS...]
          grep -qx "$5" "{state}" || echo "$5" >> "{state}"
          exit 0
        fi
        if [[ "$1" == "mcp" && "$2" == "list" ]]; then
          cat "{state}"
          exit 0
        fi
        exit 0
    """)
    (bindir / "claude").write_text(script)
    (bindir / "claude").chmod(0o755)

    monkeypatch.setenv("PATH", f"{bindir}:{os.environ['PATH']}")
    return {"log": log, "state": state}


def parse_invocations(log_path):
    """Parse a fake_claude log into a list[list[str]] of argvs."""
    text = log_path.read_text()
    chunks = [c for c in text.split("---\n") if c.strip()]
    return [chunk.strip("\n").split("\n") for chunk in chunks]


def run_ai_sync(*args, expect_success=False):
    """Invoke bin/ai-sync as a subprocess. Returns CompletedProcess."""
    r = subprocess.run(
        [sys.executable, str(AI_SYNC), *args],
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    if expect_success and r.returncode != 0:
        raise AssertionError(
            f"ai-sync {' '.join(args)} failed ({r.returncode}):\n"
            f"--- stdout ---\n{r.stdout}\n--- stderr ---\n{r.stderr}"
        )
    return r


@pytest.fixture
def ai_sync():
    return run_ai_sync
