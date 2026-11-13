#!/usr/bin/env bash
# Regenerate the hashed lockfiles (requirements.txt and requirements-dev.txt) for both Python
# services from their .in files. Runs inside a Linux Python 3.12 container, the same platform as
# the Docker images and CI. Needs Docker. Review `git diff --stat` before committing.
set -euo pipefail
cd "$(dirname "$0")/.."
docker info >/dev/null 2>&1 || { echo "ERROR: Docker daemon is not running." >&2; exit 1; }

for service in api inference; do
  echo "=== locking services/$service ==="
  docker run --rm -v "$PWD/services/$service:/work" -w /work python:3.12-slim sh -c \
    "pip install -q pip-tools && pip-compile -q --generate-hashes --strip-extras --allow-unsafe -o requirements.txt requirements.in && pip-compile -q --generate-hashes --strip-extras --allow-unsafe -o requirements-dev.txt requirements-dev.in"
done
echo "Lockfiles written. Review with: git diff --stat"
