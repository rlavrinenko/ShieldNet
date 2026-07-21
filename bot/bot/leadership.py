import discord
import httpx
from bot.config import settings

class LeadershipSyncClient:
    def __init__(self, bot: discord.Client) -> None:
        self.bot=bot
        self.base_url=settings.backend_url.rstrip('/')
        self.headers={'X-ShieldNet-Service-Token':settings.internal_service_token}
    async def fetch_pending(self)->list[dict]:
        async with httpx.AsyncClient(timeout=20) as client:
            r=await client.get(f'{self.base_url}/api/v1/internal/leadership/pending-role-sync',headers=self.headers)
        r.raise_for_status();return r.json()
    async def report(self,application_id:str,status:str,message:str|None)->None:
        async with httpx.AsyncClient(timeout=20) as client:
            r=await client.post(f'{self.base_url}/api/v1/internal/leadership/applications/{application_id}/sync-result',headers=self.headers,json={'status':status,'message':message})
        r.raise_for_status()
    async def process(self,item:dict)->None:
        guild=self.bot.get_guild(int(item['guild_id']))
        if guild is None: raise RuntimeError('Guild is not available to the bot')
        member=guild.get_member(int(item['discord_user_id'])) or await guild.fetch_member(int(item['discord_user_id']))
        roles=[]
        for key in ('rank_role_id','language_role_id'):
            role_id=item.get(key)
            if role_id:
                role=guild.get_role(int(role_id))
                if role is None: raise RuntimeError(f'Discord role not found: {role_id}')
                roles.append(role)
        if roles: await member.add_roles(*roles,reason='ShieldNet R5/R4 application approved')
        nickname=f"[{item['alliance_tag']}] {item['game_nickname']}"
        if len(nickname)>32:nickname=nickname[:32]
        await member.edit(nick=nickname,reason='ShieldNet R5/R4 application approved')
