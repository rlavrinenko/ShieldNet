from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.guild_access import require_guild_management
from app.db.session import get_db_session
from app.models.core import User
from app.models.discord import Guild
from app.models.explorer import ChannelPermissionOverwrite, GuildChannel, GuildEmoji, GuildWebhook
from app.models.guild_roles import DiscordGuildRole

router = APIRouter(tags=["Server Diff"])


def _keyed(rows: Iterable[Any], key_fn) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for row in rows:
        key = str(key_fn(row)).strip().casefold()
        if key:
            result[key] = row
    return result


def _change(kind: str, name: str, source: Any = None, target: Any = None, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"kind": kind, "name": name, "source": source, "target": target, "details": details or {}}


async def _guild(session: AsyncSession, guild_id: int) -> Guild:
    guild = (await session.execute(select(Guild).where(Guild.guild_id == guild_id))).scalar_one_or_none()
    if guild is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guild not found")
    return guild


async def _rows(session: AsyncSession, model: Any, guild_id: int) -> list[Any]:
    return list((await session.execute(select(model).where(model.guild_id == guild_id))).scalars().all())


@router.get("/discord/server-diff/options")
async def server_diff_options(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    # SuperAdmin sees all registered guilds. Other users only see guilds with active membership.
    from app.services.global_access import GlobalAccessService
    from app.models.discord import GuildMembership, MembershipStatus

    if GlobalAccessService.is_superadmin(current_user):
        query = select(Guild).order_by(Guild.name.asc())
    else:
        query = (
            select(Guild)
            .join(GuildMembership, GuildMembership.guild_id == Guild.guild_id)
            .where(GuildMembership.user_id == current_user.id, GuildMembership.status == MembershipStatus.ACTIVE)
            .order_by(Guild.name.asc())
        )
    guilds = list((await session.execute(query)).scalars().all())
    return [{"guild_id": g.guild_id, "name": g.name, "icon_url": g.icon_url, "member_count": g.member_count, "bot_status": g.bot_status.value} for g in guilds]


@router.get("/discord/server-diff/compare")
async def compare_servers(
    source_guild_id: int = Query(...),
    target_guild_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    if source_guild_id == target_guild_id:
        raise HTTPException(status_code=400, detail="Choose two different servers")

    await require_guild_management(session, current_user, source_guild_id)
    await require_guild_management(session, current_user, target_guild_id)
    source_guild = await _guild(session, source_guild_id)
    target_guild = await _guild(session, target_guild_id)

    source_roles, target_roles = await _rows(session, DiscordGuildRole, source_guild_id), await _rows(session, DiscordGuildRole, target_guild_id)
    source_channels, target_channels = await _rows(session, GuildChannel, source_guild_id), await _rows(session, GuildChannel, target_guild_id)
    source_webhooks, target_webhooks = await _rows(session, GuildWebhook, source_guild_id), await _rows(session, GuildWebhook, target_guild_id)
    source_emojis, target_emojis = await _rows(session, GuildEmoji, source_guild_id), await _rows(session, GuildEmoji, target_guild_id)
    source_overwrites, target_overwrites = await _rows(session, ChannelPermissionOverwrite, source_guild_id), await _rows(session, ChannelPermissionOverwrite, target_guild_id)

    sections: list[dict[str, Any]] = []

    def compare_named(section: str, source_rows: list[Any], target_rows: list[Any], key_fn, serialize_fn, compare_fields: list[str]):
        sm, tm = _keyed(source_rows, key_fn), _keyed(target_rows, key_fn)
        changes: list[dict[str, Any]] = []
        for key in sorted(set(sm) | set(tm)):
            s, t = sm.get(key), tm.get(key)
            if s is None:
                changes.append(_change("target_only", key_fn(t), target=serialize_fn(t)))
            elif t is None:
                changes.append(_change("source_only", key_fn(s), source=serialize_fn(s)))
            else:
                sd, td = serialize_fn(s), serialize_fn(t)
                changed = {field: {"source": sd.get(field), "target": td.get(field)} for field in compare_fields if sd.get(field) != td.get(field)}
                if changed:
                    changes.append(_change("changed", key_fn(s), source=sd, target=td, details=changed))
        sections.append({"name": section, "source_count": len(source_rows), "target_count": len(target_rows), "difference_count": len(changes), "changes": changes})

    compare_named(
        "Roles", source_roles, target_roles, lambda r: r.name,
        lambda r: {"id": r.discord_role_id, "name": r.name, "position": r.position, "color": r.color, "permissions": r.permissions, "managed": r.managed},
        ["position", "color", "permissions", "managed"],
    )
    compare_named(
        "Channels", source_channels, target_channels, lambda c: f"{c.channel_type}:{c.name}",
        lambda c: {"id": c.discord_channel_id, "name": c.name, "type": c.channel_type, "position": c.position, "parent_id": c.parent_id, "nsfw": c.nsfw, "topic": c.topic},
        ["position", "nsfw", "topic"],
    )
    compare_named(
        "Webhooks", source_webhooks, target_webhooks, lambda w: w.name or str(w.discord_webhook_id),
        lambda w: {"id": w.discord_webhook_id, "name": w.name, "type": w.webhook_type, "channel_id": w.channel_id, "owner_id": w.owner_id},
        ["type"],
    )
    compare_named(
        "Emojis", source_emojis, target_emojis, lambda e: e.name,
        lambda e: {"id": e.discord_emoji_id, "name": e.name, "animated": e.animated, "managed": e.managed, "available": e.available},
        ["animated", "managed", "available"],
    )

    # Overwrites are summarized because Discord IDs differ between servers.
    def overwrite_summary(rows: list[ChannelPermissionOverwrite]) -> dict[str, int]:
        return {
            "total": len(rows),
            "role_targets": sum(1 for r in rows if r.target_type == "role"),
            "member_targets": sum(1 for r in rows if r.target_type == "member"),
            "allow_rules": sum(1 for r in rows if int(r.allow_permissions or 0) != 0),
            "deny_rules": sum(1 for r in rows if int(r.deny_permissions or 0) != 0),
        }

    so, to = overwrite_summary(source_overwrites), overwrite_summary(target_overwrites)
    overwrite_changes = [] if so == to else [_change("changed", "Permission overwrite summary", source=so, target=to)]
    sections.append({"name": "Permission overwrites", "source_count": so["total"], "target_count": to["total"], "difference_count": len(overwrite_changes), "changes": overwrite_changes})

    total_differences = sum(section["difference_count"] for section in sections)
    similarity_base = max(1, sum(max(section["source_count"], section["target_count"]) for section in sections))
    similarity = max(0, round(100 - (total_differences / similarity_base * 100)))

    return {
        "source": {"guild_id": source_guild.guild_id, "name": source_guild.name, "icon_url": source_guild.icon_url, "member_count": source_guild.member_count, "last_sync_at": source_guild.last_sync_at},
        "target": {"guild_id": target_guild.guild_id, "name": target_guild.name, "icon_url": target_guild.icon_url, "member_count": target_guild.member_count, "last_sync_at": target_guild.last_sync_at},
        "summary": {"total_differences": total_differences, "similarity_percent": similarity, "sections_with_differences": sum(1 for s in sections if s["difference_count"] > 0)},
        "sections": sections,
    }
