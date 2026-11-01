# DESTRUCTIVE: stops the stack and deletes the local database volume.
param([switch]$ConfirmDeleteLocalData)
$ErrorActionPreference = "Continue"
Set-Location (Join-Path $PSScriptRoot "..")

if (-not $ConfirmDeleteLocalData) {
    Write-Host "This deletes ALL local CuraLLM database data (the 'pgdata' volume). It cannot be undone."
    Write-Host "To proceed, run: .\scripts\reset.ps1 -ConfirmDeleteLocalData"
    exit 2
}

docker compose down -v
if ($LASTEXITCODE -ne 0) { Write-Error "docker compose down -v failed."; exit 1 }
Write-Host "Local database data deleted. Run scripts\dev.ps1, then scripts\migrate.ps1, to start fresh."
