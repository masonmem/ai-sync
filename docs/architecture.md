# `~/.ai-config` architecture

This directory is the canonical "AI brain" — the shared layer consumed by
Claude Code, Copilot CLI, and any future LLM client. It is paired with
[`masonmem/dotfiles`](https://github.com/masonmem/dotfiles) (machine env) and
[`masonmem/homelab`](https://github.com/masonmem/homelab) (running services).

## The rule: scope is determined by path

Every file in this repo answers exactly one question: "which tools does this
affect?" That question is encoded in the **path**, not in the file's contents.

| Path under `~/.ai-config/` | Scope | Notes |
|---|---|---|
| `instructions.md`, `skills/`, `agents/`, `bin/`, `secrets/` | **shared** — every client | Symlinked into each client's home dir (`~/.claude/`, `~/.copilot/`). Formats here MUST be ones every consuming client accepts. |
| `claude/…` | **Claude Code only** | The file lives at the path Claude Code expects (`claude/settings.json` → `~/.claude/settings.json`). |
| `copilot/…` | **Copilot CLI only** | Same pattern. |
| `mcp/servers.toml` | **all clients, translated** | The single source of truth for MCP servers. `ai-sync apply` reads this and emits each client's native registration. |
| `mcp.json` | **generated** | Derived from `mcp/servers.toml` by `ai-sync apply`. Header reminds you not to hand-edit. |
| `docs/`, `README.md` | **documentation** | Not consumed by any client. |
| `tests/` | **infrastructure** | pytest suite for `bin/ai-sync`. |

You — or any LLM editing this tree — can find the right home for a change by
looking at the path. There is no decision tree to memorise beyond the table
above.

## Why we don't have a canonical-config DSL

A "shared settings.json that translates to each tool" sounds elegant, but it
makes you a translator vendor. Every time Claude Code or Copilot ships a new
setting (`statusLine`, `enabledPlugins`, `policySettings`, …) you have to
extend the DSL or it silently drops the field. We tried it implicitly with the
`mcpServers` block under `settings.json` and got bitten when Claude Code
ignored it.

The **only** concept where translation pays off is **MCP servers**: every tool
has them, every tool stores them differently, and there are only ~5 fields to
translate. So that's the only translator we maintain (`bin/ai-sync`,
~400 lines of Python). For everything else, the per-tool file is in the
per-tool directory in the tool's native schema — the rule above keeps that
honest.

## Three layers of variability

1. **Per-tool** (Claude vs Copilot) → directory: `claude/`, `copilot/`.
2. **Per-host** (Mac laptop vs Mac Mini vs QNAP) → *not yet implemented*. Tracked
   as v2 in [`README.md`](../README.md). When it lands, the shape will be
   `hosts/<hostname>.json` merged at `ai-sync apply` time into a rendered
   `~/.claude/settings.json` (Claude Code's `settings.local.json` only works at
   project scope — verified in v1 by grep'ing the binary, not at user scope).
3. **Per-project** → handled by each client's own project-scope mechanism
   (`.claude/settings.json`, `.github/copilot-instructions.md`). Not this repo's
   problem.

## The `ai-sync` CLI

A single Python entry point (`bin/ai-sync`, stdlib-only) with four subcommands.

| Command | What it does | Exit code |
|---|---|---|
| `ai-sync status` | Reports symlink state, MCP registration in each client, and secret-file permissions. Read-only. | `0` if clean, `1` if any drift detected. |
| `ai-sync apply [--pull]` | Idempotent: renders `mcp.json` from `mcp/servers.toml`; refreshes symlinks into `~/.claude/` and `~/.copilot/`; runs `claude mcp add` for any server not yet registered; sets +x on `bin/*.sh`. With `--pull`, runs `git pull --ff-only` first (refuses on dirty tree). | `0` on success. |
| `ai-sync mcp list` | Prints parsed `mcp/servers.toml` with placeholders expanded. | `0`. |
| `ai-sync test` | Runs `pytest tests/`. | pytest exit code. |

The two legacy bash scripts (`bin/bootstrap-claude.sh`, `bin/ai-config-sync`)
remain as **shims** so external callers (notably solaris's launchd job and
muscle-memory invocations) don't break. They delegate to `ai-sync apply`.

## MCP registry: `mcp/servers.toml`

The single declaration site for every MCP server. `ai-sync apply` is the only
thing that should write to either `~/.claude.json` (via `claude mcp add`) or
`~/.ai-config/mcp.json` (regenerated each apply). Schema:

```toml
[<name>]
command     = "<absolute-path-or-${AI_CONFIG}-relative>"  # required
args        = ["..."]                                     # optional
description = "..."                                       # optional, shown by `ai-sync mcp list`
secrets_env = "${AI_CONFIG}/secrets/<name>.env"           # optional, status() warns on loose perms
hosts       = ["navi", "solaris"]                         # optional, empty/missing = all
clients     = ["claude", "copilot"]                       # optional, empty/missing = all
```

Placeholders `${AI_CONFIG}` and `${HOME}` are expanded by `ai-sync` itself, not
by the shell — so the file stays machine-portable.

### Adding a new MCP server

1. If it needs secrets, write the wrapper at `bin/<name>-mcp-wrapper.sh`
   following the pattern of `bin/unifi-mcp-wrapper.sh` (sources
   `secrets/<name>.env`, execs the server binary).
2. Add a `[<name>]` table to `mcp/servers.toml`.
3. Run `ai-sync apply`.
4. Restart any running Claude Code session so it loads the new server.

That's the entire process. There is intentionally no JSON to edit twice and no
hardcoded `claude mcp add` line in any bootstrap script.

### Adding a new LLM client (e.g. Cursor)

1. Make a `cursor/` directory for its native config files.
2. Add `CURSOR_LINKS` to `bin/ai-sync` describing the symlink fan-out.
3. If it has its own MCP registration mechanism, add a `register_mcp_cursor()`
   function and call it from `apply_cmd()`. Add a `cursor:` row to the status
   output.
4. Add tests for the new symlinks and MCP path under `tests/`.

The translator stays small because each new client only adds one function and
one link table — no schema generalisation required.

## Testing

`pytest tests/` (also reachable as `ai-sync test`). The test suite runs every
subcommand against an isolated fake `$HOME` with a stub `claude` binary that
records its argv to a file. No real network, no real `claude` invocation, no
touching of the actual `~/.ai-config`. Fixtures live in `tests/conftest.py`.

A test must be added whenever:
- A new symlink is added to `*_LINKS` in `bin/ai-sync`.
- A new MCP registry field is parsed.
- A new client gets its own `register_mcp_*` or `write_*_mcp_json` function.

## What we deliberately don't do (v1)

- No per-host overlay / template rendering. Theme-on-host-A vs theme-on-host-B
  is currently a manual problem; landing this is the first v2 piece.
- No `ai-sync doctor` with actionable suggested-fix commands.
- No `ai-sync mcp add <name> <command>` — edit `mcp/servers.toml` directly.
- No conflict states beyond `MISSING` / `DRIFTED`. "in conflict" only becomes
  meaningful once render-then-write exists in v2.
- No distribution as a brew tap or pipx package. `bin/ai-sync` lives here;
  it's our tool.
