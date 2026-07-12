#!/usr/bin/env bash
# Wrapper for the Context7 MCP server (@upstash/context7-mcp).
#
# Used by both Copilot CLI and Claude Code (and any other MCP host that points
# at this wrapper). MCP hosts spawn servers with a clean environment (only PATH
# is inherited), so this wrapper loads the API key from a machine-local file
# that lives outside git, then execs the server via npx.
#
# Setup on a new machine:
#   mkdir -p ~/.ai-config/secrets
#   cat > ~/.ai-config/secrets/context7.env <<'EOF'
#   CONTEXT7_API_KEY=ctx7sk-...        # mint: https://context7.com/dashboard
#   EOF
#   chmod 600 ~/.ai-config/secrets/context7.env

set -euo pipefail

SECRETS_FILE="${HOME}/.ai-config/secrets/context7.env"

if [[ ! -f "${SECRETS_FILE}" ]]; then
  echo "context7-mcp-wrapper: missing ${SECRETS_FILE}" >&2
  echo "See the setup notes at the top of $0" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
. "${SECRETS_FILE}"
set +a

if [[ -z "${CONTEXT7_API_KEY:-}" ]]; then
  echo "context7-mcp-wrapper: CONTEXT7_API_KEY not set in ${SECRETS_FILE}" >&2
  exit 1
fi

# MCP hosts spawn this with a minimal PATH; make sure npx (Homebrew node) is
# resolvable.
export PATH="/opt/homebrew/bin:${PATH}"

# The server reads CONTEXT7_API_KEY from the environment (exported by the
# set -a sourcing above). Do NOT pass it as --api-key argv — argv is visible
# to every process on the machine via ps.
exec npx -y @upstash/context7-mcp "$@"
