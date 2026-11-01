#!/usr/bin/env bash
# Check prerequisites and create .env from .env.example. Installs nothing.
set -euo pipefail
cd "$(dirname "$0")/.."

fail() { echo "ERROR: $*" >&2; exit 1; }

command -v git >/dev/null 2>&1 || fail "git is not installed. Install it from https://git-scm.com/downloads"
command -v docker >/dev/null 2>&1 || fail "Docker is not installed. Install Docker Desktop (Windows/macOS) or Docker Engine (Linux): https://docs.docker.com/get-docker/"
docker compose version >/dev/null 2>&1 || fail "Docker Compose v2 ('docker compose') is not available. Update Docker or install the Compose plugin."
docker info >/dev/null 2>&1 || fail "Docker is installed but its daemon is not running. Start Docker and try again."

if [ -f .env ]; then
  echo ".env already exists; leaving it unchanged."
else
  cp .env.example .env
  echo "Created .env from .env.example."
fi
echo "Prerequisite checks passed."
echo "Next: set POSTGRES_PASSWORD in .env (12+ chars; letters, digits, _ or - only), then run scripts/dev.sh"
