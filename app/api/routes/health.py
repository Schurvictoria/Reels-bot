"""Health check endpoints."""

from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, str]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "ReelsBot API"
    }


@router.get("/detailed")
async def detailed_health_check(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Detailed health check including database connectivity."""
    settings = get_settings()
    
    # Test database connection
    try:
        await db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "ReelsBot API",
        "version": settings.APP_VERSION,
        "database": db_status,
        "environment": "development" if settings.DEBUG else "production"
    }