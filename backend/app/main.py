import logging
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.core.middleware import (
    AuditMiddleware,
    RequestLoggingMiddleware,
    global_exception_handler,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: open Redis connection and sync number generators. Shutdown: close Redis."""
    app.state.redis = await aioredis.from_url(
        settings.REDIS_URL, decode_responses=True
    )
    logger.info(
        "Starting %s in %s environment", settings.APP_NAME, settings.APP_ENV
    )

    try:
        from app.db.session import AsyncSessionLocal
        from app.utils.number_generator import sync_from_db

        entity_types = ["user", "publisher", "book", "kyc", "download", "review"]
        async with AsyncSessionLocal() as db:
            for entity_type in entity_types:
                await sync_from_db(entity_type, db, app.state.redis)
        logger.info("Redis counters synced from DB")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not sync Redis counters: %s", exc)

    yield

    await app.state.redis.aclose()
    logger.info("Redis connection closed")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Outermost middleware runs first on the way in and last on the way out
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(AuditMiddleware)

    app.add_exception_handler(Exception, global_exception_handler)

    if settings.STORAGE_PROVIDER == "local":
        import os

        os.makedirs("/tmp/digital-library", exist_ok=True)
        app.mount(
            "/static",
            StaticFiles(directory="/tmp/digital-library"),
            name="static",
        )

    app.include_router(api_router)

    return app


app = create_app()
