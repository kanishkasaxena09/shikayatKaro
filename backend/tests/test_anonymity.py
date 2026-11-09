"""Unit tests for anonymous grievance reporting and strict privacy guarantees."""

import os
os.environ["TESTING"] = "1"

from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal
from backend.models import Complaint, User

client = TestClient(app)


def test_anonymous_submission_privacy():
    """Verifies:
    1. is_anonymous complaints store NO complainant_id in the database.
    2. An 8-character access code is returned upon creation.
    3. Only a salted bcrypt hash is stored in the database.
    4. Complainant identity is completely omitted from the response.
    """
    payload = {
        "text": "Broken window glass in hostel washroom causing sharp glass hazard",
        "affected_count": 4,
        "is_anonymous": True
    }
    resp = client.post("/api/complaints", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    # 1. Plain access code returned on creation
    access_code = data.get("access_code")
    assert access_code is not None
    assert len(access_code) == 8

    complaint_data = data["complaint"]
    tracking_id = complaint_data["tracking_id"]
    assert complaint_data["is_anonymous"] is True
    # Identity MUST be None
    assert complaint_data.get("complainant") is None

    # 2. Check Database directly
    db = SessionLocal()
    try:
        db_cmp = db.query(Complaint).filter(Complaint.tracking_id == tracking_id).first()
        assert db_cmp is not None
        # Strict DB privacy: complainant_id MUST BE NULL
        assert db_cmp.complainant_id is None
        # Plain text access code MUST NOT be stored in DB
        assert db_cmp.access_code_hash is not None
        assert db_cmp.access_code_hash != access_code
        # Hash length check (bcrypt hash is ~60 chars)
        assert len(db_cmp.access_code_hash) >= 50
    finally:
        db.close()


def test_anonymous_tracking_without_login():
    """Verifies that GET /api/track works without login given tracking_id + access_code,
    and returns full tracking status while NEVER exposing any personal identity.
    """
    # 1. Create anonymous complaint
    submit_res = client.post("/api/complaints", json={
        "text": "Stagnant drainage water leaking near mess gate",
        "affected_count": 6,
        "is_anonymous": True
    })
    assert submit_res.status_code == 200
    data = submit_res.json()
    tracking_id = data["complaint"]["tracking_id"]
    access_code = data["access_code"]

    # 2. Track using GET /api/track with valid access code (no auth headers!)
    track_res = client.get(f"/api/track?tracking_id={tracking_id}&access_code={access_code}")
    assert track_res.status_code == 200
    track_data = track_res.json()
    assert track_data["tracking_id"] == tracking_id
    assert track_data["is_anonymous"] is True
    assert track_data.get("complainant") is None
    # No hash leaked in response
    assert "access_code_hash" not in track_data

    # 3. Track with wrong access code -> 403 Forbidden
    wrong_res = client.get(f"/api/track?tracking_id={tracking_id}&access_code=WRONG123")
    assert wrong_res.status_code == 403

    # 4. Track without access code -> 401 Unauthorized
    missing_res = client.get(f"/api/track?tracking_id={tracking_id}")
    assert missing_res.status_code == 401


def test_logged_in_user_submitting_anonymously_remains_anonymous():
    """Even if a logged-in student submits a complaint with is_anonymous=True,
    their user ID must NEVER be stored or associated with the record.
    """
    # Login as demo student
    login_res = client.post("/api/auth/login", json={"email": "student@demo", "password": "password123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Submit anonymous complaint while logged in
    resp = client.post(
        "/api/complaints",
        json={
            "text": "Confidential report of unauthorized individuals in courtyard",
            "is_anonymous": True
        },
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    tracking_id = data["complaint"]["tracking_id"]

    db = SessionLocal()
    try:
        db_cmp = db.query(Complaint).filter(Complaint.tracking_id == tracking_id).first()
        # Student ID must NOT be recorded
        assert db_cmp.complainant_id is None
    finally:
        db.close()
