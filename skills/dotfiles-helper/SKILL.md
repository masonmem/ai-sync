---
name: dotfiles-helper
description: Encodes the conventions of @masonmem's dotfiles + ~/.copilot setup. Use when the user asks to install a CLI tool, add an alias, configure a shell env var, add a new MCP server, add a custom skill or agent, or otherwise modify their machine environment so it stays reproducible across machines.
---

# dotfiles-helper

This skill captures the *house rules* for how @masonmem's machine environment is set up so that any change you make is reproducible on a fresh machine and shareable with others.

There are two repos in play:

- **`~/dotfiles`** (`masonmem/dotfiles`) — machine env: Brewfile, shell config, editors, ssh template. Managed with GNU stow, `--no-folding` so machine-local overrides live alongside stowed files.
- **`~/.copilot`** (`masonmem/copilot`) — AI brain: global instructions, skills, agents, MCP config, hooks. Plain clone (no stow).

## Golden rules

1. **Anything installed must be declared.** A change isn't done until a fresh-machine bootstrap would reproduce it.
2. **Secrets never enter git.** Use machine-local files (`~/.config/zsh/90-*.zsh`, `~/.copilot/secrets/*.env`, `~/.gitconfig.local`) and reference them from tracked code via wrappers or includes.
3. **Conventional commits, no Copilot co-author trailer.** Format: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, etc. Never add `Co-authored-by: Copilot`.

## Decision tree: where does this change go?

| Change | Location | Mechanism |
|---|---|---|
| New Homebrew formula or cask | `~/dotfiles/Brewfile` | Add line, then `brew bundle --file=~/dotfiles/Brewfile` |
| New Python CLI tool | `~/dotfiles/Brewfile` (add via `brew "pipx"` is already there) **and** `pipx install <pkg>` | Never plain `pip install` — Homebrew Python is PEP 668 externally-managed |
| Shared shell alias / env var | `~/dotfiles/zsh/.config/zsh/{20-aliases,10-env}.zsh` | Edit tracked file |
| Machine-specific shell config | `~/.config/zsh/90-*.zsh` (untracked, auto-sourced by `.zshrc`) | Create or edit local file |
| Machine-specific git identity | `~/.gitconfig.local` (untracked, `[include]`-d by `~/.gitconfig`) | Edit local file |
| New MCP server (user-global) | `~/.copilot/mcp-config.json` + optional `~/.copilot/bin/<name>-wrapper.sh` for secrets | See "Adding an MCP server" below |
| New MCP server (project-specific) | `<repo>/.github/mcp.json` or `<repo>/.mcp.json` | Same JSON schema |
| New personal skill | `~/.copilot/skills/<name>/SKILL.md` | Run `/skills reload` after |
| New personal agent | `~/.copilot/agents/<name>.agent.md` | — |
| Project-scoped instructions | `<repo>/.github/copilot-instructions.md` or `<repo>/AGENTS.md` | — |

## Installing a Python CLI tool (the right way)

```bash
pipx install <package-name>
```

Reasons:

- Homebrew's `python@3.14` sets PEP 668 `EXTERNALLY-MANAGED`, so `pip install <pkg>` globally errors out.
- `pipx` is in the Brewfile and isolates each tool in its own venv at `~/.local/pipx/venvs/<pkg>/`.
- Binaries land in `~/.local/bin/`, which is already on PATH via `~/.zprofile`.

If the tool is general enough that any of @masonmem's machines should have it, also add a `# pipx: <pkg>` comment block to the Brewfile or a small note in the dotfiles README's bootstrap section so a fresh machine reproduces it. (We don't yet have a tracked list of pipx tools — propose creating one if installing the 2nd+ pipx tool.)

## Installing a Homebrew package

```bash
# Add to ~/dotfiles/Brewfile (alphabetised within its section), then:
brew bundle --file=~/dotfiles/Brewfile
```

Commit the Brewfile change as `chore(brewfile): add <pkg>` or `feat(brewfile): add <pkg> for <reason>`.

## Adding an MCP server (user-global, in `~/.copilot/`)

Decision: does this MCP server need secrets (API keys, tokens)?

- **No secrets** → add the server definition directly to `~/.copilot/mcp-config.json`. Or run `/mcp add` interactively.
- **Yes, secrets** → use the wrapper-script pattern, because Copilot CLI spawns MCP servers with only `PATH` inherited; all other env vars must be literal in the JSON, which would leak secrets into git.

### Wrapper-script pattern for secret-bearing MCP servers

1. Create `~/.copilot/bin/<name>-wrapper.sh` that sources `~/.copilot/secrets/<name>.env` and execs the server binary. See `unifi-mcp-wrapper.sh` as the reference example.
2. `chmod +x` the wrapper.
3. Reference the wrapper as `command` in `~/.copilot/mcp-config.json` with an empty `env: {}`.
4. Add a header comment to the wrapper documenting exactly which env vars `secrets/<name>.env` must contain.
5. The user creates `~/.copilot/secrets/<name>.env` (already gitignored) with `chmod 600`.
6. Verify with `/mcp show <name>` after `/mcp reload` or a restart.

## Adding a personal skill

```text
~/.copilot/skills/<lowercase-hyphenated-name>/
└── SKILL.md          # YAML frontmatter (name, description, optional allowed-tools) + Markdown body
```

The `description` is what Copilot pattern-matches against to decide when to load the skill — write it as "Use when the user asks to …" so it surfaces at the right moments.

After adding, run `/skills reload` (no need to restart the CLI).

## Verifying the change

- Shell changes: `exec zsh` or open a new shell, then test.
- Brewfile: `brew bundle check --file=~/dotfiles/Brewfile` should report "satisfied".
- MCP: `/mcp show <name>` should list tools.
- Skill: `/skills info <name>` should display the skill.

## Commit etiquette

- One concern per commit.
- Conventional commit prefix; scope optional but encouraged (e.g. `feat(zsh): add pip alias`).
- **Never** add a `Co-authored-by: Copilot` trailer — this is an explicit user preference.
- For changes that span both repos (e.g. install a tool *and* wire its MCP server), commit each repo separately with clear, parallel commit messages.

## Related skills

- **`homelab-helper`** (global) — for anything that runs as a long-lived service on hyperion (QNAP) or solaris (Mac Mini). New docker stack, ollama model, BYOK provider key, Caddy route → that skill, not this one. This skill stays focused on **Mac client** machine env.
