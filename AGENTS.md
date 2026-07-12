# ai-sync

Shared personal AI configuration for Claude Code, Copilot CLI, and Codex.
`~/code/ai-sync` is canonical; client home directories are rendered or linked
surfaces.

## Commands

```bash
./bin/ai-sync test       # isolated pytest suite
./bin/ai-sync apply      # reconcile links, settings, and MCP registrations
./bin/ai-sync status     # read-only drift and secret-permission check
./bin/ai-sync doctor     # status with remediation hints
```

## Architecture

- `agents/general.md` is the terse global instruction source.
- `skills/general/` is portable; `skills/personal/` is linked only on hosts
  represented under `hosts/`.
- `mcp/servers.toml` is canonical; `mcp.json` is generated and gitignored.
- Native client settings stay in `claude/` and `copilot/`; host overlays are
  deep-merged into real files and may accumulate runtime drift.
- `bin/ai-sync-doctor` retains the Python-free fan-out implementation;
  `bin/ai-sync` orchestrates it.

## Conventions

- Add tests for every `bin/ai-sync` behavior change.
- Never commit secret values; inventory new local files in
  `secrets/manifest.toml`.
- Do not hand-edit generated `mcp.json` or client-side rendered settings.
- Preserve unknown real files: repair commands must fail rather than clobber.
