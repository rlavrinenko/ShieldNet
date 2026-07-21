#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="${1:-/opt/shieldnet}"
ARCHIVE="${2:-$(pwd)/shieldnet-v4.0-enterprise-dashboard.tar.gz}"
BACKUP_ROOT="/opt/shieldnet-backups"
WEB_ROOT="/var/www/shieldnet-admin"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/v4.0-$STAMP"
TMP_DIR="$(mktemp -d)"

log(){ printf '\n[%s] %s\n' "$(date '+%F %T')" "$*"; }
fail(){ echo "ERROR: $*" >&2; exit 1; }
cleanup(){ rm -rf "$TMP_DIR"; }
trap cleanup EXIT

[[ $EUID -eq 0 ]] || fail "Run as root"
[[ -f "$ARCHIVE" ]] || fail "Archive not found: $ARCHIVE"
[[ -d "$ROOT_DIR/backend" ]] || fail "ShieldNet backend not found in $ROOT_DIR"

log "Creating backup: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"
tar --exclude='backend/venv' --exclude='bot/venv' --exclude='scheduler/venv' --exclude='admin-frontend/node_modules' \
  -czf "$BACKUP_DIR/shieldnet-before-v4.0.tar.gz" -C "$ROOT_DIR" .

log "Extracting release"
tar -xzf "$ARCHIVE" -C "$TMP_DIR"
SOURCE="$TMP_DIR/shieldnet"
[[ -d "$SOURCE" ]] || fail "Invalid archive structure"

log "Preserving runtime files"
for path in backend/venv bot/venv scheduler/venv admin-frontend/node_modules; do
  if [[ -e "$ROOT_DIR/$path" ]]; then
    mkdir -p "$(dirname "$TMP_DIR/$path")"
    mv "$ROOT_DIR/$path" "$TMP_DIR/$path"
  fi
done

log "Installing release files"
rsync -a --delete \
  --exclude='backend/venv' \
  --exclude='bot/venv' \
  --exclude='scheduler/venv' \
  --exclude='admin-frontend/node_modules' \
  "$SOURCE/" "$ROOT_DIR/"

for path in backend/venv bot/venv scheduler/venv admin-frontend/node_modules; do
  if [[ -e "$TMP_DIR/$path" ]]; then
    mkdir -p "$(dirname "$ROOT_DIR/$path")"
    mv "$TMP_DIR/$path" "$ROOT_DIR/$path"
  fi
done

log "Checking backend"
cd "$ROOT_DIR/backend"
"$ROOT_DIR/backend/venv/bin/python" -m compileall -q app
runuser -u shieldnet-api -- "$ROOT_DIR/backend/venv/bin/python" -c "import app.main; print('backend import OK')"

log "Checking Alembic state"
runuser -u shieldnet-api -- "$ROOT_DIR/backend/venv/bin/alembic" upgrade head
runuser -u shieldnet-api -- "$ROOT_DIR/backend/venv/bin/alembic" current

log "Restarting backend"
systemctl restart shieldnet-backend
sleep 3
systemctl is-active --quiet shieldnet-backend || {
  journalctl -u shieldnet-backend -n 100 --no-pager
  fail "Backend failed"
}

log "Building Angular frontend"
cd "$ROOT_DIR/admin-frontend"
if [[ -d node_modules ]]; then
  npm run build
else
  npm ci --no-audit --no-fund
  npm run build
fi

DIST="$ROOT_DIR/admin-frontend/dist/shieldnet-admin/browser"
[[ -d "$DIST" ]] || DIST="$ROOT_DIR/admin-frontend/dist/shieldnet-admin"
[[ -d "$DIST" ]] || fail "Angular output not found"

log "Publishing frontend"
mkdir -p "$WEB_ROOT"
rsync -a --delete "$DIST/" "$WEB_ROOT/"
if id nginx >/dev/null 2>&1; then chown -R nginx:nginx "$WEB_ROOT"; fi

log "Reloading Nginx"
nginx -t
systemctl reload nginx

log "Service status"
for svc in shieldnet-backend shieldnet-bot shieldnet-scheduler; do
  if systemctl list-unit-files "$svc.service" --no-legend 2>/dev/null | grep -q .; then
    printf '%-24s %s\n' "$svc" "$(systemctl is-active "$svc" || true)"
  fi
done

log "ShieldNet v4.0 Enterprise Dashboard installed successfully"
echo "Open: https://YOUR-DOMAIN/"
echo "Backup: $BACKUP_DIR"
