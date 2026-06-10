#!/usr/bin/env bash
# bootstrap-claude.sh — minimal bootstrap of ~/.claude/ on a fresh machine.
#
# This script is the absolute-minimum fallback for hosts that don't yet have
# Python + pipx + pytest set up. For everyday use, prefer the full CLI:
#
#   ~/.ai-config/bin/ai-sync apply
#
# which is reproducibly tested, generates Copilot mcp.json from mcp/servers.toml,
# registers MCP servers in Claude Code, and exits non-zero on drift.
#
# What this script does (subset of ai-sync apply):
#   * Backs up any pre-existing physical ~/.claude/settings.json once.
#   * Symlinks the per-tool entry points.
#   * Delegates to ai-sync if Python 3.11+ is present (gets the rest of apply).
#
# Idempotent. Safe to run repeatedly.

set -euo pipefail

AI_CONFIG="${AI_CONFIG:-$HOME/.ai-config}"
DOT_CLAUDE="$HOME/.claude"

log() { printf '\033[36m[bootstrap-claude]\033[0m %s\n' "$*"; }

if [[ ! -d "$AI_CONFIG" ]]; then
  log "ERROR: $AI_CONFIG does not exist. Clone it first:"
  log "  git clone git@github.com:masonmem/ai-config.git $AI_CONFIG"
  exit 1
fi

mkdir -p "$DOT_CLAUDE"

# Back up any pre-existing physical settings.json the first time we run.
# On later runs (backup already exists) we do NOT delete the live file — it
# may hold runtime writebacks, or be a render-mode file (hosts/ overlay)
# that ai-sync manages. Show what diverged and point at the promote flow.
settings="$DOT_CLAUDE/settings.json"
keep_settings=0
if [[ -f "$settings" && ! -L "$settings" ]]; then
  backup="$settings.pre-aiconfig"
  if [[ ! -e "$backup" ]]; then
    log "backing up existing $settings → $backup"
    mv "$settings" "$backup"
  else
    keep_settings=1
    log "backup already exists at $backup — leaving the live $settings in place."
    log "diff vs tracked base ($AI_CONFIG/claude/settings.json):"
    diff -u "$AI_CONFIG/claude/settings.json" "$settings" || true
    log "reconcile with:  ai-sync diff claude   then"
    log "  ai-sync promote --to overlay claude   # keep per-host, OR"
    log "  ai-sync promote --to base claude      # share across hosts"
  fi
fi

# Prefer the full CLI when available — it covers MCP registration + Copilot
# mcp.json generation that this minimal script doesn't.
if command -v python3 >/dev/null 2>&1 \
   && python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null \
   && [[ -x "$AI_CONFIG/bin/ai-sync" ]]; then
  log "delegating to ai-sync apply"
  exec "$AI_CONFIG/bin/ai-sync" apply
fi

log "Python 3.11+ or ai-sync not available — doing minimal symlinks only."
log "Install Python ≥ 3.11 (Brewfile has python@3.14) and rerun to get full apply."

relink() {
  local target="$1" linkname="$2"
  if [[ ! -e "$target" ]]; then
    log "skipping $linkname → $target (target missing)"
    return
  fi
  ln -sfn "$target" "$linkname"
}

relink "$AI_CONFIG/instructions.md"      "$DOT_CLAUDE/CLAUDE.md"
relink "$AI_CONFIG/skills"               "$DOT_CLAUDE/skills"
relink "$AI_CONFIG/bin"                  "$DOT_CLAUDE/bin"
relink "$AI_CONFIG/secrets"              "$DOT_CLAUDE/secrets"
if [[ "$keep_settings" == 1 ]]; then
  log "skipping settings.json symlink (live physical file kept — reconcile via ai-sync, see above)"
else
  relink "$AI_CONFIG/claude/settings.json" "$DOT_CLAUDE/settings.json"
fi

log "symlinks done. MCP servers not registered (need ai-sync). Restart Claude Code."
