"""FastAPI main application entrypoint."""

import os
# Ensure pure Python mode for SQLAlchemy on systems with restrictive DLL policies
os.environ.setdefault("DISABLE_SQLALCHEMY_CEXT", "1")

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from orvyn.config import settings
from orvyn.core.logging import logger
from orvyn.api.v1.tasks import router as tasks_router
from orvyn.api.v1.timeline import router as timeline_router
from orvyn.database.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown hooks."""
    logger.info(f"Starting {settings.app_name} in {settings.app_env} mode...")
    # Initialize DB tables (in production, Alembic handles migrations)
    try:
        await init_db()
    except Exception as err:
        logger.warning(f"Could not auto-initialize DB on startup: {err}")
    yield
    logger.info("Shutting down ORVYN...")


app = FastAPI(
    title="ORVYN API",
    description="Autonomous Human-in-the-Loop Voice Agent Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 routers
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(timeline_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "env": settings.app_env,
        "telephony": settings.telephony_provider,
        "llm": settings.default_llm_provider,
    }
