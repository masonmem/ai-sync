# LiteLLM auth chain (opencode / aider / goose → gateway)

Two layers, often confused:

1. **Backend keys** (LiteLLM → upstream providers) live in solaris
   `/opt/homebrew/etc/komodo/periphery.config.toml` `[secrets]` and are
   materialised into the litellm container env by Komodo. This is the
   `homelab-helper` skill's territory. **Not** what client 401s are
   about. (Note: the platform is local-only since 2026-06-11 — see
   `homelab/docs/llm-platform.md` § "Cloud providers — not used".)
2. **Frontend keys** (this Mac → LiteLLM gateway) are per-tool LiteLLM
   *virtual* keys stored in `~/code/ai-sync/secrets/litellm-<tool>.txt`
   (chmod 600, gitignored; mirrored to macOS Keychain via
   `litellm-keys`). Consumption pattern by tool:

   | Tool | How it reads the key | Why |
   |---|---|---|
   | `opencode` | `apiKey: "{file:~/code/ai-sync/secrets/litellm-opencode.txt}"` in `opencode.jsonc` | opencode's `{env:VAR}` returns empty-string when the var is missing in the launching env (silent 401). `{file:}` reads at config-load time with no env dependency. |
   | `aider`    | `~/dotfiles/ollama/.config/zsh/60-aider-wrapper.zsh` injects `OPENAI_API_KEY=$AIDER_LITELLM_KEY` per call | aider's YAML config doesn't expand env vars; needs them on the process. |
   | `goose`    | `~/dotfiles/ollama/.config/zsh/61-goose-wrapper.zsh` injects `OPENAI_API_KEY=$GOOSE_LITELLM_KEY` per call | same as aider — config is static. |

   The `<TOOL>_LITELLM_KEY` env vars themselves come from
   `16-llm-gateway.zsh` (file first, Keychain fallback). For opencode
   we still load it for parity, but the live source of truth is the
   file — opencode reads disk directly so launchctl/IDE-spawned
   shells/etc. all work.

**Rule:** never store a LiteLLM virtual key directly in a tool's
config file (it's a dotfile in git). Always either (a) `{file:}` from
`~/code/ai-sync/secrets/`, or (b) a per-tool wrapper that injects
`OPENAI_API_KEY` for that one invocation. Don't export
`OPENAI_API_KEY` globally — opencode auto-detects it and pollutes the
model picker with the entire built-in OpenAI catalog.

## Smoke test (after any opencode/aider/goose version bump)

Run from a stripped env to confirm secret resolution hasn't regressed:

```sh
env -i HOME="$HOME" PATH="/opt/homebrew/bin:/usr/bin:/bin" \
  opencode run --model litellm/auto "reply with the word pong"
```

If this 401s, the tool is depending on a shell-exported env var the
launching context doesn't provide.
