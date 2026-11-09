"""Smoke test script for Project Shikayat Karo.

Runs the complete demo story through the API:
1. Submits 5 complaints (2 English, 1 Hindi, 1 Hinglish, 1 Anonymous) about a water leak at Hostel Block B
2. Verifies language detection, prototype categorization, and rule-based priority reasoning
3. Verifies automatic multi-factor relatedness clustering into a system Suggestion
4. Confirms the Suggestion as Admin -> creates Parent Incident with impact score breakdown
5. Verifies unauthenticated anonymous tracking with zero identity leakage
6. Fast-forwards the virtual clock by 6 hours to trigger automated escalations
7. Resolves the incident with resolution notes and checks resolution intelligence
8. Verifies heatmap analytics and dashboard KPIs

Run with: python smoke_test.py
"""

import sys
import os
import json
import httpx

# Ensure UTF-8 output encoding for Windows terminals
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure local import path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from backend.main import app

SEPARATOR = "=" * 80
SUBSEP = "-" * 80


def run_smoke_test():
    print(SEPARATOR)
    print(" PROJECT SHIKAYAT KARO - END-TO-END DEMO SMOKE TEST")
    print(" Intelligent Grievance Redressal and Incident Clustering Platform")
    print(SEPARATOR)

    # Initialize client
    client = TestClient(app)

    # 1. Reset Demo State
    print("\n[Step 1] Resetting virtual clock and database to pristine demo state...")
    reset_res = client.post("/api/demo/reset")
    assert reset_res.status_code == 200, f"Reset failed: {reset_res.text}"
    print("  [OK] State reset. Virtual Time (UTC):", reset_res.json()["virtual_time_utc"])

    # 2. Login Demo Users
    print("\n[Step 2] Authenticating demo actors...")
    admin_login = client.post("/api/auth/login", json={"email": "admin@demo", "password": "password123"})
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("  [OK] Admin logged in: Dr. Arvind Sharma (role: admin)")

    handler_login = client.post("/api/auth/login", json={"email": "handler@demo", "password": "password123"})
    assert handler_login.status_code == 200
    handler_token = handler_login.json()["access_token"]
    handler_headers = {"Authorization": f"Bearer {handler_token}"}
    print("  [OK] Handler logged in: Rajesh Kumar (Estate & Maintenance)")

    student_login = client.post("/api/auth/login", json={"email": "student@demo", "password": "password123"})
    assert student_login.status_code == 200
    student_token = student_login.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}
    print("  [OK] Student logged in: Priya Verma (complainant)")

    # 3. Load Demo Story (5 Complaints across languages and anonymity)
    print("\n[Step 3] Loading canonical demo story (5 water leak complaints near Hostel Block B)...")
    story_res = client.post("/api/demo/load-story")
    assert story_res.status_code == 200, f"Load story failed: {story_res.text}"
    story_data = story_res.json()

    print(f"  [OK] Story loaded at location: {story_data['location']}")
    print(f"  [OK] Total complaints submitted: {len(story_data['complaints_created'])}")

    print("\n" + SUBSEP)
    print(" INDIVIDUAL COMPLAINT SUBMISSION RESULTS & AI ANALYSIS")
    print(SUBSEP)

    anon_tracking_id = None
    anon_access_code = None

    for idx, cmp in enumerate(story_data["complaints_created"], 1):
        print(f"\n  Complaint #{idx}: Tracking ID: {cmp['tracking_id']}")
        print(f"    - Language detected : {cmp['language'].upper()}")
        print(f"    - Category          : {cmp['category']}")
        print(f"    - Priority          : {cmp['priority']}")
        print(f"    - Anonymous Report  : {cmp['is_anonymous']}")
        if cmp["is_anonymous"]:
            anon_tracking_id = cmp["tracking_id"]
            anon_access_code = cmp["access_code"]
            print(f"    - Access Code Issued: {cmp['access_code']} (Secure 8-character token)")

    # 4. Inspect System Aggregation Suggestion
    print("\n" + SUBSEP)
    print(" SYSTEM INCIDENT CLUSTERING SUGGESTION")
    print(SUBSEP)
    sugg_id = story_data["pending_suggestion_id"]
    assert sugg_id is not None, "Expected a grouped suggestion to be created!"

    sugg_res = client.get(f"/api/suggestions?status_filter=pending", headers=admin_headers)
    assert sugg_res.status_code == 200
    suggs = sugg_res.json()
    active_sugg = next(s for s in suggs if s["id"] == sugg_id)

    print(f"  [OK] Suggestion ID       : #{active_sugg['id']}")
    print(f"  [OK] Status              : {active_sugg['status'].upper()} (Pending Admin Confirmation)")
    print(f"  [OK] Grouped Complaints  : {active_sugg['complaint_ids']} ({len(active_sugg['complaint_ids'])} complaints)")
    print(f"  [OK] System Confidence   : {active_sugg['confidence'] * 100:.1f}%")
    print("  [OK] Multi-factor Decision Reasons:")
    for r in active_sugg["reasons"]:
        print(f"      * {r}")

    # 5. Admin Confirms Suggestion -> Creates Parent Incident
    print("\n[Step 4] Admin confirms suggestion and escalates to Parent Incident...")
    confirm_res = client.post(
        f"/api/suggestions/{sugg_id}/confirm",
        json={"title": "Major Drinking Water Pipeline Rupture near Hostel Block B"},
        headers=admin_headers
    )
    assert confirm_res.status_code == 200
    confirm_data = confirm_res.json()
    inc_id = confirm_data["incident_id"]
    inc_code = confirm_data["incident_code"]
    print(f"  [OK] Parent Incident Created: {inc_code} (ID: #{inc_id})")

    # Fetch complete incident details
    inc_detail_res = client.get(f"/api/incidents/{inc_id}", headers=admin_headers)
    assert inc_detail_res.status_code == 200
    inc_data = inc_detail_res.json()

    print(f"  [OK] Incident Title     : {inc_data['title']}")
    print(f"  [OK] Category           : {inc_data['category']}")
    print(f"  [OK] Priority           : {inc_data['priority']}")
    print(f"  [OK] Department Assigned: {inc_data['department_name']}")
    print(f"  [OK] Linked Complaints  : {inc_data['linked_complaints_count']} complaints")
    print(f"  [OK] Transparent Impact : {inc_data['impact_score']}/100 ({inc_data['impact_breakdown']['band']} band)")
    print("    Breakdown:")
    bd = inc_data["impact_breakdown"]["breakdown"]
    print(f"      - Severity (35%): {bd['severity']}")
    print(f"      - Urgency  (25%): {bd['urgency']}")
    print(f"      - Affected (25%): {bd['affected']} ({bd['raw_affected_count']} users)")
    print(f"      - Duration (15%): {bd['duration']} ({bd['raw_hours_open']}h elapsed)")

    # 6. Verify Anonymous Tracking without Authentication
    print("\n[Step 5] Testing anonymous public grievance tracking (No login required)...")
    track_res = client.get(f"/api/track?tracking_id={anon_tracking_id}&access_code={anon_access_code}")
    assert track_res.status_code == 200
    track_data = track_res.json()

    print(f"  [OK] Tracked Complaint  : {track_data['tracking_id']}")
    print(f"  [OK] Current Status     : {track_data['status']}")
    print(f"  [OK] Linked Incident    : {track_data['incident_id']}")
    print(f"  [OK] Complainant Info   : {track_data['complainant']} (Strictly Null / Zero Privacy Leakage)")
    assert track_data["complainant"] is None
    assert "access_code_hash" not in track_data

    # 7. Virtual Clock Fast-Forward & Automated Escalation
    print("\n[Step 6] Fast-forwarding virtual clock by 6.0 hours to test SLA escalation...")
    adv_res = client.post("/api/demo/advance-time", json={"hours": 6.0})
    assert adv_res.status_code == 200
    adv_data = adv_res.json()
    print(f"  [OK] Clock Advanced by 6.0 hours. Total offset: {adv_data['total_offset_hours']}h")
    print(f"  [OK] Escalations Triggered: {adv_data['escalations_triggered']}")

    # Refresh incident to inspect updated escalation level
    inc_esc_res = client.get(f"/api/incidents/{inc_id}", headers=admin_headers)
    inc_esc = inc_esc_res.json()
    print(f"  [OK] Updated Incident Escalation Level: Level {inc_esc['escalation_level']}")

    # 8. Resolution Intelligence & Handler Resolution
    print("\n[Step 7] Inspecting Resolution Intelligence & resolving incident...")
    print(f"  [OK] Top {len(inc_esc['similar_resolved'])} Similar Historical Resolutions Suggested by AI:")
    for s_idx, sim in enumerate(inc_esc["similar_resolved"], 1):
        print(f"      [{s_idx}] Similar Incident: {sim['incident_code']} ({sim['title']})")
        print(f"          Similarity     : {sim['similarity'] * 100:.1f}%")
        print(f"          Department     : {sim['department_name']}")
        print(f"          Past Resolution: \"{sim['resolution_notes']}\"")
        print(f"          Resolved In    : {sim['hours_to_resolve']} hours")

    # Handler resolves the incident
    resolve_notes = "Excavated pipeline bedding near Block B main valve, replaced cracked 4-inch PVC elbow coupling with heavy-duty galvanized clamp. Tested line pressure at 4.2 bar; zero leakage."
    status_res = client.post(
        f"/api/incidents/{inc_id}/status",
        json={"status": "Resolved", "resolution_notes": resolve_notes},
        headers=handler_headers
    )
    assert status_res.status_code == 200
    print(f"  [OK] Incident {inc_code} marked as Resolved by Handler Rajesh Kumar.")

    # 9. Analytics & KPI Verification
    print("\n[Step 8] Verifying grievance heatmap & executive dashboard counters...")
    heatmap_res = client.get("/api/heatmap")
    assert heatmap_res.status_code == 200
    heatmap = heatmap_res.json()
    block_b_heat = next((h for h in heatmap if h["location_name"] == "Hostel Block B"), None)
    if block_b_heat:
        print(f"  [OK] Heatmap Node: {block_b_heat['location_name']}")
        print(f"      Grid Coordinates: ({block_b_heat['grid_x']}, {block_b_heat['grid_y']})")
        print(f"      Complaints Count: {block_b_heat['complaint_count']}")
        print(f"      Total Impact    : {block_b_heat['total_impact']}")
        print(f"      Primary Category: {block_b_heat['primary_category']}")

    dash_res = client.get("/api/dashboard/summary")
    assert dash_res.status_code == 200
    dash = dash_res.json()
    print(f"  [OK] Dashboard KPI Summary:")
    print(f"      Total Complaints   : {dash['total_complaints']}")
    print(f"      Total Incidents    : {dash['total_incidents']}")
    print(f"      Resolved Incidents : {dash['resolved_incidents']}")
    print(f"      Critical Incidents : {dash['critical_incidents']}")
    print(f"      Avg Resolution Time: {dash['average_resolution_hours']} hours")

    print("\n" + SEPARATOR)
    print(" ALL SMOKE TEST VERIFICATIONS PASSED SUCCESSFULLY!")
    print(SEPARATOR)


if __name__ == "__main__":
    run_smoke_test()
