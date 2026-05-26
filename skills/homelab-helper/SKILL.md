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
| `masonmem/copilot` | AI brain — skills, agents, MCP, instructions | Service deploys |
| **`masonmem/homelab`** | Compose stacks + non-secret config for hyperion + solaris, Komodo resources, age public keys | Mac client config, network design docs |
| `masonmem/home-network` | Network design, UniFi/Cloudflare/NextDNS docs | Compose stacks (those moved to `homelab` during the migration) |

If the change is "thing X is running on hyperion or solaris," it's in `homelab`. If it's "this Mac has tool Y," it's `dotfiles`.

## Where things live (the source-of-truth table)

| Want to add… | Edit | Result |
|---|---|---|
| Brew package (Mac) | `dotfiles/Brewfile` → `brew bundle` | Available after pull |
| Shell alias / env var | `dotfiles/zsh/.config/zsh/20-aliases.zsh` | `exec zsh` |
| MCP server (user-global) | `~/.copilot/mcp-config.json` (+ wrapper for secrets) | `/mcp reload` |
| MCP server (project) | `<repo>/.github/mcp.json` | Per-project |
| Copilot skill (global) | `~/.copilot/skills/<name>/SKILL.md` | `/skills reload` |
| Copilot skill (project) | `<repo>/.copilot/skills/<name>/SKILL.md` | Auto-discovered |
| **New stack on hyperion** | `homelab/hyperion/<stack>/{compose.yml, secrets.env.sops}` + Komodo Stack resource in `homelab/komodo/` | Push → Komodo syncs |
| **New stack on solaris** | `homelab/solaris/<stack>/{compose.yml, secrets.env.sops}` + Komodo Stack resource | Push → Komodo syncs |
| **New ollama model** | `homelab/solaris/ollama/modelfiles/<name>.Modelfile` + `apply.sh` entry + `solaris/litellm/config.yaml` entry + `dotfiles/ollama/.config/opencode/opencode.jsonc` entry | Run apply.sh on solaris, restart litellm |
| **BYOK API key (Anthropic/OpenAI/Gemini/…)** | Edit `[secrets]` in solaris `periphery.config.toml` → kickstart Periphery → add model entry in `solaris/litellm/config.yaml` → `komodo.py deploy litellm` | Available at `cloud/<provider>-<short>-Nx` |
| BYOK key for local Copilot CLI tools | `~/.copilot/secrets/<provider>.env` (per `dotfiles-helper`) — these are *client-side*, not the gateway | — |
| UniFi / network change | `home-network` (docs) + UniFi UI (live state via `unifi` MCP) | — |
| **Caddy reverse-proxy entry** | `homelab/hyperion/infra/Caddyfile` | Push → Caddy reloads (compose `exec caddy reload`) |
| **Image version bump (any image)** | Renovate PR; `control-plane`-labeled PRs for Komodo Core/Periphery, FerretDB, Postgres | Merge → Komodo redeploys |

## Hard rules (anti-rules)

1. **No `:latest` image tags, ever.** Including Komodo Core + Periphery — they're pinned to `vX.Y.Z@sha256:...` and bumped in lockstep in a `control-plane`-labeled PR with release-notes review.
2. **No plaintext secrets in git.** SOPS was dropped in Round 13 (tradeoff in `docs/security.md`). Today all secrets are **Komodo Periphery `[secrets]` blocks** in `periphery.config.toml` on each host — chmod 600, plaintext on disk, never in git. Keychain is the cross-machine backup. See `docs/security.md` § "Editing a Komodo Periphery secret" for the gotcha (Komodo v2.2.0 has no Secrets UI).
3. **No Watchtower on Komodo-managed stacks.** Renovate is the bump mechanism.
4. **Don't migrate Caddy or `monitor` without an escape hatch.** They're the front door and the observatory; they're the last two stacks migrated for a reason.
5. **No SSH-and-hand-edit on hyperion/solaris** for anything that should be reproducible. That's an emergency-only path; if you used it, file a follow-up to fold the change back into git.
6. **LiteLLM model namespaces are explicit:** `local/*-0x` (ollama, free) vs `cloud/<provider>-*-Nx` (BYOK, leaves tailnet, $/Mtok ≈ N; provider = `claude`, `gemini`, …). No silent auto-promotion — clients pick the namespace, or use `auto` for "default to local + escalate on overflow".
7. **Ollama on solaris listens on `0.0.0.0:11434`** (via `~/Library/LaunchAgents/com.user.ollama-env.plist`). LiteLLM reaches it via `host.docker.internal:11434`. Off-host clients use the MagicDNS name.
8. **LiteLLM config changes require a full `docker restart litellm`** — the in-process reloader silently ignores new fields (logs `'str' object has no attribute 'get'`). Komodo redeploy via `scripts/komodo.py deploy litellm` works; a bare `compose up` does not if nothing else changed.
9. **Periphery secret rotation requires `komodo.py deploy <stack>`.** Editing `periphery.config.toml` alone won't recreate the container. The running container keeps its old env until you force-recreate. Round 25's Open WebUI miss is the cautionary tale.
10. **Periphery secrets must ALSO be declared in the stack `environment` block.** Komodo's "Write Environment File" step only materialises secrets that appear in the consuming stack's `environment = """..."""` block in `komodo/resources/*-stacks.toml`. Adding a key to `[secrets]` alone is silent — the container env stays empty. Round 28's missing `GEMINI_API_KEY` is the cautionary tale.
11. **LiteLLM model REMOVAL requires `docker restart litellm`** (not just `compose up`). The model_group cache is in-process; removed entries linger in `/v1/models` until the process restarts. Round 29 gemini-pro removal verified this.
12. **Cloud free-tier surprises silently fall back.** Mason's Google AI project has free-tier limit=0 on Gemini Pro 2.5; with fallbacks configured, the request silently serves Flash instead, skewing usage dashboards. When adding a cloud model to `litellm/config.yaml`, verify the provider's free-tier quota for that exact model id, and either (a) only expose models with real free quota, or (b) remove fallback chains for paid-only models so failures surface loudly. To diagnose: `curl … -H "x-litellm-disable-fallbacks: true"`.
13. **Ollama auto-thinking eats short replies** on any model whose Modelfile advertises the `thinking` capability (gemma4, qwen3-abliterated, granite, llama-vision, …). Set `reasoning_effort: none` in the LiteLLM model entry — LiteLLM's Ollama adapter maps that to Ollama's `think: false`. Leave reasoning on for qwen3-14b / deepseek-r1-14b and ensure clients send `max_tokens ≥ 800`. See `docs/models.md` § "Known model oddities". Gemini 2.5 has the same trap upstream: it spends ~20 tokens on internal reasoning before text — set `max_tokens ≥ ~50` even for one-word replies.
14. **Open WebUI task-model must be pinned away from slow reasoners.** OWUI fires parallel completions to the chat model for title gen, tag gen, autocomplete, follow-up suggestions, and search-query gen. With `OLLAMA_NUM_PARALLEL=1` on solaris (16GB), those serialize behind a slow local reasoner (qwen3-14b ~1-2 min) and the frontend renders `{}` once aiohttp gives up. Always set `TASK_MODEL=local/granite4.1-8b-0x` + `TASK_MODEL_EXTERNAL=cloud/claude-haiku-4.5-1x` + `AIOHTTP_CLIENT_TIMEOUT=300` in `solaris/openwebui/compose.yaml`. Round 30 was the cautionary tale: identical prompt via direct LiteLLM curl returned a clean 2-min answer; OWUI showed `{}` because its client gave up first.
15. **Local Ollama chat models use `ollama_chat/`, NOT `ollama/`.** The `ollama/` prefix routes to `/api/generate` which has no native tool support — LiteLLM embeds the schema as prompt text and the model emits raw JSON. Non-streaming curl re-parses it back into structured `tool_calls` so tests look fine, but streaming clients (opencode, OWUI, goose, aider) see `{"name":"foo","arguments":{...}}` printed into chat and the tool never executes. `ollama_chat/` → `/api/chat` with native streaming `tool_calls`. Embeddings (e.g. `nomic-embed-text`) keep `ollama/`. Round 31 cautionary tale; verified via streaming bisect.
16. **Verify `ollama show <model>` lists `tools` before marking `tools: true` in opencode/OWUI.** dolphin3, deepseek-r1, llama-vision lack the capability — sending tools to them embeds the schema in the prompt and they emit raw JSON, mimicking the rule-15 bug at a different layer. qwen2.5-coder advertises `tools` but its template is broken (emits raw JSON even at `/api/chat`); treat as `tools: false` for agent clients.

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
- **Direct ollama bypass:** `OLLAMA_HOST=http://solaris:11434` (kept in `~/.copilot/secrets/local.env` as an escape hatch from LiteLLM)

If you used an escape hatch, **fold the change back into git within the same day** or it stops being a homelab and starts being a pet.

## Related skills

- `dotfiles-helper` — for Mac client config changes (alias, env var, MCP, brew, LaunchAgent)
- `home-network-helper` — for UniFi / Cloudflare / NextDNS / VLAN changes
