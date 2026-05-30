#!/usr/bin/env bash
# bootstrap-claude.sh — set up ~/.claude/ as a thin symlinked surface
# over the canonical ~/.ai-config/ AI brain.
#
# Idempotent: safe to run before Claude Code is installed, after it's
# installed, or repeatedly. Existing physical ~/.claude/settings.json
# is backed up before being replaced with a symlink.
#
# Usage:
#   bash ~/.ai-config/bin/bootstrap-claude.sh

set -euo pipefail

AI_CONFIG="$HOME/.ai-config"
DOT_CLAUDE="$HOME/.claude"

log() { printf '\033[36m[bootstrap-claude]\033[0m %s\n' "$*"; }

if [[ ! -d "$AI_CONFIG" ]]; then
  log "ERROR: $AI_CONFIG does not exist. Clone it first:"
  log "  git clone git@github.com:masonmem/ai-config.git $AI_CONFIG"
  exit 1
fi

mkdir -p "$DOT_CLAUDE"

# Back up any pre-existing physical settings.json the first time we run.
settings="$DOT_CLAUDE/settings.json"
if [[ -f "$settings" && ! -L "$settings" ]]; then
  backup="$settings.pre-aiconfig"
  if [[ ! -e "$backup" ]]; then
    log "backing up existing $settings → $backup"
    mv "$settings" "$backup"
  else
    log "old settings backup already exists at $backup; removing physical $settings"
    rm "$settings"
  fi
fi

relink() {
  local target="$1" linkname="$2"
  if [[ ! -e "$target" ]]; then
    log "skipping $linkname → $target (target missing)"
    return
  fi
  ln -sfn "$target" "$linkname"
}

log "linking ~/.claude entry points"
relink "$AI_CONFIG/instructions.md"      "$DOT_CLAUDE/CLAUDE.md"
relink "$AI_CONFIG/skills"               "$DOT_CLAUDE/skills"
relink "$AI_CONFIG/bin"                  "$DOT_CLAUDE/bin"
relink "$AI_CONFIG/secrets"              "$DOT_CLAUDE/secrets"
relink "$AI_CONFIG/claude/settings.json" "$DOT_CLAUDE/settings.json"

log "done. Restart Claude Code to load the new instructions / skills / MCP servers."
