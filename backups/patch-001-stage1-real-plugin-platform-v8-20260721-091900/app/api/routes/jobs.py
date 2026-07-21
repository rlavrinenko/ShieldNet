from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.platform_access import require_superadmin
from app.db.session import get_db_session
from app.models.core import User
from app.services.audit_service import AuditService
from app.services.job_service import JobService

router = APIRouter(prefix="/platform/jobs", tags=["Platform Jobs"])


@router.get("/overview")
async def jobs_overview(
    _: User = Depends(require_superadmin),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    return await JobService(session).overview()


@router.post("/{job_key}/run")
async def run_job(
    job_key: str,
    current_user: User = Depends(require_superadmin),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    service = JobService(session)
    try:
        run = await service.execute(job_key, current_user.id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown job") from exc

    await AuditService(session).record(
        event_type="platform.job.manual_run",
        actor_user_id=current_user.id,
        target_type="system_job",
        target_id=job_key,
        payload={"run_id": str(run.id), "status": run.status},
        result=run.status,
        message=f"Manual system job completed: {job_key}",
    )
    await session.commit()
    return JobService.serialize_run(run)
