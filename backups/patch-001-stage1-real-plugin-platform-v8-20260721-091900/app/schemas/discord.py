from pydantic import BaseModel, Field
class GuildRegisterRequest(BaseModel):
    guild_id:int=Field(gt=0); name:str=Field(min_length=1,max_length=255); icon_url:str|None=None
    owner_discord_id:int=Field(gt=0); member_count:int=Field(default=0,ge=0); preferred_language:str='uk'
class GuildLeftRequest(BaseModel): guild_id:int=Field(gt=0)
class GuildAccessResponse(BaseModel):
    guild_id:int; name:str; icon_url:str|None; owner_discord_id:int; member_count:int
    guild_status:str; bot_status:str; access_role:str
