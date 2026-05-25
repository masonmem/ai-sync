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
| **New ollama model** | `homelab/solaris/ollama/models.txt` (launchd `ollama-sync.sh` reconciles) | Next sync tick |
| **BYOK API key (Anthropic/OpenAI/etc.)** | `homelab/solaris/litellm/secrets.env.sops` via `sops edit` | LiteLLM restart on Komodo redeploy |
| BYOK key for local Copilot CLI tools | `~/.copilot/secrets/<provider>.env` (per `dotfiles-helper`) — these are *client-side*, not the gateway | — |
| UniFi / network change | `home-network` (docs) + UniFi UI (live state via `unifi` MCP) | — |
| **Caddy reverse-proxy entry** | `homelab/hyperion/infra/Caddyfile` | Push → Caddy reloads (compose `exec caddy reload`) |
| **Image version bump (any image)** | Renovate PR; `control-plane`-labeled PRs for Komodo Core/Periphery, FerretDB, Postgres | Merge → Komodo redeploys |

## Hard rules (anti-rules)

1. **No `:latest` image tags, ever.** Including Komodo Core + Periphery — they're pinned to `vX.Y.Z@sha256:...` and bumped in lockstep in a `control-plane`-labeled PR with release-notes review.
2. **No plaintext secrets in git.** Two mechanisms:
   - **Hyperion:** Komodo-native Periphery secrets (defined in the Periphery config file on the host, never in git). Per-host blast radius, no network exposure, no API exposure.
   - **Solaris + anything portable:** SOPS + age. Decrypt target is **`secrets.env`** (NOT `.env` — that name is owned by Komodo's `[[VARIABLE]]` interpolation). Both files pass to compose via separate `--env-file` flags.
3. **Two age recipients on every `.sops.yaml` creation rule:** the host key + the admin key. Admin key (offline / 1Password) lets you `sops edit` from a laptop without ever pulling a host's private key.
4. **No Watchtower on Komodo-managed stacks.** Renovate is the bump mechanism.
5. **Don't migrate Caddy or `monitor` without an escape hatch.** They're the front door and the observatory; they're the last two stacks migrated for a reason.
6. **No SSH-and-hand-edit on hyperion/solaris** for anything that should be reproducible. That's an emergency-only path; if you used it, file a follow-up to fold the change back into git.
7. **LiteLLM model namespaces are explicit:** `local/*` (ollama, private) vs `cloud/*` (BYOK, leaves tailnet). **No silent auto-promotion.** The `--escalate` flag on `copilotp` is the explicit, per-invocation, stderr-warned middle ground.
8. **Ollama on solaris listens on `0.0.0.0:11434`** (via `~/Library/LaunchAgents/com.user.ollama-env.plist` setting `OLLAMA_HOST`). LiteLLM reaches it via `host.docker.internal:11434` (loopback). Off-host clients use the MagicDNS name, not a hardcoded tailnet IP.

## Adding a new docker stack

```
homelab/<host>/<stack>/
  compose.yml          # Image pinned to <tag>@sha256:<digest>; references ${VAR:?err} for everything
  .env.example         # Documents required vars; never the real .env
  secrets.env.sops     # SOPS-encrypted (solaris only); for hyperion, use Komodo-native secrets
  <config files>       # Caddyfile fragments, prometheus rules, dashboards, etc.
```

Then add a Komodo Stack resource in `homelab/komodo/<host>.toml` pointing at the directory. On solaris stacks add `additional_env_files = ["secrets.env"]` and a `pre_deploy` that `sops -d`s into it. Push → Komodo syncs.

See the in-repo `komodo-ops` skill for the gory details (env-file collision, GHCR pull auth, FerretDB backup, outbound mode).

## Adding an ollama model

Append the model name to `homelab/solaris/ollama/models.txt`. Commit. The launchd `ollama-sync.sh` job on solaris will pull it on its next tick (or run `ollama-sync now` to force).

## Adding a BYOK provider key (Anthropic, OpenAI, etc.)

```
cd ~/code/homelab
sops solaris/litellm/secrets.env.sops
# Add: ANTHROPIC_API_KEY=sk-ant-...
git commit -am "feat(litellm): add anthropic byok key"
git push
```

Komodo Periphery on solaris will pull, decrypt to `secrets.env`, and restart LiteLLM. The model is reachable via the LiteLLM virtual model name (e.g. `cloud/sonnet`) once configured in `litellm-config.yaml`.

## Escape hatches (use only when Komodo is the problem)

- **hyperion direct:** `ssh hyperion 'cd /share/containers/stacks/<stack> && docker compose ...'`
- **solaris direct:** `ssh solaris 'cd ~/stacks/<stack> && docker compose ...'`
- **Direct ollama bypass:** `OLLAMA_HOST=http://solaris.tailnet:11434` (kept in `~/.copilot/secrets/local.env` as an escape hatch from LiteLLM)

If you used an escape hatch, **fold the change back into git within the same day** or it stops being a homelab and starts being a pet.

## Related skills

- `dotfiles-helper` — for Mac client config changes (alias, env var, MCP, brew, LaunchAgent)
- `home-network-helper` — for UniFi / Cloudflare / NextDNS / VLAN changes
- (in-repo) `komodo-ops` — for Komodo resource format, SOPS recipe, rollback, age key rotation
