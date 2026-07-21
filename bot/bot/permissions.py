import discord
import httpx

from bot.config import settings


class PermissionClient:
    def __init__(self) -> None:
        self.base_url = settings.backend_url.rstrip("/")
        self.headers = {
            "X-ShieldNet-Service-Token": settings.internal_service_token,
            "Content-Type": "application/json",
        }

    async def check(
        self,
        *,
        guild_id: int,
        module_key: str,
        permission: str,
        discord_user_id: int,
        discord_role_ids: list[int],
    ) -> tuple[bool, str]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/internal/permissions/check",
                headers=self.headers,
                json={
                    "guild_id": guild_id,
                    "module_key": module_key,
                    "permission": permission,
                    "discord_user_id": discord_user_id,
                    "discord_role_ids": discord_role_ids,
                },
            )
        response.raise_for_status()
        data = response.json()
        return bool(data.get("allowed")), str(data.get("reason") or "Unknown")


async def require_permission(
    interaction: discord.Interaction,
    client: PermissionClient,
    *,
    module_key: str,
    permission: str,
) -> bool:
    if interaction.guild is None:
        await interaction.response.send_message(
            "This command is available only on a server.",
            ephemeral=True,
        )
        return False

    if not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message(
            "Unable to verify Discord roles.",
            ephemeral=True,
        )
        return False

    allowed, reason = await client.check(
        guild_id=interaction.guild.id,
        module_key=module_key,
        permission=permission,
        discord_user_id=interaction.user.id,
        discord_role_ids=[
            role.id
            for role in interaction.user.roles
            if not role.is_default()
        ],
    )

    if not allowed:
        await interaction.response.send_message(
            f"Permission denied: {reason}",
            ephemeral=True,
        )
        return False

    return True
