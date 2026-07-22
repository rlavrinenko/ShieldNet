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
