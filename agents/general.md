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

## Delivery workflow (PRs)

- Ship every change as a PR — never commit to `main` directly. Branch → Conventional Commits → PR.
- The PR description must stand alone: what changed and why, behavioral changes, and test evidence (commands run + results, not "tests pass"). Fill the repo's PR template if one exists.
- Mason reviews and merges — never merge or self-approve. Address review with follow-up commits on the same branch; don't force-push once review has started.
- Deployed repos are GitOps: merging to `main` is what ships (e.g. vision-utils, homelab). Read the repo's `AGENTS.md` for its pipeline before claiming anything is live.
- Update in-repo docs in the same PR when behavior changes.

## Non-interactive (`-p` / `--prompt`) sessions

- Do the requested task, reply with the result, and stop. No speculative follow-up tool calls.

## Tool selection

- Prefer a mature authenticated CLI over an equivalent MCP surface; request narrow structured output when available.
- Keep MCP only when it adds domain semantics, interactive state, or access a CLI/native tool does not provide.
- For GitHub, use `gh` with `--json`/`--jq`/`--template` or `gh api`; do not use a GitHub MCP when `gh` covers the task.

## Expensive orchestration

- Never launch a dynamic workflow or large multi-agent fan-out unless Mason explicitly requests that mechanism and confirms the proposed maximum agent count. Research requests alone do not authorize workflows; use direct search/fetch and a small bounded number of agents.
