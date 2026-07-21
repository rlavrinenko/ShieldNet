from datetime import UTC, datetime

import discord
import httpx

from bot.config import settings


TRACKED_PERMISSIONS = (
    "administrator",
    "manage_guild",
    "manage_roles",
    "manage_channels",
    "manage_webhooks",
    "ban_members",
    "kick_members",
    "moderate_members",
    "mention_everyone",
    "view_audit_log",
)


class SecuritySyncClient:
    def __init__(self) -> None:
        self.base_url = settings.backend_url.rstrip("/")
        self.headers = {
            "X-ShieldNet-Service-Token": settings.internal_service_token,
            "Content-Type": "application/json",
        }

    @staticmethod
    def permission_map(permissions: discord.Permissions) -> dict[str, bool]:
        return {name: bool(getattr(permissions, name, False)) for name in TRACKED_PERMISSIONS}

    async def synchronize(self, guild: discord.Guild) -> None:
        members_by_role: dict[int, int] = {role.id: 0 for role in guild.roles}
        for member in guild.members:
            for role in member.roles:
                members_by_role[role.id] = members_by_role.get(role.id, 0) + 1

        roles = [
            {
                "id": role.id,
                "name": role.name,
                "position": role.position,
                "managed": role.managed,
                "is_everyone": role.is_default(),
                "member_count": members_by_role.get(role.id, 0),
                "permissions": self.permission_map(role.permissions),
            }
            for role in guild.roles
        ]

        channels = []
        everyone = guild.default_role
        for channel in guild.channels:
            perms = channel.permissions_for(everyone)
            channels.append({
                "id": channel.id,
                "name": channel.name,
                "type": "text" if isinstance(channel, discord.TextChannel) else "voice" if isinstance(channel, discord.VoiceChannel) else "category" if isinstance(channel, discord.CategoryChannel) else str(channel.type),
                "everyone_permissions": self.permission_map(perms),
            })

        webhooks = []
        me = guild.me
        if me and me.guild_permissions.manage_webhooks:
            try:
                for webhook in await guild.webhooks():
                    webhooks.append({
                        "id": webhook.id,
                        "name": webhook.name,
                        "channel_id": webhook.channel_id,
                        "user_id": webhook.user.id if webhook.user else None,
                        "type": str(webhook.type),
                    })
            except discord.Forbidden:
                pass

        payload = {
            "guild_id": guild.id,
            "collected_at": datetime.now(UTC).isoformat(),
            "roles": roles,
            "channels": channels,
            "webhooks": webhooks,
            "bot_permissions": self.permission_map(me.guild_permissions) if me else {},
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/internal/security/snapshot",
                headers=self.headers,
                json=payload,
            )
        response.raise_for_status()
