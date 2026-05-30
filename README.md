# ~/.ai-config

My personal AI-CLI configuration: global instructions, custom skills, agent profiles, MCP wrapper scripts, and per-tool settings. Shared by **GitHub Copilot CLI** (via `~/.copilot/`) and **Claude Code** (via `~/.claude/`) — both treat this directory as the canonical source of the AI brain, and their tracked entries are symlinks into here.

Sibling to [my dotfiles repo](https://github.com/masonmem/dotfiles): dotfiles configures the *machine*, this repo configures the *AI brain* on top of it.

## Why a separate repo from dotfiles?

- **Different lifecycle.** Shell config changes are surgical. Skills and instructions get iterated constantly.
- **Different audience.** Someone may want my dotfiles without my MCP wiring, or vice versa.
- **Runtime hygiene.** `~/.copilot` and `~/.claude` contain lots of CLI-managed state (sessions, logs, caches, plugin data) that must never be committed. Cleaner to own that `.gitignore` here than bury it in a stow package — and cleaner still to keep the tracked content out of those runtime dirs entirely.

## Why one repo across both CLIs?

Copilot CLI and Claude Code consume the same conceptual assets (instructions, skills, MCP servers, secrets) under different on-disk names. Maintaining two copies would silently drift. Instead:

- Skills, instructions, MCP wrappers, and secrets live **once** under `~/.ai-config/`.
- Each tool gets a thin shaped surface (`~/.copilot/`, `~/.claude/`) whose tracked entries are symlinks into `~/.ai-config/`.
- Each tool's tool-specific settings file (`copilot/settings.json`, `claude/settings.json`) lives in its own subdir here so both stay version-controlled without conflicting schemas.

## Layout

| Path | Tracked? | Purpose |
|---|---|---|
| `instructions.md` | ✅ | Personal global instructions, applied to every session (both tools) |
| `skills/<name>/SKILL.md` | ✅ | Personal skills (loaded on demand by description match) |
| `bin/` | ✅ | Wrapper scripts (e.g. for MCP servers that need secrets) |
| `mcp.json` | ✅ | Copilot CLI user-level MCP definitions (Copilot's schema) |
| `copilot/settings.json` | ✅ | Copilot CLI personal settings (model, footer, allowedUrls) |
| `claude/settings.json` | ✅ | Claude Code personal settings (includes `mcpServers` block in Claude's schema) |
| `agents/`, `hooks/` | ✅ | Reserved for topic-specific agent profiles and hook scripts. Empty today. |
| `secrets/` | ❌ (gitignored) | Per-server `.env` files sourced by wrappers in `bin/` |
| `state/` | ❌ (gitignored) | Runtime side-effects (e.g. MCP server audit logs) |

## Bootstrap a new machine

```bash
# 1. Clone the canonical repo.
git clone git@github.com:masonmem/ai-config.git ~/.ai-config

# 2. Make wrappers executable.
chmod +x ~/.ai-config/bin/*.sh

# 3. Create the per-tool surfaces.
# Copilot CLI: clone into ~/.copilot (or move an existing CLI runtime dir aside first),
# then replace the tracked entries with symlinks into ~/.ai-config:
mkdir -p ~/.copilot
ln -sf ~/.ai-config/instructions.md          ~/.copilot/copilot-instructions.md
ln -sf ~/.ai-config/skills                   ~/.copilot/skills
ln -sf ~/.ai-config/bin                      ~/.copilot/bin
ln -sf ~/.ai-config/mcp.json                 ~/.copilot/mcp-config.json
ln -sf ~/.ai-config/secrets                  ~/.copilot/secrets
ln -sf ~/.ai-config/copilot/settings.json    ~/.copilot/settings.json

# Claude Code: same idea against ~/.claude:
mkdir -p ~/.claude
ln -sf ~/.ai-config/instructions.md      ~/.claude/CLAUDE.md
ln -sf ~/.ai-config/skills               ~/.claude/skills
ln -sf ~/.ai-config/bin                  ~/.claude/bin
ln -sf ~/.ai-config/secrets              ~/.claude/secrets
ln -sf ~/.ai-config/claude/settings.json ~/.claude/settings.json

# 4. Create machine-local secrets for any MCP servers you've enabled.
mkdir -p ~/.ai-config/secrets
# See mcp.json + the per-server notes in bin/*-wrapper.sh for what to put here.
```

Each CLI auto-recreates its own runtime state (logs, sessions, caches, plugin data) on first launch.

## Selective adoption

Want just one skill? Copy `skills/<name>/` into your own `~/.ai-config/skills/`. Want the MCP wiring for a server? Copy the entry from `mcp.json` (Copilot) or `claude/settings.json` mcpServers block (Claude Code) plus the matching `bin/*-wrapper.sh`, and create the matching `secrets/*.env` locally.

## Conventions

- Skills, agents, and MCP server names: lowercase, hyphen-separated.
- Secrets never appear in tracked files. Wrappers in `bin/` source `~/.ai-config/secrets/<name>.env`.
- Commits: [conventional commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `chore:`). No `Co-authored-by` trailers from any AI tool.
