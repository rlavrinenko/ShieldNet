#!/usr/bin/env bash
set -Eeuo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="/opt/shieldnet"
BACKUP_ROOT="/opt/shieldnet-backups"
TIMESTAMP="$(date '+%Y%m%d-%H%M%S')"
BACKUP_DIR="${BACKUP_ROOT}/before-release-${TIMESTAMP}"

log() {
    printf '\n[%s] %s\n' "$(date '+%F %T')" "$*"
}

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

[[ $EUID -eq 0 ]] || fail "Run as root."

mkdir -p "${BACKUP_ROOT}"

if [[ -d "${TARGET_DIR}" ]]; then
    log "Creating backup: ${BACKUP_DIR}"
    mkdir -p "${BACKUP_DIR}"

    rsync -a \
        --exclude='venv/' \
        --exclude='node_modules/' \
        --exclude='.angular/' \
        --exclude='__pycache__/' \
        "${TARGET_DIR}/" "${BACKUP_DIR}/"
fi

log "Installing release into ${TARGET_DIR}"
mkdir -p "${TARGET_DIR}"

rsync -a --delete \
    --exclude='.env' \
    --exclude='.env.*' \
    --exclude='venv/' \
    --exclude='node_modules/' \
    "${SOURCE_DIR}/" "${TARGET_DIR}/"

log "Preparing backend"
cd "${TARGET_DIR}/backend"

if [[ ! -d venv ]]; then
    python3 -m venv venv
fi

venv/bin/python -m pip install --upgrade pip wheel setuptools

if [[ -f requirements.txt ]]; then
    venv/bin/pip install -r requirements.txt
elif [[ -f pyproject.toml ]]; then
    venv/bin/pip install .
fi

log "Applying database migrations"
venv/bin/alembic upgrade head

log "Running backend tests"
PYTHONPATH="${TARGET_DIR}/backend" venv/bin/pytest -q

log "Verifying API routes"
cd "${TARGET_DIR}"

backend/venv/bin/python tools/verify_routes.py \
    --backend "${TARGET_DIR}/backend"

backend/venv/bin/python tools/verify_plugin_api.py \
    --backend "${TARGET_DIR}/backend"

log "Preparing frontend"
cd "${TARGET_DIR}/admin-frontend"

npm ci
npm run build

log "Restarting ShieldNet services"

for service in \
    shieldnet-api \
    shieldnet-bot \
    shieldnet-scheduler
do
    if systemctl list-unit-files "${service}.service" \
        --no-legend 2>/dev/null | grep -q "${service}.service"; then
        systemctl restart "${service}"
    fi
done

if systemctl list-unit-files nginx.service \
    --no-legend 2>/dev/null | grep -q nginx.service; then
    nginx -t
    systemctl reload nginx
fi

log "Installation completed"

echo
echo "========================================"
echo "ShieldNet release installed successfully"
echo "========================================"
echo "Backup: ${BACKUP_DIR}"
