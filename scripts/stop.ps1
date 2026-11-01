# Stop and remove containers. The database volume is kept.
$ErrorActionPreference = "Continue"
Set-Location (Join-Path $PSScriptRoot "..")
docker compose down
if ($LASTEXITCODE -ne 0) { Write-Error "docker compose down failed."; exit 1 }
Write-Host "Stopped. Database data is kept in the 'pgdata' volume."
