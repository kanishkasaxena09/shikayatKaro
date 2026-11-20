"""Unit and API tests for recurring-issue detection and permanent fix remediation.

Covers:
1. Recurrence Rule Definition:
   Same category at the same location/block producing >= 3 distinct parent incidents
   within 30 days of virtual-clock time.
2. Boundary Tests:
   - Incident Count Boundary: exactly 2 incidents (not recurring) vs exactly 3 incidents (recurring).
   - Time Window Boundary: 3 incidents with oldest at 31 days ago (not recurring) vs 29 days ago (recurring).
3. Configurable Thresholds:
   - Override min_incidents parameter.
   - Override window_days parameter.
4. API Endpoints:
   - GET /api/analytics/recurring: lists recurring patterns with location, category, incident count,
     total affected, avg resolution time, days since last occurrence, and incident links.
   - POST /api/analytics/recurring/mark-fix: role-guarded action to schedule permanent remediation task.
"""

from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import SessionLocal
from backend.models import Incident, Location, Department, PermanentFixTask, Update
from backend.clock import get_current_time, reset_time
from backend.ai.recurrence import detect_recurring_issues, get_block_location

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_state():
    """Ensure virtual clock and demo state are pristine before and after tests."""
    reset_time()
    client.post("/api/demo/reset")
    yield
    reset_time()
    client.post("/api/demo/reset")


def get_token(email: str = "admin@demo") -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_boundary_incident_count_two_vs_three():
    """Boundary test: exactly 2 incidents do NOT trigger recurrence; 3 incidents DO trigger it."""
    db = SessionLocal()
    try:
        now = get_current_time()
        sac_loc = db.query(Location).filter(Location.name == "Student Activity Center (SAC)").first()
        assert sac_loc is not None

        # Clean any prior incidents in SAC and its sub-locations for test isolation
        child_loc_ids = [l.id for l in db.query(Location).filter((Location.id == sac_loc.id) | (Location.parent_id == sac_loc.id)).all()]
        db.query(Incident).filter(Incident.location_id.in_(child_loc_ids), Incident.category == "Safety & Security").delete()
        db.commit()

        # Step 1: Create exactly 1 incident
        inc1 = Incident(
            code="INC-TEST-BOUND-1",
            title="Boundary Test 1",
            category="Safety & Security",
            location_id=sac_loc.id,
            priority="Medium",
            status="Resolved",
            created_at=now - timedelta(days=10),
            resolved_at=now - timedelta(days=9, hours=20)
        )
        db.add(inc1)
        db.commit()

        res1 = detect_recurring_issues(db, min_incidents=3, window_days=30, reference_time=now)
        sac_recurring = [r for r in res1 if r["block_id"] == sac_loc.id and r["category"] == "Safety & Security"]
        assert len(sac_recurring) == 0, "1 incident must not trigger recurring issue"

        # Step 2: Add 2nd incident (boundary: exactly 2 incidents)
        inc2 = Incident(
            code="INC-TEST-BOUND-2",
            title="Boundary Test 2",
            category="Safety & Security",
            location_id=sac_loc.id,
            priority="Medium",
            status="Resolved",
            created_at=now - timedelta(days=5),
            resolved_at=now - timedelta(days=4, hours=20)
        )
        db.add(inc2)
        db.commit()

        res2 = detect_recurring_issues(db, min_incidents=3, window_days=30, reference_time=now)
        sac_recurring = [r for r in res2 if r["block_id"] == sac_loc.id and r["category"] == "Safety & Security"]
        assert len(sac_recurring) == 0, "Exactly 2 incidents must NOT trigger recurring issue (threshold is 3)"

        # Step 3: Add 3rd incident (boundary: exactly 3 incidents)
        inc3 = Incident(
            code="INC-TEST-BOUND-3",
            title="Boundary Test 3",
            category="Safety & Security",
            location_id=sac_loc.id,
            priority="High",
            status="Resolved",
            created_at=now - timedelta(days=1),
            resolved_at=now - timedelta(hours=18)
        )
        db.add(inc3)
        db.commit()

        res3 = detect_recurring_issues(db, min_incidents=3, window_days=30, reference_time=now)
        sac_recurring = [r for r in res3 if r["block_id"] == sac_loc.id and r["category"] == "Safety & Security"]
        assert len(sac_recurring) == 1, "Exactly 3 incidents MUST trigger recurring issue"
        rec = sac_recurring[0]
        assert rec["incident_count"] == 3
        assert set(rec["incident_codes"]) == {"INC-TEST-BOUND-1", "INC-TEST-BOUND-2", "INC-TEST-BOUND-3"}
    finally:
        db.close()


def test_boundary_time_window_31_vs_29_days():
    """Boundary test: 3 incidents where the oldest is 31 days ago (outside 30d window) does NOT trigger;
    when oldest is 29 days ago (inside 30d window), it DOES trigger.
    """
    db = SessionLocal()
    try:
        now = get_current_time()
        admin_loc = db.query(Location).filter(Location.name == "Administrative Building").first()
        assert admin_loc is not None

        child_loc_ids = [l.id for l in db.query(Location).filter((Location.id == admin_loc.id) | (Location.parent_id == admin_loc.id)).all()]
        db.query(Incident).filter(Incident.location_id.in_(child_loc_ids), Incident.category == "Administrative").delete()
        db.commit()

        # Incident 1: 3 days ago (inside window)
        inc1 = Incident(
            code="INC-TIME-1",
            title="Time Window Test 1",
            category="Administrative",
            location_id=admin_loc.id,
            priority="Medium",
            status="Resolved",
            created_at=now - timedelta(days=3),
            resolved_at=now - timedelta(days=2)
        )
        # Incident 2: 15 days ago (inside window)
        inc2 = Incident(
            code="INC-TIME-2",
            title="Time Window Test 2",
            category="Administrative",
            location_id=admin_loc.id,
            priority="Medium",
            status="Resolved",
            created_at=now - timedelta(days=15),
            resolved_at=now - timedelta(days=14)
        )
        # Incident 3: 31 days ago (OUTSIDE 30-day window: boundary)
        inc3 = Incident(
            code="INC-TIME-3",
            title="Time Window Test 3",
            category="Administrative",
            location_id=admin_loc.id,
            priority="Medium",
            status="Resolved",
            created_at=now - timedelta(days=31),
            resolved_at=now - timedelta(days=30)
        )
        db.add_all([inc1, inc2, inc3])
        db.commit()

        # Check with window_days=30: only 2 incidents in window -> not recurring
        res_31d = detect_recurring_issues(db, min_incidents=3, window_days=30, reference_time=now)
        admin_recurring = [r for r in res_31d if r["block_id"] == admin_loc.id and r["category"] == "Administrative"]
        assert len(admin_recurring) == 0, "Incident at 31 days ago must fall outside the 30-day window"

        # Now move incident 3 to 29 days ago (INSIDE 30-day window: boundary)
        inc3.created_at = now - timedelta(days=29)
        inc3.resolved_at = now - timedelta(days=28)
        db.commit()

        res_29d = detect_recurring_issues(db, min_incidents=3, window_days=30, reference_time=now)
        admin_recurring = [r for r in res_29d if r["block_id"] == admin_loc.id and r["category"] == "Administrative"]
        assert len(admin_recurring) == 1, "All 3 incidents within 29 days must trigger recurring issue"
        assert admin_recurring[0]["incident_count"] == 3
    finally:
        db.close()


def test_configurable_thresholds():
    """Verifies that min_incidents and window_days are dynamically configurable."""
    db = SessionLocal()
    try:
        now = get_current_time()
        lib_loc = db.query(Location).filter(Location.name == "Central Library").first()
        assert lib_loc is not None

        db.query(Incident).filter(Incident.location_id == lib_loc.id).delete()
        db.commit()

        # Add 2 incidents at 40 days ago and 35 days ago
        inc1 = Incident(
            code="INC-CONFIG-1",
            title="Config Test 1",
            category="IT & Network",
            location_id=lib_loc.id,
            priority="Low",
            status="Resolved",
            created_at=now - timedelta(days=40),
            resolved_at=now - timedelta(days=39)
        )
        inc2 = Incident(
            code="INC-CONFIG-2",
            title="Config Test 2",
            category="IT & Network",
            location_id=lib_loc.id,
            priority="Low",
            status="Resolved",
            created_at=now - timedelta(days=35),
            resolved_at=now - timedelta(days=34)
        )
        db.add_all([inc1, inc2])
        db.commit()

        # Default (3 incidents, 30 days): Not recurring
        res_default = detect_recurring_issues(db, min_incidents=3, window_days=30, reference_time=now)
        lib_matches = [r for r in res_default if r["block_id"] == lib_loc.id and r["category"] == "IT & Network"]
        assert len(lib_matches) == 0

        # Custom window (50 days) and threshold (2 incidents): MUST be detected
        res_custom = detect_recurring_issues(db, min_incidents=2, window_days=50, reference_time=now)
        lib_matches = [r for r in res_custom if r["block_id"] == lib_loc.id and r["category"] == "IT & Network"]
        assert len(lib_matches) == 1
        assert lib_matches[0]["incident_count"] == 2
    finally:
        db.close()


def test_api_recurring_issues_and_mark_permanent_fix():
    """API lifecycle test:
    1. GET /api/analytics/recurring returns the seeded recurring issue at Hostel Block B.
    2. Role guard prevents complainants from scheduling a permanent fix.
    3. Admin POST /api/analytics/recurring/mark-fix creates PermanentFixTask and logs audit event.
    4. Subsequent GET /api/analytics/recurring indicates has_permanent_fix == True.
    """
    # 1. Fetch recurring issues
    res = client.get("/api/analytics/recurring")
    assert res.status_code == 200
    recurring_list = res.json()
    assert len(recurring_list) >= 1

    hostel_rec = next((r for r in recurring_list if r["block_name"] == "Hostel Block B" and r["category"] == "Sanitation & Cleanliness"), None)
    assert hostel_rec is not None, "Seeded recurring issue in Hostel Block B Sanitation must be present"
    assert hostel_rec["incident_count"] == 3
    assert len(hostel_rec["incident_codes"]) == 3
    assert hostel_rec["has_permanent_fix"] is False
    assert hostel_rec["permanent_fix_task"] is None
    assert hostel_rec["days_since_last_occurrence"] > 0
    assert hostel_rec["average_resolution_hours"] > 0

    # 2. Role guard: Complainant cannot mark permanent fix
    student_token = get_token("student@demo")
    fix_payload = {
        "category": hostel_rec["category"],
        "location_id": hostel_rec["block_id"],
        "incident_ids": hostel_rec["incident_ids"],
        "due_date_days": 14,
        "title": "Complete overhaul of Hostel Block B drainage manifold and grease traps",
        "notes": "Replace rusted cast iron drainage line with 6-inch UPVC piping."
    }
    forbidden_res = client.post(
        "/api/analytics/recurring/mark-fix",
        json=fix_payload,
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert forbidden_res.status_code == 403

    # 3. Admin can mark permanent fix
    admin_token = get_token("admin@demo")
    create_res = client.post(
        "/api/analytics/recurring/mark-fix",
        json=fix_payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert create_res.status_code == 200
    task_data = create_res.json()
    assert task_data["task_code"].startswith("PFIX-")
    assert task_data["status"] == "Scheduled"
    assert task_data["category"] == "Sanitation & Cleanliness"
    assert task_data["department_name"] == "Estate & Maintenance"
    assert task_data["due_date"] is not None

    # Verify audit log in DB
    db = SessionLocal()
    try:
        audit = db.query(Update).filter(Update.target_type == "permanent_fix", Update.target_id == task_data["id"]).first()
        assert audit is not None
        assert audit.event_type == "permanent_fix_created"
        assert audit.actor_role == "admin"
    finally:
        db.close()

    # 4. Verify GET /api/analytics/recurring now reflects the permanent fix task
    res_after = client.get("/api/analytics/recurring")
    assert res_after.status_code == 200
    after_list = res_after.json()
    updated_rec = next(r for r in after_list if r["id"] == hostel_rec["id"])
    assert updated_rec["has_permanent_fix"] is True
    assert updated_rec["permanent_fix_task"] is not None
    assert updated_rec["permanent_fix_task"]["task_code"] == task_data["task_code"]
    assert updated_rec["permanent_fix_task"]["status"] == "Scheduled"
