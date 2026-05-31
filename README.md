# ~/.ai-config

[![tests](https://github.com/masonmem/ai-config/actions/workflows/test.yml/badge.svg)](https://github.com/masonmem/ai-config/actions/workflows/test.yml)

Personal AI brain — global instructions, custom skills, agent profiles, MCP wrapper scripts, and per-tool settings. Shared by **Claude Code** (via `~/.claude/`) and **Copilot CLI** (via `~/.copilot/`); designed to be reproducible across machines via [`bin/ai-sync`](bin/ai-sync).

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

All commands are reachable via the symlink at `~/.claude/bin/ai-sync` and `~/.copilot/bin/ai-sync`, or by the absolute path `~/.ai-config/bin/ai-sync`. The CLI requires **Python 3.11+** (for `tomllib`).

The full architecture, including the scope-by-path rule, the per-host overlay writeback trap, and the rationale for not maintaining a canonical-config DSL, lives in [`docs/architecture.md`](docs/architecture.md). Start there before making structural changes.

## Layout

| Path | Tracked? | Scope | Purpose |
|---|---|---|---|
| `instructions.md`       | ✅ | shared (both tools) | Personal global instructions |
| `skills/<name>/SKILL.md`| ✅ | shared | Personal skills (loaded on demand by description match) |
| `agents/`, `hooks/`     | ✅ | shared | Reserved for topic-specific agent profiles and hook scripts |
| `bin/`                  | ✅ | shared | `ai-sync` CLI, MCP/statusline wrapper scripts |
| `mcp/servers.toml`      | ✅ | translated | **Single source of truth for MCP servers.** Read by `ai-sync apply`. |
| `mcp.json`              | ✅ | generated | Copilot's mcp.json — regenerated each `ai-sync apply` from `mcp/servers.toml`. Do not hand-edit. |
| `copilot/settings.json` | ✅ | Copilot only | Copilot CLI native settings |
| `claude/settings.json`  | ✅ | Claude Code only | Claude Code native settings (theme, plugins, statusLine, etc.) |
| `docs/architecture.md`  | ✅ | docs | The "where does this go?" rule |
| `tests/`                | ✅ | tests | pytest suite for `bin/ai-sync` |
| `hosts/<host>/*.json`   | ✅ (when present) | per-host overlay | Optional deep-merge overlays for settings.json files. Adding one switches the target from symlink to render mode — read `docs/architecture.md#the-writeback-trap` before opting in. |
| `secrets/`              | ❌ (gitignored) | per-machine | `.env` files sourced by `bin/*-wrapper.sh` |
| `state/`                | ❌ (gitignored) | per-machine | Wrapper runtime side-effects (e.g. UniFi audit logs) |

The path tells you the scope. There's no decision tree beyond that — see [`docs/architecture.md`](docs/architecture.md).

## Bootstrap a new machine

```bash
git clone git@github.com:masonmem/ai-config.git ~/.ai-config
chmod +x ~/.ai-config/bin/ai-sync ~/.ai-config/bin/*.sh
~/.ai-config/bin/ai-sync apply
# Populate ~/.ai-config/secrets/ from another machine.
# Restart any running Claude Code session so it loads new MCP servers.
```

`ai-sync apply` requires Python 3.11+ (for `tomllib`). If you're on a host without Python (rare — Brewfile installs python@3.14), [`bin/bootstrap-claude.sh`](bin/bootstrap-claude.sh) is a minimal symlink-only fallback.

### Existing machine that still has `~/.copilot/` from the old layout

```bash
# Run on the host whose ~/.copilot/.git/ is still a physical clone.
# Idempotent — exits cleanly if already migrated.
curl -fsSLo /tmp/migrate-from-copilot.sh \
  https://raw.githubusercontent.com/masonmem/ai-config/main/bin/migrate-from-copilot.sh
bash /tmp/migrate-from-copilot.sh --dry   # preview
bash /tmp/migrate-from-copilot.sh         # do it
~/.ai-config/bin/ai-sync apply
```

### Ongoing: pull and re-apply

```bash
~/.ai-config/bin/ai-config-sync   # thin shim for `ai-sync apply --pull`
```

Solaris runs `ai-config-sync` on a launchd timer; the name stays for that reason.

## Adding a new MCP server

1. If it needs secrets, write `bin/<name>-mcp-wrapper.sh` following [`bin/unifi-mcp-wrapper.sh`](bin/unifi-mcp-wrapper.sh)'s pattern.
2. Add a `[<name>]` table to [`mcp/servers.toml`](mcp/servers.toml).
3. `~/.ai-config/bin/ai-sync apply`
4. Restart any running Claude Code session.

The CLI handles `claude mcp add` and the Copilot `mcp.json` regeneration. There is no JSON to edit twice.

## Per-host divergence (opt-in)

Some settings legitimately differ across hosts (theme, statusLine command, enabled plugins). The pattern is opt-in: by default `settings.json` files stay symlinks and Claude Code's runtime writebacks flow naturally into the canonical tracked file. To override a setting for one host:

```bash
# 1. Create the overlay (only the keys you want to override)
mkdir -p ~/.ai-config/hosts/$(hostname -s)
echo '{"theme": "dark"}' > ~/.ai-config/hosts/$(hostname -s)/claude-settings.json

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

Read [`docs/architecture.md#the-writeback-trap`](docs/architecture.md#the-writeback-trap) before opting in on more than one machine.

## Selective adoption

Want just one skill? Copy `skills/<name>/` into your own `~/.ai-config/skills/`. Want the MCP wiring for one server? Copy the matching `bin/<name>-mcp-wrapper.sh`, the entry from `mcp/servers.toml`, and create `secrets/<name>.env` locally.

## Conventions

- Skills, agents, and MCP server names: lowercase, hyphen-separated.
- Secrets never appear in tracked files. Wrappers in `bin/` source `~/.ai-config/secrets/<name>.env`.
- Commits: [conventional commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `chore:`). No `Co-authored-by` trailers from any AI tool.
- New behaviour in `bin/ai-sync` needs a test under `tests/`. Run with `~/.ai-config/bin/ai-sync test`.
