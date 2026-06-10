"""secrets/manifest.toml drives a host-scoped secrets section in status/doctor.

The manifest is the tracked inventory of every gitignored file expected under
secrets/ (mirrors homelab's secrets-inventory.toml). For each entry scoped to
the current host, doctor reports present / missing / loose-perms, using the
entry's `source` recipe as the fix hint. Missing scoped secrets exit 1.
"""

from __future__ import annotations

import os
import textwrap


def _hostname():
    return os.uname().nodename.split(".")[0].lower()


def _write_manifest(fake_home, hosts, file="example.txt",
                    source="keychain: example-keys pull"):
    hosts_toml = ", ".join(f'"{h}"' for h in hosts)
    manifest = fake_home / ".ai-config" / "secrets" / "manifest.toml"
    manifest.write_text(textwrap.dedent(f"""\
        [meta]
        schema_version = 1

        [[secret]]
        file = "{file}"
        hosts = [{hosts_toml}]
        consumer = "test consumer"
        source = "{source}"
        perms = "600"
    """))
    return manifest


def test_doctor_reports_missing_scoped_secret_with_source_recipe(
        fake_home, fake_claude, ai_sync):
    _write_manifest(fake_home, hosts=[_hostname()])
    ai_sync("apply", expect_success=True)

    r = ai_sync("doctor")
    assert r.returncode == 1
    assert "example.txt" in r.stdout
    assert "MISSING" in r.stdout
    # The fix hint is the manifest's source recipe.
    assert "keychain: example-keys pull" in r.stdout


def test_doctor_ignores_secret_scoped_to_another_host(
        fake_home, fake_claude, ai_sync):
    _write_manifest(fake_home, hosts=["some-other-host"])
    ai_sync("apply", expect_success=True)

    r = ai_sync("doctor")
    assert r.returncode == 0
    assert "example.txt" not in r.stdout


def test_status_green_when_scoped_secret_present_with_tight_perms(
        fake_home, fake_claude, ai_sync):
    _write_manifest(fake_home, hosts=[_hostname()])
    secret = fake_home / ".ai-config" / "secrets" / "example.txt"
    secret.write_text("hunter2\n")
    secret.chmod(0o600)
    ai_sync("apply", expect_success=True)

    r = ai_sync("status")
    assert r.returncode == 0
    assert "example.txt" in r.stdout


def test_doctor_warns_chmod_for_loose_manifest_secret_perms(
        fake_home, fake_claude, ai_sync):
    _write_manifest(fake_home, hosts=[_hostname()])
    secret = fake_home / ".ai-config" / "secrets" / "example.txt"
    secret.write_text("hunter2\n")
    secret.chmod(0o644)
    ai_sync("apply", expect_success=True)

    r = ai_sync("doctor")
    assert r.returncode == 1
    assert "loose perms" in r.stdout
    assert f"chmod 600 {secret}" in r.stdout


def test_doctor_warns_on_secret_file_not_in_manifest(
        fake_home, fake_claude, ai_sync):
    _write_manifest(fake_home, hosts=[_hostname()])
    secret = fake_home / ".ai-config" / "secrets" / "example.txt"
    secret.write_text("hunter2\n")
    secret.chmod(0o600)
    stray = fake_home / ".ai-config" / "secrets" / "stale-key.bak"
    stray.write_text("old\n")
    stray.chmod(0o600)
    ai_sync("apply", expect_success=True)

    r = ai_sync("doctor")
    assert r.returncode == 1
    assert "stale-key.bak" in r.stdout
    assert "manifest" in r.stdout


def test_no_manifest_means_no_secrets_manifest_checks(
        fake_home, fake_claude, ai_sync):
    # Stray files in secrets/ are NOT flagged when there's no manifest at all
    # (feature is opt-in via the manifest's presence).
    stray = fake_home / ".ai-config" / "secrets" / "whatever.txt"
    stray.write_text("x\n")
    ai_sync("apply", expect_success=True)

    r = ai_sync("status")
    assert r.returncode == 0
    assert "whatever.txt" not in r.stdout
