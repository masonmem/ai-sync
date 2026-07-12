---
name: dotfiles-helper
description: Use when installing a CLI tool, adding a shell alias or env var, adding an MCP server, adding a custom skill or agent, or otherwise changing this Mac's environment — keeps every change reproducible via ~/dotfiles + ~/code/ai-sync. Not for long-lived services on hyperion/solaris (use homelab-helper) or project-scoped repo config.
---

# dotfiles-helper

This skill captures the *house rules* for how @masonmem's machine environment is set up so that any change you make is reproducible on a fresh machine and shareable with others.

There are two repos in play:

- **`~/dotfiles`** (`masonmem/dotfiles`) — machine env: Brewfile, shell config, editors, ssh template. Managed with GNU stow, `--no-folding` so machine-local overrides live alongside stowed files.
- **`~/code/ai-sync`** (`masonmem/ai-sync`) — shared AI brain consumed by **Claude Code** (via `~/.claude/`), **Copilot CLI** (via `~/.copilot/`), and **Codex** (via `~/.codex/AGENTS.md`). Holds global instructions (`agents/general.md`), skills (`skills/personal/`; `skills/general/` is reserved for portable skills but currently empty), MCP wrapper scripts, per-tool settings, and secrets. Plain clone (no stow).

## Golden rules

1. **Anything installed must be declared.** A change isn't done until a fresh-machine bootstrap would reproduce it.
2. **Secrets never enter git.** Use machine-local files (`~/.config/zsh/90-*.zsh`, `~/code/ai-sync/secrets/*.env`, `~/.gitconfig.local`) and reference them from tracked code via wrappers or includes.
3. **Commit rules are global.** The Conventional-Commits format and no-AI-co-author-trailer rule live in `agents/general.md` (§ Commits) and apply here unchanged.

## Decision tree: where does this change go?

| Change | Location | Mechanism |
|---|---|---|
| New Homebrew formula or cask | `~/dotfiles/Brewfile` | Add line, then `brew bundle --file=~/dotfiles/Brewfile` |
| New Python CLI tool | `pipx install <pkg>` + `~/dotfiles/pipx-tools.txt` | Never plain `pip install` — Homebrew Python is PEP 668 externally-managed |
| Shared shell alias / env var | `~/dotfiles/zsh/.config/zsh/{20-aliases,10-env}.zsh` | Edit tracked file |
| Machine-specific shell config | `~/.config/zsh/90-*.zsh` (untracked, auto-sourced by `.zshrc`) | Create or edit local file |
| Machine-specific git identity | `~/.gitconfig.local` (untracked, `[include]`-d by `~/.gitconfig`) | Edit local file |
| New MCP server (user-global) | `~/code/ai-sync/mcp/servers.toml` (single source of truth) + optional `~/code/ai-sync/bin/<name>-wrapper.sh` for secrets, then `ai-sync apply` | See "Adding an MCP server" below |
| New MCP server (project-specific) | `<repo>/.github/mcp.json` (Copilot) or `<repo>/.mcp.json` (Claude Code) | Same wrapper pattern works |
| New personal skill | `~/code/ai-sync/skills/personal/<name>/SKILL.md` (or `skills/general/<name>/` once portable skills exist), then `ai-sync apply` | See "Adding a personal skill" below |
| New personal agent | `~/code/ai-sync/agents/` holds only `general.md` (the global instruction file); per-agent files are **reserved, not yet wired** (no fan-out link; propose wiring before relying on it) | — |
| Machine-specific AI-tool setting (model, effortLevel, plugins) | `~/code/ai-sync/hosts/<lowercase-short-hostname>/claude-settings.json` overlay (deep-merged over `claude/settings.json`), then `ai-sync apply` | Reconcile later runtime writebacks with `ai-sync diff claude` + `ai-sync promote --to overlay\|base claude`. Never hand-edit the shared `claude/settings.json` for one machine's prefs. |
| Project-scoped instructions | `<repo>/AGENTS.md` (canonical, PROJECT-SPECIFIC only) + `<repo>/CLAUDE.md` containing `@AGENTS.md` — see `~/code/ai-sync/templates/` | — |

## Installing a Python CLI tool (the right way)

```bash
pipx install <package-name>
```

Reasons:

- Homebrew's `python@3.14` sets PEP 668 `EXTERNALLY-MANAGED`, so `pip install <pkg>` globally errors out.
- `pipx` is in the Brewfile and isolates each tool in its own venv at `~/.local/pipx/venvs/<pkg>/`.
- Binaries land in `~/.local/bin/`, which is already on PATH via `~/.zprofile`.

If the tool is general enough that any of @masonmem's machines should have it, also add it to `~/dotfiles/pipx-tools.txt` (the tracked list of pipx tools, installed by the dotfiles bootstrap) with a rationale comment, in the same commit.

## Installing a Homebrew package

```bash
# Add to ~/dotfiles/Brewfile (alphabetised within its section), then:
brew bundle --file=~/dotfiles/Brewfile
```

Commit the Brewfile change as `chore(brewfile): add <pkg>` or `feat(brewfile): add <pkg> for <reason>`.

## Adding an MCP server (user-global, in `~/code/ai-sync/`)

`~/code/ai-sync/mcp/servers.toml` is the **single source of truth**. `ai-sync apply` reads it and registers each server with every installed client (Claude Code via `claude mcp add --scope user`; Copilot CLI by regenerating `~/code/ai-sync/mcp.json`). You never edit `mcp.json` or `~/.claude.json` by hand.

Decision: does this MCP server need secrets (API keys, tokens)?

- **No secrets** → just add an entry to `servers.toml` pointing `command` at the server URL or binary. Run `ai-sync apply`.
- **Yes, secrets** → use the wrapper-script pattern (below), because both Copilot CLI and Claude Code spawn MCP servers with only `PATH` inherited; secret env vars must come from a file the wrapper sources rather than from the registration JSON.

### Wrapper-script pattern for secret-bearing MCP servers

1. Create `~/code/ai-sync/bin/<name>-mcp-wrapper.sh` that sources `~/code/ai-sync/secrets/<name>.env` and execs the server binary. See `unifi-mcp-wrapper.sh` as the reference example. `chmod +x` it.
2. Add a `[<name>]` table to `~/code/ai-sync/mcp/servers.toml`:
   ```toml
   [<name>]
   command     = "${AI_CONFIG}/bin/<name>-mcp-wrapper.sh"
   description = "..."
   secrets_env = "${AI_CONFIG}/secrets/<name>.env"
   # optional: hosts = ["navi"], clients = ["claude"]
   ```
3. Document required env vars in the wrapper's header comment.
4. The user creates `~/code/ai-sync/secrets/<name>.env` (gitignored) with `chmod 600`.
5. Run `~/code/ai-sync/bin/ai-sync apply`.
6. Verify: `~/code/ai-sync/bin/ai-sync status` should show `✓ registered` and `✓ present in mcp.json`. Restart any running Claude Code session so it loads the new server.

`ai-sync` covers all the mechanical steps (claude mcp add, mcp.json regeneration, secret-perm check), so the only place a new server is *declared* is `servers.toml`.

## Adding a personal skill

```text
~/code/ai-sync/skills/personal/<lowercase-hyphenated-name>/
└── SKILL.md          # YAML frontmatter (name, description) + Markdown body
```

1. `name` must match the directory; `description` is what the host CLI pattern-matches against to decide when to load the skill — write it as "Use when … Not for …" so it surfaces at the right moments and stays out of adjacent ones. Same SKILL.md format works for both Copilot CLI and Claude Code.
2. Run `ai-sync apply`; it creates the per-skill hub links for every installed client and excludes personal skills from hosts without a `hosts/<host>/` marker.
3. Verify with `ai-sync doctor`. Copilot: `/skills reload`. Claude Code: restart the session.

## Verifying the change

- Shell changes: `exec zsh` or open a new shell, then test.
- Brewfile: `brew bundle check --file=~/dotfiles/Brewfile` should report "satisfied".
- MCP: `/mcp show <name>` should list tools.
- Skill: `/skills info <name>` should display the skill.
- LLM client config (opencode/aider/goose) after any version bump: run the stripped-env smoke test in [references/litellm-auth.md](references/litellm-auth.md) — if it 401s, the tool depends on an env var the launching context doesn't provide.

## LiteLLM client auth (opencode / aider / goose)

Frontend virtual keys live in `~/code/ai-sync/secrets/litellm-<tool>.txt`; never put a key in a tracked config file, and never export `OPENAI_API_KEY` globally. Full chain, per-tool consumption table, and smoke test: [references/litellm-auth.md](references/litellm-auth.md).

## Commit etiquette

Global rules (`agents/general.md` § Commits) apply. Additionally, for this territory:

- One concern per commit; scope encouraged (e.g. `feat(zsh): add pip alias`).
- For changes that span both repos (e.g. install a tool *and* wire its MCP server), commit each repo separately with clear, parallel commit messages.

## Related skills

- **`homelab-helper`** — for anything that runs as a long-lived service on hyperion (QNAP) or solaris (Mac Mini). New docker stack, ollama model, Caddy route → that skill, not this one. This skill stays focused on **Mac client** machine env.
