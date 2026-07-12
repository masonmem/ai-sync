# Skills pass 2026-07-12 — consolidation record

Branch: `chore/skills-pass-2026-07` (ai-sync + homelab).

## What merged into what

- **homelab-helper**: original preserved here as
  `homelab-helper-SKILL-pre-pass.md`. Cloud/BYOK workflow and rules 6/12
  removed — contradicted `homelab/docs/llm-platform.md` § "Cloud providers
  — not used" (local-only since 2026-06-11). Model-behaviour rules
  (13, 19, 20, 22) deferred to `docs/llm-platform.md` § "Rules learned the
  hard way"; OWUI rules (14, 15, 17) deferred to `docs/openwebui.md`;
  Komodo secret mechanics (parts of 2, 9, 10) deferred to the in-repo
  `komodo-ops` skill. Skill went 114 → 92 lines and is now the
  conventions/router layer.
- **dotfiles-helper**: LiteLLM auth chain moved to
  `skills/personal/dotfiles-helper/references/litellm-auth.md` (heavy
  reference, niche trigger).
- **context7-mcp**: body condensed; the Context7 MCP server ships server
  instructions covering the same guidance. Skill kept only because
  Copilot CLI does not surface MCP server instructions. If that changes,
  demote this skill.

## Stale facts fixed during the pass

- `~/.ai-config` symlink no longer exists (where-things-live).
- `~/code/ai-sync/instructions.md` → canonical file is `agents/general.md`.
- `docs/models.md` → renamed to `docs/llm-platform.md`.
- Skills live in `skills/personal/<name>/`, not `skills/<name>/`.
- OWUI `TASK_MODEL_EXTERNAL` is `local/granite4.1-8b-0x`, not a cloud model.
- Ollama on solaris is a standalone install (brew formula broken per
  `docs/disaster-recovery.md`), so `brew services restart ollama` is dead advice.
