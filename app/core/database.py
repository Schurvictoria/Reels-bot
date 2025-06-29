import asyncio
import os
from typing import AsyncGenerator, Optional

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

settings = get_settings()

if os.environ.get("PYTEST_CURRENT_TEST"):
    engine = None  # type: ignore
else:
    if settings.DATABASE_URL.startswith("sqlite"):
        async_database_url = settings.DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
        engine = create_async_engine(async_database_url, echo=settings.DEBUG)
    else:
        engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)

AsyncSessionLocal: Optional[async_sessionmaker[AsyncSession]]
if engine is None:
    AsyncSessionLocal = None
else:
    AsyncSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if AsyncSessionLocal is None:
        raise RuntimeError("Database session not initialized in test mode")
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    if engine is None:
        return
    async with engine.begin() as conn:
        from app.models import content, user  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)