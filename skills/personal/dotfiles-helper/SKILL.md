---
name: dotfiles-helper
description: Encodes the conventions of @masonmem's dotfiles + ~/.ai-config setup. Use when the user asks to install a CLI tool, add an alias, configure a shell env var, add a new MCP server, add a custom skill or agent, or otherwise modify their machine environment so it stays reproducible across machines.
---

# dotfiles-helper

This skill captures the *house rules* for how @masonmem's machine environment is set up so that any change you make is reproducible on a fresh machine and shareable with others.

There are two repos in play:

- **`~/dotfiles`** (`masonmem/dotfiles`) — machine env: Brewfile, shell config, editors, ssh template. Managed with GNU stow, `--no-folding` so machine-local overrides live alongside stowed files.
- **`~/code/ai-sync`** (`masonmem/ai-sync`) — shared AI brain consumed by **Claude Code** (via `~/.claude/`), **Copilot CLI** (via `~/.copilot/`), and **Codex** (via `~/.codex/AGENTS.md`). Holds global instructions (`agents/general.md`), skills (`skills/general/`, `skills/personal/`), MCP wrapper scripts, per-tool settings, and secrets. Plain clone (no stow); `~/.ai-config` is a compatibility symlink to it.

## Golden rules

1. **Anything installed must be declared.** A change isn't done until a fresh-machine bootstrap would reproduce it.
2. **Secrets never enter git.** Use machine-local files (`~/.config/zsh/90-*.zsh`, `~/.ai-config/secrets/*.env`, `~/.gitconfig.local`) and reference them from tracked code via wrappers or includes.
3. **Commit rules are global.** The Conventional-Commits format and no-AI-co-author-trailer rule live in `agents/general.md` (§ Commits) and apply here unchanged.

## Decision tree: where does this change go?

| Change | Location | Mechanism |
|---|---|---|
| New Homebrew formula or cask | `~/dotfiles/Brewfile` | Add line, then `brew bundle --file=~/dotfiles/Brewfile` |
| New Python CLI tool | `~/dotfiles/Brewfile` (add via `brew "pipx"` is already there) **and** `pipx install <pkg>` | Never plain `pip install` — Homebrew Python is PEP 668 externally-managed |
| Shared shell alias / env var | `~/dotfiles/zsh/.config/zsh/{20-aliases,10-env}.zsh` | Edit tracked file |
| Machine-specific shell config | `~/.config/zsh/90-*.zsh` (untracked, auto-sourced by `.zshrc`) | Create or edit local file |
| Machine-specific git identity | `~/.gitconfig.local` (untracked, `[include]`-d by `~/.gitconfig`) | Edit local file |
| New MCP server (user-global) | `~/.ai-config/mcp/servers.toml` (single source of truth) + optional `~/.ai-config/bin/<name>-wrapper.sh` for secrets, then `ai-sync apply` | See "Adding an MCP server" below |
| New MCP server (project-specific) | `<repo>/.github/mcp.json` (Copilot) or `<repo>/.mcp.json` (Claude Code) | Same wrapper pattern works |
| New personal skill | `~/code/ai-sync/skills/general/<name>/SKILL.md` (portable) or `skills/personal/<name>/SKILL.md` (machine/homelab-specific), plus a per-skill symlink in `~/.claude/skills/` | Verify with `ai-sync-doctor`. Copilot: `/skills reload`. Claude Code: restart session. |
| New personal agent | `~/code/ai-sync/agents/` holds only `general.md` (the global instruction file); per-agent files are **reserved, not yet wired** (no fan-out link; propose wiring before relying on it) | — |
| Machine-specific AI-tool setting (model, effortLevel, plugins) | `~/.ai-config/hosts/<lowercase-short-hostname>/claude-settings.json` overlay (deep-merged over `claude/settings.json`), then `ai-sync apply` | Reconcile later runtime writebacks with `ai-sync diff claude` + `ai-sync promote --to overlay\|base claude` — see ai-config README § "Per-host divergence". Never hand-edit the shared `claude/settings.json` for one machine's prefs. |
| Project-scoped instructions | `<repo>/AGENTS.md` (canonical, PROJECT-SPECIFIC only) + `<repo>/CLAUDE.md` containing `@AGENTS.md` — see `~/code/ai-sync/templates/` | — |

## Installing a Python CLI tool (the right way)

```bash
pipx install <package-name>
```

Reasons:

- Homebrew's `python@3.14` sets PEP 668 `EXTERNALLY-MANAGED`, so `pip install <pkg>` globally errors out.
- `pipx` is in the Brewfile and isolates each tool in its own venv at `~/.local/pipx/venvs/<pkg>/`.
- Binaries land in `~/.local/bin/`, which is already on PATH via `~/.zprofile`.

If the tool is general enough that any of @masonmem's machines should have it, also add it to `~/dotfiles/pipx-tools.txt` (the tracked list of pipx tools, installed by the dotfiles bootstrap via `grep -v '^#' pipx-tools.txt | xargs -n1 pipx install`) with a rationale comment, in the same commit.

## Installing a Homebrew package

```bash
# Add to ~/dotfiles/Brewfile (alphabetised within its section), then:
brew bundle --file=~/dotfiles/Brewfile
```

Commit the Brewfile change as `chore(brewfile): add <pkg>` or `feat(brewfile): add <pkg> for <reason>`.

## Adding an MCP server (user-global, in `~/.ai-config/`)

`~/.ai-config/mcp/servers.toml` is the **single source of truth**. `ai-sync apply` reads it and registers each server with every installed client (Claude Code via `claude mcp add --scope user`; Copilot CLI by regenerating `~/.ai-config/mcp.json`). You never edit `mcp.json` or `~/.claude.json` by hand.

Decision: does this MCP server need secrets (API keys, tokens)?

- **No secrets** → just add an entry to `servers.toml` pointing `command` at the server URL or binary. Run `ai-sync apply`.
- **Yes, secrets** → use the wrapper-script pattern (below), because both Copilot CLI and Claude Code spawn MCP servers with only `PATH` inherited; secret env vars must come from a file the wrapper sources rather than from the registration JSON.

### Wrapper-script pattern for secret-bearing MCP servers

1. Create `~/.ai-config/bin/<name>-mcp-wrapper.sh` that sources `~/.ai-config/secrets/<name>.env` and execs the server binary. See `unifi-mcp-wrapper.sh` as the reference example. `chmod +x` it.
2. Add a `[<name>]` table to `~/.ai-config/mcp/servers.toml`:
   ```toml
   [<name>]
   command     = "${AI_CONFIG}/bin/<name>-mcp-wrapper.sh"
   description = "..."
   secrets_env = "${AI_CONFIG}/secrets/<name>.env"
   # optional: hosts = ["navi"], clients = ["claude"]
   ```
3. Document required env vars in the wrapper's header comment.
4. The user creates `~/.ai-config/secrets/<name>.env` (gitignored) with `chmod 600`.
5. Run `~/.ai-config/bin/ai-sync apply`.
6. Verify: `~/.ai-config/bin/ai-sync status` should show `✓ registered` and `✓ present in mcp.json`. Restart any running Claude Code session so it loads the new server.

`ai-sync` covers all four mechanical steps that used to be manual (claude mcp add, mcp.json edit, symlink fan-out, secret-perm check), so the only place a new server is *declared* is `servers.toml`. Updating the dotfiles-helper skill or other docs is not required for new servers.

## Adding a personal skill

```text
~/.ai-config/skills/<lowercase-hyphenated-name>/
└── SKILL.md          # YAML frontmatter (name, description, optional allowed-tools) + Markdown body
```

The `description` is what the host CLI pattern-matches against to decide when to load the skill — write it as "Use when the user asks to …" so it surfaces at the right moments. Same SKILL.md format works for both Copilot CLI and Claude Code.

After adding: Copilot `/skills reload`; Claude Code requires a session restart to pick up new skills.

## Verifying the change

- Shell changes: `exec zsh` or open a new shell, then test.
- Brewfile: `brew bundle check --file=~/dotfiles/Brewfile` should report "satisfied".
- MCP: `/mcp show <name>` should list tools.
- Skill: `/skills info <name>` should display the skill.
- **LLM client config (opencode/aider/goose) after any version bump:**
  smoke-test against `auto` from a stripped env to confirm secret
  resolution hasn't regressed:
  ```sh
  env -i HOME="$HOME" PATH="/opt/homebrew/bin:/usr/bin:/bin" \
    opencode run --model litellm/auto "reply with the word pong"
  ```
  If this 401s, the tool is depending on a shell-exported env var the
  launching context doesn't provide. See "LiteLLM auth chain" below.

## LiteLLM auth chain (opencode / aider / goose → gateway)

Two layers, often confused:

1. **Backend keys** (LiteLLM → Anthropic/Gemini upstreams) live in
   solaris `/opt/homebrew/etc/komodo/periphery.config.toml` `[secrets]`
   and are materialised into the litellm container env by Komodo. This
   is the `homelab-helper` skill's territory. **Not** what client 401s
   are about.
2. **Frontend keys** (this Mac → LiteLLM gateway) are per-tool LiteLLM
   *virtual* keys stored in `~/.ai-config/secrets/litellm-<tool>.txt`
   (chmod 600, gitignored; mirrored to macOS Keychain via
   `litellm-keys`). Consumption pattern by tool:

   | Tool | How it reads the key | Why |
   |---|---|---|
   | `opencode` | `apiKey: "{file:~/.ai-config/secrets/litellm-opencode.txt}"` in `opencode.jsonc` | opencode's `{env:VAR}` returns empty-string when the var is missing in the launching env (silent 401). `{file:}` reads at config-load time with no env dependency. |
   | `aider`    | `~/dotfiles/ollama/.config/zsh/60-aider-wrapper.zsh` injects `OPENAI_API_KEY=$AIDER_LITELLM_KEY` per call | aider's YAML config doesn't expand env vars; needs them on the process. |
   | `goose`    | `~/dotfiles/ollama/.config/zsh/61-goose-wrapper.zsh` injects `OPENAI_API_KEY=$GOOSE_LITELLM_KEY` per call | same as aider — config is static. |

   The `<TOOL>_LITELLM_KEY` env vars themselves come from
   `16-llm-gateway.zsh` (file first, Keychain fallback). For opencode
   we still load it for parity, but the live source of truth is the
   file — opencode reads disk directly so launchctl/IDE-spawned
   shells/etc. all work.

**Rule:** never store a LiteLLM virtual key directly in a tool's
config file (it's a dotfile in git). Always either (a) `{file:}` from
`~/.ai-config/secrets/`, or (b) a per-tool wrapper that injects
`OPENAI_API_KEY` for that one invocation. Don't export
`OPENAI_API_KEY` globally — opencode auto-detects it and pollutes the
model picker with the entire built-in OpenAI catalog.

## Commit etiquette

Global rules (`agents/general.md` § Commits) apply. Additionally, for this territory:

- One concern per commit; scope encouraged (e.g. `feat(zsh): add pip alias`).
- For changes that span both repos (e.g. install a tool *and* wire its MCP server), commit each repo separately with clear, parallel commit messages.

## Related skills

- **`homelab-helper`** (global) — for anything that runs as a long-lived service on hyperion (QNAP) or solaris (Mac Mini). New docker stack, ollama model, BYOK provider key, Caddy route → that skill, not this one. This skill stays focused on **Mac client** machine env.
