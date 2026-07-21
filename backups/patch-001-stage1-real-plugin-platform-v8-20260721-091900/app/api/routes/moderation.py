import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.guild_access import require_guild_management
from app.db.session import get_db_session
from app.models.core import User
from app.models.member_actions import MemberAction, MemberActionStatus, MemberActionType
from app.models.moderation import (
    ModerationAction, ModerationAppeal, ModerationAttachment, ModerationCase,
    ModerationCaseNote, ModerationReport, ModerationTemplate, ModerationViolationType,
)
from app.schemas.moderation import (
    ActionCreate, ActionResponse, AppealCreate, AppealDecision, AppealResponse,
    CaseCreate, CaseResponse, CaseUpdate, ModerationStats, NoteCreate, NoteResponse,
    ReportCreate, ReportDecision, ReportResponse, TemplateCreate, TemplateResponse,
    ViolationTypeCreate, ViolationTypeResponse,
)

router = APIRouter(prefix="/discord/guilds/{guild_id}/moderation-center", tags=["Moderation Center"])

ALLOWED_ACTIONS = {"warning", "send_dm", "kick", "ban", "remove_role", "custom"}


async def _access(session: AsyncSession, user: User, guild_id: int) -> None:
    await require_guild_management(session, user, guild_id)


@router.get("/violation-types", response_model=list[ViolationTypeResponse])
async def list_violation_types(guild_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await _access(session, current_user, guild_id)
    rows = await session.scalars(select(ModerationViolationType).where(ModerationViolationType.guild_id == guild_id).order_by(ModerationViolationType.name))
    return list(rows)


@router.post("/violation-types", response_model=ViolationTypeResponse, status_code=201)
async def create_violation_type(guild_id: int, payload: ViolationTypeCreate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await _access(session, current_user, guild_id)
    item = ModerationViolationType(guild_id=guild_id, created_by=current_user.id, **payload.model_dump())
    session.add(item); await session.commit(); await session.refresh(item)
    return item


@router.get("/reports", response_model=list[ReportResponse])
async def list_reports(guild_id: int, status_filter: str = "all", page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200), current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await _access(session, current_user, guild_id)
    q = select(ModerationReport).where(ModerationReport.guild_id == guild_id)
    if status_filter != "all": q = q.where(ModerationReport.status == status_filter)
    rows = await session.scalars(q.order_by(ModerationReport.created_at.desc()).offset((page-1)*page_size).limit(page_size))
    return list(rows)


@router.post("/reports", response_model=ReportResponse, status_code=201)
async def create_report(guild_id: int, payload: ReportCreate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await _access(session, current_user, guild_id)
    data = payload.model_dump(exclude={"evidence_urls"})
    item = ModerationReport(guild_id=guild_id, reporter_user_id=current_user.id, **data)
    session.add(item); await session.flush()
    for url in payload.evidence_urls:
        session.add(ModerationAttachment(report_id=item.id, url=url, uploaded_by=current_user.id))
    await session.commit(); await session.refresh(item)
    return item


@router.post("/reports/{report_id}/take", response_model=ReportResponse)
async def take_report(guild_id: int, report_id: uuid.UUID, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await _access(session, current_user, guild_id)
    item = await session.scalar(select(ModerationReport).where(ModerationReport.id == report_id, ModerationReport.guild_id == guild_id))
    if not item: raise HTTPException(404, "Report not found")
    item.assigned_to = current_user.id; item.status = "in_review"
    await session.commit(); await session.refresh(item); return item


@router.post("/reports/{report_id}/reject", response_model=ReportResponse)
async def reject_report(guild_id: int, report_id: uuid.UUID, payload: ReportDecision, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await _access(session, current_user, guild_id)
    item = await session.scalar(select(ModerationReport).where(ModerationReport.id == report_id, ModerationReport.guild_id == guild_id))
    if not item: raise HTTPException(404, "Report not found")
    item.status = "rejected"; item.rejection_reason = payload.reason
    await session.commit(); await session.refresh(item); return item


@router.post("/reports/{report_id}/convert", response_model=CaseResponse, status_code=201)
async def convert_report(guild_id: int, report_id: uuid.UUID, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await _access(session, current_user, guild_id)
    report = await session.scalar(select(ModerationReport).where(ModerationReport.id == report_id, ModerationReport.guild_id == guild_id))
    if not report: raise HTTPException(404, "Report not found")
    case = ModerationCase(guild_id=guild_id, report_id=report.id, reported_discord_user_id=report.reported_discord_user_id, violation_type_id=report.violation_type_id, title=report.title, description=report.description, priority=report.priority, assigned_to=current_user.id, created_by=current_user.id)
    session.add(case); report.status = "accepted"; await session.commit(); await session.refresh(case); return case


@router.get("/cases", response_model=list[CaseResponse])
async def list_cases(guild_id: int, status_filter: str = "all", discord_user_id: int | None = None, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200), current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await _access(session, current_user, guild_id)
    q = select(ModerationCase).where(ModerationCase.guild_id == guild_id)
    if status_filter != "all": q = q.where(ModerationCase.status == status_filter)
    if discord_user_id is not None: q = q.where(ModerationCase.reported_discord_user_id == discord_user_id)
    rows = await session.scalars(q.order_by(ModerationCase.created_at.desc()).offset((page-1)*page_size).limit(page_size))
    return list(rows)


@router.post("/cases", response_model=CaseResponse, status_code=201)
async def create_case(guild_id: int, payload: CaseCreate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await _access(session, current_user, guild_id)
    item = ModerationCase(guild_id=guild_id, created_by=current_user.id, **payload.model_dump())
    session.add(item); await session.commit(); await session.refresh(item); return item


@router.patch("/cases/{case_id}", response_model=CaseResponse)
async def update_case(guild_id: int, case_id: uuid.UUID, payload: CaseUpdate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await _access(session, current_user, guild_id)
    item = await session.scalar(select(ModerationCase).where(ModerationCase.id == case_id, ModerationCase.guild_id == guild_id))
    if not item: raise HTTPException(404, "Case not found")
    for key, value in payload.model_dump(exclude_unset=True).items(): setattr(item, key, value)
    if item.status in {"resolved", "closed"}: item.resolved_at = datetime.now(timezone.utc)
    await session.commit(); await session.refresh(item); return item


@router.get("/cases/{case_id}/notes", response_model=list[NoteResponse])
async def list_notes(guild_id: int, case_id: uuid.UUID, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await _access(session, current_user, guild_id)
    rows = await session.scalars(select(ModerationCaseNote).join(ModerationCase, ModerationCase.id == ModerationCaseNote.case_id).where(ModerationCaseNote.case_id == case_id, ModerationCase.guild_id == guild_id).order_by(ModerationCaseNote.created_at))
    return list(rows)


@router.post("/cases/{case_id}/notes", response_model=NoteResponse, status_code=201)
async def add_note(guild_id: int, case_id: uuid.UUID, payload: NoteCreate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await _access(session, current_user, guild_id)
    exists = await session.scalar(select(ModerationCase.id).where(ModerationCase.id == case_id, ModerationCase.guild_id == guild_id))
    if not exists: raise HTTPException(404, "Case not found")
    item = ModerationCaseNote(case_id=case_id, author_user_id=current_user.id, **payload.model_dump())
    session.add(item); await session.commit(); await session.refresh(item); return item


@router.post("/cases/{case_id}/actions", response_model=ActionResponse, status_code=201)
async def create_action(guild_id: int, case_id: uuid.UUID, payload: ActionCreate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await _access(session, current_user, guild_id)
    case = await session.scalar(select(ModerationCase).where(ModerationCase.id == case_id, ModerationCase.guild_id == guild_id))
    if not case: raise HTTPException(404, "Case not found")
    if payload.action_type not in ALLOWED_ACTIONS: raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unsupported action")
    action = ModerationAction(case_id=case.id, guild_id=guild_id, discord_user_id=case.reported_discord_user_id, requested_by=current_user.id, **payload.model_dump())
    session.add(action)
    if payload.action_type in {"send_dm", "kick", "ban", "remove_role"}:
        member_action = MemberAction(guild_id=guild_id, discord_user_id=case.reported_discord_user_id, action_type=MemberActionType(payload.action_type), payload={**payload.payload, "reason": payload.reason}, status=MemberActionStatus.PENDING, requested_by=current_user.id)
        session.add(member_action); await session.flush(); action.member_action_id = member_action.id
    else:
        action.status = "completed"; action.completed_at = datetime.now(timezone.utc); action.result_message = "Recorded in ShieldNet."
    await session.commit(); await session.refresh(action); return action


@router.get("/cases/{case_id}/actions", response_model=list[ActionResponse])
async def list_actions(guild_id: int, case_id: uuid.UUID, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await _access(session, current_user, guild_id)
    rows = await session.scalars(select(ModerationAction).join(ModerationCase, ModerationCase.id == ModerationAction.case_id).where(ModerationAction.case_id == case_id, ModerationCase.guild_id == guild_id).order_by(ModerationAction.created_at.desc()))
    return list(rows)


@router.post("/cases/{case_id}/appeals", response_model=AppealResponse, status_code=201)
async def create_appeal(guild_id: int, case_id: uuid.UUID, payload: AppealCreate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await _access(session, current_user, guild_id)
    exists = await session.scalar(select(ModerationCase.id).where(ModerationCase.id == case_id, ModerationCase.guild_id == guild_id))
    if not exists: raise HTTPException(404, "Case not found")
    item = ModerationAppeal(case_id=case_id, **payload.model_dump()); session.add(item); await session.commit(); await session.refresh(item); return item


@router.post("/appeals/{appeal_id}/decision", response_model=AppealResponse)
async def decide_appeal(guild_id: int, appeal_id: uuid.UUID, payload: AppealDecision, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await _access(session, current_user, guild_id)
    item = await session.scalar(select(ModerationAppeal).join(ModerationCase, ModerationCase.id == ModerationAppeal.case_id).where(ModerationAppeal.id == appeal_id, ModerationCase.guild_id == guild_id))
    if not item: raise HTTPException(404, "Appeal not found")
    item.status = payload.status; item.decision_reason = payload.reason; item.decided_by = current_user.id; item.decided_at = datetime.now(timezone.utc)
    await session.commit(); await session.refresh(item); return item


@router.get("/templates", response_model=list[TemplateResponse])
async def list_templates(guild_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await _access(session, current_user, guild_id)
    rows = await session.scalars(select(ModerationTemplate).where(ModerationTemplate.guild_id == guild_id, ModerationTemplate.active.is_(True)).order_by(ModerationTemplate.name))
    return list(rows)


@router.post("/templates", response_model=TemplateResponse, status_code=201)
async def create_template(guild_id: int, payload: TemplateCreate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await _access(session, current_user, guild_id)
    item = ModerationTemplate(guild_id=guild_id, created_by=current_user.id, **payload.model_dump()); session.add(item); await session.commit(); await session.refresh(item); return item


@router.get("/stats", response_model=ModerationStats)
async def stats(guild_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    await _access(session, current_user, guild_id)
    async def count(model, condition):
        return int((await session.scalar(select(func.count()).select_from(model).where(condition))) or 0)
    return ModerationStats(
        reports_pending=await count(ModerationReport, (ModerationReport.guild_id == guild_id) & (ModerationReport.status.in_(["pending", "in_review"]))),
        cases_open=await count(ModerationCase, (ModerationCase.guild_id == guild_id) & (ModerationCase.status.in_(["open", "in_review"]))),
        cases_resolved=await count(ModerationCase, (ModerationCase.guild_id == guild_id) & (ModerationCase.status.in_(["resolved", "closed"]))),
        actions_pending=await count(ModerationAction, (ModerationAction.guild_id == guild_id) & (ModerationAction.status.in_(["pending", "processing"]))),
        appeals_pending=int((await session.scalar(select(func.count()).select_from(ModerationAppeal).join(ModerationCase, ModerationCase.id == ModerationAppeal.case_id).where(ModerationCase.guild_id == guild_id, ModerationAppeal.status == "pending"))) or 0),
    )
