---
name: where-things-live
description: "Map of @masonmem's repos and config surfaces. Use when deciding which repo a change belongs in, locating the source of truth for machine env / AI config / homelab / network, or when the user asks where something lives."
---

# Where things live

- `~/dotfiles` — machine env (Brewfile, zsh, editors), GNU stow.
- `~/code/ai-sync` (`masonmem/ai-config`) — shared AI brain (global
  instructions in `agents/general.md`, skills, MCP wrappers, per-tool
  settings). `~/.ai-config` is a compatibility symlink to it. `~/.claude/`,
  `~/.copilot/`, and `~/.codex/` are thin tool-shaped surfaces whose
  tracked entries link back into here.
- `~/code/homelab` (`masonmem/homelab`) — GitOps source of truth for hyperion (QNAP) + solaris (Mac Mini) docker stacks; orchestrated by Komodo.
- `~/code/network` (`masonmem/network`) — network design + UniFi/Cloudflare/NextDNS docs only (NOT stacks; those live in `homelab`).
- For dotfiles/ai-config changes, the `dotfiles-helper` skill has the conventions. For homelab/stack/ollama/BYOK changes, the `homelab-helper` skill does. Prefer loading them over guessing.
