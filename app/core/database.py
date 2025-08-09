"""Database configuration and session management."""

import asyncio
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

settings = get_settings()

# Create async engine for SQLite
if settings.DATABASE_URL.startswith("sqlite"):
    # Convert sqlite URL to async format
    async_database_url = settings.DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
    engine = create_async_engine(async_database_url, echo=settings.DEBUG)
else:
    engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base class for all models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        # Import all models to ensure they are registered
        from app.models import content, user  # noqa: F401
        
        await conn.run_sync(Base.metadata.create_all)