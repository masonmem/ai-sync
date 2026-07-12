# ~/code/ai-sync

[![tests](https://github.com/masonmem/ai-sync/actions/workflows/test.yml/badge.svg)](https://github.com/masonmem/ai-sync/actions/workflows/test.yml)

Personal AI brain — global instructions, custom skills, MCP wrappers, and per-tool settings. Shared by **Claude Code**, **Copilot CLI**, and **Codex** through their native home-directory surfaces; reproducible across machines via [`bin/ai-sync`](bin/ai-sync).

Sibling to [my dotfiles repo](https://github.com/masonmem/dotfiles): dotfiles configures the *machine*, this repo configures the *AI brain* on top of it.

## TL;DR

```bash
ai-sync status                    # what's linked, what's drifted, MCP state; exit 1 if anything's off
ai-sync apply                     # idempotent: re-link, re-register, regenerate mcp.json
ai-sync apply --pull              # git pull --ff-only first
ai-sync apply --force             # overwrite drifted rendered files (loses tool writebacks)
ai-sync doctor                    # status + a one-line suggested fix per failure
ai-sync diff [claude|copilot]     # for render-mode targets: unified diff of file vs expected render
ai-sync promote --to overlay [claude|copilot]   # move render drift into per-host overlay
ai-sync promote --to base    [claude|copilot]   # move render drift into shared base (warns on overlay shadow)
ai-sync mcp list                  # parsed mcp/servers.toml
ai-sync test                      # pytest tests/
```

All commands are reachable via the symlink at `~/.claude/bin/ai-sync` and `~/.copilot/bin/ai-sync`, or by the absolute path `~/code/ai-sync/bin/ai-sync`. The CLI requires **Python 3.11+** (for `tomllib`).

The full architecture, including the scope-by-path rule, the per-host overlay writeback trap, and the rationale for not maintaining a canonical-config DSL, lives in [`docs/architecture.md`](docs/architecture.md). Start there before making structural changes.

## Layout

| Path | Tracked? | Scope | Purpose |
|---|---|---|---|
| `agents/general.md`     | ✅ | shared | Global instructions linked/imported by all three clients |
| `skills/general/`       | ✅ | all hosts | Portable skills (currently reserved/empty) |
| `skills/personal/`      | ✅ | personal hosts | Machine/homelab-aware skills, linked per skill |
| `rules/`                | ✅ | Claude only | Optional shared Claude rules; linked only when non-empty |
| `bin/`                  | ✅ | shared | `ai-sync` CLI, MCP/statusline wrapper scripts |
| `mcp/servers.toml`      | ✅ | translated | **Single source of truth for MCP servers.** Read by `ai-sync apply`. |
| `mcp.json`              | ❌ (gitignored) | generated | Copilot's mcp.json — regenerated each `ai-sync apply` from `mcp/servers.toml`; embeds machine-absolute paths, so it can't be tracked. Do not hand-edit. |
| `copilot/settings.json` | ✅ | Copilot only | Copilot CLI native settings |
| `claude/settings.json`  | ✅ | Claude Code only | Claude Code native settings (theme, plugins, statusLine, etc.) |
| `docs/architecture.md`  | ✅ | docs | The "where does this go?" rule |
| `tests/`                | ✅ | tests | pytest suite for `bin/ai-sync` |
| `hosts/<host>/*.json`   | ✅ (when present) | per-host overlay + host identity | Optional settings overlays; the host directory also marks a personal machine eligible for `skills/personal/`. |
| `secrets/`              | ❌ (gitignored) | per-machine | `.env` files sourced by `bin/*-wrapper.sh` |
| `state/`                | ❌ (gitignored) | per-machine | Wrapper runtime side-effects (e.g. UniFi audit logs) |

The path tells you the scope. There's no decision tree beyond that — see [`docs/architecture.md`](docs/architecture.md).

## Bootstrap a new machine

Order matters: **dotfiles first** — `brew bundle` there provides Python 3.11+ (python@3.14) and jq, which `ai-sync` needs. Then:

```bash
# 1. ~/dotfiles bootstrapped (brew bundle done — gives python 3.11+)
# 2. Clone this repo
git clone git@github.com:masonmem/ai-sync.git ~/code/ai-sync
chmod +x ~/code/ai-sync/bin/ai-sync ~/code/ai-sync/bin/*.sh
# 3. Apply (instruction/skill fan-out, settings, MCP registration/generation)
~/code/ai-sync/bin/ai-sync apply
# 4. Populate secrets, guided by the manifest:
~/code/ai-sync/bin/ai-sync doctor   # lists every secret THIS host needs + how to obtain each
# Restart any running Claude Code session so it loads new MCP servers.
```

`ai-sync apply` requires Python 3.11+ (for `tomllib`). If Python is unavailable, [`bin/bootstrap-claude.sh`](bin/bootstrap-claude.sh) performs the safe Claude/link subset using the portable shell doctor.

### Secrets manifest

[`secrets/manifest.toml`](secrets/manifest.toml) is the tracked inventory of the gitignored files in `secrets/`: per entry — file name, which hosts need it, what consumes it, and a one-line recipe for obtaining it (never the value itself). `ai-sync doctor` and `status` check it: missing required-on-this-host files fail (exit 1) with the recipe as the fix hint, loose perms warn, and unlisted files in `secrets/` warn. Adding a secret file? Add its `[[secret]]` entry in the same commit.

### Existing machine that still has `~/.copilot/` from the old layout

```bash
# Run on the host whose ~/.copilot/.git/ is still a physical clone.
# Idempotent — exits cleanly if already migrated.
curl -fsSLo /tmp/migrate-from-copilot.sh \
  https://raw.githubusercontent.com/masonmem/ai-sync/main/bin/migrate-from-copilot.sh
bash /tmp/migrate-from-copilot.sh --dry   # preview
bash /tmp/migrate-from-copilot.sh         # do it
~/code/ai-sync/bin/ai-sync apply
```

### Ongoing: pull and re-apply

```bash
~/code/ai-sync/bin/ai-config-sync   # thin shim for `ai-sync apply --pull`
```

No host runs this automatically by default — run it manually after pushing (remote hosts: invoke via `bin/ai-config-sync`, which fixes PATH for Homebrew Python; a bare `ssh host '~/code/ai-sync/bin/ai-sync …'` finds only system Python 3.9 and exits 2).

**Optional: auto-sync timer.** [`launchd/sh.user.ai-config-sync.plist`](launchd/sh.user.ai-config-sync.plist) runs `ai-config-sync` every 5 minutes. Not installed by default; opt a host in with:

```bash
cp ~/code/ai-sync/launchd/sh.user.ai-config-sync.plist ~/Library/LaunchAgents/ && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/sh.user.ai-config-sync.plist
```

Caveat: `apply --pull` refuses on a dirty tree, so the timer silently no-ops (check `/opt/homebrew/var/log/ai-config-sync.err.log`) until local drift is committed or reconciled via `ai-sync promote`.

## Adding a new MCP server

1. If it needs secrets, write `bin/<name>-mcp-wrapper.sh` following [`bin/unifi-mcp-wrapper.sh`](bin/unifi-mcp-wrapper.sh)'s pattern.
2. Add a `[<name>]` table to [`mcp/servers.toml`](mcp/servers.toml).
3. `~/code/ai-sync/bin/ai-sync apply`
4. Restart any running Claude Code session.

The CLI handles `claude mcp add` and the Copilot `mcp.json` regeneration. There is no JSON to edit twice.

## Per-host divergence (opt-in)

Some settings legitimately differ across hosts (theme, statusLine command, enabled plugins). The pattern is opt-in: by default `settings.json` files stay symlinks and Claude Code's runtime writebacks flow naturally into the canonical tracked file. To override a setting for one host:

```bash
# 1. Create the overlay (only the keys you want to override)
mkdir -p ~/code/ai-sync/hosts/$(hostname -s)
echo '{"theme": "dark"}' > ~/code/ai-sync/hosts/$(hostname -s)/claude-settings.json

# 2. Re-render
ai-sync apply
```

This switches that host's `~/.claude/settings.json` from a symlink to a rendered file (base + overlay, deep-merged). **Trade-off**: now Claude Code's runtime writes to `settings.json` (theme toggles, plugin enables, accepted permission prompts, etc.) become DRIFT instead of flowing into canonical. `ai-sync status` flags them and you reconcile manually:

```bash
ai-sync diff claude                     # inspect what drifted
ai-sync promote --to overlay claude     # keep this change per-host, OR
ai-sync promote --to base claude        # share it across all hosts (warns on overlay shadow), OR
ai-sync apply --force                   # discard the drift
```

Read [`docs/architecture.md` § "The writeback trap"](docs/architecture.md#the-writeback-trap-read-before-adding-your-first-overlay) before opting in on more than one machine.

## Selective adoption

Want just one skill? Copy `skills/general/<name>/` or `skills/personal/<name>/` into the matching tier. Want one MCP server? Copy its wrapper and registry entry, then create its local secret file.

## Conventions

- Skill and MCP server names: lowercase, hyphen-separated.
- Secrets never appear in tracked files. Wrappers in `bin/` source `~/code/ai-sync/secrets/<name>.env`.
- Commits: [conventional commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `chore:`). No `Co-authored-by` trailers from any AI tool.
- New behaviour in `bin/ai-sync` needs a test under `tests/`. Run with `~/code/ai-sync/bin/ai-sync test`.
