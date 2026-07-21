import uuid
from datetime import UTC, datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.auth import get_current_user
from app.api.dependencies.guild_access import require_guild_management
from app.db.session import get_db_session
from app.models.core import User
from app.models.discord import Guild
from app.models.verification import VerificationSettings
from app.models.leadership import LeadershipApplicationSettings
from app.models.role_channel_management import DiscordStructureChange
from app.models.setup_wizard import SetupItem, SetupSession
from app.schemas.setup_wizard import SetupApplyRequest, SetupCreateRequest, SetupImportRequest

router = APIRouter(tags=["Server Setup Wizard"])

TEMPLATES = {
    "minimal": [
        ("verified_role", "role", "✅ Verified", {"name": "✅ Verified", "color": 5763719}),
        ("verify_channel", "channel", "✅-verify", {"name": "✅-verify", "channel_type": "text"}),
    ],
    "standard": [
        ("verified_role", "role", "✅ Verified", {"name": "✅ Verified", "color": 5763719}),
        ("r5_role", "role", "⭐ R5 Verified", {"name": "⭐ R5 Verified", "color": 15844367}),
        ("r4_role", "role", "🛡️ R4 Verified", {"name": "🛡️ R4 Verified", "color": 3447003}),
        ("shieldnet_category", "category", "SHIELDNET", {"name": "SHIELDNET"}),
        ("verify_channel", "channel", "✅-verify", {"name": "✅-verify", "channel_type": "text"}),
        ("leadership_channel", "channel", "📝-apply-r5-r4", {"name": "📝-apply-r5-r4", "channel_type": "text"}),
        ("moderation_channel", "channel", "🛡️-moderation-log", {"name": "🛡️-moderation-log", "channel_type": "text"}),
    ],
    "full": [
        ("verified_role", "role", "✅ Verified", {"name": "✅ Verified", "color": 5763719}),
        ("r5_role", "role", "⭐ R5 Verified", {"name": "⭐ R5 Verified", "color": 15844367}),
        ("r4_role", "role", "🛡️ R4 Verified", {"name": "🛡️ R4 Verified", "color": 3447003}),
        ("shieldnet_category", "category", "SHIELDNET", {"name": "SHIELDNET"}),
        ("welcome_channel", "channel", "👋-welcome", {"name": "👋-welcome", "channel_type": "text"}),
        ("verify_channel", "channel", "✅-verify", {"name": "✅-verify", "channel_type": "text"}),
        ("leadership_channel", "channel", "📝-apply-r5-r4", {"name": "📝-apply-r5-r4", "channel_type": "text"}),
        ("language_channel", "channel", "🌍-choose-language", {"name": "🌍-choose-language", "channel_type": "text"}),
        ("moderation_channel", "channel", "🛡️-moderation-log", {"name": "🛡️-moderation-log", "channel_type": "text"}),
        ("audit_channel", "channel", "📋-audit-log", {"name": "📋-audit-log", "channel_type": "text"}),
    ],
}

def serialize(session, items):
    return {
        "id": str(session.id), "guild_id": session.guild_id, "status": session.status,
        "template_key": session.template_key, "preferred_language": session.preferred_language,
        "features": session.features, "diagnostics": session.diagnostics,
        "configuration": session.configuration, "created_at": session.created_at,
        "updated_at": session.updated_at, "completed_at": session.completed_at,
        "items": [{
            "id": str(x.id), "item_key": x.item_key, "object_type": x.object_type,
            "display_name": x.display_name, "payload": x.payload, "required": x.required,
            "position": x.position, "change_id": str(x.change_id) if x.change_id else None,
            "status": x.status, "discord_object_id": x.discord_object_id,
            "error_message": x.error_message,
        } for x in items],
    }

@router.get("/discord/guilds/{guild_id}/setup/diagnostics")
async def diagnostics(guild_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    await require_guild_management(db, current_user, guild_id)
    guild = await db.get(Guild, guild_id)
    if not guild: raise HTTPException(404, "Guild not found")
    return {
        "guild_registered": True, "bot_online": str(guild.bot_status.value if hasattr(guild.bot_status, "value") else guild.bot_status) == "online",
        "member_count": guild.member_count, "last_sync_at": guild.last_sync_at,
        "required_bot_permissions": ["manage_roles", "manage_channels", "manage_nicknames", "view_audit_log", "send_messages"],
        "note": "Discord permission details are verified during execution by the bot.",
    }

@router.post("/discord/guilds/{guild_id}/setup/sessions")
async def create_session(guild_id: int, payload: SetupCreateRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    await require_guild_management(db, current_user, guild_id)
    features = {
        "verification": payload.enable_verification,
        "leadership": payload.enable_leadership,
        "moderation": payload.enable_moderation,
        "welcome_channel": payload.create_welcome_channel,
        "language_channel": payload.create_language_channel,
    }
    session = SetupSession(guild_id=guild_id, template_key=payload.template_key, preferred_language=payload.preferred_language.lower(), features=features, created_by=current_user.id)
    db.add(session); await db.flush()
    template = TEMPLATES[payload.template_key]
    position = 0
    for key, kind, name, data in template:
        if key == "welcome_channel" and not payload.create_welcome_channel: continue
        if key == "language_channel" and not payload.create_language_channel: continue
        if key in {"r5_role","r4_role","leadership_channel"} and not payload.enable_leadership: continue
        if key == "moderation_channel" and not payload.enable_moderation: continue
        if key in {"verified_role","verify_channel"} and not payload.enable_verification: continue
        db.add(SetupItem(session_id=session.id, item_key=key, object_type=kind, display_name=name, payload=data, position=position))
        position += 1
    await db.commit()
    items=(await db.execute(select(SetupItem).where(SetupItem.session_id==session.id).order_by(SetupItem.position))).scalars().all()
    return serialize(session, items)

@router.get("/discord/guilds/{guild_id}/setup/sessions/{session_id}")
async def get_session(guild_id: int, session_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    await require_guild_management(db, current_user, guild_id)
    session=(await db.execute(select(SetupSession).where(SetupSession.id==session_id, SetupSession.guild_id==guild_id))).scalar_one_or_none()
    if not session: raise HTTPException(404, "Setup session not found")
    items=(await db.execute(select(SetupItem).where(SetupItem.session_id==session.id).order_by(SetupItem.position))).scalars().all()
    for item in items:
        if item.change_id:
            change=await db.get(DiscordStructureChange,item.change_id)
            if change:
                item.status=change.status
                result=(change.payload or {}).get("_result") or {}
                if result.get("role_id"): item.discord_object_id=int(result["role_id"])
                if result.get("channel_id"): item.discord_object_id=int(result["channel_id"])
                item.error_message=change.result_message
    await db.commit()
    return serialize(session,items)

@router.post("/discord/guilds/{guild_id}/setup/sessions/{session_id}/apply")
async def apply_session(guild_id: int, session_id: uuid.UUID, payload: SetupApplyRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    await require_guild_management(db,current_user,guild_id)
    session=(await db.execute(select(SetupSession).where(SetupSession.id==session_id,SetupSession.guild_id==guild_id))).scalar_one_or_none()
    if not session: raise HTTPException(404,"Setup session not found")
    if session.status not in {"draft","failed"}: raise HTTPException(409,"Setup session cannot be applied")
    items=(await db.execute(select(SetupItem).where(SetupItem.session_id==session.id).order_by(SetupItem.position))).scalars().all()
    category_change_id=None
    for item in items:
        data=dict(item.payload)
        if item.object_type=="channel" and category_change_id:
            data["_parent_change_id"]=str(category_change_id)
        change=DiscordStructureChange(guild_id=guild_id,object_type=item.object_type,operation="create",payload=data,preview={"safe_to_apply":True,"wizard":True},status="pending",requested_by=current_user.id)
        db.add(change); await db.flush()
        item.change_id=change.id; item.status="pending"
        if item.item_key=="shieldnet_category": category_change_id=change.id
    session.status="applying"
    await db.commit()
    return {"status":"applying","queued":len(items)}

@router.post("/discord/guilds/{guild_id}/setup/sessions/{session_id}/finalize")
async def finalize_session(guild_id:int,session_id:uuid.UUID,current_user:User=Depends(get_current_user),db:AsyncSession=Depends(get_db_session)):
    await require_guild_management(db,current_user,guild_id)
    session=(await db.execute(select(SetupSession).where(SetupSession.id==session_id,SetupSession.guild_id==guild_id))).scalar_one_or_none()
    if not session: raise HTTPException(404,"Setup session not found")
    items=(await db.execute(select(SetupItem).where(SetupItem.session_id==session.id))).scalars().all()
    await get_session(guild_id,session_id,current_user,db)
    if any(x.status in {"pending","processing","preview"} for x in items): raise HTTPException(409,"Setup operations are still running")
    failed=[x for x in items if x.status=="failed" and x.required]
    if failed:
        session.status="failed"; await db.commit()
        raise HTTPException(409,{"message":"Required setup items failed","items":[x.item_key for x in failed]})
    ids={x.item_key:x.discord_object_id for x in items if x.discord_object_id}
    if session.features.get("verification"):
        settings=(await db.execute(select(VerificationSettings).where(VerificationSettings.guild_id==guild_id))).scalar_one_or_none()
        if not settings: settings=VerificationSettings(guild_id=guild_id); db.add(settings)
        settings.enabled=True; settings.verified_role_id=ids.get("verified_role"); settings.review_channel_id=ids.get("verify_channel"); settings.updated_by=current_user.id
    if session.features.get("leadership"):
        settings=(await db.execute(select(LeadershipApplicationSettings).where(LeadershipApplicationSettings.guild_id==guild_id))).scalar_one_or_none()
        if not settings: settings=LeadershipApplicationSettings(guild_id=guild_id); db.add(settings)
        settings.enabled=True; settings.r5_role_id=ids.get("r5_role"); settings.r4_role_id=ids.get("r4_role"); settings.review_channel_id=ids.get("leadership_channel"); settings.updated_by=current_user.id
    guild=await db.get(Guild,guild_id)
    guild.preferred_language=session.preferred_language
    guild.status="active"
    session.configuration={"object_ids":ids,"features":session.features}
    session.status="completed"; session.completed_at=datetime.now(UTC)
    await db.commit()
    return {"status":"completed","configuration":session.configuration}

@router.get("/discord/guilds/{guild_id}/setup/export")
async def export_setup(guild_id:int,current_user:User=Depends(get_current_user),db:AsyncSession=Depends(get_db_session)):
    await require_guild_management(db,current_user,guild_id)
    verification=(await db.execute(select(VerificationSettings).where(VerificationSettings.guild_id==guild_id))).scalar_one_or_none()
    leadership=(await db.execute(select(LeadershipApplicationSettings).where(LeadershipApplicationSettings.guild_id==guild_id))).scalar_one_or_none()
    return {"version":1,"guild_id":guild_id,"verification":{"enabled":verification.enabled,"nickname_template":verification.nickname_template} if verification else None,"leadership":{"enabled":leadership.enabled,"require_evidence":leadership.require_evidence} if leadership else None}

@router.post("/discord/guilds/{guild_id}/setup/import")
async def import_setup(guild_id:int,payload:SetupImportRequest,current_user:User=Depends(get_current_user),db:AsyncSession=Depends(get_db_session)):
    await require_guild_management(db,current_user,guild_id)
    config=payload.configuration
    verification=config.get("verification")
    if verification:
        settings=(await db.execute(select(VerificationSettings).where(VerificationSettings.guild_id==guild_id))).scalar_one_or_none()
        if not settings: settings=VerificationSettings(guild_id=guild_id); db.add(settings)
        settings.enabled=bool(verification.get("enabled",False)); settings.nickname_template=str(verification.get("nickname_template","[{alliance}] {nickname}")); settings.updated_by=current_user.id
    leadership=config.get("leadership")
    if leadership:
        settings=(await db.execute(select(LeadershipApplicationSettings).where(LeadershipApplicationSettings.guild_id==guild_id))).scalar_one_or_none()
        if not settings: settings=LeadershipApplicationSettings(guild_id=guild_id); db.add(settings)
        settings.enabled=bool(leadership.get("enabled",False)); settings.require_evidence=bool(leadership.get("require_evidence",True)); settings.updated_by=current_user.id
    await db.commit()
    return {"status":"imported"}
