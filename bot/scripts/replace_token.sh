#!/usr/bin/env bash
set -Eeuo pipefail
[[ $EUID -eq 0 ]] || { echo "Run as root"; exit 1; }
read -r -s -p "New Discord Bot Token: " TOKEN; echo
sed -i "s|^SHIELDNET_DISCORD_BOT_TOKEN=.*|SHIELDNET_DISCORD_BOT_TOKEN=${TOKEN}|" /etc/shieldnet/bot/bot.env
systemctl restart shieldnet-bot
