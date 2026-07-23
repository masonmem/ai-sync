# Validated versions and compatibility

Audit date: 2026-07-23. Host: Apple Silicon macOS.

## Host

| Component | Observed |
| --- | --- |
| Git | 2.55.0; `git worktree add --relative-paths` supported |
| GitHub Copilot CLI | 1.0.73 |
| Node / npm / pnpm / Yarn | 26.5.0 / 11.17.0 / 11.15.1 / 1.22.22 |
| Python | 3.14.6 |
| VS Code | 1.129.1 arm64 |
| Dev Containers extension / bundled CLI | 0.466.0 / 0.88.0 |
| Docker client | 29.6.2 |
| tmux / GNU Stow / GitHub CLI | 3.7b / 2.4.1 / 2.96.0 |

Bun and Corepack are not installed. The standalone `devcontainer` command is
not on `PATH`; VS Code bundles it. Docker Desktop's daemon was stopped during
the audit, so no current dev-container could be opened.

## Dev container

Container Git, Node, Copilot CLI, and package-manager versions remain
unverified. The historical dev-container workspace no longer exists and the
Docker daemon was unavailable. First use must run:

```sh
~/code/ai-sync/install.sh --work --container
~/code/ai-sync/install.sh --work --check
```

Record the resulting versions here only after a real approved work container is
available. No team `devcontainer.json` was changed.

## Skills

- Installer: `skills@1.5.20`.
- Source: `mattpocock/skills`.
- Revision: `ed37663cc5fbef691ddfecd080dff42f7e7e350d`.
- Revision date: 2026-07-21.
- Installed catalog: 22 promoted engineering/productivity skills.
- Installation was staged in an isolated home for `github-copilot` with copy
  mode, reviewed, then vendored unchanged into `skills/general`.

The installer otherwise chooses `~/.agents/skills` as its canonical global
location even for GitHub Copilot. `ai-sync` deliberately does not use that
topology because Copilot also scans `~/.copilot/skills`, producing duplicate
discovery.

## Copilot CLI behavior

Available hosted models observed in 1.0.73:

`claude-sonnet-5`, `claude-sonnet-4.6`, `claude-sonnet-4.5`,
`claude-haiku-4.5`, `claude-fable-5`, `claude-opus-4.8`,
`claude-opus-4.8-fast`, `claude-opus-4.7`, `claude-opus-4.6`,
`claude-opus-4.5`, `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`,
`gpt-5.5`, `gpt-5.4`, `gpt-5.3-codex`, `gpt-5.4-mini`, `gpt-5-mini`,
`gemini-3.1-pro-preview`, `gemini-3.5-flash`, and `kimi-k2.7-code`.

Custom `.agent.md` files support `name`, required `description`, `infer`,
`tools`, and optional `model`. Baseline agents use `infer: false` and inherit
the launch-session model. Tool lists only control visibility; launch flags and
the `preToolUse` hook enforce the writer/reviewer boundary.

User hooks are loaded from `~/.copilot/hooks/*.json`. The validated version-1
schema supports synchronous `preToolUse` commands and
`permissionDecision: deny`.

`--max-ai-credits` is supported with a minimum of 30. It is an opt-in soft cap:
usage is known only after a model call, so one call can cross the cap; the next
call is blocked. Subagents share the session limit. `/clear` or `/new` resets
observed usage while retaining the configured cap. The launchers provisionally
use 50 credits for review and 100 for a normal hosted session; use 200
explicitly for architecture or difficult debugging.

## Laguna BYOK

The approved work-machine gateway model identifier is `laguna-s-2-1`. The
gateway URL and credential are configured locally and are deliberately not
recorded here.

A non-sensitive disposable-repository smoke test verified streaming, file
reading, two small file creations, shell execution, executable permission
changes, and a passing regression test. Tool arguments were correct for those
operations. One shell command (`git log`) exited 128 because the scratch
repository had an unborn `main` branch; this was benign but is still counted as
a tool-call failure.

Copilot CLI 1.0.73 does not recognize `laguna-s-2-1` in its built-in catalog,
so exact `COPILOT_PROVIDER_MAX_PROMPT_TOKENS` and
`COPILOT_PROVIDER_MAX_OUTPUT_TOKENS` values remain required from the approved
gateway or VS Code model configuration. Do not guess them.

Pending smoke tests: web fetch, `/research`, GitHub access, required MCPs,
session-state location, and proof of zero hosted-credit use. `/fleet` is
intentionally excluded. Subagent provider inheritance is unverified.

A 30-credit-capped, non-sensitive hosted writer test was attempted in a
disposable Git repository. Copilot returned “Access denied by policy settings”
before a model turn or tool call, so actual custom-agent enforcement and credit
consumption could not be observed on this account. Repeat that test with the
approved work account.

No approved record was available for work-data classifications, retention,
training use, tenancy/isolation, endpoint operator, log access,
vulnerability-data handling, organization BYOK policy, or permitted MCP/network
destinations. Use only non-sensitive scratch content until those are confirmed.

References:

- GitHub BYOK documentation: <https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-byok-models>
- Copilot CLI hooks: <https://docs.github.com/en/copilot/reference/hooks-reference>
- Models and pricing: <https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing>
