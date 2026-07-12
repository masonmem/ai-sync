#!/usr/bin/env bash
# Claude Code statusLine — mirrors the p10k lean aesthetic.
#
#   left:  model | cwd (with ~ abbreviation) | git branch
#   right: kube context | context window % remaining
#
# Referenced from claude/settings.json as:
#   "statusLine": { "type": "command", "command": "bash ~/code/ai-sync/bin/statusline.sh" }
#
# Claude Code pipes a JSON status payload on stdin every render. Schema docs:
# https://docs.claude.com/en/docs/claude-code/settings#statusline

set -u

input=$(cat)

if ! command -v jq >/dev/null 2>&1; then
  printf 'jq missing — install via Brewfile\n'
  exit 0
fi

model=$(printf '%s' "$input"      | jq -r '.model.display_name // "Claude"')
cwd_raw=$(printf '%s' "$input"    | jq -r '.workspace.current_dir // .cwd // "."')
remaining=$(printf '%s' "$input"  | jq -r '.context_window.remaining_percentage // empty')

home="$HOME"
cwd="${cwd_raw/#$home/~}"

branch=$(git -C "$cwd_raw" --no-optional-locks branch --show-current 2>/dev/null)

kube=""
if command -v kubectl >/dev/null 2>&1; then
  kube=$(kubectl config current-context 2>/dev/null || true)
fi

cyan='\033[36m'; blue='\033[34m'; yellow='\033[33m'
magenta='\033[35m'; dim='\033[90m'; reset='\033[0m'

left=$(printf "${cyan}%s${reset} ${blue}%s${reset}" "$model" "$cwd")
if [[ -n "$branch" ]]; then
  left=$(printf "%b ${yellow} %s${reset}" "$left" "$branch")
fi

right=""
if [[ -n "$kube" ]]; then
  right=$(printf "${magenta}⎈ %s${reset}" "$kube")
fi
if [[ -n "$remaining" ]]; then
  [[ -n "$right" ]] && right="${right} "
  right="${right}$(printf "${dim}ctx %.0f%%${reset}" "$remaining")"
fi

if [[ -n "$right" ]]; then
  printf '%b  %b\n' "$left" "$right"
else
  printf '%b\n' "$left"
fi
