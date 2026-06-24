"""
Database Configuration
SQLAlchemy session and engine setup
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings


def _normalize_database_url(database_url: str) -> str:
    """
    Normalize provider URLs for SQLAlchemy.

    Render/other hosts often provide `postgresql://...` or `postgres://...`.
    We prefer the psycopg v3 SQLAlchemy driver explicitly in production.
    """
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)

    if database_url.startswith("postgresql://") and "+psycopg" not in database_url and "+psycopg2" not in database_url:
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    return database_url

# ============================================================
# Database Engine
# ============================================================

normalized_database_url = _normalize_database_url(settings.database_url)
connect_args = {"check_same_thread": False} if normalized_database_url.startswith("sqlite") else {}

engine = create_engine(
    normalized_database_url,
    echo=settings.debug,  # Print SQL queries in development
    pool_pre_ping=True,  # Verify connection before using
    pool_recycle=300,
    connect_args=connect_args,
)

# ============================================================
# Database Session Factory
# ============================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ============================================================
# Dependency for FastAPI
# ============================================================

def get_db() -> Session:
    """
    Get database session for use in FastAPI dependencies
    
    Usage in routes:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
