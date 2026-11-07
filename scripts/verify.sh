#!/usr/bin/env bash
# Check that a RUNNING Phase 1a stack behaves as documented. Prints PASS/FAIL per check.
set -uo pipefail
cd "$(dirname "$0")/.."

command -v curl >/dev/null 2>&1 || { echo "ERROR: curl is required for verify.sh" >&2; exit 1; }
envval() { grep -E "^$1=" .env 2>/dev/null | head -n1 | cut -d= -f2- | tr -d '\r' || true; }

api_port="$(envval API_HOST_PORT)"; api_port="${api_port:-8000}"
inf_port="$(envval INFERENCE_HOST_PORT)"; inf_port="${inf_port:-8001}"
api="http://127.0.0.1:${api_port}"
inf="http://127.0.0.1:${inf_port}"
failures=0

pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1"; failures=$((failures + 1)); }

status_of() { curl -s -o /dev/null -w '%{http_code}' --max-time 8 "$@" || true; }

code="$(status_of "$api/health")"
[ "$code" = "200" ] && pass "api /health (HTTP 200)" || fail "api /health expected 200, got '$code'"

code="$(status_of "$inf/health")"
[ "$code" = "200" ] && pass "inference /health (HTTP 200)" || fail "inference /health expected 200, got '$code'"

ready="$(curl -s --max-time 8 "$api/ready" || true)"
echo "$ready" | grep -q '"status":"ready"' && pass "api /ready reports ready" || fail "api /ready is not ready: $ready"
echo "$ready" | grep -q '"pgvector":"installed"' && pass "pgvector extension installed" || fail "pgvector not installed (run scripts/migrate.sh)"

chat="$(curl -s --max-time 15 -X POST "$api/api/v1/chat" -H 'Content-Type: application/json' -d '{"message":"Hello"}' || true)"
echo "$chat" | grep -q '"is_demo":true' && pass "chat answers in labelled demo mode" || fail "chat did not return a demo-labelled answer: $chat"
echo "$chat" | grep -q '"citations":\[\]' && pass "chat citations empty (expected in Phase 1)" || fail "chat citations were not empty"

search="$(curl -s --max-time 15 -X POST "$api/api/v1/search" -H 'Content-Type: application/json' -d '{"query":"fever"}' || true)"
echo "$search" | grep -q '"results":\[' && pass "search endpoint returns a results list" || fail "search endpoint did not return a results list (run scripts/migrate.sh): $search"

code="$(status_of -X POST "$api/api/v1/chat" -H 'Content-Type: application/json' -d '{"message":"   "}')"
[ "$code" = "422" ] && pass "blank message rejected (HTTP 422)" || fail "blank message expected 422, got '$code'"

if [ "$failures" -eq 0 ]; then echo "All checks passed."; exit 0; fi
echo "$failures check(s) failed."
exit 1
