from pydantic import BaseModel
class GuildRoleItem(BaseModel):
    discord_role_id: int
    name: str
    position: int = 0
    color: int = 0
    permissions: int = 0
    managed: bool = False
    assignable: bool = False
class GuildRoleSyncRequest(BaseModel):
    roles: list[GuildRoleItem]
