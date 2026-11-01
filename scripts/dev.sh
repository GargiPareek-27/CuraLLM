#!/usr/bin/env bash
# Validate configuration, then build and start the stack in the background.
set -euo pipefail
cd "$(dirname "$0")/.."

fail() { echo "ERROR: $*" >&2; exit 1; }
envval() { grep -E "^$1=" .env | head -n1 | cut -d= -f2- | tr -d '\r' || true; }

[ -f .env ] || fail ".env not found. Run scripts/setup.sh first."
docker info >/dev/null 2>&1 || fail "Docker daemon is not running."

pw="$(envval POSTGRES_PASSWORD)"
[ -n "$pw" ] || fail "POSTGRES_PASSWORD is empty in .env."
[ "$pw" != "CHANGE_ME" ] || fail "POSTGRES_PASSWORD is still CHANGE_ME. Set a real password in .env."
[[ "$pw" =~ ^[A-Za-z0-9_-]{12,}$ ]] || fail "POSTGRES_PASSWORD must be 12+ characters using only letters, digits, '_' or '-'."

api_port="$(envval API_HOST_PORT)"; api_port="${api_port:-8000}"

docker compose up -d --build

command -v curl >/dev/null 2>&1 || { echo "curl not found; skipping the readiness wait. Check http://127.0.0.1:${api_port}/ready yourself."; exit 0; }

echo "Waiting for http://127.0.0.1:${api_port}/ready ..."
for _ in $(seq 1 45); do
  if curl -fsS "http://127.0.0.1:${api_port}/ready" >/dev/null 2>&1; then
    echo "Ready."
    echo "  API:       http://127.0.0.1:${api_port}  (docs: /docs)"
    echo "  Next steps: scripts/migrate.sh (enable pgvector), then scripts/verify.sh"
    exit 0
  fi
  sleep 2
done
echo "The API did not become ready within 90 seconds. Inspect logs with: docker compose logs api inference postgres" >&2
exit 1
