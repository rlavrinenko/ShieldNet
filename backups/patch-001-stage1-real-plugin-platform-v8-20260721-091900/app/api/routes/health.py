from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from app.db.session import AsyncSessionFactory

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "shieldnet-backend",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/database")
async def database_health() -> dict[str, str]:
    try:
        async with AsyncSessionFactory() as session:
            result = await session.execute(
                text(
                    """
                    SELECT
                        current_database() AS database_name,
                        current_user AS database_user,
                        current_setting('TimeZone') AS timezone
                    """
                )
            )
            row = result.mappings().one()

        return {
            "status": "ok",
            "database": row["database_name"],
            "user": row["database_user"],
            "timezone": row["timezone"],
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed",
        ) from exc
