from fastapi import APIRouter,Depends
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.internal import verify_internal_service_token
from app.db.session import get_db_session
from app.models.explorer import GuildChannel,GuildWebhook,GuildEmoji,GuildInvite,ChannelPermissionOverwrite
from app.schemas.explorer import ExplorerSyncRequest
router=APIRouter(prefix="/internal/discord/guilds",tags=["Internal Explorer"],dependencies=[Depends(verify_internal_service_token)])
@router.post("/{guild_id}/explorer/sync")
async def sync_explorer(guild_id:int,payload:ExplorerSyncRequest,session:AsyncSession=Depends(get_db_session)):
 for model in (ChannelPermissionOverwrite,GuildChannel,GuildWebhook,GuildEmoji,GuildInvite): await session.execute(delete(model).where(model.guild_id==guild_id))
 for x in payload.channels: session.add(GuildChannel(guild_id=guild_id,**x.model_dump()))
 for x in payload.webhooks: session.add(GuildWebhook(guild_id=guild_id,**x.model_dump()))
 for x in payload.emojis: session.add(GuildEmoji(guild_id=guild_id,**x.model_dump()))
 for x in payload.invites: session.add(GuildInvite(guild_id=guild_id,**x.model_dump()))
 for x in payload.permission_overwrites: session.add(ChannelPermissionOverwrite(guild_id=guild_id,**x.model_dump()))
 await session.commit(); return {"status":"synchronized","counts":{"channels":len(payload.channels),"webhooks":len(payload.webhooks),"emojis":len(payload.emojis),"invites":len(payload.invites),"permission_overwrites":len(payload.permission_overwrites)}}
