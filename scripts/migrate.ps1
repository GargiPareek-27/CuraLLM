# Run Alembic. Default: upgrade head. Example: scripts\migrate.ps1 downgrade -1
$ErrorActionPreference = "Continue"
Set-Location (Join-Path $PSScriptRoot "..")
if (-not (Test-Path ".env")) { Write-Error "ERROR: .env not found. Run scripts\setup.ps1 first."; exit 1 }

docker compose up -d --wait postgres
if ($LASTEXITCODE -ne 0) { Write-Error "Could not start a healthy postgres."; exit 1 }

if ($args.Count -eq 0) { $alembicArgs = @("upgrade", "head") } else { $alembicArgs = $args }
docker compose run --rm --no-deps api alembic @alembicArgs
if ($LASTEXITCODE -ne 0) { Write-Error "alembic failed."; exit 1 }
