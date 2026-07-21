from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.guild_access import require_guild_management
from app.db.session import get_db_session
from app.models.core import User
from app.models.discord import Guild
from app.models.explorer import ChannelPermissionOverwrite, GuildChannel
from app.models.guild_roles import DiscordGuildRole
from app.models.members import DiscordMember, DiscordMemberRole

router = APIRouter(tags=["Permission Simulator"])

PERMISSIONS: list[tuple[int, str, str]] = [
    (0, "create_instant_invite", "Create Invite"),
    (1, "kick_members", "Kick Members"),
    (2, "ban_members", "Ban Members"),
    (3, "administrator", "Administrator"),
    (4, "manage_channels", "Manage Channels"),
    (5, "manage_guild", "Manage Server"),
    (6, "add_reactions", "Add Reactions"),
    (7, "view_audit_log", "View Audit Log"),
    (8, "priority_speaker", "Priority Speaker"),
    (9, "stream", "Video"),
    (10, "view_channel", "View Channel"),
    (11, "send_messages", "Send Messages"),
    (12, "send_tts_messages", "Send TTS Messages"),
    (13, "manage_messages", "Manage Messages"),
    (14, "embed_links", "Embed Links"),
    (15, "attach_files", "Attach Files"),
    (16, "read_message_history", "Read Message History"),
    (17, "mention_everyone", "Mention Everyone"),
    (18, "use_external_emojis", "Use External Emojis"),
    (20, "connect", "Connect"),
    (21, "speak", "Speak"),
    (22, "mute_members", "Mute Members"),
    (23, "deafen_members", "Deafen Members"),
    (24, "move_members", "Move Members"),
    (25, "use_vad", "Use Voice Activity"),
    (27, "change_nickname", "Change Nickname"),
    (28, "manage_nicknames", "Manage Nicknames"),
    (29, "manage_roles", "Manage Roles"),
    (30, "manage_webhooks", "Manage Webhooks"),
    (31, "manage_expressions", "Manage Expressions"),
    (34, "manage_threads", "Manage Threads"),
    (35, "create_public_threads", "Create Public Threads"),
    (36, "create_private_threads", "Create Private Threads"),
    (37, "use_external_stickers", "Use External Stickers"),
    (38, "send_messages_in_threads", "Send Messages in Threads"),
    (39, "use_embedded_activities", "Use Activities"),
    (40, "moderate_members", "Timeout Members"),
    (41, "view_creator_monetization_analytics", "View Monetization Analytics"),
    (42, "use_soundboard", "Use Soundboard"),
    (43, "create_expressions", "Create Expressions"),
    (44, "create_events", "Create Events"),
    (45, "use_external_sounds", "Use External Sounds"),
    (46, "send_voice_messages", "Send Voice Messages"),
    (49, "send_polls", "Send Polls"),
]
ALL_KNOWN = sum(1 << bit for bit, _, _ in PERMISSIONS)
ADMINISTRATOR = 1 << 3


def permission_rows(value: int) -> list[dict]:
    return [
        {"key": key, "label": label, "bit": bit, "allowed": bool(value & (1 << bit))}
        for bit, key, label in PERMISSIONS
    ]


@router.get("/discord/guilds/{guild_id}/permission-simulator/options")
async def simulator_options(
    guild_id: int,
    q: str = Query(default="", max_length=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    await require_guild_management(session, current_user, guild_id)
    member_stmt = select(DiscordMember).where(DiscordMember.guild_id == guild_id, DiscordMember.is_active.is_(True))
    if q.strip():
        pattern = f"%{q.strip()}%"
        member_stmt = member_stmt.where(or_(DiscordMember.username.ilike(pattern), DiscordMember.global_name.ilike(pattern), DiscordMember.nickname.ilike(pattern)))
    member_stmt = member_stmt.order_by(DiscordMember.username).limit(100)
    members = (await session.execute(member_stmt)).scalars().all()
    channels = (await session.execute(select(GuildChannel).where(GuildChannel.guild_id == guild_id).order_by(GuildChannel.position, GuildChannel.name))).scalars().all()
    return {
        "members": [{"id": str(x.discord_user_id), "username": x.username, "display_name": x.nickname or x.global_name or x.username, "avatar_url": x.avatar_url, "bot": x.bot} for x in members],
        "channels": [{"id": str(x.discord_channel_id), "name": x.name, "type": x.channel_type, "parent_id": str(x.parent_id) if x.parent_id else None} for x in channels],
    }


@router.get("/discord/guilds/{guild_id}/permission-simulator/check")
async def simulate_permissions(
    guild_id: int,
    member_id: int,
    channel_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    await require_guild_management(session, current_user, guild_id)
    guild = (await session.execute(select(Guild).where(Guild.guild_id == guild_id))).scalar_one_or_none()
    member = (await session.execute(select(DiscordMember).where(DiscordMember.guild_id == guild_id, DiscordMember.discord_user_id == member_id))).scalar_one_or_none()
    channel = (await session.execute(select(GuildChannel).where(GuildChannel.guild_id == guild_id, GuildChannel.discord_channel_id == channel_id))).scalar_one_or_none()
    if not guild or not member or not channel:
        raise HTTPException(status_code=404, detail="Guild, member or channel not found")

    member_role_rows = (await session.execute(select(DiscordMemberRole).where(DiscordMemberRole.member_id == member.id))).scalars().all()
    member_role_ids = {x.discord_role_id for x in member_role_rows}
    roles = (await session.execute(select(DiscordGuildRole).where(DiscordGuildRole.guild_id == guild_id))).scalars().all()
    role_map = {x.discord_role_id: x for x in roles}
    everyone = role_map.get(guild_id)

    base = everyone.permissions if everyone else 0
    sources: list[dict] = []
    if everyone:
        sources.append({"stage": "base", "effect": "allow", "source": "@everyone", "permissions": everyone.permissions})
    for role_id in member_role_ids:
        role = role_map.get(role_id)
        if role:
            base |= role.permissions
            sources.append({"stage": "role", "effect": "allow", "source": role.name, "source_id": str(role.discord_role_id), "permissions": role.permissions})

    is_owner = member.discord_user_id == guild.owner_discord_id
    has_admin = bool(base & ADMINISTRATOR)
    if is_owner or has_admin:
        effective = ALL_KNOWN
        sources.append({"stage": "bypass", "effect": "allow", "source": "Server owner" if is_owner else "Administrator permission", "permissions": ALL_KNOWN})
    else:
        effective = base
        channel_ids = [channel.discord_channel_id]
        if channel.parent_id:
            channel_ids.append(channel.parent_id)
        overwrite_rows = (await session.execute(
            select(ChannelPermissionOverwrite).where(
                ChannelPermissionOverwrite.guild_id == guild_id,
                ChannelPermissionOverwrite.discord_channel_id.in_(channel_ids),
            )
        )).scalars().all()
        own = [x for x in overwrite_rows if x.discord_channel_id == channel.discord_channel_id]
        if not own and channel.parent_id:
            own = [x for x in overwrite_rows if x.discord_channel_id == channel.parent_id]

        everyone_ow = next((x for x in own if x.target_type == "role" and x.target_id == guild_id), None)
        if everyone_ow:
            effective &= ~everyone_ow.deny_permissions
            effective |= everyone_ow.allow_permissions
            sources.append({"stage": "channel_everyone", "effect": "mixed", "source": "@everyone overwrite", "allow": everyone_ow.allow_permissions, "deny": everyone_ow.deny_permissions})

        role_ows = [x for x in own if x.target_type == "role" and x.target_id in member_role_ids]
        role_deny = 0
        role_allow = 0
        for ow in role_ows:
            role_deny |= ow.deny_permissions
            role_allow |= ow.allow_permissions
        if role_ows:
            effective &= ~role_deny
            effective |= role_allow
            sources.append({"stage": "channel_roles", "effect": "mixed", "source": "Role overwrites", "allow": role_allow, "deny": role_deny, "count": len(role_ows)})

        member_ow = next((x for x in own if x.target_type == "member" and x.target_id == member.discord_user_id), None)
        if member_ow:
            effective &= ~member_ow.deny_permissions
            effective |= member_ow.allow_permissions
            sources.append({"stage": "channel_member", "effect": "mixed", "source": "Member overwrite", "allow": member_ow.allow_permissions, "deny": member_ow.deny_permissions})

    return {
        "guild_id": str(guild_id),
        "member": {"id": str(member.discord_user_id), "username": member.username, "display_name": member.nickname or member.global_name or member.username, "avatar_url": member.avatar_url, "owner": is_owner},
        "channel": {"id": str(channel.discord_channel_id), "name": channel.name, "type": channel.channel_type, "parent_id": str(channel.parent_id) if channel.parent_id else None},
        "base_permissions": str(base),
        "effective_permissions": str(effective),
        "administrator_bypass": has_admin,
        "owner_bypass": is_owner,
        "permissions": permission_rows(effective),
        "sources": sources,
        "role_count": len(member_role_ids),
        "snapshot_complete": channel.permissions_synced,
    }
