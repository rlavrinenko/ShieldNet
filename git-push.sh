#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="/opt/shieldnet"

echo "========================================"
echo "       ShieldNet → GitHub"
echo "========================================"

cd "$PROJECT_DIR"

if [[ ! -d .git ]]; then
    echo "Git metadata not found. Restoring repository connection..."

    git init
    git remote remove origin 2>/dev/null || true
    git remote add origin git@github.com:rlavrinenko/ShieldNet.git
    git fetch origin main
    git branch -M main
    git reset --mixed origin/main
fi

echo
echo "Поточні зміни:"
git status --short

if [[ -z "$(git status --porcelain)" ]]; then
    echo
    echo "Немає змін для завантаження."
    exit 0
fi

echo
read -r -p "Введіть назву коміту: " COMMIT_MESSAGE

if [[ -z "${COMMIT_MESSAGE// }" ]]; then
    echo "Помилка: назва коміту не може бути порожньою."
    exit 1
fi

echo
echo "Додавання файлів..."

git add \
    backend \
    bot \
    scheduler \
    admin-frontend \
    tools \
    alembic.ini \
    README.md \
    .gitignore \
    2>/dev/null || git add .

echo
echo "Створення коміту..."
git commit -m "$COMMIT_MESSAGE"

echo
echo "Синхронізація з GitHub..."
git pull --rebase origin main
git push origin main

echo
echo "========================================"
echo "ShieldNet успішно завантажено на GitHub"
echo "========================================"
