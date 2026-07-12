#!/usr/bin/env bash
# Wrapper for unifi-mcp-server.
#
# Used by both Copilot CLI and Claude Code (and any other MCP host that points
# at this wrapper). MCP hosts spawn servers with a clean environment (only PATH
# is inherited), so this wrapper loads UNIFI_* secrets from a machine-local
# file that lives outside git, then execs the server.
#
# Setup on a new machine:
#   mkdir -p ~/code/ai-sync/secrets
#   cat > ~/code/ai-sync/secrets/unifi.env <<'EOF'
#   UNIFI_API_KEY=your-unifi-api-key-here
#   # Optional overrides — see unifi-mcp-server docs:
#   # UNIFI_API_TYPE=cloud-ea        # cloud-v1 | cloud-ea | local
#   # UNIFI_LOCAL_HOST=10.0.0.1      # required for UNIFI_API_TYPE=local
#   EOF
#   chmod 600 ~/code/ai-sync/secrets/unifi.env

set -euo pipefail

SECRETS_FILE="${HOME}/code/ai-sync/secrets/unifi.env"

if [[ ! -f "${SECRETS_FILE}" ]]; then
  echo "unifi-mcp-wrapper: missing ${SECRETS_FILE}" >&2
  echo "See the setup notes at the top of $0" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
. "${SECRETS_FILE}"
set +a

# The unifi-mcp-server writes audit.log into its cwd. Run it from a dedicated
# state dir so the log doesn't land in whichever repo the user is working in.
STATE_DIR="${HOME}/code/ai-sync/state/unifi-mcp"
mkdir -p "${STATE_DIR}"
cd "${STATE_DIR}"

# MCP hosts (Claude Code, Copilot CLI) spawn this with a minimal PATH that
# typically excludes ~/.local/bin (where pipx installs). Resolve the binary
# explicitly to avoid "not found" failures.
UNIFI_MCP_BIN="${HOME}/.local/bin/unifi-mcp-server"
if [[ ! -x "${UNIFI_MCP_BIN}" ]]; then
  UNIFI_MCP_BIN=$(command -v unifi-mcp-server 2>/dev/null) || {
    echo "unifi-mcp-wrapper: unifi-mcp-server not found in ~/.local/bin or PATH" >&2
    exit 1
  }
fi

exec "${UNIFI_MCP_BIN}" "$@"
