from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.backups import GuildBackup
from app.models.discord import Guild
from app.models.explorer import ChannelPermissionOverwrite, GuildChannel, GuildEmoji, GuildWebhook
from app.models.guild_roles import DiscordGuildRole
from app.models.modules import GuildModule, ModuleCatalog
from app.models.permissions import GuildPermissionRule
from app.models.verification import VerificationSettings


def _enum(value: Any) -> Any:
    return getattr(value, "value", value)


class BackupService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _all(self, model: Any, guild_id: int) -> list[Any]:
        return list((await self.session.execute(select(model).where(model.guild_id == guild_id))).scalars().all())

    async def build_snapshot(self, guild_id: int) -> dict[str, Any]:
        guild = (await self.session.execute(select(Guild).where(Guild.guild_id == guild_id))).scalar_one()
        roles = await self._all(DiscordGuildRole, guild_id)
        channels = await self._all(GuildChannel, guild_id)
        overwrites = await self._all(ChannelPermissionOverwrite, guild_id)
        webhooks = await self._all(GuildWebhook, guild_id)
        emojis = await self._all(GuildEmoji, guild_id)
        permissions = await self._all(GuildPermissionRule, guild_id)
        modules = list((await self.session.execute(
            select(GuildModule, ModuleCatalog).join(ModuleCatalog, ModuleCatalog.id == GuildModule.module_id).where(GuildModule.guild_id == guild_id)
        )).all())
        verification = (await self.session.execute(select(VerificationSettings).where(VerificationSettings.guild_id == guild_id))).scalar_one_or_none()

        return {
            "format_version": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "guild": {"guild_id": guild.guild_id, "name": guild.name, "owner_discord_id": guild.owner_discord_id, "preferred_language": guild.preferred_language},
            "roles": [{"discord_role_id": x.discord_role_id, "name": x.name, "position": x.position, "color": x.color, "permissions": x.permissions, "managed": x.managed, "assignable": x.assignable} for x in roles],
            "channels": [{"discord_channel_id": x.discord_channel_id, "parent_id": x.parent_id, "name": x.name, "channel_type": x.channel_type, "position": x.position, "nsfw": x.nsfw, "topic": x.topic} for x in channels],
            "permission_overwrites": [{"discord_channel_id": x.discord_channel_id, "target_id": x.target_id, "target_type": x.target_type, "allow_permissions": x.allow_permissions, "deny_permissions": x.deny_permissions} for x in overwrites],
            "webhooks": [{"discord_webhook_id": x.discord_webhook_id, "channel_id": x.channel_id, "name": x.name, "webhook_type": x.webhook_type, "owner_id": x.owner_id} for x in webhooks],
            "emojis": [{"discord_emoji_id": x.discord_emoji_id, "name": x.name, "animated": x.animated, "managed": x.managed, "available": x.available} for x in emojis],
            "verification": None if verification is None else {"enabled": verification.enabled, "verified_role_id": verification.verified_role_id, "review_channel_id": verification.review_channel_id, "nickname_template": verification.nickname_template, "auto_approve": verification.auto_approve, "alliance_min_length": verification.alliance_min_length, "alliance_max_length": verification.alliance_max_length},
            "modules": [{"module_key": catalog.module_key, "enabled": item.enabled, "configuration": item.configuration, "revision": item.revision} for item, catalog in modules],
            "permission_rules": [{"module_key": x.module_key, "permission": _enum(x.permission), "effect": _enum(x.effect), "subject_type": x.subject_type, "subject_value": x.subject_value, "enabled": x.enabled, "priority": x.priority} for x in permissions],
        }

    async def create(self, guild_id: int, name: str, description: str | None, user_id: UUID | None) -> GuildBackup:
        snapshot = await self.build_snapshot(guild_id)
        raw = json.dumps(snapshot, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        count = sum(len(snapshot.get(key, [])) for key in ("roles", "channels", "permission_overwrites", "webhooks", "emojis", "modules", "permission_rules"))
        item = GuildBackup(guild_id=guild_id, name=name.strip(), description=description, object_count=count, size_bytes=len(raw), snapshot=snapshot, created_by=user_id)
        self.session.add(item)
        await self.session.flush()
        return item

    async def get(self, backup_id: UUID, guild_id: int) -> GuildBackup | None:
        return (await self.session.execute(select(GuildBackup).where(GuildBackup.id == backup_id, GuildBackup.guild_id == guild_id))).scalar_one_or_none()

    async def list(self, guild_id: int) -> list[GuildBackup]:
        return list((await self.session.execute(select(GuildBackup).where(GuildBackup.guild_id == guild_id).order_by(GuildBackup.created_at.desc()))).scalars().all())

    async def remove(self, backup_id: UUID, guild_id: int) -> bool:
        result = await self.session.execute(delete(GuildBackup).where(GuildBackup.id == backup_id, GuildBackup.guild_id == guild_id))
        return bool(result.rowcount)

    async def restore_plan(self, backup: GuildBackup) -> dict[str, Any]:
        current = await self.build_snapshot(backup.guild_id)
        stored = backup.snapshot
        sections = []
        for key in ("roles", "channels", "permission_overwrites", "emojis", "modules", "permission_rules"):
            before, after = len(current.get(key, [])), len(stored.get(key, []))
            sections.append({"section": key, "current": before, "backup": after, "delta": after-before})
        return {
            "mode": "dry_run",
            "safe_to_apply": False,
            "message": "Dry-run only. Discord object restoration requires explicit Worker execution and ID remapping.",
            "backup_id": str(backup.id),
            "guild_id": backup.guild_id,
            "sections": sections,
            "warnings": [
                "Managed roles and webhooks cannot be recreated automatically.",
                "Discord IDs change when roles or channels are recreated.",
                "Permission overwrites require role and channel ID remapping.",
            ],
        }
