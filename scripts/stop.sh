#!/usr/bin/env bash
# Stop and remove containers. The database volume is kept.
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose down
echo "Stopped. Database data is kept in the 'pgdata' volume."
