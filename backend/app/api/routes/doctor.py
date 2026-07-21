from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.platform_access import require_superadmin
from app.db.session import get_db_session
from app.models.core import User
from app.services.platform_doctor import PlatformDoctorService

router = APIRouter(prefix="/platform/doctor", tags=["Platform Doctor"])


@router.get("/report")
async def doctor_report(
    _: User = Depends(require_superadmin),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    return await PlatformDoctorService().run(session)
