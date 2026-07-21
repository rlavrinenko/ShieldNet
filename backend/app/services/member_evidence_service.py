from datetime import UTC, datetime
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member_cases import MemberCase
from app.models.member_evidence import MemberCaseAppeal, MemberCaseEvidence
from app.models.members import DiscordMember
from app.schemas.member_evidence import (
    CaseAppealCreate,
    CaseAppealResponse,
    CaseAppealUpdate,
    CaseEvidenceCreate,
    CaseEvidenceResponse,
)


class MemberEvidenceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _case(self, guild_id: int, discord_user_id: int, case_id: uuid.UUID) -> MemberCase:
        row = (await self.session.execute(
            select(MemberCase)
            .join(DiscordMember, DiscordMember.id == MemberCase.member_id)
            .where(
                MemberCase.id == case_id,
                MemberCase.guild_id == guild_id,
                DiscordMember.discord_user_id == discord_user_id,
            )
        )).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
        return row

    @staticmethod
    def serialize_evidence(item: MemberCaseEvidence) -> CaseEvidenceResponse:
        return CaseEvidenceResponse(
            id=item.id,
            guild_id=item.guild_id,
            case_id=item.case_id,
            evidence_type=item.evidence_type,
            title=item.title,
            source_url=item.source_url,
            notes=item.notes,
            created_by=item.created_by,
            created_at=item.created_at,
        )

    @staticmethod
    def serialize_appeal(item: MemberCaseAppeal) -> CaseAppealResponse:
        return CaseAppealResponse(
            id=item.id,
            guild_id=item.guild_id,
            case_id=item.case_id,
            status=item.status,
            statement=item.statement,
            decision=item.decision,
            submitted_by_name=item.submitted_by_name,
            reviewed_by=item.reviewed_by,
            reviewed_at=item.reviewed_at,
            created_by=item.created_by,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    async def list_evidence(self, guild_id: int, discord_user_id: int, case_id: uuid.UUID) -> list[CaseEvidenceResponse]:
        await self._case(guild_id, discord_user_id, case_id)
        rows = (await self.session.execute(
            select(MemberCaseEvidence)
            .where(MemberCaseEvidence.guild_id == guild_id, MemberCaseEvidence.case_id == case_id)
            .order_by(MemberCaseEvidence.created_at.desc())
        )).scalars().all()
        return [self.serialize_evidence(row) for row in rows]

    async def create_evidence(self, guild_id: int, discord_user_id: int, case_id: uuid.UUID, user_id: uuid.UUID, payload: CaseEvidenceCreate) -> CaseEvidenceResponse:
        await self._case(guild_id, discord_user_id, case_id)
        row = MemberCaseEvidence(
            guild_id=guild_id,
            case_id=case_id,
            evidence_type=payload.evidence_type,
            title=payload.title.strip(),
            source_url=str(payload.source_url) if payload.source_url else None,
            notes=payload.notes.strip() if payload.notes else None,
            created_by=user_id,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return self.serialize_evidence(row)

    async def delete_evidence(self, guild_id: int, discord_user_id: int, case_id: uuid.UUID, evidence_id: uuid.UUID) -> None:
        await self._case(guild_id, discord_user_id, case_id)
        row = (await self.session.execute(
            select(MemberCaseEvidence).where(
                MemberCaseEvidence.id == evidence_id,
                MemberCaseEvidence.guild_id == guild_id,
                MemberCaseEvidence.case_id == case_id,
            )
        )).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
        await self.session.delete(row)
        await self.session.commit()

    async def list_appeals(self, guild_id: int, discord_user_id: int, case_id: uuid.UUID) -> list[CaseAppealResponse]:
        await self._case(guild_id, discord_user_id, case_id)
        rows = (await self.session.execute(
            select(MemberCaseAppeal)
            .where(MemberCaseAppeal.guild_id == guild_id, MemberCaseAppeal.case_id == case_id)
            .order_by(MemberCaseAppeal.created_at.desc())
        )).scalars().all()
        return [self.serialize_appeal(row) for row in rows]

    async def create_appeal(self, guild_id: int, discord_user_id: int, case_id: uuid.UUID, user_id: uuid.UUID, payload: CaseAppealCreate) -> CaseAppealResponse:
        await self._case(guild_id, discord_user_id, case_id)
        row = MemberCaseAppeal(
            guild_id=guild_id,
            case_id=case_id,
            statement=payload.statement.strip(),
            submitted_by_name=payload.submitted_by_name.strip() if payload.submitted_by_name else None,
            created_by=user_id,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return self.serialize_appeal(row)

    async def update_appeal(self, guild_id: int, discord_user_id: int, case_id: uuid.UUID, appeal_id: uuid.UUID, user_id: uuid.UUID, payload: CaseAppealUpdate) -> CaseAppealResponse:
        await self._case(guild_id, discord_user_id, case_id)
        row = (await self.session.execute(
            select(MemberCaseAppeal).where(
                MemberCaseAppeal.id == appeal_id,
                MemberCaseAppeal.guild_id == guild_id,
                MemberCaseAppeal.case_id == case_id,
            )
        )).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appeal not found")

        changes = payload.model_dump(exclude_unset=True)
        for key, value in changes.items():
            if key == "decision" and isinstance(value, str):
                value = value.strip() or None
            setattr(row, key, value)

        if payload.status in {"accepted", "rejected", "withdrawn"}:
            row.reviewed_by = user_id
            row.reviewed_at = datetime.now(UTC)
        elif payload.status in {"submitted", "under_review"}:
            row.reviewed_by = None
            row.reviewed_at = None

        await self.session.commit()
        await self.session.refresh(row)
        return self.serialize_appeal(row)
