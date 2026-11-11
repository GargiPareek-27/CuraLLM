# Regenerate the hashed lockfiles (requirements.txt and requirements-dev.txt) for both Python
# services from their .in files. Runs inside a Linux Python 3.12 container, the same platform as
# the Docker images and CI. Needs Docker. Review `git diff --stat` before committing.
$ErrorActionPreference = "Continue"
Set-Location (Join-Path $PSScriptRoot "..")

docker info *> $null
if ($LASTEXITCODE -ne 0) { Write-Error "ERROR: Docker daemon is not running."; exit 1 }

foreach ($service in @("api", "inference")) {
    Write-Host "=== locking services/$service ==="
    $mount = "$((Resolve-Path "services\$service").Path):/work"
    docker run --rm -v $mount -w /work python:3.12-slim sh -c "pip install -q pip-tools && pip-compile -q --generate-hashes --strip-extras --allow-unsafe -o requirements.txt requirements.in && pip-compile -q --generate-hashes --strip-extras --allow-unsafe -o requirements-dev.txt requirements-dev.in"
    if ($LASTEXITCODE -ne 0) { Write-Error "Locking $service failed."; exit 1 }
}
Write-Host "Lockfiles written. Review with: git diff --stat"
