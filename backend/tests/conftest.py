"""Shared pytest fixtures for Project Shikayat Karo.

Follows the pattern from Brandpilot's conftest:
- Temporary in-memory SQLite database per test session with StaticPool
- Auto-creates all tables and seeds master data
- Overrides FastAPI get_db dependency
- Redirects SessionLocal to the test database so tests never touch dev database
- Automatically resets virtual clock before and after every test
"""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Ensure test mode and fallback embedder are set immediately
os.environ["TESTING"] = "1"
os.environ["EMBEDDER"] = "fallback"

import backend.database as db_module
from backend.database import Base, get_db
from backend.main import app
from backend.seed import seed_database
from backend.clock import reset_time
from backend.models import User
from backend.routers.auth import create_access_token

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Patch backend.database engine and SessionLocal so direct calls in tests use test DB
db_module.engine = engine
db_module.SessionLocal = TestingSessionLocal


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Session-scoped fixture to create tables, seed data, and override app DB dependency."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    seed_database(db=session, bind_engine=engine)
    session.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


from backend.limiter import login_limiter, track_limiter


@pytest.fixture(autouse=True)
def reset_virtual_clock():
    """Resets the virtual clock to UTC real-world time before and after each test."""
    reset_time()
    login_limiter.reset()
    track_limiter.reset()
    yield
    reset_time()
    login_limiter.reset()
    track_limiter.reset()


@pytest.fixture(scope="function")
def db_session():
    """Yields a database session bound to the test database."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Yields a FastAPI TestClient with get_db bound to the test session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    # Restore session-level get_db override
    def default_override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = default_override_get_db


@pytest.fixture(scope="function")
def auth_headers(db_session):
    """Generates auth headers for manager, handler, and student test users."""
    admin = db_session.query(User).filter(User.email == "admin@demo").first()
    handler = db_session.query(User).filter(User.email == "handler@demo").first()
    student = db_session.query(User).filter(User.email == "student@demo").first()

    admin_token = create_access_token({"sub": str(admin.id)}) if admin else ""
    handler_token = create_access_token({"sub": str(handler.id)}) if handler else ""
    student_token = create_access_token({"sub": str(student.id)}) if student else ""

    return {
        "admin": {"Authorization": f"Bearer {admin_token}"},
        "handler": {"Authorization": f"Bearer {handler_token}"},
        "student": {"Authorization": f"Bearer {student_token}"},
    }
