from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from app.api.router import api_router
from app.api.routes.internal_leadership import router as internal_leadership_router
from app.api.routes.leadership import router as leadership_router
from app.core.config import settings
from app.db.session import close_database


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await close_database()


app = FastAPI(
    title="ShieldNet API",
    description="Backend API for ShieldNet.",
    version="5.3.4",
    debug=settings.debug,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

app.include_router(api_router, prefix="/api/v1")

# Compatibility fallback. Some older api_router baselines do not expose the
# Leadership routers even though their modules are installed. Register only
# the missing routers to avoid duplicate routes.
def _registered_paths() -> set[str]:
    return {
        getattr(route, "path", "")
        for route in app.routes
        if getattr(route, "path", None)
    }


paths = _registered_paths()
if "/api/v1/internal/leadership/pending-role-sync" not in paths:
    app.include_router(internal_leadership_router, prefix="/api/v1")

paths = _registered_paths()
if not any(path.startswith("/api/v1/discord/guilds/") and "/leadership" in path for path in paths):
    app.include_router(leadership_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": "ShieldNet API",
        "version": "5.3.4",
        "status": "running",
    }
