import httpx
from bot.config import settings


class BackendClient:
    def __init__(self) -> None:
        self.base_url = settings.backend_url.rstrip("/")
        self.headers = {
            "X-ShieldNet-Service-Token": settings.internal_service_token,
            "Content-Type": "application/json",
        }

    async def register_guild(self, guild) -> None:
        payload = {
            "guild_id": guild.id,
            "name": guild.name,
            "icon_url": str(guild.icon.url) if guild.icon else None,
            "owner_discord_id": guild.owner_id,
            "member_count": guild.member_count or 0,
            "preferred_language": settings.default_language,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/internal/discord/guilds/register",
                headers=self.headers,
                json=payload,
            )
        response.raise_for_status()

    async def mark_guild_left(self, guild_id: int) -> None:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/internal/discord/guilds/left",
                headers=self.headers,
                json={"guild_id": guild_id},
            )
        response.raise_for_status()

    async def get_guild_modules(self, guild_id: int) -> dict:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/internal/modules/guilds/{guild_id}",
                headers=self.headers,
            )
        response.raise_for_status()
        return response.json()

    async def heartbeat(self, *, worker_name: str, worker_type: str, status: str, metadata: dict | None = None) -> None:
        payload = {
            "worker_name": worker_name,
            "worker_type": worker_type,
            "status": status,
            "metadata": metadata or {},
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/internal/runtime/heartbeat",
                headers=self.headers,
                json=payload,
            )
        response.raise_for_status()
