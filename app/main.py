import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import wandb
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.api.routes import content, health
from app.core.config import get_settings
from app.core.database import init_db
from app.core.exceptions import setup_exception_handlers
from app.core.middleware import add_middlewares


async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    await init_db()
    logger.info("Database initialized")
    if settings.WANDB_API_KEY:
        wandb.init(
            project=settings.WANDB_PROJECT,
            config={
                "app_version": settings.APP_VERSION,
                "environment": "production" if not settings.DEBUG else "development"
            }
        )
        logger.info("Weights & Biases initialized")
    yield
    if settings.WANDB_API_KEY:
        wandb.finish()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Snappy content generation for Reels, Shorts, and TikTok",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.DEBUG else ["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    add_middlewares(app)
    setup_exception_handlers(app)
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(content.router, prefix="/api/v1/content", tags=["content"])
    
    return app


# Create the app instance
app = create_app()


@app.get("/")
async def root():
    return {
        "message": "ReelsBot API is up — let's make something catchy.",
        "version": get_settings().APP_VERSION,
        "docs": "/docs"
    }