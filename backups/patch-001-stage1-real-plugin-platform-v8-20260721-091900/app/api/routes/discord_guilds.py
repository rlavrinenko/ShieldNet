from fastapi import APIRouter,Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.auth import get_current_user
from app.db.session import get_db_session
from app.models.core import User
from app.models.discord import Guild,GuildMembership,MembershipStatus
from app.schemas.discord import GuildAccessResponse
router=APIRouter(prefix='/discord',tags=['Discord'])
@router.get('/guilds',response_model=list[GuildAccessResponse])
async def list_my_guilds(current_user:User=Depends(get_current_user),session:AsyncSession=Depends(get_db_session)):
    result=await session.execute(select(Guild,GuildMembership).join(GuildMembership,GuildMembership.guild_id==Guild.guild_id).where(GuildMembership.user_id==current_user.id,GuildMembership.status==MembershipStatus.ACTIVE).order_by(Guild.name))
    return [GuildAccessResponse(guild_id=g.guild_id,name=g.name,icon_url=g.icon_url,owner_discord_id=g.owner_discord_id,member_count=g.member_count,guild_status=g.status.value,bot_status=g.bot_status.value,access_role=m.role.value) for g,m in result.all()]
