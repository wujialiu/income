#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8080}"

echo "=== Health Check ==="
curl -s "$BASE_URL/healthz" | jq .

echo
echo "=== List Users ==="
curl -s "$BASE_URL/api/users" | jq .

echo
echo "=== Version Info ==="
curl -s "$BASE_URL/version" | jq .
