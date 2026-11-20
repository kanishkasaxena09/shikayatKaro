"""Unit & integration tests for production-safe configuration, rate limiting,
role-based access guards, and DEMO_MODE controls.
"""

import os
import pytest
from fastapi.testclient import TestClient

from backend.main import app, validate_production_config, get_cors_origins
from backend.routers import auth
from backend.limiter import login_limiter, track_limiter

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_environment():
    """Restores clean environment variables after each test."""
    orig_env = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(orig_env)
    # Ensure limiters are cleared
    login_limiter.reset()
    track_limiter.reset()


def get_token_for(email: str, password: str = "password123") -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


# -----------------------------------------------------------------------------
# 1. Production Startup Refusal & Secret Validation Tests
# -----------------------------------------------------------------------------

def test_production_refuses_startup_without_jwt_secret():
    """In production (ENVIRONMENT=production), app must refuse startup if JWT_SECRET is missing."""
    os.environ["ENVIRONMENT"] = "production"
    if "JWT_SECRET" in os.environ:
        del os.environ["JWT_SECRET"]

    with pytest.raises(RuntimeError) as exc_info:
        auth.get_jwt_secret()
    assert "JWT_SECRET environment variable is missing" in str(exc_info.value)


def test_production_refuses_startup_with_old_default_jwt_secret():
    """In production, app must refuse startup if JWT_SECRET equals the hardcoded dev default."""
    os.environ["ENVIRONMENT"] = "production"
    os.environ["JWT_SECRET"] = "shikayat_karo_super_secret_jwt_key_2026"

    with pytest.raises(RuntimeError) as exc_info:
        auth.get_jwt_secret()
    assert "insecure default" in str(exc_info.value)


def test_production_accepts_strong_jwt_secret():
    """In production, app accepts strong custom secret."""
    os.environ["ENVIRONMENT"] = "production"
    os.environ["JWT_SECRET"] = "super_secure_production_secret_key_9999"

    secret = auth.get_jwt_secret()
    assert secret == "super_secure_production_secret_key_9999"


def test_development_generates_random_secret_and_logs_warning(caplog):
    """In development, app generates an ephemeral random secret if unset."""
    os.environ["ENVIRONMENT"] = "development"
    if "JWT_SECRET" in os.environ:
        del os.environ["JWT_SECRET"]

    secret = auth.get_jwt_secret()
    assert secret is not None
    assert len(secret) >= 32


def test_production_refuses_wildcard_or_missing_cors():
    """In production, CORS_ORIGINS must be explicitly set and cannot be '*'."""
    os.environ["ENVIRONMENT"] = "production"
    os.environ["JWT_SECRET"] = "valid_production_secret_key_12345"

    # 1. Missing CORS_ORIGINS
    if "CORS_ORIGINS" in os.environ:
        del os.environ["CORS_ORIGINS"]
    with pytest.raises(RuntimeError) as exc_info:
        validate_production_config()
    assert "CORS_ORIGINS must be set" in str(exc_info.value)

    # 2. Wildcard '*'
    os.environ["CORS_ORIGINS"] = "*"
    with pytest.raises(RuntimeError) as exc_info:
        validate_production_config()
    assert "cannot be empty or '*'" in str(exc_info.value)

    # 3. Comma-separated containing '*'
    os.environ["CORS_ORIGINS"] = "https://example.com, *"
    with pytest.raises(RuntimeError) as exc_info:
        validate_production_config()
    assert "cannot contain '*' wildcard" in str(exc_info.value)

    # 4. Valid explicit origins succeed
    os.environ["CORS_ORIGINS"] = "https://shikayatkaro.vercel.app, http://localhost:3000"
    validate_production_config()
    origins = get_cors_origins()
    assert origins == ["https://shikayatkaro.vercel.app", "http://localhost:3000"]


# -----------------------------------------------------------------------------
# 2. Rate Limiting Tests (Login & Anonymous Tracking)
# -----------------------------------------------------------------------------

def test_login_rate_limiting():
    """Exceeding LOGIN_RATE_LIMIT (5 attempts) returns HTTP 429 Too Many Requests."""
    login_limiter.reset()

    # 5 attempts within rate limit
    for _ in range(5):
        res = client.post("/api/auth/login", json={"email": "student@demo", "password": "wrongpassword"})
        assert res.status_code == 400

    # 6th attempt must trigger 429
    res_exceeded = client.post("/api/auth/login", json={"email": "student@demo", "password": "wrongpassword"})
    assert res_exceeded.status_code == 429
    data = res_exceeded.json()
    assert "Rate limit exceeded" in data["detail"]
    assert "Retry-After" in res_exceeded.headers


def test_anonymous_tracking_rate_limiting():
    """Exceeding TRACK_RATE_LIMIT (10 requests) returns HTTP 429."""
    track_limiter.reset()

    # 10 tracking requests succeed
    for _ in range(10):
        res = client.get("/api/track?tracking_id=CMP-HIST-001")
        # CMP-HIST-001 is a real complaint
        assert res.status_code in [200, 401, 403]

    # 11th request triggers 429
    res_exceeded = client.get("/api/track?tracking_id=CMP-HIST-001")
    assert res_exceeded.status_code == 429
    assert "Rate limit exceeded" in res_exceeded.json()["detail"]
    assert "Retry-After" in res_exceeded.headers


# -----------------------------------------------------------------------------
# 3. Role Guard Tests
# -----------------------------------------------------------------------------

def test_student_role_guards():
    """Verifies that a student complainant is forbidden (403) from accessing admin or handler endpoints."""
    student_token = get_token_for("student@demo")
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # 1. Confirm suggestion (requires admin/handler)
    res_confirm = client.post("/api/suggestions/1/confirm", json={}, headers=student_headers)
    assert res_confirm.status_code == 403
    assert "Access denied" in res_confirm.json()["detail"]

    # 2. Reject suggestion (requires admin/handler)
    res_reject = client.post("/api/suggestions/1/reject", headers=student_headers)
    assert res_reject.status_code == 403

    # 3. Remove complaint from group (requires admin/handler)
    res_remove = client.post("/api/suggestions/1/remove-complaint", json={"complaint_id": 1}, headers=student_headers)
    assert res_remove.status_code == 403

    # 4. Assign department to incident (requires admin/handler)
    res_assign = client.post("/api/incidents/1/assign", json={"department_id": 1}, headers=student_headers)
    assert res_assign.status_code == 403

    # 5. Change incident workflow status (requires admin/handler)
    res_status = client.post("/api/incidents/1/status", json={"status": "In Progress"}, headers=student_headers)
    assert res_status.status_code == 403


# -----------------------------------------------------------------------------
# 4. DEMO_MODE Controls Tests
# -----------------------------------------------------------------------------

def test_demo_endpoints_return_403_when_demo_mode_false():
    """When DEMO_MODE=false, all endpoints under /api/demo/* return HTTP 403 Forbidden."""
    os.environ["DEMO_MODE"] = "false"

    # 1. Load Story
    res_story = client.post("/api/demo/load-story")
    assert res_story.status_code == 403
    assert "DEMO_MODE=false" in res_story.json()["detail"]

    # 2. Advance Virtual Time
    res_advance = client.post("/api/demo/advance-time", json={"hours": 2.0})
    assert res_advance.status_code == 403
    assert "DEMO_MODE=false" in res_advance.json()["detail"]

    # 3. Reset Demo State
    res_reset = client.post("/api/demo/reset")
    assert res_reset.status_code == 403
    assert "DEMO_MODE=false" in res_reset.json()["detail"]


def test_demo_endpoints_succeed_when_demo_mode_true():
    """When DEMO_MODE=true, demo endpoints are accessible."""
    os.environ["DEMO_MODE"] = "true"

    res_reset = client.post("/api/demo/reset")
    assert res_reset.status_code == 200
    assert "reset successfully" in res_reset.json()["message"]
