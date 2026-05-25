#!/usr/bin/env bash
# Wrapper for unifi-mcp-server.
#
# Copilot CLI launches MCP servers with a clean environment (only PATH is
# inherited). This wrapper loads UNIFI_* secrets from a machine-local file
# that lives outside the git repo, then execs the server.
#
# Setup on a new machine:
#   mkdir -p ~/.copilot/secrets
#   cat > ~/.copilot/secrets/unifi.env <<'EOF'
#   UNIFI_API_KEY=your-unifi-api-key-here
#   # Optional overrides — see unifi-mcp-server docs:
#   # UNIFI_API_TYPE=cloud-ea        # cloud-v1 | cloud-ea | local
#   # UNIFI_LOCAL_HOST=10.0.0.1      # required for UNIFI_API_TYPE=local
#   EOF
#   chmod 600 ~/.copilot/secrets/unifi.env

set -euo pipefail

SECRETS_FILE="${HOME}/.copilot/secrets/unifi.env"

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
STATE_DIR="${HOME}/.copilot/state/unifi-mcp"
mkdir -p "${STATE_DIR}"
cd "${STATE_DIR}"

exec unifi-mcp-server "$@"
