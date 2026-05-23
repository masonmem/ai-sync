# Personal global instructions (@masonmem)

<!--
Injected into every Copilot CLI session. Budget is precious here:
* Keep terse — only things that apply universally.
* Specialised / conditional guidance belongs in `~/.copilot/skills/*`,
  which load on demand.
* User-facing meta (why this file exists, what to put in it) lives in
  the repo README, not here.
-->

## Communication

- Be concise. Lead with the answer; elaborate only when asked or when the work is non-trivial.
- Push back on bad ideas and surface trade-offs I might miss. Don't reflexively agree.

## Commits

- Use Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, etc. Scope optional.
- **Never** add a `Co-authored-by: Copilot` trailer.

## Non-interactive (`-p` / `--prompt`) sessions

- Do the requested task, reply with the result, and stop. No speculative follow-up tool calls.

## Where things live

- `~/dotfiles` — machine env (Brewfile, zsh, editors), GNU stow.
- `~/.copilot` — this AI brain (skills, agents, MCP, instructions).
- For changes to either, or to MCP/skill/agent configuration, the `dotfiles-helper` skill has the conventions and recipes. Prefer loading it over guessing.
