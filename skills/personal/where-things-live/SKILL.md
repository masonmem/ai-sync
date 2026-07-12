---
name: where-things-live
description: "Use when deciding which repo a change belongs in, or locating the source of truth for machine env, AI config, homelab services, or network docs — e.g. \"where does X live\", \"which repo should this go in\". Not for making the change itself: load dotfiles-helper or homelab-helper for that."
---

# Where things live

- `~/dotfiles` (`masonmem/dotfiles`) — machine env (Brewfile, zsh, editors), GNU stow.
- `~/code/ai-sync` (`masonmem/ai-sync`) — shared AI brain (global
  instructions in `agents/general.md`, skills in `skills/personal/`, MCP
  wrappers, per-tool settings). `~/.claude/`, `~/.copilot/`, and
  `~/.codex/` are thin tool-shaped surfaces whose tracked entries link
  back into here.
- `~/code/homelab` (`masonmem/homelab`) — GitOps source of truth for hyperion (QNAP) + solaris (Mac Mini) docker stacks; orchestrated by Komodo.
- `~/code/network` (`masonmem/network`) — network design + UniFi/Cloudflare/NextDNS docs only (NOT stacks; those live in `homelab`).
- For dotfiles/ai-sync changes, the `dotfiles-helper` skill has the conventions. For homelab/stack/ollama changes, the `homelab-helper` skill does. Prefer loading them over guessing.
