#!/usr/bin/env bash
set -Eeuo pipefail
systemctl status shieldnet-bot --no-pager -l
journalctl -u shieldnet-bot -n 80 --no-pager
sudo -u postgres psql -d shieldnet -P pager=off -c "SELECT guild_id,name,owner_discord_id,status,bot_status,last_sync_at FROM discord.guilds ORDER BY name;"
