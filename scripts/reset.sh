#!/usr/bin/env bash
# DESTRUCTIVE: stops the stack and deletes the local database volume.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ "${1:-}" != "--confirm-delete-local-data" ]; then
  echo "This deletes ALL local CuraLLM database data (the 'pgdata' volume). It cannot be undone."
  echo "To proceed, run: scripts/reset.sh --confirm-delete-local-data"
  exit 2
fi

docker compose down -v
echo "Local database data deleted. Run scripts/dev.sh, then scripts/migrate.sh, to start fresh."
