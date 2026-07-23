#!/usr/bin/env bash
# Idempotent personal bootstrap for host and dev-container homes.

set -euo pipefail

repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
mode="host"
action="install"
profile="${AI_SYNC_PROFILE:-personal}"
skill_scope="${AI_SYNC_SKILL_SCOPE:-auto}"

while (($#)); do
  case "$1" in
    --container) mode="container" ;;
    --work)
      profile="work"
      skill_scope="general"
      ;;
    --check) action="check" ;;
    -h|--help)
      printf 'usage: ./install.sh [--work] [--container] [--check]\n'
      exit 0
      ;;
    *)
      printf 'unknown option: %s\n' "$1" >&2
      exit 2
      ;;
  esac
  shift
done

export AI_SYNC_PROFILE="$profile"
export AI_SYNC_SKILL_SCOPE="$skill_scope"

run_checks() {
  local status=0
  AI_CONFIG="$repo" "$repo/bin/ai-sync" doctor || status=1
  "$repo/bin/ai-health" --repo "$repo" || status=1
  return "$status"
}

if [[ "$action" == "check" ]]; then
  run_checks
  exit
fi

printf 'Installing %s AI configuration (%s mode) from %s\n' "$profile" "$mode" "$repo"
AI_CONFIG="$repo" "$repo/bin/ai-sync" apply --force
"$repo/bin/ai-runtime-permissions"
run_checks
