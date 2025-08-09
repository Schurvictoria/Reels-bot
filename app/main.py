"""Main FastAPI application entry point."""

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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    settings = get_settings()
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Initialize Weights & Biases
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
    
    # Cleanup
    if settings.WANDB_API_KEY:
        wandb.finish()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-powered content generation for social media reels",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.DEBUG else ["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add custom middlewares
    add_middlewares(app)
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Include routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(content.router, prefix="/api/v1/content", tags=["content"])
    
    return app


# Create the app instance
app = create_app()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to ReelsBot API",
        "version": get_settings().APP_VERSION,
        "docs": "/docs"
    }