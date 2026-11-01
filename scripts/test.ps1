# Run the unit tests of the API and inference services inside containers. Needs no GPU.
$ErrorActionPreference = "Continue"
Set-Location (Join-Path $PSScriptRoot "..")
if (-not (Test-Path ".env")) { Write-Error "ERROR: .env not found. Run scripts\setup.ps1 first."; exit 1 }

docker compose build api inference
if ($LASTEXITCODE -ne 0) { Write-Error "Build failed."; exit 1 }

foreach ($service in @("api", "inference")) {
    Write-Host "=== tests: $service ==="
    docker compose run --rm --no-deps $service sh -c "python -m pip install --user -q -r requirements-dev.txt && python -m pytest -q"
    if ($LASTEXITCODE -ne 0) { Write-Error "Tests failed for $service."; exit 1 }
}
