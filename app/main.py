"""
Majiscope Backend - Main Entry Point
FastAPI application initialization and route registration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from contextlib import asynccontextmanager

from app.config import settings
from app.database.session import engine
from app.middleware import LoggingMiddleware, RequestIDMiddleware, RateLimitMiddleware, register_exception_handlers
from app.models import Base
from app.api import (
    auth_router,
    users_router,
    utilities_router,
    dmas_router,
    teams_router,
    engineers_router,
    reports_router,
    utility_managers_router,
    dma_managers_router,
    notifications_router,
    push_tokens_router,
    logs_router,
    health_router,
    uploads_router,
)
from app.services.database_migrations import run_heavy_startup_migrations, run_safe_startup_migrations
from import_legacy_duwasa_reports import DEFAULT_CSV_PATH, import_legacy_duwasa_data

# ============================================================
# Lifecycle Events
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events
    """
    print("=" * 60)
    print(f"🚀 {settings.app_name} v{settings.app_version} Starting...")
    print(f"   Environment: {settings.environment}")
    print(f"   Backend URL: http://{settings.host}:{settings.port}")
    print(f"   Frontend URL: {settings.frontend_url}")
    print(f"   CORS Origins: {settings.get_cors_origins()}")
    print(f"   CORS Origin Regex: {settings.cors_origin_regex}")
    print(f"   Safe Startup Migrations: always on")
    print(f"   Heavy Startup Migrations Enabled: {settings.run_startup_migrations}")
    print(f"   Startup Schema Sync Enabled: {settings.run_startup_schema_sync}")
    print(f"   Legacy DUWASA Startup Import: {settings.legacy_duwasa_import_on_startup}")
    print("=" * 60)
    run_safe_startup_migrations(engine)
    if settings.run_startup_migrations:
        run_heavy_startup_migrations(engine)
    if settings.run_startup_schema_sync:
        Base.metadata.create_all(bind=engine)
    if settings.legacy_duwasa_import_on_startup:
        csv_path = (
            settings.legacy_duwasa_import_csv_path.strip()
            or str(DEFAULT_CSV_PATH)
        )
        try:
            import_legacy_duwasa_data(
                database_url=settings.database_url,
                csv_path=csv_path,
                limit=settings.legacy_duwasa_import_limit,
                execute=True,
            )
        except Exception as exc:
            print(f"Legacy DUWASA startup import failed: {exc}")
            if settings.legacy_duwasa_import_strict:
                raise
    yield
    print("=" * 60)
    print(f"🛑 {settings.app_name} Shutting Down...")
    print("=" * 60)


# ============================================================
# FastAPI Application
# ============================================================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Water Leakage Management System - Backend API",
    lifespan=lifespan,
)

# ============================================================
# Global Middleware & Exception Handlers
# ============================================================

# Add custom middleware first.
# CORSMiddleware must be added last so it runs first and can answer browser
# OPTIONS preflight requests before the custom middleware chain.
app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)

# ============================================================
# CORS Configuration
# ============================================================
# Frontend URL is dynamically included in CORS origins via settings.get_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
    max_age=86400,
)

# Register global exception handlers
register_exception_handlers(app)

# ============================================================
# API Routes
# ============================================================

# Register all API routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(utilities_router)
app.include_router(dmas_router)
app.include_router(teams_router)
app.include_router(engineers_router)
app.include_router(reports_router)
app.include_router(utility_managers_router)
app.include_router(dma_managers_router)
app.include_router(notifications_router)
app.include_router(push_tokens_router)
app.include_router(logs_router)
app.include_router(health_router)
app.include_router(uploads_router)

# ============================================================
# Health Check & Status Endpoints
# ============================================================
# Health check endpoints are provided by health_router
# See app/api/health.py for detailed health checks


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint
    Returns API information
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": f"http://{settings.host}:{settings.port}/docs",
        "api_prefix": settings.api_prefix,
    }


@app.options("/{full_path:path}", include_in_schema=False)
async def cors_preflight_passthrough(full_path: str):
    """
    Safety net for browsers issuing OPTIONS preflight requests.
    CORSMiddleware should normally handle these, but keeping an explicit route
    avoids framework/router edge cases during production deploys.
    """
    return Response(status_code=204)


@app.get("/api", tags=["root"])
async def api_root():
    """
    API root endpoint
    Returns information about available endpoints
    """
    return {
        "message": "Majiscope API",
        "version": settings.app_version,
        "endpoints": {
            "auth": f"{settings.api_prefix}/auth",
            "users": f"{settings.api_prefix}/users",
            "utilities": f"{settings.api_prefix}/utilities",
            "dmas": f"{settings.api_prefix}/dmas",
            "teams": f"{settings.api_prefix}/teams",
            "engineers": f"{settings.api_prefix}/engineers",
            "reports": f"{settings.api_prefix}/reports",
            "dma_managers": f"{settings.api_prefix}/dma-managers",
            "utility_managers": f"{settings.api_prefix}/utility-managers",
            "notifications": f"{settings.api_prefix}/notifications",
            "push_tokens": f"{settings.api_prefix}/push-tokens",
            "logs": f"{settings.api_prefix}/logs",
        },
        "documentation": "/docs",
        "openapi_schema": "/openapi.json",
    }


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info",
    )
