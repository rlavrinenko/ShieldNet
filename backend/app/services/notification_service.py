from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.jobs import SystemJobRun
from app.models.member_cases import MemberCase
from app.models.notifications import PlatformNotification
from app.models.runtime import RuntimeHeartbeat
from app.models.security import SecurityFinding, SecuritySeverity


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _upsert(
        self,
        *,
        fingerprint: str,
        severity: str,
        category: str,
        source: str,
        title: str,
        message: str,
        guild_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PlatformNotification:
        now = datetime.now(UTC)
        item = (
            await self.session.execute(
                select(PlatformNotification).where(PlatformNotification.fingerprint == fingerprint)
            )
        ).scalar_one_or_none()
        if item is None:
            item = PlatformNotification(
                fingerprint=fingerprint,
                severity=severity,
                category=category,
                source=source,
                title=title,
                message=message,
                guild_id=guild_id,
                metadata_json=metadata or {},
                status="open",
                first_seen_at=now,
                last_seen_at=now,
            )
            self.session.add(item)
        else:
            item.severity = severity
            item.category = category
            item.source = source
            item.title = title
            item.message = message
            item.guild_id = guild_id
            item.metadata_json = metadata or {}
            item.last_seen_at = now
            if item.status == "resolved":
                item.status = "open"
                item.resolved_at = None
                item.resolved_by = None
        await self.session.flush()
        return item

    async def evaluate(self) -> dict[str, int]:
        now = datetime.now(UTC)
        created_or_refreshed = 0

        stale_cutoff = now - timedelta(seconds=90)
        stale_workers = list((await self.session.scalars(
            select(RuntimeHeartbeat).where(RuntimeHeartbeat.last_seen_at < stale_cutoff)
        )).all())
        for worker in stale_workers:
            await self._upsert(
                fingerprint=f"runtime:{worker.worker_name}:stale",
                severity="critical" if worker.worker_type == "backend" else "high",
                category="runtime",
                source="heartbeat",
                title=f"{worker.worker_name} heartbeat is stale",
                message=f"No heartbeat has been received since {worker.last_seen_at.isoformat()}.",
                metadata={"worker_type": worker.worker_type, "last_seen_at": worker.last_seen_at.isoformat()},
            )
            created_or_refreshed += 1

        failed_jobs = list((await self.session.scalars(
            select(SystemJobRun)
            .where(SystemJobRun.status == "failed", SystemJobRun.created_at >= now - timedelta(hours=24))
            .order_by(SystemJobRun.created_at.desc())
            .limit(50)
        )).all())
        for job in failed_jobs:
            await self._upsert(
                fingerprint=f"job:{job.id}:failed",
                severity="high",
                category="jobs",
                source="jobs-center",
                title=f"Job failed: {job.job_key}",
                message=job.error_message or "The job finished with a failed status.",
                metadata={"job_id": str(job.id), "job_key": job.job_key},
            )
            created_or_refreshed += 1

        overdue_rows = (await self.session.execute(
            select(MemberCase.guild_id, func.count(MemberCase.id))
            .where(
                MemberCase.due_at.is_not(None),
                MemberCase.due_at < now,
                MemberCase.status.notin_(("resolved", "dismissed")),
            )
            .group_by(MemberCase.guild_id)
        )).all()
        for guild_id, count in overdue_rows:
            await self._upsert(
                fingerprint=f"moderation:{guild_id}:overdue",
                severity="high" if count >= 5 else "medium",
                category="moderation",
                source="member-cases",
                guild_id=int(guild_id),
                title=f"{count} overdue moderation case(s)",
                message="One or more member cases have passed their due date.",
                metadata={"overdue_count": int(count)},
            )
            created_or_refreshed += 1

        security_rows = (await self.session.execute(
            select(SecurityFinding.guild_id, SecurityFinding.severity, func.count(SecurityFinding.id))
            .where(
                SecurityFinding.status == "open",
                SecurityFinding.severity.in_((SecuritySeverity.HIGH, SecuritySeverity.CRITICAL)),
            )
            .group_by(SecurityFinding.guild_id, SecurityFinding.severity)
        )).all()
        for guild_id, severity, count in security_rows:
            sev = severity.value if hasattr(severity, "value") else str(severity)
            await self._upsert(
                fingerprint=f"security:{guild_id}:{sev}",
                severity="critical" if sev == "critical" else "high",
                category="security",
                source="security-center",
                guild_id=int(guild_id),
                title=f"{count} open {sev} security finding(s)",
                message="Security Center has unresolved high-risk findings.",
                metadata={"finding_count": int(count), "severity": sev},
            )
            created_or_refreshed += 1

        redis = Redis.from_url(settings.redis_url, decode_responses=True)
        try:
            await redis.ping()
        except Exception as exc:
            await self._upsert(
                fingerprint="infrastructure:valkey:offline",
                severity="critical",
                category="infrastructure",
                source="valkey",
                title="Valkey / Redis is unavailable",
                message=str(exc)[:500] or "The backend could not connect to the queue service.",
            )
            created_or_refreshed += 1
        finally:
            await redis.aclose()

        await self.session.commit()
        return {
            "evaluated_at": int(now.timestamp()),
            "alerts_created_or_refreshed": created_or_refreshed,
            "stale_workers": len(stale_workers),
            "failed_jobs": len(failed_jobs),
            "overdue_guilds": len(overdue_rows),
            "security_groups": len(security_rows),
        }

    async def summary(self) -> dict[str, int]:
        rows = (await self.session.execute(
            select(PlatformNotification.status, PlatformNotification.severity, func.count(PlatformNotification.id))
            .group_by(PlatformNotification.status, PlatformNotification.severity)
        )).all()
        result = {"open": 0, "acknowledged": 0, "resolved": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for status, severity, count in rows:
            result[status] = result.get(status, 0) + int(count)
            if status != "resolved":
                result[severity] = result.get(severity, 0) + int(count)
        return result
