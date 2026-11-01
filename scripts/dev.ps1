# Validate configuration, then build and start the stack in the background.
$ErrorActionPreference = "Continue"
Set-Location (Join-Path $PSScriptRoot "..")

function Fail($message) { Write-Error "ERROR: $message"; exit 1 }
function EnvValue($key) {
    $line = Get-Content ".env" | Where-Object { $_ -match "^$key=" } | Select-Object -First 1
    if ($line) { return ($line -replace "^$key=", "").Trim() }
    return ""
}

if (-not (Test-Path ".env")) { Fail ".env not found. Run scripts\setup.ps1 first." }
docker info *> $null
if ($LASTEXITCODE -ne 0) { Fail "Docker daemon is not running. Start Docker Desktop." }

$pw = EnvValue "POSTGRES_PASSWORD"
if ($pw -eq "") { Fail "POSTGRES_PASSWORD is empty in .env." }
if ($pw -eq "CHANGE_ME") { Fail "POSTGRES_PASSWORD is still CHANGE_ME. Set a real password in .env." }
if ($pw -notmatch "^[A-Za-z0-9_-]{12,}$") { Fail "POSTGRES_PASSWORD must be 12+ characters using only letters, digits, '_' or '-'." }

$apiPort = EnvValue "API_HOST_PORT"
if ($apiPort -eq "") { $apiPort = "8000" }

docker compose up -d --build
if ($LASTEXITCODE -ne 0) { Fail "docker compose up failed. Inspect with: docker compose logs" }

Write-Host "Waiting for http://127.0.0.1:$apiPort/ready ..."
for ($i = 0; $i -lt 45; $i++) {
    try {
        $r = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$apiPort/ready" -TimeoutSec 3
        if ($r.StatusCode -eq 200) {
            Write-Host "Ready."
            Write-Host "  API:       http://127.0.0.1:$apiPort  (docs: /docs)"
            Write-Host "  Next steps: scripts\migrate.ps1 (enable pgvector), then scripts\verify.ps1"
            exit 0
        }
    } catch { }
    Start-Sleep -Seconds 2
}
Write-Error "The API did not become ready within 90 seconds. Inspect logs with: docker compose logs api inference postgres"
exit 1
