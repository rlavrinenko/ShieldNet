import secrets
from typing import Annotated
from fastapi import Header, HTTPException, status
from app.core.config import settings
async def verify_internal_service_token(token:Annotated[str|None,Header(alias='X-ShieldNet-Service-Token')]=None)->None:
    if not token or not secrets.compare_digest(token,settings.internal_service_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail='Invalid internal service token')
