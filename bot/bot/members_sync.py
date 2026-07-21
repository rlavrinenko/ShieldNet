from datetime import UTC, datetime
import discord
import httpx
from bot.config import settings


class MemberSyncClient:
    def __init__(self) -> None:
        self.base_url = settings.backend_url.rstrip("/")
        self.headers = {"X-ShieldNet-Service-Token": settings.internal_service_token}

    @staticmethod
    def serialize(member: discord.Member) -> dict:
        activity = member.activity
        voice_channel = member.voice.channel if member.voice and member.voice.channel else None
        client_status = member.client_status
        return {
            "discord_user_id": member.id,
            "username": member.name,
            "global_name": member.global_name,
            "nickname": member.nick,
            "avatar_url": str(member.display_avatar.url),
            "bot": member.bot,
            "pending": member.pending,
            "joined_at": member.joined_at.isoformat() if member.joined_at else None,
            "communication_disabled_until": member.timed_out_until.isoformat() if member.timed_out_until else None,
            "presence_status": str(member.status),
            "activity_type": str(activity.type).split(".")[-1] if activity else None,
            "activity_name": getattr(activity, "name", None) if activity else None,
            "voice_channel_id": voice_channel.id if voice_channel else None,
            "voice_channel_name": voice_channel.name if voice_channel else None,
            "client_desktop": str(client_status.desktop) != "offline",
            "client_mobile": str(client_status.mobile) != "offline",
            "client_web": str(client_status.web) != "offline",
            "last_presence_at": datetime.now(UTC).isoformat(),
            "roles": [{
                "discord_role_id": role.id,
                "role_name": role.name,
                "role_position": role.position,
                "role_color": role.color.value,
            } for role in member.roles if not role.is_default()],
        }

    async def full_sync(self, guild: discord.Guild) -> None:
        members = [member async for member in guild.fetch_members(limit=None)]
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/internal/discord/guilds/{guild.id}/members/sync",
                headers=self.headers,
                json={"members": [self.serialize(m) for m in members], "complete_snapshot": True},
            )
        response.raise_for_status()

    async def sync_member(self, member: discord.Member) -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/internal/discord/guilds/{member.guild.id}/members/sync",
                headers=self.headers,
                json={"members": [self.serialize(member)], "complete_snapshot": False},
            )
        response.raise_for_status()

    async def mark_left(self, guild_id: int, user_id: int) -> None:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/internal/discord/guilds/{guild_id}/members/left",
                headers=self.headers,
                json={"discord_user_id": user_id, "left_at": datetime.now(UTC).isoformat()},
            )
        response.raise_for_status()

    async def mark_activity(self, guild_id: int, user_id: int) -> None:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/internal/discord/guilds/{guild_id}/members/activity",
                headers=self.headers,
                json={"discord_user_id": user_id, "activity_at": datetime.now(UTC).isoformat()},
            )
        response.raise_for_status()
