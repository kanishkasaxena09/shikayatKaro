"""Production simulation test.

Simulates cold-start production deployment:
- ENVIRONMENT=production
- CORS_ORIGINS set to explicit production frontend domains (no wildcards)
- Strong JWT_SECRET configured
- EMBEDDER configured
- Cold start with fresh database
- Verifies:
  1. Startup / config validation passes
  2. Health check endpoint responds with 200 OK
  3. User authentication / login works with JWT issuance
  4. Complaint submission runs through full AI analysis pipeline
"""

import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import Base, get_db
import backend.database as db_module
from backend.models import User, Department, Location, EscalationRule
from backend.routers.auth import hash_password


def test_production_cold_start_simulation():
    # 1. Configure strict production environment variables
    temp_dir = tempfile.mkdtemp()
    prod_db_path = os.path.join(temp_dir, "prod_coldstart.db")
    prod_db_url = f"sqlite:///{prod_db_path}"

    old_env = os.environ.copy()
    os.environ["ENVIRONMENT"] = "production"
    os.environ["JWT_SECRET"] = "production_super_strong_cryptographic_secret_2026_x99!"
    os.environ["CORS_ORIGINS"] = "https://shikayatkaro.vercel.app,https://admin.shikayatkaro.org"
    os.environ["EMBEDDER"] = "fallback"

    prod_engine = create_engine(prod_db_url, connect_args={"check_same_thread": False})
    ProdSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=prod_engine)

    # Initialize fresh tables on empty database
    Base.metadata.create_all(bind=prod_engine)

    # Seed minimal organization structure for cold-start test
    db = ProdSessionLocal()
    dept = Department(name="Estate & Maintenance", code="EST", description="Estate works")
    db.add(dept)
    loc = Location(name="Main Campus Gate", type="area", grid_x=10.0, grid_y=10.0)
    db.add(loc)
    rule = EscalationRule(priority="High", deadline_hours=24.0, level_1_percent=100.0, level_2_percent=150.0, level_3_percent=200.0)
    db.add(rule)
    user = User(
        email="prod_admin@shikayatkaro.org",
        password_hash=hash_password("ProdPassword!2026"),
        full_name="Production Administrator",
        role="admin"
    )
    db.add(user)
    db.commit()
    db.close()

    def override_prod_get_db():
        session = ProdSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_prod_get_db

    try:
        client = TestClient(app)

        # 2. Health check
        health_res = client.get("/health")
        assert health_res.status_code == 200
        health_data = health_res.json()
        assert health_data["status"] == "healthy"
        assert health_data["environment"] == "production"

        # 3. User Login
        login_res = client.post("/api/auth/login", json={
            "email": "prod_admin@shikayatkaro.org",
            "password": "ProdPassword!2026"
        })
        assert login_res.status_code == 200
        token_data = login_res.json()
        token = token_data["access_token"]
        assert token is not None

        # 4. Submit complaint under production environment
        complaint_res = client.post(
            "/api/complaints",
            json={
                "text": "Main water pipeline valve cracked near campus entrance gate",
                "affected_count": 12,
                "is_anonymous": False
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert complaint_res.status_code == 200
        complaint_data = complaint_res.json()
        assert complaint_data["complaint"]["tracking_id"].startswith("CMP-")
        assert complaint_data["complaint"]["category"] == "Water & Plumbing"
        assert complaint_data["ai_analysis"]["classification"]["category"] == "Water & Plumbing"

    finally:
        # Clean up overrides and environment
        app.dependency_overrides.pop(get_db, None)
        os.environ.clear()
        os.environ.update(old_env)
        prod_engine.dispose()
        try:
            if os.path.exists(prod_db_path):
                os.remove(prod_db_path)
            os.rmdir(temp_dir)
        except Exception:
            pass
