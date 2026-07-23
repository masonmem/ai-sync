# Personal global instructions (@masonmem)

<!--
Injected into every session of any AI CLI that points at this file
(Claude Code via the @-import in ~/.claude/CLAUDE.md, Copilot CLI via
~/.copilot/copilot-instructions.md, Codex via ~/.codex/AGENTS.md).
Budget is precious:
* Keep terse — GENERAL, portable content only.
* Machine-, homelab-, or personal-environment-specific guidance belongs
  in skills/personal/*, which load on demand.
* Project facts live in each repo's AGENTS.md.
* User-facing meta (why this file exists, what to put in it) lives in
  the repo README, not here.
-->

## Communication

- Be concise. Lead with the answer; elaborate only when asked or when the work is non-trivial.
- Push back on bad ideas and surface trade-offs I might miss. Don't reflexively agree.
- Don't create documentation files to summarize work unless explicitly asked.

## Commits

- Use Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, etc. Scope optional.
- **Never** add a `Co-authored-by: Copilot` *or* `Co-authored-by: Claude` trailer. Mason treats commits as his own regardless of which assistant produced the diff.

## Repository boundaries

- Before editing, identify the repository root, branch, current worktree, and status. Work only inside that worktree.
- Never modify the canonical checkout during implementation.
- Do not push, merge, rebase, reset, clean, switch branches, create or delete branches, update refs, or manipulate worktrees unless explicitly requested.
- Never hand-edit generated code. Use the repository's existing commands and conventions.
- Do not create AI workflow artifacts—context files, ADRs, specifications, ticket drafts, handoffs, or research notes—inside a work repository unless explicitly authorized.
- Keep personal project state under `~/.local/share/ai-sync/projects/<stable-repository-key>/` by default.

## Validation and data

- For defects, reproduce the problem and add a regression test when feasible.
- Run the smallest relevant validation first, then the repository's existing normal verification commands.
- Report exact validation commands, results, and unresolved risks.
- Send source, vulnerability findings, and other work information only to providers approved for that data classification. Follow provider, MCP, and network-destination restrictions.

## Non-interactive (`-p` / `--prompt`) sessions

- Do the requested task, reply with the result, and stop. No speculative follow-up tool calls.

## Tool selection

- Prefer a mature authenticated CLI over an equivalent MCP surface; request narrow structured output when available.
- Keep MCP only when it adds domain semantics, interactive state, or access a CLI/native tool does not provide.
- For GitHub, use `gh` with `--json`/`--jq`/`--template` or `gh api`; do not use a GitHub MCP when `gh` covers the task.

## Expensive orchestration

- Never launch a dynamic workflow or large multi-agent fan-out unless Mason explicitly requests that mechanism and confirms the proposed maximum agent count. Research requests alone do not authorize workflows; use direct search/fetch and a small bounded number of agents.
