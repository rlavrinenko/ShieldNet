from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.internal import verify_internal_service_token
from app.db.session import get_db_session
from app.schemas.ai_runtime import AIRuntimeRequest, AIRuntimeResponse
from app.services.ai_runtime import AIRuntimeService

router = APIRouter(prefix="/internal/ai", tags=["Internal AI"], dependencies=[Depends(verify_internal_service_token)])

@router.post("/execute", response_model=AIRuntimeResponse)
async def execute_ai(payload: AIRuntimeRequest, session: AsyncSession = Depends(get_db_session)):
    try:
        provider, result = await AIRuntimeService(session).execute(**payload.model_dump())
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return AIRuntimeResponse(text=result.text, provider_id=str(provider.id), provider_name=provider.name,
        provider_type=provider.provider_type, model=result.model, input_units=result.input_units,
        output_units=result.output_units, latency_ms=result.latency_ms)
