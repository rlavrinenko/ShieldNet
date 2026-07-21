from collections import Counter

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security import SecurityFinding, SecuritySeverity, SecuritySnapshot
from app.schemas.security import SecuritySnapshotIn


WEIGHTS = {
    SecuritySeverity.INFO: 0,
    SecuritySeverity.LOW: 4,
    SecuritySeverity.MEDIUM: 10,
    SecuritySeverity.HIGH: 20,
    SecuritySeverity.CRITICAL: 35,
}


class SecurityService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def ingest(self, payload: SecuritySnapshotIn) -> SecuritySnapshot:
        snapshot = SecuritySnapshot(
            guild_id=payload.guild_id,
            payload=payload.model_dump(mode="json"),
            role_count=len(payload.roles),
            channel_count=len(payload.channels),
            webhook_count=len(payload.webhooks),
            collected_at=payload.collected_at,
        )
        self.session.add(snapshot)
        await self.session.flush()
        await self.session.execute(delete(SecurityFinding).where(SecurityFinding.guild_id == payload.guild_id))
        for item in self._analyse(payload):
            self.session.add(SecurityFinding(guild_id=payload.guild_id, snapshot_id=snapshot.id, **item))
        await self.session.commit()
        await self.session.refresh(snapshot)
        return snapshot

    async def latest(self, guild_id: int):
        snapshot = (await self.session.execute(
            select(SecuritySnapshot).where(SecuritySnapshot.guild_id == guild_id).order_by(SecuritySnapshot.created_at.desc()).limit(1)
        )).scalar_one_or_none()
        findings = list((await self.session.execute(
            select(SecurityFinding).where(SecurityFinding.guild_id == guild_id).order_by(SecurityFinding.created_at.desc())
        )).scalars().all())
        counts = Counter(f.severity.value for f in findings)
        score = min(100, sum(WEIGHTS[f.severity] for f in findings))
        return snapshot, findings, dict(counts), score

    def _analyse(self, payload: SecuritySnapshotIn) -> list[dict]:
        findings: list[dict] = []

        def add(key: str, category: str, severity: SecuritySeverity, title: str, description: str, *, resource_type=None, resource_id=None, resource_name=None, recommendation=None, details=None):
            findings.append({
                "finding_key": key,
                "category": category,
                "severity": severity,
                "title": title,
                "description": description,
                "resource_type": resource_type,
                "resource_id": str(resource_id) if resource_id is not None else None,
                "resource_name": resource_name,
                "recommendation": recommendation,
                "status": "open",
                "details": details or {},
            })

        for role in payload.roles:
            name = str(role.get("name") or "Unknown role")
            rid = role.get("id")
            perms = role.get("permissions") or {}
            if role.get("managed"):
                continue
            if role.get("is_everyone") and perms.get("administrator"):
                add(f"role:{rid}:everyone_admin", "roles", SecuritySeverity.CRITICAL, "@everyone has Administrator", "Every member receives unrestricted server access.", resource_type="role", resource_id=rid, resource_name=name, recommendation="Remove Administrator from @everyone immediately.")
            elif perms.get("administrator"):
                sev = SecuritySeverity.HIGH if int(role.get("member_count") or 0) <= 5 else SecuritySeverity.CRITICAL
                add(f"role:{rid}:administrator", "roles", sev, "Role has Administrator", f"Role {name} bypasses all channel permission checks.", resource_type="role", resource_id=rid, resource_name=name, recommendation="Keep Administrator only on a minimal trusted role.", details={"member_count": role.get("member_count", 0)})
            dangerous = [p for p in ("manage_guild", "manage_roles", "manage_channels", "manage_webhooks", "ban_members", "kick_members", "moderate_members", "mention_everyone") if perms.get(p)]
            if len(dangerous) >= 4 and not perms.get("administrator"):
                add(f"role:{rid}:broad_permissions", "roles", SecuritySeverity.HIGH, "Role has broad management permissions", f"Role {name} combines several sensitive permissions.", resource_type="role", resource_id=rid, resource_name=name, recommendation="Split responsibilities and remove permissions that are not required.", details={"permissions": dangerous, "member_count": role.get("member_count", 0)})
            if perms.get("manage_webhooks") and int(role.get("member_count") or 0) > 10:
                add(f"role:{rid}:webhooks_many", "webhooks", SecuritySeverity.MEDIUM, "Webhook management granted widely", f"{role.get('member_count')} members can manage webhooks through {name}.", resource_type="role", resource_id=rid, resource_name=name, recommendation="Restrict Manage Webhooks to trusted automation administrators.")

        for webhook in payload.webhooks:
            wid = webhook.get("id")
            name = str(webhook.get("name") or "Unnamed webhook")
            if webhook.get("user_id") is None:
                add(f"webhook:{wid}:owner_unknown", "webhooks", SecuritySeverity.MEDIUM, "Webhook owner is unavailable", "The webhook has no visible creator account and should be reviewed.", resource_type="webhook", resource_id=wid, resource_name=name, recommendation="Confirm that the webhook is expected; rotate or delete it otherwise.")
            if not webhook.get("channel_id"):
                add(f"webhook:{wid}:channel_missing", "webhooks", SecuritySeverity.HIGH, "Webhook is detached from a channel", "A webhook exists without a valid destination channel.", resource_type="webhook", resource_id=wid, resource_name=name, recommendation="Delete the orphaned webhook.")

        for channel in payload.channels:
            cid = channel.get("id")
            name = str(channel.get("name") or "Unknown channel")
            everyone = channel.get("everyone_permissions") or {}
            if everyone.get("manage_channels") or everyone.get("manage_webhooks"):
                add(f"channel:{cid}:everyone_manage", "channels", SecuritySeverity.CRITICAL, "@everyone can manage a channel", f"Channel {name} grants channel or webhook management to everyone.", resource_type="channel", resource_id=cid, resource_name=name, recommendation="Remove management permissions from @everyone.", details=everyone)
            if channel.get("type") == "text" and everyone.get("mention_everyone"):
                add(f"channel:{cid}:mention_everyone", "channels", SecuritySeverity.LOW, "@everyone mentions are allowed", f"All members can use mass mentions in {name}.", resource_type="channel", resource_id=cid, resource_name=name, recommendation="Disable Mention @everyone unless this is intentional.")

        if payload.bot_permissions and not payload.bot_permissions.get("view_audit_log", False):
            add("bot:missing_audit", "bot", SecuritySeverity.MEDIUM, "Bot cannot view the audit log", "Security monitoring cannot correlate critical Discord changes.", resource_type="bot", recommendation="Grant View Audit Log to the ShieldNet bot role.")
        if payload.bot_permissions and not payload.bot_permissions.get("manage_roles", False):
            add("bot:missing_manage_roles", "bot", SecuritySeverity.LOW, "Bot cannot manage roles", "Automated remediation and verification role assignment may be limited.", resource_type="bot", recommendation="Grant Manage Roles and place the bot role above managed roles.")
        if not findings:
            add("baseline:clean", "baseline", SecuritySeverity.INFO, "No high-risk configuration detected", "The latest snapshot did not trigger current ShieldNet security rules.", recommendation="Continue periodic review and keep administrator access minimal.")
        return findings
