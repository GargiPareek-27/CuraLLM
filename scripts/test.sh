#!/usr/bin/env bash
# Run the unit tests of the API and inference services inside containers. Needs no GPU.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] || { echo "ERROR: .env not found. Run scripts/setup.sh first." >&2; exit 1; }

docker compose build api inference
for service in api inference; do
  echo "=== tests: $service ==="
  docker compose run --rm --no-deps "$service" sh -c \
    "python -m pip install --user -q -r requirements-dev.txt && python -m pytest -q"
done
