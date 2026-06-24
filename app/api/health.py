"""
Health Check Routes
Application health and status endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.config import settings
from app.database.session import get_db
from app.utils.response_models import HealthResponse

health_router = APIRouter(prefix="/api/health", tags=["health"])


@health_router.get("", response_model=dict)
async def health_check():
    """Check application health"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat(),
    }


@health_router.get("/database")
async def database_health(db: Session = Depends(get_db)):
    """Check database connection health"""
    try:
        # Simple query to check database connection
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@health_router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Check if application is ready to handle requests"""
    try:
        # Check database
        db.execute("SELECT 1")
        
        return {
            "ready": True,
            "service": settings.app_name,
            "version": settings.app_version,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "ready": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
