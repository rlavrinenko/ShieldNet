#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="/opt/shieldnet"
BRANCH="main"
REMOTE="origin"

cd "$PROJECT_DIR" || {
    echo "Помилка: каталог $PROJECT_DIR не знайдено."
    exit 1
}

echo "========================================"
echo " ShieldNet → GitHub"
echo "========================================"

if [ ! -d ".git" ]; then
    echo "Помилка: $PROJECT_DIR не є Git-репозиторієм."
    exit 1
fi

echo
git status --short
echo

read -r -p "Введіть назву коміту: " COMMIT_MESSAGE

if [ -z "${COMMIT_MESSAGE// }" ]; then
    echo "Помилка: назва коміту не може бути порожньою."
    exit 1
fi

echo
echo "Додавання змін..."
git add --all

if git diff --cached --quiet; then
    echo "Немає змін для створення коміту."
    exit 0
fi

echo "Створення коміту..."
git commit -m "$COMMIT_MESSAGE"

echo "Перевірка змін на GitHub..."
git pull --rebase "$REMOTE" "$BRANCH"

echo "Завантаження на GitHub..."
git push "$REMOTE" "$BRANCH"

echo
echo "Готово."
echo "Коміт: $COMMIT_MESSAGE"
echo "Гілка: $BRANCH"
