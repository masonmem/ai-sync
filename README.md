# ~/.ai-config

Personal AI brain — global instructions, custom skills, agent profiles, MCP wrapper scripts, and per-tool settings. Shared by **Claude Code** (via `~/.claude/`) and **Copilot CLI** (via `~/.copilot/`); designed to be reproducible across machines via [`bin/ai-sync`](bin/ai-sync).

Sibling to [my dotfiles repo](https://github.com/masonmem/dotfiles): dotfiles configures the *machine*, this repo configures the *AI brain* on top of it.

## TL;DR

```bash
~/.ai-config/bin/ai-sync status        # what's linked, what's drifted, MCP state
~/.ai-config/bin/ai-sync apply         # idempotent: re-link, re-register, regenerate mcp.json
~/.ai-config/bin/ai-sync apply --pull  # git pull --ff-only first
~/.ai-config/bin/ai-sync mcp list      # registered MCP servers
~/.ai-config/bin/ai-sync test          # run the pytest suite
```

The full architecture, including the scope-by-path rule and the rationale for not maintaining a canonical-config DSL, lives in [`docs/architecture.md`](docs/architecture.md). Start there before making structural changes.

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

## Selective adoption

Want just one skill? Copy `skills/<name>/` into your own `~/.ai-config/skills/`. Want the MCP wiring for one server? Copy the matching `bin/<name>-mcp-wrapper.sh`, the entry from `mcp/servers.toml`, and create `secrets/<name>.env` locally.

## Conventions

- Skills, agents, and MCP server names: lowercase, hyphen-separated.
- Secrets never appear in tracked files. Wrappers in `bin/` source `~/.ai-config/secrets/<name>.env`.
- Commits: [conventional commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `chore:`). No `Co-authored-by` trailers from any AI tool.
- New behaviour in `bin/ai-sync` needs a test under `tests/`. Run with `~/.ai-config/bin/ai-sync test`.
