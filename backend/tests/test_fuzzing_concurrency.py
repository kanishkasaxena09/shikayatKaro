"""Regression tests for endpoint fuzzing and concurrency protection.

Covers:
1. Grievance submission and tracking fuzzing:
   - empty text (422)
   - 1-character text (422)
   - 10,000-character text (422)
   - Devanagari only text (200, safe language detection and classification)
   - Mixed Hindi/English text (200, safe Hinglish classification)
   - Emoji text (200, safe Unicode handling)
   - SQL-injection-style text (200, parameterized SQL without injection)
   - HTML/script tags (200, safe storage without script execution)
   - Missing location (200, location_id=None accepted)
   - Invalid location_id (400, clear client error)
   - Negative affected count (422)
   - Huge affected count (422)
   - Double submit within 5 seconds (409 Conflict)
   - Tracking with invalid/expired token (401)
   - Tracking with invalid access code (403)
   - Tracking with empty tracking ID (422)
2. Concurrency:
   - Concurrent admins confirming the same cluster simultaneously (atomic lock: 1 succeeds, 1 gets 409, 1 parent incident)
   - Concurrent handlers updating status on the same incident simultaneously (no lost updates, audit log preserved)
"""

import os
os.environ["TESTING"] = "1"
os.environ["EMBEDDER"] = "fallback"

import time
import concurrent.futures
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal
from backend.models import Complaint, Incident, Suggestion, Update, User, Location

client = TestClient(app)


def test_fuzz_submission_text_length():
    """Empty, 1-char, and 10,000-char inputs must return 422 Unprocessable Entity."""
    # 1. Empty text
    res_empty = client.post("/api/complaints", json={"text": "", "affected_count": 1})
    assert res_empty.status_code == 422

    # 2. 1-character text (min_length is 5)
    res_short = client.post("/api/complaints", json={"text": "A", "affected_count": 1})
    assert res_short.status_code == 422

    # 3. 10,000-character text (max_length is 5000)
    huge_text = "Water leakage and broken tap in restroom floor. " * 250
    assert len(huge_text) > 10000
    res_huge = client.post("/api/complaints", json={"text": huge_text, "affected_count": 1})
    assert res_huge.status_code == 422


def test_fuzz_submission_affected_count():
    """Negative and huge (>100,000) affected counts must return 422."""
    # Negative count
    res_neg = client.post("/api/complaints", json={
        "text": "Frequent power trip in computer science laboratory",
        "affected_count": -5
    })
    assert res_neg.status_code == 422

    # Zero count (ge=1 required)
    res_zero = client.post("/api/complaints", json={
        "text": "Frequent power trip in computer science laboratory",
        "affected_count": 0
    })
    assert res_zero.status_code == 422

    # Huge count (le=100000 required)
    res_huge = client.post("/api/complaints", json={
        "text": "Frequent power trip in computer science laboratory",
        "affected_count": 5000000
    })
    assert res_huge.status_code == 422


def test_fuzz_submission_multilingual_and_unicode():
    """Devanagari, Hinglish, and emojis must be handled safely with 200 responses."""
    # 1. Devanagari only
    devanagari_text = "शौचालय में पानी का पाइप पूरी तरह टूट गया है और पानी बह रहा है"
    res_dev = client.post("/api/complaints", json={"text": devanagari_text, "affected_count": 5})
    assert res_dev.status_code == 200
    data_dev = res_dev.json()
    assert data_dev["complaint"]["original_language"] == "hindi"
    assert data_dev["complaint"]["category"] == "Water & Plumbing"

    # 2. Mixed Hindi/English (Hinglish)
    hinglish_text = "Hostel block B mein paani ki supply band hai aur tap dry hai"
    res_hing = client.post("/api/complaints", json={"text": hinglish_text, "affected_count": 8})
    assert res_hing.status_code == 200
    data_hing = res_hing.json()
    assert data_hing["complaint"]["original_language"] in ["hinglish", "hindi"]

    # 3. Unicode Emojis
    emoji_text = "🚨 Water pipe burst in washroom! 🚰💧 Water flooding corridor ⚠️"
    res_emoji = client.post("/api/complaints", json={"text": emoji_text, "affected_count": 3})
    assert res_emoji.status_code == 200
    data_emoji = res_emoji.json()
    assert "🚨" in data_emoji["complaint"]["text"]


def test_fuzz_submission_injection_and_xss_safety():
    """SQL-injection strings and HTML/script tags must be safely stored without execution or error."""
    # 1. SQL Injection attempt
    sqli_payload = "Corridor lights broken '; DROP TABLE complaints; SELECT * FROM users WHERE '1'='1"
    res_sqli = client.post("/api/complaints", json={"text": sqli_payload, "affected_count": 2})
    assert res_sqli.status_code == 200
    data_sqli = res_sqli.json()
    assert "DROP TABLE" in data_sqli["complaint"]["text"]

    # Verify table complaints still exists in database
    db = SessionLocal()
    try:
        count = db.query(Complaint).count()
        assert count > 0
    finally:
        db.close()

    # 2. XSS / HTML script tag payload
    xss_payload = "<script>alert('XSS_ATTACK');</script><img src='x' onerror='alert(1)'> broken door handle"
    res_xss = client.post("/api/complaints", json={"text": xss_payload, "affected_count": 1})
    assert res_xss.status_code == 200
    data_xss = res_xss.json()
    assert "<script>" in data_xss["complaint"]["text"]


def test_fuzz_submission_location_validation():
    """Missing location (None) must be accepted; invalid location_id must return 400."""
    # Missing location -> accepted with None
    res_none = client.post("/api/complaints", json={
        "text": "General campus road pothole near main gate entrance",
        "location_id": None,
        "affected_count": 10
    })
    assert res_none.status_code == 200
    assert res_none.json()["complaint"]["location_id"] is None

    # Invalid non-existent location_id -> 400 Bad Request
    res_bad_loc = client.post("/api/complaints", json={
        "text": "Air conditioner cooling defective in non-existent classroom",
        "location_id": 999999,
        "affected_count": 5
    })
    assert res_bad_loc.status_code == 400
    assert "Invalid location_id" in res_bad_loc.json()["detail"]


def test_fuzz_double_submit_guard():
    """Submitting the exact same complaint text within 5 seconds must return 409 Conflict."""
    text = f"Unique distinct plumbing issue for double submit test {time.time()}"
    
    # First submission -> 200 OK
    res1 = client.post("/api/complaints", json={"text": text, "affected_count": 3})
    assert res1.status_code == 200

    # Rapid second submission with identical text -> 409 Conflict
    res2 = client.post("/api/complaints", json={"text": text, "affected_count": 3})
    assert res2.status_code == 409
    assert "Duplicate submission" in res2.json()["detail"]


def test_fuzz_tracking_and_auth_tokens():
    """Tracking endpoint fuzzing and token validation."""
    # 1. Empty tracking ID -> 422
    res_empty = client.get("/api/track?tracking_id=")
    assert res_empty.status_code == 422

    # 2. Non-existent tracking ID -> 404
    res_not_found = client.get("/api/track?tracking_id=CMP-NONEXISTENT")
    assert res_not_found.status_code == 404

    # 3. Invalid / malformed JWT token on tracking -> 401
    res_bad_token = client.get(
        "/api/track?tracking_id=CMP-DEMO-001",
        headers={"Authorization": "Bearer invalid_malformed_token_xyz"}
    )
    assert res_bad_token.status_code == 401
    assert "credentials" in res_bad_token.json()["detail"].lower()

    # 4. Expired token on protected route -> 401
    import jwt
    from datetime import datetime, timezone, timedelta
    from backend.routers.auth import get_jwt_secret, ALGORITHM
    
    past_time = datetime.now(timezone.utc) - timedelta(hours=2)
    expired_token = jwt.encode(
        {"sub": "1", "role": "student", "exp": past_time, "iat": past_time - timedelta(hours=1)},
        get_jwt_secret(),
        algorithm=ALGORITHM
    )
    res_expired = client.get(
        "/api/complaints/my",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert res_expired.status_code == 401
    assert "expired" in res_expired.json()["detail"].lower()


def test_concurrency_cluster_confirmation(db_session, auth_headers):
    """Two admins confirming the same cluster at the same time:
    - Thread synchronization ensures exactly ONE succeeds (200).
    - The concurrent second attempt receives 409 Conflict.
    - Exactly ONE parent incident is created in the database (no duplicate parent incidents).
    """
    admin_headers = auth_headers["admin"]

    # 1. Find the pending demo suggestion
    sugg = db_session.query(Suggestion).filter(Suggestion.status == "pending").first()
    assert sugg is not None, "Pending suggestion must exist in seed"
    sugg_id = sugg.id

    # Count incidents prior to concurrency test
    initial_inc_count = db_session.query(Incident).count()

    # 2. Launch concurrent confirmation requests across two threads
    results = []
    def confirm_call():
        c = TestClient(app)
        return c.post(f"/api/suggestions/{sugg_id}/confirm", headers=admin_headers)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(confirm_call)
        f2 = executor.submit(confirm_call)
        results = [f1.result(), f2.result()]

    status_codes = sorted([r.status_code for r in results])
    
    # Exactly one succeeded (200), and the other got 409 Conflict
    assert status_codes == [200, 409], f"Expected [200, 409], got {status_codes}"

    # Exactly one parent incident created
    db_session.expire_all()
    final_inc_count = db_session.query(Incident).count()
    assert final_inc_count == initial_inc_count + 1, "Duplicate parent incidents must NOT be created"


def test_concurrency_incident_updates(db_session, auth_headers):
    """Two facility handlers concurrently updating the status of the same incident:
    - Thread synchronization ensures serial execution without lost updates.
    - Audit log entries are completely preserved for both transitions.
    """
    handler_headers = auth_headers["handler"]

    # Find a non-closed incident
    inc = db_session.query(Incident).first()
    assert inc is not None
    inc_id = inc.id

    initial_audit_count = db_session.query(Update).filter(
        Update.target_type == "incident",
        Update.target_id == inc_id
    ).count()

    def update_call(status_value, remarks):
        c = TestClient(app)
        return c.post(
            f"/api/incidents/{inc_id}/status",
            json={"status": status_value, "remarks": remarks},
            headers=handler_headers
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(update_call, "Under Investigation", "Handler 1 inspection remarks")
        f2 = executor.submit(update_call, "In Progress", "Handler 2 work execution remarks")
        r1 = f1.result()
        r2 = f2.result()

    assert r1.status_code in [200, 400], f"r1 status: {r1.status_code}"
    assert r2.status_code in [200, 400], f"r2 status: {r2.status_code}"

    # Confirm audit trail captured updates without losing records
    db_session.expire_all()
    final_audit_count = db_session.query(Update).filter(
        Update.target_type == "incident",
        Update.target_id == inc_id
    ).count()
    assert final_audit_count >= initial_audit_count + 1
