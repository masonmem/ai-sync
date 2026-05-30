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

Three scripts in `bin/` handle the per-machine setup; pick the path that matches your starting point.

### Fresh machine (Claude Code only, never had Copilot CLI)

```bash
git clone git@github.com:masonmem/ai-config.git ~/.ai-config
chmod +x ~/.ai-config/bin/*.sh
bash ~/.ai-config/bin/bootstrap-claude.sh   # sets up ~/.claude/ symlinks
# Populate ~/.ai-config/secrets/ from your Keychain or `secrets-push`
# from another machine. Restart Claude Code.
```

### Fresh machine (Copilot CLI + optionally Claude Code)

```bash
git clone git@github.com:masonmem/ai-config.git ~/.ai-config
chmod +x ~/.ai-config/bin/*.sh

# Set up ~/.copilot/ as a symlinked surface (matches the layout in this repo)
mkdir -p ~/.copilot
ln -sfn ~/.ai-config/instructions.md          ~/.copilot/copilot-instructions.md
ln -sfn ~/.ai-config/skills                   ~/.copilot/skills
ln -sfn ~/.ai-config/bin                      ~/.copilot/bin
ln -sfn ~/.ai-config/mcp.json                 ~/.copilot/mcp-config.json
ln -sfn ~/.ai-config/secrets                  ~/.copilot/secrets
ln -sfn ~/.ai-config/copilot/settings.json    ~/.copilot/settings.json

# And/or set up Claude Code:
bash ~/.ai-config/bin/bootstrap-claude.sh

# Populate ~/.ai-config/secrets/ (`secrets-push` from another Mac).
```

### Existing machine that already had `~/.copilot/` from the old layout

The migration script itself lives in this renamed repo, so on a host
whose `~/.copilot/` still points at the old clone, fetch the script
directly via HTTPS rather than waiting for a local pull:

```bash
# Run on the host that still has ~/.copilot/.git/ as a physical clone.
# The script is idempotent — exits cleanly if already migrated.
curl -fsSLo /tmp/migrate-from-copilot.sh \
  https://raw.githubusercontent.com/masonmem/ai-config/main/bin/migrate-from-copilot.sh
bash /tmp/migrate-from-copilot.sh --dry   # preview every step
bash /tmp/migrate-from-copilot.sh         # do it

# After the migration: bin/ is now at ~/.ai-config/bin/. Optionally
# bootstrap Claude Code:
bash ~/.ai-config/bin/bootstrap-claude.sh
```

The script (1) updates the local `origin` URL to `masonmem/ai-config`,
(2) `git pull --ff-only` so the working tree matches the renamed
layout, (3) moves `.git` + tracked content from `~/.copilot/` into
`~/.ai-config/`, and (4) recreates the per-tool symlinks under
`~/.copilot/`. Leaves Copilot CLI runtime state (`config.json`,
`session-state/`, `logs/`, etc.) untouched.

### Ongoing: pull updates from navi

```bash
ai-config-sync   # ~/.ai-config/bin/ai-config-sync; mirror of dotfiles-sync
```

This `git pull --ff-only`s the repo and re-applies the per-tool symlinks (safe if already linked). Bails on a dirty working tree. Pair with `dotfiles-sync` from the dotfiles repo.

Each CLI auto-recreates its own runtime state (logs, sessions, caches, plugin data) on first launch.

## Selective adoption

Want just one skill? Copy `skills/<name>/` into your own `~/.ai-config/skills/`. Want the MCP wiring for a server? Copy the entry from `mcp.json` (Copilot) or `claude/settings.json` mcpServers block (Claude Code) plus the matching `bin/*-wrapper.sh`, and create the matching `secrets/*.env` locally.

## Conventions

- Skills, agents, and MCP server names: lowercase, hyphen-separated.
- Secrets never appear in tracked files. Wrappers in `bin/` source `~/.ai-config/secrets/<name>.env`.
- Commits: [conventional commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `chore:`). No `Co-authored-by` trailers from any AI tool.
