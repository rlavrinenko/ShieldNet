from datetime import datetime
from pydantic import BaseModel, Field
class ChannelItem(BaseModel):
 discord_channel_id:int; parent_id:int|None=None; name:str; channel_type:str; position:int=0; nsfw:bool=False; topic:str|None=None; permissions_synced:bool=False
class WebhookItem(BaseModel):
 discord_webhook_id:int; channel_id:int|None=None; name:str|None=None; webhook_type:str="incoming"; owner_id:int|None=None
class EmojiItem(BaseModel):
 discord_emoji_id:int; name:str; animated:bool=False; managed:bool=False; available:bool=True
class InviteItem(BaseModel):
 code:str; channel_id:int|None=None; inviter_id:int|None=None; uses:int=0; max_uses:int=0; temporary:bool=False; expires_at:datetime|None=None
class PermissionOverwriteItem(BaseModel):
 discord_channel_id:int; target_id:int; target_type:str; allow_permissions:int=0; deny_permissions:int=0
class ExplorerSyncRequest(BaseModel):
 channels:list[ChannelItem]=Field(default_factory=list); webhooks:list[WebhookItem]=Field(default_factory=list); emojis:list[EmojiItem]=Field(default_factory=list); invites:list[InviteItem]=Field(default_factory=list); permission_overwrites:list[PermissionOverwriteItem]=Field(default_factory=list)
