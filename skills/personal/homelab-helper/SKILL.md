---
name: homelab-helper
description: Use when adding or changing a docker stack, ollama model, Caddy route, homelab service, or anything long-lived on hyperion (QNAP) or solaris (Mac Mini) — all managed GitOps-style from masonmem/homelab via Komodo. Not for Mac client config (use dotfiles-helper) or network/UniFi design docs (masonmem/network).
---

# homelab-helper

This skill captures @masonmem's homelab GitOps conventions. The promise: **anything that runs as a long-lived service on hyperion or solaris is described in `masonmem/homelab` and deployed by Komodo from git.** SSH-and-hand-edit is an emergency-only escape hatch.

For Komodo *mechanics* (resource TOML format, Periphery secrets procedure, auth debugging, backups, rollback), use the in-repo `komodo-ops` skill at `homelab/.claude/skills/komodo-ops/` — it auto-loads when working in that repo. This skill covers what-goes-where and the conventions.

## The repos (don't get them confused)

| Repo | Owns | NOT for |
|---|---|---|
| `masonmem/dotfiles` | Mac machine env (Brewfile, zsh, stow), Mac-local launchd agents | Anything on hyperion or solaris-the-Docker-host |
| `masonmem/ai-sync` | Shared AI brain — skills, instructions, MCP wrappers; consumed by Claude Code, Copilot CLI, Codex | Service deploys |
| **`masonmem/homelab`** | Compose stacks + non-secret config for hyperion + solaris, Komodo resources | Mac client config, network design docs |
| `masonmem/network` (at `~/code/network`) | Network design, UniFi/Cloudflare/NextDNS docs | Compose stacks (those live in `homelab`) |

If the change is "thing X is running on hyperion or solaris," it's in `homelab`. If it's "this Mac has tool Y," it's `dotfiles`.

## Where things live (the source-of-truth table)

| Want to add… | Edit | Result |
|---|---|---|
| Brew package (Mac) | `dotfiles/Brewfile` → `brew bundle` | Available after pull |
| Shell alias / env var | `dotfiles/zsh/.config/zsh/20-aliases.zsh` | `exec zsh` |
| MCP server (user-global) | `~/code/ai-sync/mcp/servers.toml` + optional wrapper, then `ai-sync apply` (see `dotfiles-helper`) | Copilot `/mcp reload`; Claude Code session restart |
| AI skill (global) | `~/code/ai-sync/skills/personal/<name>/SKILL.md` + `~/.claude/skills/` symlink (see `dotfiles-helper`) | Copilot `/skills reload`; Claude Code session restart |
| AI skill (project) | `<repo>/.copilot/skills/<name>/SKILL.md` (Copilot) or `<repo>/.claude/skills/<name>/SKILL.md` (Claude Code) | Auto-discovered |
| **New stack on hyperion** | `homelab/hyperion/<stack>/compose.yaml` + Komodo Stack resource in `homelab/komodo/resources/` | Push → Komodo syncs |
| **New stack on solaris** | `homelab/solaris/<stack>/compose.yaml` + Komodo Stack resource | Push → Komodo syncs |
| **New ollama model** | `homelab/solaris/ollama/modelfiles/<name>.Modelfile` + `apply.sh` entry + `solaris/litellm/config.yaml` entry + `dotfiles/ollama/.config/opencode/opencode.jsonc` entry | Run apply.sh on solaris, restart litellm |
| UniFi / network change | `network` repo at `~/code/network` (docs) + UniFi UI (live state via `unifi` MCP) | — |
| **Caddy reverse-proxy entry** | `homelab/hyperion/infra/Caddyfile` | Push → Caddy reloads |
| **Image version bump (any image)** | Renovate PR; `control-plane`-labeled PRs for Komodo Core/Periphery, FerretDB, Postgres | Merge → Komodo redeploys |

**Cloud/BYOK provider keys: non-goal.** The LLM platform is local-only since 2026-06-11 — no `cloud/*` model entries, no provider keys in Periphery secrets. Do not re-add them. See `homelab/docs/llm-platform.md` § "Cloud providers — not used".

## Hard rules

1. **No `:latest` image tags, ever.** Everything is pinned `vX.Y.Z@sha256:...`; the control plane bumps in lockstep in a `control-plane`-labeled PR.
2. **No plaintext secrets in git.** All secrets are Komodo Periphery `[secrets]` blocks in each host's `periphery.config.toml`. The canonical index is `komodo/resources/secrets-inventory.toml` — **always update it in the same PR** as the `[[NAME]]` reference or the `validate-stacks` CI job fails. Prefer `scripts/periphery-secrets.py {pull,edit,push,check} <host>` over raw ssh+vi. Mechanics: `komodo-ops` skill + `docs/security.md`.
3. **Secret rotation needs a redeploy, and the key must appear in the stack's `environment` block.** Editing `periphery.config.toml` alone changes nothing (container keeps old env); a key in `[secrets]` that isn't in the consuming stack's `environment = """…"""` block in `komodo/resources/*-stacks.toml` is silently absent. Rotate → `komodo.py deploy <stack>`.
4. **Secrets embedded in URLs (DATABASE_URL, AMQP/Redis URIs) must be URL-safe.** Generate with `openssl rand -hex 24`, never `-base64` (a `/` or `+` inside `postgres://user:pass@host` crash-loops the consumer). Postgres only honors `POSTGRES_PASSWORD` at first init — rotating after the data dir exists requires `ALTER USER` or a fresh data dir.
5. **No Watchtower on Komodo-managed stacks.** Renovate is the bump mechanism.
6. **No SSH-and-hand-edit on hyperion/solaris** for anything that should be reproducible. Emergency-only; if you used it, fold the change back into git the same day.
7. **Don't touch Caddy or `monitor` without an escape hatch.** They're the front door and the observatory.
8. **Config changes flow through GitOps automatically.** The `GitOps Auto-Deploy` Komodo procedure (5-min poll) syncs, diffs each stack's runtime inputs (compose `file_paths` + `EXTRA_WATCH_PATHS` additions), and deploys; LiteLLM gets a post-deploy restart to flush its in-process model cache (covers model removal too). Lives in `komodo/resources/actions.toml`. Manual override: `python3 scripts/komodo.py deploy litellm && ssh solaris '/opt/homebrew/bin/docker restart litellm'`.
9. **Ollama on solaris listens on `0.0.0.0:11434`** (LaunchAgent-managed, standalone install — the Homebrew formula is broken, see `docs/disaster-recovery.md`) and reads models from `/Volumes/Helio/ollama/models` via `OLLAMA_MODELS`. LiteLLM reaches it at `host.docker.internal:11434`. If every `local/*` model 500s "model not found", the external volume dropped — kickstart the ollama LaunchAgent after confirming `/Volumes/Helio` is mounted.
10. **Model behaviour rules live in `docs/llm-platform.md` § "Rules learned the hard way"** — `ollama_chat/` vs `ollama/` prefixes, `reasoning_effort: none` for non-reasoning models, verifying `ollama show <model>` lists `tools` before enabling them, OWUI task-model pinning. Read that section before editing `solaris/litellm/config.yaml` or model capability flags.
11. **OWUI conventions live in `docs/openwebui.md`** — default tools must be per-model (Workspace Model `meta.toolIds`), never user-level; tool-server registration is not declarative (curl recipe there). MCP tools for OWUI run as `mcpo`-wrapped stacks on loopback `127.0.0.1:81XX`, auth via per-tool `*_MCP_KEY` Periphery secret.
12. **Chat plane is read-only; agent plane is `opencode` over Tailscale SSH.** OWUI only gets read-class tools (filesystem `:ro`, `git log/diff/show`, fetch, search) — the vault syncs from git, so anything pasted into a note is an injection vector; read-only mounts are the enforcement. Anything that mutates (shell, file edits, git mutation, installs) belongs behind `opencode`'s approval gate in tmux on solaris.
13. **Host-level repo sync uses a LaunchAgent in `solaris/<name>-sync/`** (install.sh + plist + script trio, mirroring `komodo-monitor` and `notes-sync`). Script does `git fetch && git merge --ff-only` only — never push — on `StartInterval=300`. Use this pattern whenever a file tree from GitHub must live on solaris/hyperion outside a Docker volume.
14. **Cross-surface guidance for shared resources must be mirrored.** The CLI surfaces (Claude Code, Copilot CLI, Codex) share one instruction file: `~/code/ai-sync/agents/general.md`. opencode (`~/dotfiles/ollama/.config/opencode/AGENTS.md`) and the OWUI workspace-model prompt (`homelab/solaris/openwebui/system-prompts/granite-tools.md`, re-applied to webui.db via the `docs/openwebui.md` bootstrap recipe) are separate and must be updated in parallel when vault or shared-tool conventions change.

## Adding a new docker stack

```
homelab/<host>/<stack>/
  compose.yaml         # Image pinned to <tag>@sha256:<digest>; references ${VAR:?err} for everything
  .env.example         # Documents required vars; never the real values
  <config files>       # Caddyfile fragments, prometheus rules, dashboards, etc.
```

Then add a Komodo Stack resource in `komodo/resources/<host>-stacks.toml` pointing at the directory. Any secret the stack consumes goes in that host's Periphery `[secrets]` block, referenced from compose via `${KEY:?}`. Push → Komodo syncs. Full checklist and resource format: `komodo-ops` skill.

## Adding an ollama model

1. Add a Modelfile to `homelab/solaris/ollama/modelfiles/<short>.Modelfile` (bake `num_ctx`, sampler params, optional SYSTEM prompt per the author's recipe).
2. Add the rebuild to `apply.sh`.
3. Add a matching `local/<short>-0x` entry to `solaris/litellm/config.yaml` with `reasoning_effort: none` unless it's a true reasoning model.
4. Push, then on solaris run `~/code/homelab/solaris/ollama/modelfiles/apply.sh` to rebuild + tag, and `docker restart litellm` to load the config.
5. Add to `dotfiles/ollama/.config/opencode/opencode.jsonc` with sampler overrides.

See `solaris/ollama/modelfiles/README.md` for conventions and `docs/llm-platform.md` for naming/routing.

## Escape hatches (use only when Komodo is the problem)

- **hyperion direct:** `ssh hyperion '/share/CACHEDEV3_DATA/.qpkg/container-station/bin/docker compose -f /share/containers/stacks/<stack>/compose.yaml ...'`
- **solaris direct:** `ssh solaris 'bash -lc "docker compose -f ~/komodo/stacks/<stack>/solaris/<stack>/compose.yaml ..."'`
- **Direct ollama bypass:** `OLLAMA_HOST=http://solaris:11434` (kept in `~/code/ai-sync/secrets/local.env` as an escape hatch from LiteLLM)

If you used an escape hatch, **fold the change back into git within the same day** or it stops being a homelab and starts being a pet.

## Related skills

- `dotfiles-helper` — Mac client config (alias, env var, MCP, brew, LaunchAgent)
- `komodo-ops` (in `masonmem/homelab`) — Komodo resource format, Periphery secrets procedure, auth debugging, backup/restore, rollback

(No network skill exists; UniFi / Cloudflare / NextDNS / VLAN changes are docs in `masonmem/network` at `~/code/network`, with live state via the `unifi` MCP.)
