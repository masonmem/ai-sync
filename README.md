# ~/.copilot

My personal GitHub Copilot CLI configuration: global instructions, custom skills, agent profiles, MCP server wiring, and hooks. Sibling to [my dotfiles repo](https://github.com/masonmem/dotfiles) — dotfiles configures the *machine*, this repo configures the *AI brain* on top of it.

## Why a separate repo?

- **Different lifecycle.** Shell config changes are surgical. Skills/instructions get iterated constantly.
- **Different audience.** Someone may want my dotfiles without my MCP wiring, or vice versa.
- **Runtime hygiene.** `~/.copilot` contains lots of CLI-managed state (`logs/`, `session-state/`, `session-store.db*`, `config.json`, …) that must never be committed. Cleaner to own that `.gitignore` here than bury it in a stow package.

## Bootstrap a new machine

```bash
# 1. Back up any existing ~/.copilot state (CLI runtime files), then:
git clone git@github.com:masonmem/copilot.git ~/.copilot-repo

# 2. Either move ~/.copilot-repo into place, or symlink the tracked items.
#    Simplest: clone directly over an empty/non-existent ~/.copilot.
#    The CLI will recreate its runtime files (logs/, session-state/, ...) automatically.

# 3. Make wrappers executable
chmod +x ~/.copilot/bin/*.sh

# 4. Create machine-local secrets for any MCP servers you enable
mkdir -p ~/.copilot/secrets
# See mcp-config.json and the per-server notes in bin/*-wrapper.sh for what to put here.
```

## Layout

| Path | Tracked? | Purpose |
|---|---|---|
| `copilot-instructions.md` | ✅ | Personal global instructions, applied to every session |
| `instructions/*.instructions.md` | ✅ | Topic-specific personal instructions |
| `skills/<name>/SKILL.md` | ✅ | Personal skills (loaded on demand by description match) |
| `agents/*.agent.md` | ✅ | Personal custom agent profiles |
| `mcp-config.json` | ✅ | User-level MCP server definitions |
| `lsp-config.json` | ✅ | User-level LSP server definitions |
| `hooks/` | ✅ | User-level hook scripts |
| `bin/` | ✅ | Small wrapper scripts (e.g. for MCP servers that need secrets) |
| `secrets/` | ❌ (gitignored) | Per-server `.env` files sourced by wrappers in `bin/` |
| `settings.json` | ✅ | Personal CLI settings (model, footer, allowedUrls) |
| `config.json`, `logs/`, `session-state/`, `session-store.db*`, `ide/`, `restart/`, `command-history-state*`, `installed-plugins/`, `plugin-data/`, `permissions-config.json` | ❌ | CLI-managed runtime state |

## Selective adoption

Want just one skill? Copy `skills/<name>/` into your own `~/.copilot/skills/`. Want the MCP wiring for a server? Copy that block out of `mcp-config.json` plus the matching `bin/*-wrapper.sh`, and create the matching `secrets/*.env` locally.

## Conventions

- Skills, agents, and MCP server names: lowercase, hyphen-separated.
- Secrets never appear in tracked files. Wrappers in `bin/` source `~/.copilot/secrets/<name>.env`.
- Commits: [conventional commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `chore:`).
