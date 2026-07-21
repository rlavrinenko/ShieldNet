import discord
import httpx
from bot.config import settings


class MemberActionWorker:
    def __init__(self, bot: discord.Client) -> None:
        self.bot = bot
        self.base_url = settings.backend_url.rstrip("/")
        self.headers = {"X-ShieldNet-Service-Token": settings.internal_service_token}

    async def fetch(self, guild_id: int) -> list[dict]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/internal/discord/guilds/{guild_id}/member-actions",
                headers=self.headers,
            )
        response.raise_for_status()
        return response.json().get("items", [])

    async def report(self, action_id: str, ok: bool, message: str) -> None:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/internal/discord/guilds/member-actions/{action_id}/result",
                headers=self.headers,
                json={
                    "status": "completed" if ok else "failed",
                    "result_message": message,
                },
            )
        response.raise_for_status()

    async def execute(self, guild: discord.Guild, action: dict) -> None:
        action_id = str(action["id"])
        user_id = int(action["discord_user_id"])
        kind = str(action["action_type"])
        payload = action.get("payload") or {}

        try:
            member = guild.get_member(user_id)
            if member is None and kind not in {"send_dm", "ban"}:
                member = await guild.fetch_member(user_id)

            if kind == "send_dm":
                user = member or await self.bot.fetch_user(user_id)
                await user.send(str(payload.get("message") or ""))
                message = "DM sent."
            elif kind == "rename":
                await member.edit(nick=payload.get("nickname"), reason="ShieldNet")
                message = "Nickname changed."
            elif kind == "kick":
                await member.kick(reason=str(payload.get("reason") or "ShieldNet"))
                message = "Member kicked."
            elif kind == "ban":
                target = member or discord.Object(id=user_id)
                await guild.ban(target, reason=str(payload.get("reason") or "ShieldNet"))
                message = "Member banned."
            elif kind in {"add_role", "remove_role"}:
                role = guild.get_role(int(payload["role_id"]))
                if role is None:
                    raise RuntimeError("Role not found.")
                if kind == "add_role":
                    await member.add_roles(role, reason="ShieldNet")
                    message = "Role added."
                else:
                    await member.remove_roles(role, reason="ShieldNet")
                    message = "Role removed."
            else:
                message = "No Discord-side action required."

            await self.report(action_id, True, message)
        except Exception as exc:
            await self.report(action_id, False, str(exc)[:1000])
