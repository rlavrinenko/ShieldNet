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
