# Personal global instructions (@masonmem)

<!--
Injected into every session of any AI CLI that points at this file
(currently Copilot CLI via ~/.copilot/copilot-instructions.md and
Claude Code via ~/.claude/CLAUDE.md, both symlinks into here). Budget
is precious:
* Keep terse — only things that apply universally.
* Specialised / conditional guidance belongs in `~/.ai-config/skills/*`,
  which load on demand.
* User-facing meta (why this file exists, what to put in it) lives in
  the repo README, not here.
-->

## Communication

- Be concise. Lead with the answer; elaborate only when asked or when the work is non-trivial.
- Push back on bad ideas and surface trade-offs I might miss. Don't reflexively agree.

## Commits

- Use Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, etc. Scope optional.
- **Never** add a `Co-authored-by: Copilot` *or* `Co-authored-by: Claude` trailer. Mason treats commits as his own regardless of which assistant produced the diff.

## Non-interactive (`-p` / `--prompt`) sessions

- Do the requested task, reply with the result, and stop. No speculative follow-up tool calls.

## Personal notes vault

- `~/notes` is the Obsidian vault (journal, inbox, projects, writing).
  Same vault is exposed to opencode as the `notes` MCP server and to
  Open WebUI as the `notes` tool server, so vault behaviour is symmetric
  across all agent surfaces.
- When the user mentions "my notes", "the inbox", "what did I write
  about X", or anything implying the personal vault, USE the available
  notes/filesystem tools rather than refusing. Don't reply with "I
  don't have access to your personal notes" — you do.
- Latest-by-mtime: start with `~/notes/00-inbox/` or the most recent
  dated subfolder; fall back to a search by query for topical asks.
- Treat the vault as **read-only by default**. Only write under
  `~/notes/00-inbox/agent-drafts/` (matches the OWUI airlock), and
  only when the user explicitly asks you to save / draft something.

## Where things live

- `~/dotfiles` — machine env (Brewfile, zsh, editors), GNU stow.
- `~/.ai-config` (`masonmem/ai-config`) — shared AI brain (skills, agents, MCP wrappers, per-tool settings, instructions). `~/.copilot/` and `~/.claude/` are thin Copilot-/Claude-Code-shaped surfaces whose tracked entries are symlinks into here.
- `~/code/homelab` (`masonmem/homelab`) — GitOps source of truth for hyperion (QNAP) + solaris (Mac Mini) docker stacks; orchestrated by Komodo.
- `~/code/network` (`masonmem/network`) — network design + UniFi/Cloudflare/NextDNS docs only (NOT stacks; those live in `homelab`).
- For dotfiles/ai-config changes, the `dotfiles-helper` skill has the conventions. For homelab/stack/ollama/BYOK changes, the `homelab-helper` skill does. Prefer loading them over guessing.
