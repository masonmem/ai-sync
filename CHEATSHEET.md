# Personal AI engineering cheatsheet

## Sessions and boundaries

```sh
cop-cloud                         # hosted, BYOK vars cleared, Luna, 100-credit cap
cop-laguna                        # approved Laguna config + Keychain; currently pending
cop-implement cloud               # bounded writer; use "laguna" only after governance approval
cop-review cloud --model <model>  # invoke-only reviewer; default 50-credit cap
ai-project-state --ensure         # external project workflow state
```

`cop-cloud` is the safe default until Laguna's data boundary is documented.
Never put a provider credential in `laguna.env`, a repository env file, shell
history, `ai-sync`, or dotfiles.

## Workflow

```text
/grill-with-docs → /to-spec → /to-tickets → fresh /implement
                                            ↳ /tdd as the inner discipline
```

Keep context, ADR/spec/ticket drafts, research, and retained handoffs under the
path from `ai-project-state --ensure`. Repository-resident AI artifacts are
opt-in. Run `/handoff` before escalating to a fresh or more expensive model.
Never run `/setup-matt-pocock-skills` in a real work repository.

## Worktrees, tmux, and containers

```sh
wt new feature/name [base]
wt ls
wt path feature/name
wt rm feature/name
wt delete-branch feature/name
wt prune

tmux new -s ticket
cop-implement cloud
```

`wt rm` refuses dirty tracked or untracked state and does not delete the branch.
`wt prune` prints a dry run and requires confirmation. Worktrees live under the
canonical checkout's `.worktrees/<safe-slug>` while keeping the real branch
name unchanged.

`wt` never copies `.env` or `.env.local`. A future repository-provided
initialization command may be added only by that repository's owners. Where
policy permits, a future worktree may explicitly symlink a canonical local env
file; that is not automatic.

Generic container launch pattern:

```sh
devcontainer exec --workspace-folder <canonical-path> \
  zsh -lc 'cd .worktrees/<slug> && cop-implement cloud'
```

After cloning `ai-sync` inside a work container, run
`./install.sh --work --container`. No team-owned `devcontainer.json` is needed.

## Model and cost routing

Use the least expensive model that has demonstrated adequate capability.

| Level | Initial route |
| --- | --- |
| L0 | Laguna for approved high-volume research, planning, implementation, test scaffolding, and mechanical fixes |
| L1 | GPT-5.6 Luna for small deterministic tasks or Laguna tooling failure |
| L2 | Cheapest validated general model; compare GPT-5.6 Terra with Claude Sonnet 5 |
| L3 | GPT-5.6 Sol for deep codebase reasoning; Claude Opus 4.8 for difficult independent judgment when validated |
| Review | Different model family for medium/high risk; skip paid cross-family review for trivial deterministic changes |

Current published per-million-token list prices are Luna
`$1 input / $0.10 cached / $6 output`, Terra
`$2.50 / $0.25 / $15`, and Sol `$5 / $0.50 / $30`. Sonnet 5's stated
promotion through August 31, 2026 is provisional. Re-evaluate routing and
allowances around September 1.

Hosted soft-cap starting points:

```sh
COPILOT_MAX_AI_CREDITS=50 cop-cloud    # small task
COPILOT_MAX_AI_CREDITS=100 cop-cloud   # normal ticket
COPILOT_MAX_AI_CREDITS=200 cop-cloud   # architecture / difficult debugging
```

Plan around Mason's normal 3,000-credit baseline, not the one-time extra
5,000-credit approval.

Escalate after two evidence-based fix/test loops fail, repeated bad tool calls,
no falsifiable diagnosis, scope expansion, false assumptions, multiple
architectural boundaries, or any auth/secrets/security boundary:

```text
current session → /handoff → fresh session → higher model
```

## Canaries and deferrals

Copy `canaries/` to external scratch state and record results in `RESULTS.md`.
Zed is deferred to avoid a second editor/configuration surface. `/fleet` is
deferred until provider inheritance, credit behavior, and agent-count controls
are validated.
