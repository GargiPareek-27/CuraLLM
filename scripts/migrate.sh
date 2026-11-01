#!/usr/bin/env bash
# Run Alembic. Default: upgrade head. Example: scripts/migrate.sh downgrade -1
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] || { echo "ERROR: .env not found. Run scripts/setup.sh first." >&2; exit 1; }

docker compose up -d --wait postgres
if [ "$#" -eq 0 ]; then set -- upgrade head; fi
docker compose run --rm --no-deps api alembic "$@"
