from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plugins import PluginInstallJob, PluginInstallLog, PluginMarketplaceItem
from app.schemas.plugin_jobs import (
    PluginJobCreate,
    PluginJobDetailResponse,
    PluginJobLogResponse,
    PluginJobPageResponse,
    PluginJobResponse,
)

ALLOWED_ACTIONS = {"install", "update", "rollback", "uninstall"}
ACTIVE_STATUSES = {"queued", "running"}


class PluginJobConflictError(Exception):
    pass


class PluginJobService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def enqueue(
        self,
        *,
        plugin_key: str,
        action: str,
        payload: PluginJobCreate,
        requested_by_user_id: UUID | None,
    ) -> PluginJobResponse:
        if action not in ALLOWED_ACTIONS:
            raise ValueError("unsupported plugin job action")

        if action != "uninstall":
            exists = (
                await self.session.execute(
                    select(PluginMarketplaceItem.id).where(
                        PluginMarketplaceItem.plugin_key == plugin_key
                    )
                )
            ).scalar_one_or_none()
            if exists is None:
                raise LookupError("Marketplace plugin not found")

        active = (
            await self.session.execute(
                select(PluginInstallJob.id).where(
                    PluginInstallJob.plugin_key == plugin_key,
                    PluginInstallJob.status.in_(ACTIVE_STATUSES),
                )
            )
        ).scalar_one_or_none()
        if active is not None:
            raise PluginJobConflictError(
                "plugin already has a queued or running installation job"
            )

        job = PluginInstallJob(
            plugin_key=plugin_key,
            requested_version=payload.version,
            action=action,
            status="queued",
            requested_by_user_id=requested_by_user_id,
            progress=0,
            payload_json=payload.payload_json,
        )
        self.session.add(job)
        await self.session.flush()
        self.session.add(
            PluginInstallLog(
                job_id=job.id,
                level="info",
                message=f"{action} job queued",
                metadata_json={"requested_version": payload.version},
            )
        )
        await self.session.commit()
        await self.session.refresh(job)
        return self._job_response(job)

    async def list_jobs(
        self,
        *,
        status: str | None,
        plugin_key: str | None,
        limit: int,
        offset: int,
    ) -> PluginJobPageResponse:
        filters = []
        if status:
            filters.append(PluginInstallJob.status == status)
        if plugin_key:
            filters.append(PluginInstallJob.plugin_key == plugin_key)

        total = int(
            (
                await self.session.execute(
                    select(func.count(PluginInstallJob.id)).where(*filters)
                )
            ).scalar_one()
        )
        jobs = list(
            (
                await self.session.execute(
                    select(PluginInstallJob)
                    .where(*filters)
                    .order_by(PluginInstallJob.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
            ).scalars().all()
        )
        return PluginJobPageResponse(
            items=[self._job_response(job) for job in jobs],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_job(self, job_id: UUID) -> PluginJobDetailResponse:
        job = (
            await self.session.execute(
                select(PluginInstallJob).where(PluginInstallJob.id == job_id)
            )
        ).scalar_one_or_none()
        if job is None:
            raise LookupError("Plugin job not found")

        logs = list(
            (
                await self.session.execute(
                    select(PluginInstallLog)
                    .where(PluginInstallLog.job_id == job_id)
                    .order_by(PluginInstallLog.created_at.asc())
                )
            ).scalars().all()
        )
        base = self._job_response(job)
        return PluginJobDetailResponse(
            **base.model_dump(),
            logs=[
                PluginJobLogResponse(
                    id=log.id,
                    job_id=log.job_id,
                    level=log.level,
                    message=log.message,
                    metadata_json=log.metadata_json or {},
                    created_at=log.created_at,
                )
                for log in logs
            ],
        )

    @staticmethod
    def _job_response(job: PluginInstallJob) -> PluginJobResponse:
        return PluginJobResponse(
            id=job.id,
            plugin_key=job.plugin_key,
            requested_version=job.requested_version,
            action=job.action,
            status=job.status,
            progress=job.progress,
            error=job.error,
            payload_json=job.payload_json or {},
            created_at=job.created_at,
            started_at=job.started_at,
            finished_at=job.finished_at,
        )
