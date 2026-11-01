# Check that a RUNNING Phase 1a stack behaves as documented. Prints PASS/FAIL per check.
$ErrorActionPreference = "Continue"
Set-Location (Join-Path $PSScriptRoot "..")

function EnvValue($key) {
    if (-not (Test-Path ".env")) { return "" }
    $line = Get-Content ".env" | Where-Object { $_ -match "^$key=" } | Select-Object -First 1
    if ($line) { return ($line -replace "^$key=", "").Trim() }
    return ""
}

$apiPort = EnvValue "API_HOST_PORT";       if ($apiPort -eq "") { $apiPort = "8000" }
$infPort = EnvValue "INFERENCE_HOST_PORT"; if ($infPort -eq "") { $infPort = "8001" }
$api = "http://127.0.0.1:$apiPort"
$inf = "http://127.0.0.1:$infPort"
$script:failures = 0

function Pass($message) { Write-Host "PASS  $message" -ForegroundColor Green }
function Fail($message) { Write-Host "FAIL  $message" -ForegroundColor Red; $script:failures++ }

function Call($method, $url, $body) {
    try {
        $params = @{ Uri = $url; Method = $method; UseBasicParsing = $true; TimeoutSec = 15 }
        if ($body) { $params.Body = $body; $params.ContentType = "application/json" }
        $r = Invoke-WebRequest @params
        return @{ Code = [int]$r.StatusCode; Body = [string]$r.Content }
    } catch {
        $resp = $_.Exception.Response
        if ($resp) { return @{ Code = [int]$resp.StatusCode; Body = "" } }
        return @{ Code = 0; Body = "" }
    }
}

$r = Call "GET" "$api/health" $null
if ($r.Code -eq 200) { Pass "api /health (HTTP 200)" } else { Fail "api /health expected 200, got $($r.Code)" }

$r = Call "GET" "$inf/health" $null
if ($r.Code -eq 200) { Pass "inference /health (HTTP 200)" } else { Fail "inference /health expected 200, got $($r.Code)" }

$r = Call "GET" "$api/ready" $null
if ($r.Code -eq 200) {
    $j = $r.Body | ConvertFrom-Json
    if ($j.status -eq "ready") { Pass "api /ready reports ready" } else { Fail "api /ready status is '$($j.status)'" }
    if ($j.pgvector -eq "installed") { Pass "pgvector extension installed" } else { Fail "pgvector not installed (run scripts\migrate.ps1)" }
} else {
    Fail "api /ready expected 200, got $($r.Code) (database or inference not ready)"
}

$r = Call "POST" "$api/api/v1/chat" '{"message":"Hello"}'
if ($r.Code -eq 200) {
    $j = $r.Body | ConvertFrom-Json
    if ($j.is_demo -eq $true) { Pass "chat answers in labelled demo mode" } else { Fail "chat is_demo was not true" }
    if (($null -eq $j.citations) -or (@($j.citations).Count -eq 0)) { Pass "chat citations empty (expected in Phase 1)" } else { Fail "chat citations were not empty" }
} else {
    Fail "chat expected 200, got $($r.Code)"
}

$r = Call "POST" "$api/api/v1/chat" '{"message":"   "}'
if ($r.Code -eq 422) { Pass "blank message rejected (HTTP 422)" } else { Fail "blank message expected 422, got $($r.Code)" }

if ($script:failures -eq 0) { Write-Host "All checks passed."; exit 0 }
Write-Host "$($script:failures) check(s) failed."
exit 1
