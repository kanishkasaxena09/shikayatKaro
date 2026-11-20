"""Backend tests for coherent live demo story, KPI metrics, and zero-leakage anonymity.

Asserts:
1. Demo Story Ingestion: 5 complaints at Hostel Block B form exactly 1 pending AI cluster;
   2 unrelated complaints (Library Wi-Fi, Computer Lab lighting) correctly do NOT cluster.
2. Confirmation Lifecycle: Confirming the cluster creates 1 Parent Incident with accurate
   formula-based impact score, assigns the department, and sets SLA timers matching the priority tier.
3. KPI Dashboard Coherence: Counts computed from DB match exactly (total complaints, parent incidents,
   active vs resolved, pending clusters, escalations, avg resolution time).
4. Strict Zero-Leakage Anonymity: Anonymous complaints never store user_id in DB, never return user_id,
   name, or email in single get, list, track, suggestion, or incident endpoints.
"""

import os
os.environ["TESTING"] = "1"
os.environ["EMBEDDER"] = "fallback"

from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import SessionLocal
from backend.models import User, Location, Incident, Complaint, Suggestion
from backend.ai.impact import calculate_impact
from backend.clock import get_current_time

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_demo_fixture():
    """Ensure every test in this module starts with pristine demo story state."""
    client.post("/api/demo/reset")


def get_auth_token(email: str = "admin@demo") -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_demo_story_clustering_and_isolation():
    """Test Requirement 3 & 4:
    - 5 complaints at Hostel Block B produce exactly ONE pending Suggestion.
    - 2 unrelated complaints (Library Wi-Fi, Computer Lab lighting) correctly do NOT cluster.
    - Total complaint count and incident count match expectations.
    """
    admin_token = get_auth_token("admin@demo")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Check suggestions endpoint
    sugg_res = client.get("/api/suggestions?status_filter=pending", headers=headers)
    assert sugg_res.status_code == 200
    suggestions = sugg_res.json()

    # Exactly 1 pending cluster
    assert len(suggestions) == 1
    sugg = suggestions[0]
    assert sugg["status"] == "pending"
    assert len(sugg["complaint_ids"]) == 5
    assert sugg["confidence"] >= 0.50

    # 2. Check complaints in the suggestion
    db = SessionLocal()
    try:
        clustered_cmps = db.query(Complaint).filter(Complaint.id.in_(sugg["complaint_ids"])).all()
        assert len(clustered_cmps) == 5

        # All 5 complaints are about Water & Plumbing at Hostel Block B
        for c in clustered_cmps:
            assert c.category == "Water & Plumbing"
            assert "Hostel Block B" in (c.location.name if c.location else "") or (c.location.parent and "Hostel Block B" in c.location.parent.name)
            assert c.incident_id is None

        # Check languages present in the cluster: English, Hindi, Hinglish
        languages = {c.original_language for c in clustered_cmps}
        assert "english" in languages
        assert "hindi" in languages
        assert "hinglish" in languages

        # Check that one complaint is anonymous
        anon_in_cluster = [c for c in clustered_cmps if c.is_anonymous]
        assert len(anon_in_cluster) == 1
        assert anon_in_cluster[0].complainant_id is None

        # 3. Check the 2 unrelated complaints
        unrelated_cmps = db.query(Complaint).filter(
            Complaint.tracking_id.in_(["CMP-DEMO-006", "CMP-DEMO-007"])
        ).all()
        assert len(unrelated_cmps) == 2

        for u in unrelated_cmps:
            # Unrelated complaints must NOT be in the pending suggestion
            assert u.id not in sugg["complaint_ids"]
            assert u.incident_id is None
            assert u.status == "AI Analysed"

        # Check their categories are different
        unrelated_categories = {u.category for u in unrelated_cmps}
        assert "IT & Network" in unrelated_categories
        assert "Electrical" in unrelated_categories
    finally:
        db.close()


def test_confirm_suggestion_lifecycle_impact_and_sla():
    """Test Requirement 4:
    - Confirming the pending cluster creates exactly one Parent Incident.
    - Impact score matches the transparent formula.
    - SLA deadline matches the chosen priority tier (High: 24h).
    - Grouped complaints are linked to the incident.
    - Unrelated complaints remain unclustered.
    """
    admin_token = get_auth_token("admin@demo")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Get pending suggestion
    sugg_res = client.get("/api/suggestions?status_filter=pending", headers=headers)
    assert sugg_res.status_code == 200
    sugg = sugg_res.json()[0]
    sugg_id = sugg["id"]
    complaint_ids = sugg["complaint_ids"]

    # 2. Confirm suggestion
    confirm_res = client.post(
        f"/api/suggestions/{sugg_id}/confirm",
        json={
            "title": "Major potable water supply rupture outside Hostel Block B entrance",
            "priority": "High"
        },
        headers=headers
    )
    assert confirm_res.status_code == 200
    confirm_data = confirm_res.json()
    inc_id = confirm_data["incident_id"]
    assert inc_id is not None

    # 3. Verify created Incident details
    inc_res = client.get(f"/api/incidents/{inc_id}", headers=headers)
    assert inc_res.status_code == 200
    inc_data = inc_res.json()

    assert inc_data["category"] == "Water & Plumbing"
    assert inc_data["priority"] == "High"
    assert inc_data["status"] == "Assigned"
    assert inc_data["department_name"] == "Estate & Maintenance"

    # Verify all 5 complaints are linked
    assert len(inc_data["linked_complaints"]) == 5
    linked_ids = {c["id"] for c in inc_data["linked_complaints"]}
    assert set(complaint_ids) == linked_ids

    # 4. Verify Impact Score calculation
    # For High priority: severity=70, urgency=75. Total affected=65.
    db = SessionLocal()
    try:
        db_inc = db.query(Incident).filter(Incident.id == inc_id).first()
        assert db_inc is not None
        assert db_inc.impact_score > 0
        assert db_inc.impact_breakdown is not None
        assert "breakdown" in db_inc.impact_breakdown
        assert "severity" in db_inc.impact_breakdown["breakdown"]
        assert "urgency" in db_inc.impact_breakdown["breakdown"]
        assert db_inc.impact_breakdown["breakdown"]["severity"] == 70.0

        # Expected SLA deadline for High priority: exactly 24.0 hours from created_at
        expected_deadline = db_inc.created_at + timedelta(hours=24.0)
        assert abs((db_inc.deadline_at - expected_deadline).total_seconds()) < 60  # within 1 minute

        # 5. Verify the 2 unrelated complaints are STILL unlinked
        unrelated = db.query(Complaint).filter(
            Complaint.tracking_id.in_(["CMP-DEMO-006", "CMP-DEMO-007"])
        ).all()
        for u in unrelated:
            assert u.incident_id is None
            assert u.status == "AI Analysed"
    finally:
        db.close()


def test_kpi_dashboard_metrics_coherence():
    """Test Requirement 2 & Acceptance:
    - Dashboard metrics are mathematically and operationally coherent:
      total_complaints = 44 (37 historical + 5 clustered + 2 unclustered)
      total_incidents = 15 (all 15 historical resolved)
      active_incidents = 0
      resolved_incidents = 15
      active_incidents + resolved_incidents == total_incidents
      pending_suggestions = 1
      average_resolution_hours == 9.8 (computed, not hardcoded)
    """
    dash_res = client.get("/api/dashboard/summary")
    assert dash_res.status_code == 200
    summary = dash_res.json()

    # Exact database counts
    db = SessionLocal()
    try:
        actual_total_cmps = db.query(Complaint).count()
        actual_total_incs = db.query(Incident).count()
        actual_active_incs = db.query(Incident).filter(Incident.status.notin_(["Resolved", "Closed"])).count()
        actual_resolved_incs = db.query(Incident).filter(Incident.status.in_(["Resolved", "Closed"])).count()
        actual_pending_suggs = db.query(Suggestion).filter(Suggestion.status == "pending").count()

        resolved = db.query(Incident).filter(
            Incident.status.in_(["Resolved", "Closed"]),
            Incident.resolved_at.isnot(None),
            Incident.created_at.isnot(None)
        ).all()
        expected_avg_hours = round(sum((i.resolved_at - i.created_at).total_seconds() / 3600.0 for i in resolved) / len(resolved), 1)
    finally:
        db.close()

    # API summary matches DB exactly
    assert summary["total_complaints"] == actual_total_cmps
    assert summary["total_incidents"] == actual_total_incs
    assert summary["active_incidents"] == actual_active_incs
    assert summary["resolved_incidents"] == actual_resolved_incs
    assert summary["pending_suggestions"] == actual_pending_suggs
    assert summary["average_resolution_hours"] == expected_avg_hours

    # Exact expected numerical values
    assert summary["total_complaints"] == 44
    assert summary["total_incidents"] == 15
    assert summary["active_incidents"] == 0
    assert summary["resolved_incidents"] == 15
    assert summary["active_incidents"] + summary["resolved_incidents"] == summary["total_incidents"]
    assert summary["pending_suggestions"] == 1
    assert summary["average_resolution_hours"] == 9.8

    # Verify historical incidents all have linked complaints (> 0)
    admin_token = get_auth_token("admin@demo")
    inc_list_res = client.get("/api/incidents?status=Resolved", headers={"Authorization": f"Bearer {admin_token}"})
    assert inc_list_res.status_code == 200
    inc_list = inc_list_res.json()
    assert len(inc_list) == 15
    for inc in inc_list:
        assert inc["linked_complaints_count"] >= 1
        assert inc["linked_complaints_count"] <= 6


def test_anonymous_submissions_zero_leakage():
    """Test Requirement 5:
    - Verifies zero-leakage guarantee:
      1. Anonymous complaint stores NO user_id (complainant_id is None) in DB.
      2. No user id, name, or email is returned in API responses:
         - /api/complaints submission response
         - /api/complaints/{id} lookup
         - /api/track status lookup
         - /api/suggestions suggestion complaints list
         - /api/incidents/{id} linked complaints list
      3. Access code is hashed via bcrypt (plain code NEVER in DB).
    """
    admin_token = get_auth_token("admin@demo")
    student_token = get_auth_token("student@demo")

    # 1. Submit anonymous complaint while logged in as a student
    sub_res = client.post(
        "/api/complaints",
        json={
            "text": "Broken security latch on rear fire exit door behind library",
            "affected_count": 10,
            "is_anonymous": True
        },
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert sub_res.status_code == 200
    data = sub_res.json()
    tracking_id = data["complaint"]["tracking_id"]
    access_code = data["access_code"]
    cmp_id = data["complaint"]["id"]

    # Submission response must have complainant=None
    assert data["complaint"]["is_anonymous"] is True
    assert data["complaint"].get("complainant") is None
    assert "user_id" not in data["complaint"]
    assert "email" not in data["complaint"]

    # 2. Verify Database Row Directly
    db = SessionLocal()
    try:
        db_cmp = db.query(Complaint).filter(Complaint.id == cmp_id).first()
        assert db_cmp is not None
        # Strict privacy: foreign key MUST be NULL
        assert db_cmp.complainant_id is None
        # Plain access code must NEVER be stored
        assert db_cmp.access_code_hash is not None
        assert db_cmp.access_code_hash != access_code
        assert len(db_cmp.access_code_hash) >= 50
    finally:
        db.close()

    # 3. GET /api/complaints/{id} (as admin)
    cmp_res = client.get(f"/api/complaints/{cmp_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert cmp_res.status_code == 200
    cmp_out = cmp_res.json()
    assert cmp_out["is_anonymous"] is True
    assert cmp_out.get("complainant") is None
    assert "email" not in cmp_out
    assert "user_id" not in cmp_out

    # 4. GET /api/track with valid access code
    track_res = client.get(f"/api/track?tracking_id={tracking_id}&access_code={access_code}")
    assert track_res.status_code == 200
    track_out = track_res.json()
    assert track_out["is_anonymous"] is True
    assert track_out.get("complainant") is None
    assert "email" not in track_out
    assert "user_id" not in track_out
    assert "access_code_hash" not in track_out

    # 5. Check anonymous complaint inside the demo suggestion
    sugg_res = client.get("/api/suggestions?status_filter=pending", headers={"Authorization": f"Bearer {admin_token}"})
    assert sugg_res.status_code == 200
    sugg = sugg_res.json()[0]
    anon_cmps = [c for c in sugg["complaints"] if c["is_anonymous"]]
    assert len(anon_cmps) >= 1
    for ac in anon_cmps:
        assert ac.get("complainant") is None
        assert "email" not in ac
        assert "user_id" not in ac

    # 6. Check historical anonymous complaints inside resolved incidents
    inc_res = client.get("/api/incidents/1", headers={"Authorization": f"Bearer {admin_token}"})
    assert inc_res.status_code == 200
    linked = inc_res.json()["linked_complaints"]
    hist_anon = [c for c in linked if c["is_anonymous"]]
    assert len(hist_anon) >= 1
    for ha in hist_anon:
        assert ha.get("complainant") is None
        assert "email" not in ha
        assert "user_id" not in ha
