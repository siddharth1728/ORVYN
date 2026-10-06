"""Main FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.agents import router as agents_router
from app.api.routes.health import router as health_router
from app.api.routes.tasks import router as tasks_router
from app.core.config import settings
from app.core.logging import logger
from app.infrastructure.tools.builtin import register_foundational_tools


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} Foundation Engine [{settings.app_env}]")
    register_foundational_tools()
    yield
    logger.info(f"Stopping {settings.app_name}")


app = FastAPI(
    title="ORVYN Platform API",
    description="Autonomous Human-in-the-Loop Voice Agent Foundation Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes under /api
app.include_router(tasks_router, prefix="/api")
app.include_router(agents_router, prefix="/api")
app.include_router(health_router, prefix="/api")
