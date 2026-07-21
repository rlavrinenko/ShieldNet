from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.db.session import close_database


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await close_database()


app = FastAPI(
    title="ShieldNet API",
    description="Backend API for ShieldNet.",
    version="3.2.0",
    debug=settings.debug,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": "ShieldNet API",
        "version": "3.2.0",
        "status": "running",
    }

# SHIELDNET_V536_DIRECT_LEADERSHIP
# The internal Leadership router is attached directly to the FastAPI app.
# This is intentionally independent of app.api.router to guarantee that
# bot-facing endpoints are available even when an aggregate router is stale.
from app.api.routes.internal_leadership import router as _internal_leadership_router

_v536_required_paths = {
    "/api/v1/internal/leadership/pending-role-sync",
    "/api/v1/internal/leadership/applications/{application_id}/sync-result",
}
_v536_existing_paths = {
    getattr(route, "path", "")
    for route in app.routes
}
if not _v536_required_paths.issubset(_v536_existing_paths):
    app.include_router(_internal_leadership_router, prefix="/api/v1")
