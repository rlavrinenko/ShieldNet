#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="/opt/shieldnet"
RELEASE_DIR="/opt/shieldnet-releases"
VERSION="${1:-1.0.0-rc1}"
NAME="ShieldNet-${VERSION}"
STAGING="${RELEASE_DIR}/${NAME}"
ARCHIVE="${RELEASE_DIR}/${NAME}.tar.gz"

log() {
    printf '\n[%s] %s\n' "$(date '+%F %T')" "$*"
}

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

[[ $EUID -eq 0 ]] || fail "Run as root."
[[ -d "${PROJECT_DIR}/.git" ]] || fail "${PROJECT_DIR} is not a Git repository."

mkdir -p "${RELEASE_DIR}"
rm -rf "${STAGING}" "${ARCHIVE}"

log "Updating repository"
cd "${PROJECT_DIR}"

git fetch origin
git checkout main
git pull --ff-only origin main

log "Checking repository status"
git status --short

log "Running backend tests"
cd "${PROJECT_DIR}/backend"

if [[ -x venv/bin/python ]]; then
    PYTHON="${PROJECT_DIR}/backend/venv/bin/python"
    PYTEST="${PROJECT_DIR}/backend/venv/bin/pytest"
    ALEMBIC="${PROJECT_DIR}/backend/venv/bin/alembic"
else
    PYTHON="python3"
    PYTEST="pytest"
    ALEMBIC="alembic"
fi

PYTHONPATH="${PROJECT_DIR}/backend" "${PYTEST}" -q
"${ALEMBIC}" upgrade head

log "Verifying API routes"
cd "${PROJECT_DIR}"

"${PYTHON}" tools/verify_routes.py \
    --backend "${PROJECT_DIR}/backend"

"${PYTHON}" tools/verify_plugin_api.py \
    --backend "${PROJECT_DIR}/backend"

log "Building frontend"
cd "${PROJECT_DIR}/admin-frontend"

npm ci
npm run build

log "Creating release staging directory"
mkdir -p "${STAGING}"

rsync -a \
    --exclude='.git/' \
    --exclude='.github/' \
    --exclude='backups/' \
    --exclude='logs/' \
    --exclude='tmp/' \
    --exclude='node_modules/' \
    --exclude='.angular/' \
    --exclude='venv/' \
    --exclude='.venv/' \
    --exclude='__pycache__/' \
    --exclude='.pytest_cache/' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='.env' \
    --exclude='.env.*' \
    --exclude='*.bak' \
    --exclude='*.backup-*' \
    "${PROJECT_DIR}/" "${STAGING}/"

log "Adding release metadata"

cat > "${STAGING}/RELEASE" <<EOF
NAME=${NAME}
VERSION=${VERSION}
CREATED_AT=$(date --iso-8601=seconds)
SOURCE_REPOSITORY=https://github.com/rlavrinenko/ShieldNet
SOURCE_BRANCH=main
SOURCE_COMMIT=$(git -C "${PROJECT_DIR}" rev-parse HEAD)
EOF

cat > "${STAGING}/install-release.sh" <<'INSTALL'
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
INSTALL

chmod +x "${STAGING}/install-release.sh"

cat > "${STAGING}/verify-release.sh" <<'VERIFY'
#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "${PROJECT_DIR}/backend"

PYTHONPATH="${PROJECT_DIR}/backend" \
    venv/bin/pytest -q

venv/bin/alembic upgrade head

cd "${PROJECT_DIR}"

backend/venv/bin/python tools/verify_routes.py \
    --backend "${PROJECT_DIR}/backend"

backend/venv/bin/python tools/verify_plugin_api.py \
    --backend "${PROJECT_DIR}/backend"

cd "${PROJECT_DIR}/admin-frontend"
npm run build

echo
echo "ShieldNet verification completed successfully."
VERIFY

chmod +x "${STAGING}/verify-release.sh"

cat > "${STAGING}/rollback-release.sh" <<'ROLLBACK'
#!/usr/bin/env bash
set -Eeuo pipefail

TARGET_DIR="/opt/shieldnet"
BACKUP_ROOT="/opt/shieldnet-backups"

LATEST_BACKUP="$(
    find "${BACKUP_ROOT}" \
        -mindepth 1 \
        -maxdepth 1 \
        -type d \
        -name 'before-release-*' \
        -printf '%T@ %p\n' |
    sort -nr |
    head -n1 |
    cut -d' ' -f2-
)"

if [[ -z "${LATEST_BACKUP}" ]]; then
    echo "No release backup found." >&2
    exit 1
fi

echo "Restoring ${LATEST_BACKUP}"

rsync -a --delete \
    "${LATEST_BACKUP}/" "${TARGET_DIR}/"

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

echo "Rollback completed."
ROLLBACK

chmod +x "${STAGING}/rollback-release.sh"

log "Creating archive"
cd "${RELEASE_DIR}"

tar \
    --owner=0 \
    --group=0 \
    --numeric-owner \
    -czf "${ARCHIVE}" \
    "${NAME}"

log "Generating checksum"
sha256sum "${ARCHIVE}" > "${ARCHIVE}.sha256"

log "Release created"
ls -lh "${ARCHIVE}" "${ARCHIVE}.sha256"

echo
echo "Archive:"
echo "${ARCHIVE}"
echo
echo "Checksum:"
cat "${ARCHIVE}.sha256"
