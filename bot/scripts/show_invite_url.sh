#!/usr/bin/env bash
set -Eeuo pipefail
APP_ID="$(grep '^SHIELDNET_DISCORD_APPLICATION_ID=' /etc/shieldnet/bot/bot.env | cut -d= -f2-)"
echo "https://discord.com/oauth2/authorize?client_id=${APP_ID}&permissions=0&scope=bot%20applications.commands"
