#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="${1:-/opt/shieldnet}"
failures=0
pass(){ printf 'PASS  %s\n' "$*"; }
warn(){ printf 'WARN  %s\n' "$*"; }
fail(){ printf 'FAIL  %s\n' "$*"; failures=$((failures+1)); }

[[ $EUID -eq 0 ]] || { echo "Run as root: sudo $0"; exit 2; }
echo "ShieldNet Doctor $(date -Is)"
echo

for pair in "shieldnet-api:/etc/shieldnet/backend/backend.env" "shieldnet-bot:/etc/shieldnet/bot/bot.env" "shieldnet-scheduler:/etc/shieldnet/scheduler/scheduler.env"; do
  user="${pair%%:*}"; file="${pair#*:}"
  if [[ ! -f "$file" ]]; then fail "Missing $file"; continue; fi
  if runuser -u "$user" -- test -r "$file"; then pass "$user can read $file"; else fail "$user cannot read $file"; namei -l "$file" || true; fi
done

for svc in shieldnet-backend shieldnet-bot shieldnet-scheduler valkey; do
  if systemctl is-active --quiet "$svc"; then pass "$svc active"; else fail "$svc inactive"; systemctl --no-pager --full status "$svc" || true; fi
done

if nginx -t >/tmp/shieldnet-nginx-test 2>&1; then pass "nginx configuration valid"; else fail "nginx configuration invalid"; cat /tmp/shieldnet-nginx-test; fi
if grep -Rqs 'proxy_set_header[[:space:]]\+Upgrade' /etc/nginx; then pass "Nginx WebSocket Upgrade header found"; else warn "Nginx WebSocket Upgrade header not found"; fi

for executable in "$ROOT/backend/venv/bin/python" "$ROOT/bot/venv/bin/python" "$ROOT/scheduler/venv/bin/python"; do
  [[ -x "$executable" ]] && pass "$executable exists" || fail "$executable missing"
done

if curl -fsS http://127.0.0.1:8000/api/v1/health >/tmp/shieldnet-health 2>/dev/null || curl -fsS http://127.0.0.1:8000/health >/tmp/shieldnet-health 2>/dev/null; then
  pass "Backend HTTP health responds"
else
  fail "Backend HTTP health unavailable"
fi

if command -v valkey-cli >/dev/null 2>&1 && valkey-cli ping | grep -q PONG; then pass "Valkey PING"; elif command -v redis-cli >/dev/null 2>&1 && redis-cli ping | grep -q PONG; then pass "Redis PING"; else fail "Valkey/Redis PING failed"; fi

if [[ -x "$ROOT/backend/venv/bin/alembic" ]]; then
  if (cd "$ROOT/backend" && runuser -u shieldnet-api -- "$ROOT/backend/venv/bin/alembic" current); then pass "Alembic current succeeded"; else fail "Alembic current failed"; fi
fi

DB_NAME=$(sed -n 's/^SHIELDNET_DB_NAME=//p' /etc/shieldnet/backend/backend.env | tail -1 | tr -d '"\r')
DB_USER=$(sed -n 's/^SHIELDNET_DB_USER=//p' /etc/shieldnet/backend/backend.env | tail -1 | tr -d '"\r')
DB_NAME=${DB_NAME:-shieldnet}
if [[ -n "$DB_USER" ]] && id postgres >/dev/null 2>&1; then
  schemas=(core discord verification audit security system)
  for schema in "${schemas[@]}"; do
    ok=$(runuser -u postgres -- psql -d "$DB_NAME" -Atqc "SELECT has_schema_privilege('$DB_USER','$schema','USAGE')" 2>/dev/null || echo f)
    [[ "$ok" == "t" ]] && pass "$DB_USER has USAGE on schema $schema" || fail "$DB_USER lacks USAGE on schema $schema"
  done
fi

echo
if ((failures)); then echo "Doctor completed with $failures failure(s)."; exit 1; fi
echo "Doctor completed successfully."
