#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Resolve API base: prod exposes only nginx (:80); dev exposes the controller port.
env_val() { grep -E "^$1=" .env 2>/dev/null | tail -n1 | cut -d= -f2- | tr -d '[:space:]'; }
targets=()
if [[ -n "${CONTROLLER_URL:-}" ]]; then
  targets+=("$CONTROLLER_URL")
fi
if [[ -f .env ]]; then
  nport="$(env_val NGINX_HTTP_PORT)"
  cport="$(env_val CONTROLLER_PORT)"
  [[ -n "$nport" ]] && targets+=("http://127.0.0.1:$nport")
  [[ -n "$cport" ]] && targets+=("http://127.0.0.1:$cport")
fi
targets+=("http://127.0.0.1:80" "http://127.0.0.1:8000")

api_ok=""
for t in "${targets[@]}"; do
  if curl -fsS "$t/health" >/dev/null 2>&1; then
    api_ok="$t"
    break
  fi
done

fail=0
check() {
  local name="$1"
  local cmd="$2"
  if eval "$cmd" >/dev/null 2>&1; then
    echo "ok  $name"
  else
    echo "FAIL $name"
    fail=1
  fi
}

if [[ -n "$api_ok" ]]; then
  echo "ok  controller /health ($api_ok)"
  check "controller /api/v1/workers" "curl -fsS ${api_ok}/api/v1/workers"
else
  echo "FAIL controller /health"
  fail=1
fi
check "postgres" "docker compose exec -T postgres pg_isready"
check "redis" "docker compose exec -T redis redis-cli ping"

exit "$fail"
