#!/usr/bin/env bash
# Wrapper for ynab-mcp-server.
#
# Used by both Copilot CLI and Claude Code (and any other MCP host that points
# at this wrapper). MCP hosts spawn servers with a clean environment (only PATH
# is inherited), so this wrapper loads the YNAB_API_TOKEN secret from a
# machine-local file that lives outside git, then execs the server.
#
# Setup on a new machine:
#   mkdir -p ~/.ai-config/secrets
#   cat > ~/.ai-config/secrets/ynab.env <<'EOF'
#   # Personal access token from YNAB → Account Settings → Developer Settings.
#   YNAB_API_TOKEN=your-ynab-personal-access-token-here
#   EOF
#   chmod 600 ~/.ai-config/secrets/ynab.env

set -euo pipefail

SECRETS_FILE="${HOME}/.ai-config/secrets/ynab.env"

if [[ ! -f "${SECRETS_FILE}" ]]; then
  echo "ynab-mcp-wrapper: missing ${SECRETS_FILE}" >&2
  echo "See the setup notes at the top of $0" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
. "${SECRETS_FILE}"
set +a

# MCP hosts (Claude Code, Copilot CLI) spawn this with a minimal PATH that
# typically excludes ~/.local/bin (where pipx installs). Resolve the binary
# explicitly to avoid "not found" failures.
YNAB_MCP_BIN="${HOME}/.local/bin/ynab-mcp-server"
if [[ ! -x "${YNAB_MCP_BIN}" ]]; then
  YNAB_MCP_BIN=$(command -v ynab-mcp-server 2>/dev/null) || {
    echo "ynab-mcp-wrapper: ynab-mcp-server not found in ~/.local/bin or PATH" >&2
    exit 1
  }
fi

exec "${YNAB_MCP_BIN}" "$@"
