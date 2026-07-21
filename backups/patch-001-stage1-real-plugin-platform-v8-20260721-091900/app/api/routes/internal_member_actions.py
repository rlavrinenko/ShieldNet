import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.internal import verify_internal_service_token
from app.db.session import get_db_session
from app.schemas.member_actions import MemberActionResult
from app.services.member_action_service import MemberActionService

router = APIRouter(
    prefix="/internal/discord/guilds",
    tags=["Internal Member Actions"],
    dependencies=[Depends(verify_internal_service_token)],
)


@router.get("/{guild_id}/member-actions")
async def pending_actions(guild_id: int, session: AsyncSession = Depends(get_db_session)):
    return {"items": [item.model_dump() for item in await MemberActionService(session).pending(guild_id)]}


@router.post("/member-actions/{action_id}/result")
async def action_result(
    action_id: uuid.UUID,
    payload: MemberActionResult,
    session: AsyncSession = Depends(get_db_session),
):
    await MemberActionService(session).complete(
        action_id, payload.status, payload.result_message
    )
    return {"status": "saved"}
