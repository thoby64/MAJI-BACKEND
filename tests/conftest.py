"""
Pytest Configuration and Fixtures
Shared test fixtures and configuration
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.session import get_db
from app.models.base import Base
from app.models import User
from app.security.auth import hash_password


# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for tests"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db():
    """Create test database and tables"""
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session):
    """Create test client with overridden database"""
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db: Session) -> User:
    """Create a test user"""
    user = User(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        phone_number="+1234567890",
        password_hash=hash_password("testpassword123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user: User):
    """Generate auth headers with valid token"""
    from app.security.auth import create_access_token
    
    token = create_access_token(test_user.id, test_user.email)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def admin_user(db: Session) -> User:
    """Create an admin test user"""
    user = User(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        phone_number="+9876543210",
        password_hash=hash_password("adminpassword123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_auth_headers(admin_user: User):
    """Generate auth headers for admin user"""
    from app.security.auth import create_access_token
    
    token = create_access_token(admin_user.id, admin_user.email)
    return {"Authorization": f"Bearer {token}"}
