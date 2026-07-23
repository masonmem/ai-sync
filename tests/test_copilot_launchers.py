"""Hosted and Laguna launchers must not leak provider state across sessions."""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import textwrap


ROOT = pathlib.Path(__file__).resolve().parent.parent


def fake_commands(tmp_path: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    bindir = tmp_path / "bin"
    bindir.mkdir()
    log = tmp_path / "copilot.json"
    (bindir / "copilot").write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import json, os, sys
            keys = [
                "COPILOT_PROVIDER_BASE_URL",
                "COPILOT_PROVIDER_TYPE",
                "COPILOT_PROVIDER_API_KEY",
                "COPILOT_PROVIDER_BEARER_TOKEN",
                "COPILOT_PROVIDER_WIRE_API",
                "COPILOT_PROVIDER_TRANSPORT",
                "COPILOT_PROVIDER_AZURE_API_VERSION",
                "COPILOT_PROVIDER_MODEL_ID",
                "COPILOT_PROVIDER_WIRE_MODEL",
                "COPILOT_PROVIDER_MAX_PROMPT_TOKENS",
                "COPILOT_PROVIDER_MAX_OUTPUT_TOKENS",
                "COPILOT_PROVIDER_HEADERS",
                "COPILOT_MODEL",
            ]
            data = {
                "argv": sys.argv[1:],
                "env": {key: os.environ[key] for key in keys if key in os.environ},
            }
            open(os.environ["COPILOT_TEST_LOG"], "w").write(json.dumps(data))
            """
        )
    )
    (bindir / "security").write_text("#!/bin/sh\nprintf '%s\\n' test-keychain-secret\n")
    for path in bindir.iterdir():
        path.chmod(0o755)
    return bindir, log


def test_cop_cloud_clears_inherited_byok_state(tmp_path):
    bindir, log = fake_commands(tmp_path)
    env = {
        "HOME": str(tmp_path),
        "PATH": f"{bindir}:{os.environ['PATH']}",
        "COPILOT_TEST_LOG": str(log),
        "COPILOT_PROVIDER_BASE_URL": "https://wrong.invalid",
        "COPILOT_PROVIDER_TYPE": "openai",
        "COPILOT_PROVIDER_API_KEY": "wrong-secret",
        "COPILOT_PROVIDER_WIRE_API": "responses",
        "COPILOT_PROVIDER_TRANSPORT": "websockets",
        "COPILOT_PROVIDER_AZURE_API_VERSION": "2024-10-21",
        "COPILOT_PROVIDER_MODEL_ID": "wrong-base-model",
        "COPILOT_PROVIDER_WIRE_MODEL": "wrong-wire-model",
        "COPILOT_PROVIDER_MAX_PROMPT_TOKENS": "1234",
        "COPILOT_PROVIDER_MAX_OUTPUT_TOKENS": "5678",
        "COPILOT_PROVIDER_HEADERS": "X-Leaked-Header: wrong",
        "COPILOT_MODEL": "wrong-model",
    }

    subprocess.run(
        [str(ROOT / "bin" / "cop-cloud"), "--stream", "on"],
        check=True,
        env=env,
    )
    data = json.loads(log.read_text())

    assert data["env"] == {}
    assert data["argv"][:4] == [
        "--model",
        "gpt-5.6-luna",
        "--max-ai-credits",
        "100",
    ]
    assert data["argv"][-2:] == ["--stream", "on"]
    assert log.stat().st_mode & 0o077 == 0


def test_cop_laguna_loads_nonsecret_config_and_keychain_credential(tmp_path):
    bindir, log = fake_commands(tmp_path)
    config = tmp_path / ".config" / "ai-sync" / "laguna.env"
    config.parent.mkdir(parents=True)
    config.write_text(
        "\n".join(
            (
                "COPILOT_PROVIDER_BASE_URL=https://laguna.invalid/v1",
                "COPILOT_PROVIDER_TYPE=openai",
                "COPILOT_MODEL=exact-model-id",
                "AI_SYNC_LAGUNA_CREDENTIAL_KIND=bearer",
                "",
            )
        )
    )
    config.chmod(0o600)
    env = {
        "HOME": str(tmp_path),
        "PATH": f"{bindir}:{os.environ['PATH']}",
        "COPILOT_TEST_LOG": str(log),
        "USER": "tester",
        "COPILOT_PROVIDER_TRANSPORT": "websockets",
        "COPILOT_PROVIDER_AZURE_API_VERSION": "2024-10-21",
        "COPILOT_PROVIDER_HEADERS": "X-Leaked-Header: wrong",
    }

    subprocess.run([str(ROOT / "bin" / "cop-laguna")], check=True, env=env)
    data = json.loads(log.read_text())

    assert data["env"] == {
        "COPILOT_PROVIDER_BASE_URL": "https://laguna.invalid/v1",
        "COPILOT_PROVIDER_TYPE": "openai",
        "COPILOT_PROVIDER_BEARER_TOKEN": "test-keychain-secret",
        "COPILOT_MODEL": "exact-model-id",
    }
    assert "test-keychain-secret" not in " ".join(data["argv"])
    assert "--no-remote-export" in data["argv"]
    assert log.stat().st_mode & 0o077 == 0
