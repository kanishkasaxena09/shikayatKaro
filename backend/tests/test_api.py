"""End-to-end integration tests for Project Shikayat Karo API."""

import os
os.environ["TESTING"] = "1"

from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal
from backend.models import User, Location, Incident, Complaint, Suggestion

client = TestClient(app)


def test_auth_and_roles():
    # Login as seeded demo admin
    res = client.post("/api/auth/login", json={"email": "admin@demo", "password": "password123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] == "admin"

    # Login as student
    res_stu = client.post("/api/auth/login", json={"email": "student@demo", "password": "password123"})
    assert res_stu.status_code == 200
    assert res_stu.json()["user"]["role"] == "complainant"

    # Access /api/auth/me
    token = data["access_token"]
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "admin@demo"


def test_complaint_to_incident_lifecycle():
    # 1. Reset demo state
    client.post("/api/demo/reset")

    # 2. Login admin and student
    admin_token = client.post("/api/auth/login", json={"email": "admin@demo", "password": "password123"}).json()["access_token"]
    student_token = client.post("/api/auth/login", json={"email": "student@demo", "password": "password123"}).json()["access_token"]

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # 3. Get Hostel Block B location
    db = SessionLocal()
    block_b = db.query(Location).filter(Location.name == "Hostel Block B").first()
    loc_id = block_b.id if block_b else 1
    db.close()

    # 4. Submit first complaint (English)
    c1_res = client.post(
        "/api/complaints",
        json={
            "text": "Drinking water pipeline ruptured outside Hostel Block B entrance, water overflowing heavily",
            "location_id": loc_id,
            "affected_count": 8,
            "is_anonymous": False
        },
        headers=student_headers
    )
    assert c1_res.status_code == 200
    c1_data = c1_res.json()
    assert c1_data["complaint"]["category"] == "Water & Plumbing"
    c1_id = c1_data["complaint"]["id"]

    # 5. Submit second complaint (Hinglish, at same place within minutes)
    c2_res = client.post(
        "/api/complaints",
        json={
            "text": "Hostel Block B mein paani ka pipe phat gaya hai poora paani beh raha hai",
            "location_id": loc_id,
            "affected_count": 12,
            "is_anonymous": False
        },
        headers=student_headers
    )
    assert c2_res.status_code == 200
    c2_data = c2_res.json()
    assert c2_data["complaint"]["category"] == "Water & Plumbing"
    assert c2_data["suggestion_created"] is True
    sugg_id = c2_data["suggestion_id"]
    assert sugg_id is not None

    # 6. Admin checks pending suggestions
    sugg_list_res = client.get("/api/suggestions?status_filter=pending", headers=admin_headers)
    assert sugg_list_res.status_code == 200
    suggs = sugg_list_res.json()
    assert len(suggs) >= 1
    target_sugg = next(s for s in suggs if s["id"] == sugg_id)
    assert c1_id in target_sugg["complaint_ids"]
    assert target_sugg["confidence"] >= 0.50  # Valid system suggestion band (>= 0.50)

    # 7. Admin confirms suggestion -> creates Parent Incident
    confirm_res = client.post(
        f"/api/suggestions/{sugg_id}/confirm",
        json={"title": "Major water pipeline rupture at Hostel Block B"},
        headers=admin_headers
    )
    assert confirm_res.status_code == 200
    confirm_data = confirm_res.json()
    inc_id = confirm_data["incident_id"]
    assert inc_id is not None
    assert confirm_data["impact_score"] > 0

    # 8. Check incident details
    inc_detail_res = client.get(f"/api/incidents/{inc_id}", headers=admin_headers)
    assert inc_detail_res.status_code == 200
    inc_detail = inc_detail_res.json()
    assert inc_detail["category"] == "Water & Plumbing"
    assert len(inc_detail["linked_complaints"]) >= 2
    assert len(inc_detail["similar_resolved"]) > 0  # Resolution intel populated!

    # 9. Status update without resolution notes fails for Resolved
    bad_status_res = client.post(
        f"/api/incidents/{inc_id}/status",
        json={"status": "Resolved", "resolution_notes": ""},
        headers=admin_headers
    )
    assert bad_status_res.status_code == 400

    # 10. Status update with valid resolution notes succeeds
    good_status_res = client.post(
        f"/api/incidents/{inc_id}/status",
        json={
            "status": "Resolved",
            "resolution_notes": "Excavated line and installed new 4-inch PVC joint, line pressure restored."
        },
        headers=admin_headers
    )
    assert good_status_res.status_code == 200
    assert good_status_res.json()["new_status"] == "Resolved"

    # 11. Check Heatmap and Dashboard
    heat_res = client.get("/api/heatmap")
    assert heat_res.status_code == 200
    heat_data = heat_res.json()
    assert len(heat_data) > 0

    dash_res = client.get("/api/dashboard/summary")
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["total_complaints"] >= 2
    assert dash_data["resolved_incidents"] >= 1


def test_virtual_clock_advance_and_escalation():
    # 1. Reset
    client.post("/api/demo/reset")
    admin_token = client.post("/api/auth/login", json={"email": "admin@demo", "password": "password123"}).json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Submit critical complaint (4h deadline)
    db = SessionLocal()
    sac = db.query(Location).filter(Location.type == "block").first()
    loc_id = sac.id if sac else 1
    db.close()

    res = client.post(
        "/api/complaints",
        json={
            "text": "Severe electrical spark and smoke pouring from corridor distribution panel, dangerous hazard",
            "location_id": loc_id,
            "affected_count": 30,
            "is_anonymous": False
        },
        headers=admin_headers
    )
    assert res.status_code == 200
    cmp_id = res.json()["complaint"]["id"]

    # 3. Fast-forward virtual clock by 5 hours (> 4h deadline)
    adv_res = client.post("/api/demo/advance-time", json={"hours": 5.0})
    assert adv_res.status_code == 200
    data = adv_res.json()
    assert data["total_offset_hours"] >= 5.0

    # 4. Check that complaint escalated to Level 1
    cmp_res = client.get(f"/api/complaints/{cmp_id}", headers=admin_headers)
    assert cmp_res.status_code == 200
    assert cmp_res.json()["escalation_level"] >= 1
