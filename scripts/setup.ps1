# Check prerequisites and create .env from .env.example. Installs nothing.
$ErrorActionPreference = "Continue"
Set-Location (Join-Path $PSScriptRoot "..")

function Fail($message) { Write-Error "ERROR: $message"; exit 1 }

if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Fail "git is not installed. Install it from https://git-scm.com/downloads" }
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { Fail "Docker is not installed. Install Docker Desktop: https://docs.docker.com/desktop/setup/install/windows-install/" }

docker compose version *> $null
if ($LASTEXITCODE -ne 0) { Fail "Docker Compose v2 ('docker compose') is not available. Update Docker Desktop." }
docker info *> $null
if ($LASTEXITCODE -ne 0) { Fail "Docker is installed but its daemon is not running. Start Docker Desktop and try again." }

if (Test-Path ".env") {
    Write-Host ".env already exists; leaving it unchanged."
} else {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example."
}
Write-Host "Prerequisite checks passed."
Write-Host "Next: set POSTGRES_PASSWORD in .env (12+ chars; letters, digits, _ or - only), then run scripts\dev.ps1"
