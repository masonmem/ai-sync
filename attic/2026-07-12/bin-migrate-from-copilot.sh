#!/usr/bin/env bash
# migrate-from-copilot.sh — one-shot migration from the old ~/.copilot/
# physical clone (masonmem/copilot) to the new shared ~/.ai-config/
# layout (masonmem/ai-config) with ~/.copilot/ as a symlinked surface.
#
# Run this on a machine that still has ~/.copilot/.git/ (i.e. it hasn't
# yet been migrated). Idempotent in the sense that it detects the
# already-migrated state and exits cleanly without touching anything.
#
# Usage:
#   bash ~/.ai-config/bin/migrate-from-copilot.sh          # do it
#   bash ~/.ai-config/bin/migrate-from-copilot.sh --dry    # print only
#
# After running, re-launch any open Copilot CLI / Claude Code sessions
# so they pick up the new symlinked files.

set -euo pipefail

DRY=0
if [[ "${1:-}" == "--dry" ]]; then DRY=1; fi

DOT_COPILOT="$HOME/.copilot"
AI_CONFIG="$HOME/.ai-config"
REMOTE_NEW="git@github.com:masonmem/ai-config.git"

log()  { printf '\033[36m[migrate]\033[0m %s\n' "$*"; }
do_()  { if (( DRY )); then printf '  WOULD: %s\n' "$*"; else eval "$*"; fi; }

# ---------------------------------------------------------------------
# Detect already-migrated state and bail.
# ---------------------------------------------------------------------
if [[ -L "$DOT_COPILOT/copilot-instructions.md" ]]; then
  log "~/.copilot/copilot-instructions.md is already a symlink — nothing to do."
  ls -la "$DOT_COPILOT/copilot-instructions.md" 2>/dev/null || true
  exit 0
fi

if [[ ! -d "$DOT_COPILOT/.git" ]]; then
  log "~/.copilot/.git not found. Either you've never set up Copilot here,"
  log "or you've already migrated. Nothing to do."
  exit 0
fi

# ---------------------------------------------------------------------
# Sanity checks before we move anything.
# ---------------------------------------------------------------------
log "preflight checks"
cd "$DOT_COPILOT"
if ! git diff --quiet HEAD || ! git diff --quiet --cached; then
  log "ERROR: ~/.copilot has uncommitted changes. Commit or stash, then re-run:"
  git status --short
  exit 1
fi

if [[ -e "$AI_CONFIG" && -n "$(ls -A "$AI_CONFIG" 2>/dev/null)" ]]; then
  log "ERROR: $AI_CONFIG already exists and is non-empty. Aborting to"
  log "       avoid clobbering. If this is leftover from a partial migration,"
  log "       inspect and remove it manually, then re-run."
  exit 1
fi

# ---------------------------------------------------------------------
# 1. Update remote to the new repo URL (GitHub redirects either way,
#    but explicit is better) and pull so we land on the rename commit.
# ---------------------------------------------------------------------
log "1. updating remote → $REMOTE_NEW"
do_ "git -C \"$DOT_COPILOT\" remote set-url origin \"$REMOTE_NEW\""
do_ "git -C \"$DOT_COPILOT\" fetch --quiet origin"
do_ "git -C \"$DOT_COPILOT\" pull --ff-only --quiet origin main || git -C \"$DOT_COPILOT\" pull --ff-only --quiet"

# ---------------------------------------------------------------------
# 2. Move tracked content (and .git) to ~/.ai-config/, preserving the
#    new layout (settings.json → copilot/settings.json, etc.).
# ---------------------------------------------------------------------
log "2. relocating tracked content to $AI_CONFIG"
do_ "mkdir -p \"$AI_CONFIG\""

# After the pull, the on-disk layout matches the new repo, so:
#   .git, .gitignore, README.md, instructions.md, mcp.json,
#   skills/, bin/, copilot/, claude/ → ai-config
#   secrets/ (gitignored but present) → ai-config
# Things NOT to move (runtime state): config.json, logs/, etc.
for entry in .git .gitignore README.md instructions.md mcp.json skills bin copilot claude secrets; do
  if [[ -e "$DOT_COPILOT/$entry" ]]; then
    do_ "mv \"$DOT_COPILOT/$entry\" \"$AI_CONFIG/$entry\""
  fi
done

# ---------------------------------------------------------------------
# 3. Re-create the Copilot CLI symlink surface in ~/.copilot/.
# ---------------------------------------------------------------------
log "3. re-creating ~/.copilot symlinks"
do_ "ln -sfn \"$AI_CONFIG/instructions.md\"       \"$DOT_COPILOT/copilot-instructions.md\""
do_ "ln -sfn \"$AI_CONFIG/skills\"                \"$DOT_COPILOT/skills\""
do_ "ln -sfn \"$AI_CONFIG/bin\"                   \"$DOT_COPILOT/bin\""
do_ "ln -sfn \"$AI_CONFIG/mcp.json\"              \"$DOT_COPILOT/mcp-config.json\""
do_ "ln -sfn \"$AI_CONFIG/secrets\"               \"$DOT_COPILOT/secrets\""
do_ "ln -sfn \"$AI_CONFIG/copilot/settings.json\" \"$DOT_COPILOT/settings.json\""

log "done."
log ""
log "If Claude Code is installed on this host, also run:"
log "  bash $AI_CONFIG/bin/bootstrap-claude.sh"
