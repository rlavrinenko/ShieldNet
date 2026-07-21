#!/usr/bin/env bash
set -Eeuo pipefail
APP_USER=shieldnet-bot
APP_DIR=/opt/shieldnet/bot
CFG_DIR=/etc/shieldnet/bot
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ $EUID -eq 0 ]] || { echo "Run as root"; exit 1; }
[[ -f /etc/shieldnet/backend/backend.env ]] || { echo "Missing backend.env"; exit 1; }
INTERNAL_TOKEN="$(grep '^SHIELDNET_INTERNAL_SERVICE_TOKEN=' /etc/shieldnet/backend/backend.env | cut -d= -f2-)"
[[ -n "$INTERNAL_TOKEN" ]] || { echo "Internal token missing"; exit 1; }
read -r -p "Discord Application ID: " APP_ID
read -r -s -p "Discord Bot Token: " BOT_TOKEN; echo
[[ -n "$APP_ID" && -n "$BOT_TOKEN" ]] || { echo "Values required"; exit 1; }
id "$APP_USER" >/dev/null 2>&1 || useradd --system --home-dir "$APP_DIR" --shell /sbin/nologin "$APP_USER"
mkdir -p "$APP_DIR" "$CFG_DIR"
rsync -a --delete --exclude venv "$SRC_DIR/" "$APP_DIR/"
rm -rf "$APP_DIR/venv"
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/python" -m pip install --upgrade pip setuptools wheel
"$APP_DIR/venv/bin/python" -m pip install -r "$APP_DIR/requirements.txt"
cat > "$CFG_DIR/bot.env" <<ENV
SHIELDNET_DISCORD_BOT_TOKEN=${BOT_TOKEN}
SHIELDNET_DISCORD_APPLICATION_ID=${APP_ID}
SHIELDNET_BACKEND_URL=http://127.0.0.1:8000
SHIELDNET_INTERNAL_SERVICE_TOKEN=${INTERNAL_TOKEN}
SHIELDNET_DEFAULT_LANGUAGE=uk
SHIELDNET_SYNC_COMMANDS_ON_START=true
SHIELDNET_LOG_LEVEL=INFO
ENV
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
chown root:"$APP_USER" /etc/shieldnet "$CFG_DIR"
chmod 750 /etc/shieldnet "$CFG_DIR"
chmod 640 "$CFG_DIR/bot.env"
find "$APP_DIR/bot" -type d -exec chmod 750 {} \;
find "$APP_DIR/bot" -type f -exec chmod 640 {} \;
install -m 0644 "$APP_DIR/deploy/shieldnet-bot.service" /etc/systemd/system/shieldnet-bot.service
systemctl daemon-reload
systemctl enable --now shieldnet-bot
echo "ShieldNet Bot Worker installed"
