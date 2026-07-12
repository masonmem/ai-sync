---
name: homelab-helper
description: Encodes the GitOps conventions of @masonmem's homelab (hyperion QNAP + solaris Mac Mini), orchestrated by Komodo from masonmem/homelab. Use when the user wants to add or change a docker stack, ollama model, homelab service, BYOK provider key, Caddy route, or anything that runs on hyperion or solaris.
---

# homelab-helper

This skill captures @masonmem's homelab GitOps conventions. The promise: **anything that runs as a long-lived service on hyperion or solaris is described in `masonmem/homelab` and deployed by Komodo from git.** SSH-and-hand-edit is an emergency-only escape hatch.

## The three repos (don't get them confused)

| Repo | Owns | NOT for |
|---|---|---|
| `masonmem/dotfiles` | Mac machine env (Brewfile, zsh, stow), Mac-local launchd agents | Anything on hyperion or solaris-the-Docker-host |
| `masonmem/ai-sync` (was `masonmem/copilot`) | Shared AI brain — skills, agents, MCP wrappers, instructions; consumed by both Copilot CLI (`~/.copilot/`) and Claude Code (`~/.claude/`) via symlinks into `~/.ai-config/` | Service deploys |
| **`masonmem/homelab`** | Compose stacks + non-secret config for hyperion + solaris, Komodo resources, age public keys | Mac client config, network design docs |
| `masonmem/network` (at `~/code/network`) | Network design, UniFi/Cloudflare/NextDNS docs | Compose stacks (those moved to `homelab` during the migration) |

If the change is "thing X is running on hyperion or solaris," it's in `homelab`. If it's "this Mac has tool Y," it's `dotfiles`.

## Where things live (the source-of-truth table)

| Want to add… | Edit | Result |
|---|---|---|
| Brew package (Mac) | `dotfiles/Brewfile` → `brew bundle` | Available after pull |
| Shell alias / env var | `dotfiles/zsh/.config/zsh/20-aliases.zsh` | `exec zsh` |
| MCP server (user-global) | `~/.ai-config/mcp/servers.toml` (single source of truth) + optional `~/.ai-config/bin/<name>-mcp-wrapper.sh` for secrets, then `ai-sync apply` (never hand-edit the generated `mcp.json` or settings.json `mcpServers`) | Copilot `/mcp reload`; Claude Code session restart |
| MCP server (project) | `<repo>/.github/mcp.json` (Copilot) or `<repo>/.mcp.json` (Claude Code) | Per-project |
| AI skill (global) | `~/.ai-config/skills/<name>/SKILL.md` (consumed by both Copilot and Claude Code) | Copilot `/skills reload`; Claude Code session restart |
| AI skill (project) | `<repo>/.copilot/skills/<name>/SKILL.md` (Copilot) or `<repo>/.claude/skills/<name>/SKILL.md` (Claude Code) | Auto-discovered |
| **New stack on hyperion** | `homelab/hyperion/<stack>/{compose.yml, secrets.env.sops}` + Komodo Stack resource in `homelab/komodo/` | Push → Komodo syncs |
| **New stack on solaris** | `homelab/solaris/<stack>/{compose.yml, secrets.env.sops}` + Komodo Stack resource | Push → Komodo syncs |
| **New ollama model** | `homelab/solaris/ollama/modelfiles/<name>.Modelfile` + `apply.sh` entry + `solaris/litellm/config.yaml` entry + `dotfiles/ollama/.config/opencode/opencode.jsonc` entry | Run apply.sh on solaris, restart litellm |
| **BYOK API key (Anthropic/OpenAI/Gemini/…)** | Edit `[secrets]` in solaris `periphery.config.toml` → kickstart Periphery → add model entry in `solaris/litellm/config.yaml` → `komodo.py deploy litellm` | Available at `cloud/<provider>-<short>-Nx` |
| BYOK key for local AI CLI tools (Copilot/Claude Code/etc.) | `~/.ai-config/secrets/<provider>.env` (per `dotfiles-helper`) — these are *client-side*, not the gateway | — |
| UniFi / network change | `network` repo at `~/code/network` (docs) + UniFi UI (live state via `unifi` MCP) | — |
| **Caddy reverse-proxy entry** | `homelab/hyperion/infra/Caddyfile` | Push → Caddy reloads (compose `exec caddy reload`) |
| **Image version bump (any image)** | Renovate PR; `control-plane`-labeled PRs for Komodo Core/Periphery, FerretDB, Postgres | Merge → Komodo redeploys |

## Hard rules (anti-rules)

1. **No `:latest` image tags, ever.** Including Komodo Core + Periphery — they're pinned to `vX.Y.Z@sha256:...` and bumped in lockstep in a `control-plane`-labeled PR with release-notes review.
2. **No plaintext secrets in git.** SOPS was dropped in Round 13 (tradeoff in `docs/security.md`). Today all secrets are **Komodo Periphery `[secrets]` blocks** in `periphery.config.toml` on each host — chmod 600, plaintext on disk, never in git. Keychain is the cross-machine backup. The canonical human-readable index is `komodo/resources/secrets-inventory.toml`; **always update it in the same PR** as the [[NAME]] reference, or the `validate-stacks` CI job fails. Prefer `scripts/periphery-secrets.py {pull,edit,push,check} <host>` over raw `ssh+vi` — it validates against the inventory before pushing, restarts Periphery cleanly, and mirrors to Keychain. The manual procedure stays documented in `docs/security.md` § "Editing a Komodo Periphery secret" as the fallback.
3. **No Watchtower on Komodo-managed stacks.** Renovate is the bump mechanism.
4. **Don't migrate Caddy or `monitor` without an escape hatch.** They're the front door and the observatory; they're the last two stacks migrated for a reason.
5. **No SSH-and-hand-edit on hyperion/solaris** for anything that should be reproducible. That's an emergency-only path; if you used it, file a follow-up to fold the change back into git.
6. **LiteLLM model namespaces are explicit:** `local/*-0x` (ollama, free) vs `cloud/<provider>-*-Nx` (BYOK, leaves tailnet, $/Mtok ≈ N; provider = `claude`, `gemini`, …). No silent auto-promotion — clients pick the namespace, or use `auto` for "default to local + escalate on overflow".
7. **Ollama on solaris listens on `0.0.0.0:11434`** (via `~/Library/LaunchAgents/com.user.ollama-env.plist`). LiteLLM reaches it via `host.docker.internal:11434`. Off-host clients use the MagicDNS name.
8. **LiteLLM config changes** flow through GitOps automatically: the `GitOps Auto-Deploy` Komodo procedure (every 5 min) runs `DeployStack` and — for litellm specifically — a follow-up `RestartStack` to force re-read of the bind-mounted `config.yaml` (litellm's in-process `model_group` cache otherwise serves stale data; `docker compose up -d` alone won't recreate the container when only the mounted file changed). The post-deploy restart hook lives in `komodo/resources/actions.toml` → `auto-deploy-pending-stacks`. Manual override (skip the wait): `python3 scripts/komodo.py deploy litellm && ssh solaris '/opt/homebrew/bin/docker restart litellm'`.
9. **Periphery secret rotation requires `komodo.py deploy <stack>`.** Editing `periphery.config.toml` alone won't recreate the container. The running container keeps its old env until you force-recreate. Round 25's Open WebUI miss is the cautionary tale.
10. **Periphery secrets must ALSO be declared in the stack `environment` block.** Komodo's "Write Environment File" step only materialises secrets that appear in the consuming stack's `environment = """..."""` block in `komodo/resources/*-stacks.toml`. Adding a key to `[secrets]` alone is silent — the container env stays empty. Round 28's missing `GEMINI_API_KEY` is the cautionary tale.
11. **LiteLLM model REMOVAL** also benefits from the auto-restart hook in rule #8 — the model_group cache is in-process so removed entries linger in `/v1/models` until the process restarts. Round 29 gemini-pro removal verified the underlying need; the auto-deploy hook now handles it.
12. **Cloud free-tier surprises silently fall back.** Mason's Google AI project has free-tier limit=0 on Gemini Pro 2.5; with fallbacks configured, the request silently serves Flash instead, skewing usage dashboards. When adding a cloud model to `litellm/config.yaml`, verify the provider's free-tier quota for that exact model id, and either (a) only expose models with real free quota, or (b) remove fallback chains for paid-only models so failures surface loudly. To diagnose: `curl … -H "x-litellm-disable-fallbacks: true"`.
13. **Ollama auto-thinking eats short replies** on any model whose Modelfile advertises the `thinking` capability (gemma4, qwen3-abliterated, granite, llama-vision, …). Set `reasoning_effort: none` in the LiteLLM model entry — LiteLLM's Ollama adapter maps that to Ollama's `think: false`. Leave reasoning on for qwen3-14b / deepseek-r1-14b and ensure clients send `max_tokens ≥ 800`. See `docs/models.md` § "Known model oddities". Gemini 2.5 has the same trap upstream: it spends ~20 tokens on internal reasoning before text — set `max_tokens ≥ ~50` even for one-word replies.
14. **Open WebUI task-model must be pinned away from slow reasoners.** OWUI fires parallel completions to the chat model for title gen, tag gen, autocomplete, follow-up suggestions, and search-query gen. With `OLLAMA_NUM_PARALLEL=1` on solaris (16GB), those serialize behind a slow local reasoner (qwen3-14b ~1-2 min) and the frontend renders `{}` once aiohttp gives up. Always set `TASK_MODEL=local/granite4.1-8b-0x` + `TASK_MODEL_EXTERNAL=cloud/claude-haiku-4.5-1x` + `AIOHTTP_CLIENT_TIMEOUT=300` in `solaris/openwebui/compose.yaml`. Round 30 was the cautionary tale: identical prompt via direct LiteLLM curl returned a clean 2-min answer; OWUI showed `{}` because its client gave up first.
15. **OWUI default tools must be per-model (Workspace Model `meta.toolIds`), NEVER user-level (`user.settings.ui.toolIds`).** User-level attaches tools to every chat regardless of model — models without a `tools` capability (dolphin3, deepseek-r1, llama3.2-vision per `ollama show`) immediately error `Ollama_chatException: does not support tools` (HTTP 500) the moment the user picks them. Bootstrap recipe + the `granite-tools` wrapper lives in `docs/openwebui.md § Default-enable tools`.
16. **Host-level repo sync uses a LaunchAgent in `solaris/<name>-sync/`** with the install.sh + plist + script trio (mirrors `komodo-monitor` and `notes-sync`). The script does `git fetch && git merge --ff-only` only — never push — and the plist runs it on `StartInterval=300`. `install.sh` is copied to the target host (not run from a checkout there; solaris doesn't keep a homelab clone) and uses `launchctl bootout → bootstrap → kickstart`. Use this pattern any time you need a file tree from GitHub to live on solaris/hyperion outside a Docker volume.
17. **MCP tools exposed to Open WebUI run as `mcpo`-wrapped docker stacks** on `127.0.0.1:81XX` (loopback only, never published to the tailnet). OWUI reaches them via `host.docker.internal:81XX`. Auth is a per-tool `*_MCP_KEY` periphery secret (Bearer). Registration in OWUI is **NOT declarative** — it lives in `webui.db` under `configs/tool_servers`. Codify as a `curl POST /api/v1/configs/tool_servers` recipe in `docs/openwebui.md` so the registration step is reproducible after a DB wipe. The wrapper pattern: `mcpo --host 0.0.0.0 --port 8000 --api-key "$KEY" -- <stdio-mcp-cmd>`. Image: `ghcr.io/open-webui/mcpo:main` (digest-pin when you stabilise). `mcpo` is still the right bridge in 2026 — OWUI's native MCP support is Streamable-HTTP only by design (multi-tenant), so stdio/SSE servers must go through `mcpo`.
18. **Chat plane is read-only; agent plane is `opencode` over Tailscale SSH.** OWUI (granite + tools, served on `chat.hyperionx.dev`) only gets read-class tools — filesystem `:ro`, `git log/diff/show`, fetch, search. *Never* expose shell, write tools, or git mutation behind the chat model. Reason: granite-4 8B + auto-read of `~/notes` (which syncs from git, i.e. anything ever pasted into a note becomes an injection vector) + ability to act = the lethal trifecta. Enforcement is the read-only mount, not MCP-server good behaviour. Anything that *mutates* state — `bash`, file edits, `git add/commit`, package installs — belongs in the agent plane: `opencode` running in a persistent `tmux` on solaris, reached from mobile via Tailscale SSH (Blink/Termius). `opencode` already ships native bash/read/write/edit/grep + per-tool approval gating; no need to bridge those through MCP into OWUI. The invariant: if a tool only reads, OWUI may have it; the moment it can mutate or shell out, it belongs behind `opencode`'s approval gate.
19. **Local Ollama chat models use `ollama_chat/`, NOT `ollama/`.** LiteLLM's own docs recommend `ollama_chat/` for chat models — it routes to Ollama's `/api/chat` and uses the native tool path. The `ollama/` prefix routes to `/api/generate`, and per LiteLLM docs falls back to **JSON-mode tool emulation** when native tool calling isn't wired up on that path — so the model is asked to emit a JSON blob as content, which then has to be re-parsed. (Ollama itself supports tools on both endpoints; this is a LiteLLM-adapter behaviour, not an Ollama endpoint limitation.) Embeddings (e.g. `nomic-embed-text`) keep `ollama/` — `ollama_chat/` is chat-only. **Local round-31 observation (2026-05-26):** under `ollama/`, non-streaming requests came back with structured `tool_calls` while streaming requests leaked the raw JSON as `content` deltas to opencode/OWUI/goose; switching to `ollama_chat/` fixed both. Treat that streaming-vs-non-streaming split as our empirical finding, not a general law — the real fault layer is LiteLLM's translation/parsing, which bisects with curl (Ollama direct → LiteLLM → client). If `ollama_chat/` ever starts returning empty/plain-text instead of `tool_calls`, that's a known LiteLLM parser regression — pin a known-good LiteLLM version rather than reverting the prefix.
20. **Verify `ollama show <model>` lists `tools` before marking `tools: true` in opencode/OWUI.** When a client sends tools to a model whose adapter doesn't actually drive native tool calling, LiteLLM falls back to the JSON-mode shim and the model emits a raw `{"name":...,"arguments":...}` blob as content — mimicking the rule-19 (`ollama_chat/`) symptom at a different layer. Verified locally on solaris on 2026-05-26 via `ollama show`: `deepseek-r1-14b`, `llama3.2-vision-11b`, and `dolphin3-8b` do not advertise `tools`; `qwen2.5-coder-7b` advertises `tools` but in our testing emits a raw JSON blob as content even when hit directly at `/api/chat`, so we treat it as `tools: false` for agent clients. Re-check with `ollama show` whenever a model build is rebuilt — capabilities can change between Ollama versions and Modelfile edits.
21. **Cross-surface guidance for shared resources (notes vault, etc.) must be mirrored across all agent surfaces.** Same Mason, same `~/notes` vault. The CLI surfaces (Copilot CLI and Claude Code) share **one** instruction file via `~/.ai-config/instructions.md` (symlinked as `~/.copilot/copilot-instructions.md` and `~/.claude/CLAUDE.md`), so editing the canonical file updates both. Other surfaces remain separate and must be updated in parallel: opencode (`~/dotfiles/ollama/.config/opencode/AGENTS.md`) and OWUI's `Granite (with tools)` workspace model (system prompt loaded from `homelab/solaris/openwebui/system-prompts/granite-tools.md` by the bootstrap recipe in `docs/openwebui.md`). When you add or change vault-related instructions (new airlock dir, new tool, new convention), update `~/.ai-config/instructions.md` (covers Copilot + Claude Code) plus opencode AGENTS.md plus the OWUI prompt — otherwise behaviour silently diverges. The OWUI prompt also has to be re-applied to webui.db via the bootstrap recipe (it's not declarative). Same pattern applies to any future shared-resource guidance (e.g. when we add a `tasks` MCP, a `calendar` MCP, etc.).
22. **Ollama on solaris reads models from `/Volumes/Helio/ollama/models`, not `~/.ollama/models`.** `OLLAMA_MODELS` is set by `~/dotfiles/ollama/launchagents/com.user.ollama-host.plist`, which uses `WatchPaths /Volumes/Helio` for self-healing on USB replug / wake-from-sleep. Symptom of this breaking: every `local/*-0x` model 500s with "model not found" even though `du -sh /Volumes/Helio/ollama/models` shows 52G of blobs. Recovery: `launchctl bootout gui/$(id -u)/com.user.ollama-host && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.user.ollama-host.plist && brew services restart ollama`.
23. **Secrets that get embedded in URLs (DATABASE_URL, AMQP/Redis URIs, …) must be URL-safe.** Generate with `openssl rand -hex 24`, never `-base64` — a base64 `/` or `+` inside `postgres://user:pass@host` makes the URL unparseable and the consumer crash-loops at boot (Lines round 1, 2026-06-11, was the cautionary tale). Also: postgres only honors `POSTGRES_PASSWORD` at first init — rotating the secret after the data dir exists requires `ALTER USER` or a fresh data dir.

## Adding a new docker stack

```
homelab/<host>/<stack>/
  compose.yaml         # Image pinned to <tag>@sha256:<digest>; references ${VAR:?err} for everything
  .env.example         # Documents required vars; never the real values
  <config files>       # Caddyfile fragments, prometheus rules, dashboards, etc.
```

Then add a Komodo Stack resource in `homelab/komodo/<host>.toml` pointing at the directory. Any secret the stack consumes goes in that host's Periphery `[secrets]` block and is referenced from compose via `${KEY:?}`. Push → Komodo syncs.

## Adding an ollama model

1. Add a Modelfile to `homelab/solaris/ollama/modelfiles/<short>.Modelfile`
   (bake `num_ctx`, sampler params, optional SYSTEM prompt per the author's recipe).
2. Add the rebuild to `apply.sh`.
3. Add a matching `local/<short>-0x` entry to `solaris/litellm/config.yaml`
   with `reasoning_effort: none` unless it's a true reasoning model.
4. Push, then on solaris run `~/code/homelab/solaris/ollama/modelfiles/apply.sh`
   to rebuild + tag, and `docker restart litellm` to load the config.
5. Add to `dotfiles/ollama/.config/opencode/opencode.jsonc` with sampler overrides.

See `solaris/ollama/modelfiles/README.md` for conventions.

## Adding a BYOK provider key (Anthropic, OpenAI, Gemini, …)

1. SSH to solaris, edit `/opt/homebrew/etc/komodo/periphery.config.toml` `[secrets]`:
   ```toml
   [secrets]
   GEMINI_API_KEY = "AIza..."
   ```
2. `ssh solaris 'launchctl kickstart -k "gui/$(id -u)/sh.komodo.periphery"'`
3. Add a model entry to `solaris/litellm/config.yaml` referencing `os.environ/GEMINI_API_KEY`.
4. Push, then `python3 scripts/komodo.py deploy litellm` (this force-recreates — required for env-only changes).
5. Verify: `curl -sS https://llm.hyperionx.dev/v1/models -H "Authorization: Bearer $MASTER" | jq '.data[].id' | grep cloud/`

## Escape hatches (use only when Komodo is the problem)

- **hyperion direct:** `ssh hyperion '/share/CACHEDEV3_DATA/.qpkg/container-station/bin/docker compose -f /share/containers/stacks/<stack>/compose.yaml ...'`
- **solaris direct:** `ssh solaris 'bash -lc "docker compose -f ~/komodo/stacks/litellm/solaris/<stack>/compose.yaml ..."'`
- **Direct ollama bypass:** `OLLAMA_HOST=http://solaris:11434` (kept in `~/.ai-config/secrets/local.env` as an escape hatch from LiteLLM)

If you used an escape hatch, **fold the change back into git within the same day** or it stops being a homelab and starts being a pet.

## Related skills

- `dotfiles-helper` — for Mac client config changes (alias, env var, MCP, brew, LaunchAgent)

(No network skill exists; UniFi / Cloudflare / NextDNS / VLAN changes are docs in `masonmem/network` at `~/code/network`, with live state via the `unifi` MCP.)
