"""Database seeding script for Project Shikayat Karo.

Seeds:
- 1 Organisation / Campus root location
- 6 Departments
- 14 Locations in a campus > block > floor/area tree with 2D grid coordinates
- 3 Demo Users: admin@demo, handler@demo, student@demo (password: password123)
- 4 Escalation rules (Critical 4h, High 24h, Medium 72h, Low 168h)
- 15 Realistic resolved incidents with comprehensive resolution notes and 37 linked complaints
- Live demo story: 5 new complaints grouped in 1 pending AI cluster + 2 unclustered complaints
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import bcrypt
from sqlalchemy.orm import Session

from backend.database import SessionLocal, engine, Base
from backend.models import (
    Department, User, Location, Incident, Complaint, EscalationRule, Suggestion, Update, Notification, PermanentFixTask
)
from backend.ai.embedder import get_embedder
from backend.clock import get_current_time, reset_time


def hash_password(password: str) -> str:
    rounds = 4 if os.getenv("TESTING") else 12
    salt = bcrypt.gensalt(rounds=rounds)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def hash_access_code(code: str) -> str:
    rounds = 4 if os.getenv("TESTING") else 12
    salt = bcrypt.gensalt(rounds=rounds)
    return bcrypt.hashpw(code.encode("utf-8"), salt).decode("utf-8")


def seed_demo_story(db: Session, now: Optional[datetime] = None) -> Dict[str, Any]:
    """Seeds the canonical live demo story:
    - 5 complaints about a major water pipe leak near Hostel Block B (EN, HI, Hinglish, Anonymous)
      forming exactly ONE pending Suggestion for admin review.
    - 2 unrelated complaints (Library Wi-Fi, Computer Lab lighting) that correctly do NOT cluster.
    """
    if now is None:
        now = get_current_time()

    embedder = get_embedder()

    # Find locations
    block_b = db.query(Location).filter(Location.name == "Hostel Block B").first()
    loc_b_first = db.query(Location).filter(Location.name == "Hostel Block B - First Floor").first()
    loc_lib_hall = db.query(Location).filter(Location.name == "Library - Reading Hall 1").first()
    loc_lab_2 = db.query(Location).filter(Location.name == "Computer Lab 2").first()

    b_loc_id = block_b.id if block_b else 1
    b_first_id = loc_b_first.id if loc_b_first else b_loc_id
    lib_loc_id = loc_lib_hall.id if loc_lib_hall else 1
    lab_loc_id = loc_lab_2.id if loc_lab_2 else 1

    # Find department for water
    est_dept = db.query(Department).filter(Department.name == "Estate & Maintenance").first()
    it_dept = db.query(Department).filter(Department.name == "IT & Networking").first()
    elec_dept = db.query(Department).filter(Department.name == "Electrical & Power").first()

    student = db.query(User).filter(User.email == "student@demo").first()
    student_id = student.id if student else None

    # Clear previous non-historical complaints, suggestions, notifications, and non-historical incidents
    db.query(Complaint).filter(Complaint.tracking_id.notlike("CMP-HIST-%")).delete()
    db.query(Incident).filter(Incident.code.notlike("INC-HIST-%")).delete()
    db.query(Suggestion).delete()
    db.query(Notification).delete()
    db.query(PermanentFixTask).delete()
    db.query(Update).filter(Update.target_type != "historical").delete()
    db.flush()

    # 1. Five clustered complaints about water leak at Hostel Block B
    demo_clustered = [
        {
            "tracking_id": "CMP-DEMO-001",
            "text": "Water pipe ruptured outside Hostel Block B entrance, drinking water pipeline leaking heavily onto the pathway",
            "lang": "english",
            "anon": False,
            "loc_id": b_loc_id,
            "hours_ago": 3.5,
            "affected": 8,
            "priority": "High"
        },
        {
            "tracking_id": "CMP-DEMO-002",
            "text": "Severe water leakage from main supply pipe near Hostel Block B, clean water flowing continuously and flooding the corridor entrance",
            "lang": "english",
            "anon": False,
            "loc_id": b_first_id,
            "hours_ago": 2.5,
            "affected": 12,
            "priority": "High"
        },
        {
            "tracking_id": "CMP-DEMO-003",
            "text": "हॉस्टल ब्लॉक बी के मुख्य गेट के पास पानी का पाइप फटा हुआ है और सड़क पर बहुत सारा पानी बह रहा है",
            "lang": "hindi",
            "anon": False,
            "loc_id": b_loc_id,
            "hours_ago": 1.8,
            "affected": 15,
            "priority": "High"
        },
        {
            "tracking_id": "CMP-DEMO-004",
            "text": "Hostel Block B ground floor ke paas paani ka main pipe leak ho raha hai, nal ka paani waste ho raha hai turant theek kijiye",
            "lang": "hinglish",
            "anon": False,
            "loc_id": b_loc_id,
            "hours_ago": 1.0,
            "affected": 10,
            "priority": "High"
        },
        {
            "tracking_id": "CMP-DEMO-005",
            "text": "Water pipeline broken near Block B hostel entrance, water logging is blocking student access, please fix urgently",
            "lang": "english",
            "anon": True,
            "loc_id": b_loc_id,
            "hours_ago": 0.5,
            "affected": 20,
            "priority": "High"
        }
    ]

    clustered_complaints: List[Complaint] = []
    for item in demo_clustered:
        created_at = now - timedelta(hours=item["hours_ago"])
        access_hash = hash_access_code("DEMO1234") if item["anon"] else None
        c = Complaint(
            tracking_id=item["tracking_id"],
            complainant_id=None if item["anon"] else student_id,
            is_anonymous=item["anon"],
            access_code_hash=access_hash,
            text=item["text"],
            original_language=item["lang"],
            category="Water & Plumbing",
            category_confidence=0.92,
            priority=item["priority"],
            priority_reasons=[
                "High priority: Pipeline leakage impacting student movement and continuous potable water wastage.",
                f"Affects estimated {item['affected']} students."
            ],
            location_id=item["loc_id"],
            department_id=est_dept.id if est_dept else None,
            status="AI Analysed",
            incident_id=None,
            affected_count=item["affected"],
            embedding=embedder.embed(item["text"]),
            deadline_at=created_at + timedelta(hours=24.0),
            escalation_level=0,
            created_at=created_at
        )
        db.add(c)
        db.flush()
        clustered_complaints.append(c)

    # Create the single pending Suggestion grouping all 5 complaints
    cluster_ids = [c.id for c in clustered_complaints]
    cluster_suggestion = Suggestion(
        complaint_ids=cluster_ids,
        confidence=0.88,
        engine=embedder.engine_type,
        status="pending",
        reasons=[
            f"Engine: {embedder.engine_type}",
            "Strong multi-factor correlation across 5 grievances at Hostel Block B.",
            "Text similarity: high semantic overlap regarding main water pipeline rupture and flooding.",
            "Location match: identical block/floor proximity within Hostel Block B.",
            "Time proximity: all reports filed within 3.5 hours.",
            "Category match: exact match on Water & Plumbing.",
            "System suggestion requires admin confirmation."
        ],
        created_at=now - timedelta(hours=0.5)
    )
    db.add(cluster_suggestion)
    db.flush()

    # 2. Two unrelated complaints that correctly do NOT cluster
    unrelated_data = [
        {
            "tracking_id": "CMP-DEMO-006",
            "text": "Central Library reading hall Wi-Fi access point offline, portal connection timing out",
            "lang": "english",
            "category": "IT & Network",
            "dept_id": it_dept.id if it_dept else None,
            "loc_id": lib_loc_id,
            "priority": "Medium",
            "anon": False,
            "hours_ago": 2.0,
            "affected": 40
        },
        {
            "tracking_id": "CMP-DEMO-007",
            "text": "Computer Lab 2 mein ceiling fluorescent tube light continuously flicker ho rahi hai aur spark sound aa rahi hai",
            "lang": "hinglish",
            "category": "Electrical",
            "dept_id": elec_dept.id if elec_dept else None,
            "loc_id": lab_loc_id,
            "priority": "High",
            "anon": True,
            "hours_ago": 1.2,
            "affected": 25
        }
    ]

    unrelated_complaints: List[Complaint] = []
    for item in unrelated_data:
        created_at = now - timedelta(hours=item["hours_ago"])
        access_hash = hash_access_code("ANON9999") if item["anon"] else None
        c = Complaint(
            tracking_id=item["tracking_id"],
            complainant_id=None if item["anon"] else student_id,
            is_anonymous=item["anon"],
            access_code_hash=access_hash,
            text=item["text"],
            original_language=item["lang"],
            category=item["category"],
            category_confidence=0.89,
            priority=item["priority"],
            priority_reasons=[f"Rule-based match for {item['category']}"],
            location_id=item["loc_id"],
            department_id=item["dept_id"],
            status="AI Analysed",
            incident_id=None,
            affected_count=item["affected"],
            embedding=embedder.embed(item["text"]),
            deadline_at=created_at + timedelta(hours=24.0 if item["priority"] == "High" else 72.0),
            escalation_level=0,
            created_at=created_at
        )
        db.add(c)
        db.flush()
        unrelated_complaints.append(c)

    db.commit()

    return {
        "pending_suggestion_id": cluster_suggestion.id,
        "clustered_complaint_ids": cluster_ids,
        "unrelated_complaint_ids": [c.id for c in unrelated_complaints]
    }


def seed_database(db: Optional[Session] = None, bind_engine = None):
    """Seeds the database with required master data, 15 resolved historical incidents
    with 37 realistic linked complaints, and the canonical live demo story.
    """
    active_engine = bind_engine or engine
    Base.metadata.create_all(bind=active_engine)
    close_on_exit = False
    if db is None:
        db = SessionLocal()
        close_on_exit = True

    try:
        # Check if already seeded
        if db.query(User).filter(User.email == "admin@demo").first():
            print("Database already seeded. Skipping initial master seed.")
            return

        print("Seeding Organisation, Departments, Locations, Users, and Historical Incidents...")

        # 1. Departments
        departments_data = [
            {"name": "Estate & Maintenance", "code": "EST-MAINT", "description": "Civil infrastructure, water supply, plumbing, building maintenance and sanitation."},
            {"name": "Electrical & Power", "code": "ELEC-PWR", "description": "High and low voltage distribution, substation, lighting, fans, ACs and generators."},
            {"name": "IT & Networking", "code": "IT-NET", "description": "Campus Wi-Fi, optical fiber backbones, lab networking and central computing facilities."},
            {"name": "Hostel & Food Services", "code": "HOSTEL-FOOD", "description": "Student residence allocation, mess kitchens, dining hygiene and warden oversight."},
            {"name": "Campus Security & Proctorial", "code": "SEC-PROC", "description": "Perimeter security, gates, vigilance, emergency response and student safety."},
            {"name": "Academic & Student Affairs", "code": "ACAD-STU", "description": "Lecture hall facilities, timetables, grievances, fee accounts and administration."}
        ]
        dept_map: Dict[str, Department] = {}
        for d in departments_data:
            dept = Department(**d)
            db.add(dept)
            db.flush()
            dept_map[d["name"]] = dept

        # 2. Locations: Campus > Block > Floor/Area
        campus = Location(name="Main Campus (Vidyanagar)", parent_id=None, type="campus", grid_x=50.0, grid_y=50.0)
        db.add(campus)
        db.flush()

        # Blocks
        block_a = Location(name="Academic Block A", parent_id=campus.id, type="block", grid_x=35.0, grid_y=60.0)
        block_b = Location(name="Hostel Block B", parent_id=campus.id, type="block", grid_x=70.0, grid_y=30.0)
        library = Location(name="Central Library", parent_id=campus.id, type="block", grid_x=45.0, grid_y=40.0)
        sac = Location(name="Student Activity Center (SAC)", parent_id=campus.id, type="block", grid_x=60.0, grid_y=65.0)
        admin_block = Location(name="Administrative Building", parent_id=campus.id, type="block", grid_x=50.0, grid_y=75.0)
        
        db.add_all([block_a, block_b, library, sac, admin_block])
        db.flush()

        # Floors and Areas
        loc_a_ground = Location(name="Academic Block A - Ground Floor", parent_id=block_a.id, type="floor", grid_x=35.0, grid_y=59.0)
        loc_lab_2 = Location(name="Computer Lab 2", parent_id=block_a.id, type="area", grid_x=36.0, grid_y=61.0)
        
        loc_b_first = Location(name="Hostel Block B - First Floor", parent_id=block_b.id, type="floor", grid_x=70.0, grid_y=31.0)
        loc_b_second = Location(name="Hostel Block B - Second Floor", parent_id=block_b.id, type="floor", grid_x=70.0, grid_y=32.0)
        loc_b_mess = Location(name="Hostel Block B - Mess Dining Hall", parent_id=block_b.id, type="area", grid_x=72.0, grid_y=28.0)
        
        loc_lib_hall = Location(name="Library - Reading Hall 1", parent_id=library.id, type="floor", grid_x=45.0, grid_y=41.0)
        loc_sports = Location(name="Sports Complex & Gym", parent_id=sac.id, type="area", grid_x=62.0, grid_y=66.0)
        
        loc_adm_ground = Location(name="Admin Building - Ground Floor", parent_id=admin_block.id, type="floor", grid_x=50.0, grid_y=74.0)
        loc_accounts = Location(name="Accounts & Registrar Office", parent_id=admin_block.id, type="area", grid_x=51.0, grid_y=76.0)

        db.add_all([
            loc_a_ground, loc_lab_2, loc_b_first, loc_b_second,
            loc_b_mess, loc_lib_hall, loc_sports, loc_adm_ground, loc_accounts
        ])
        db.flush()

        # 3. Escalation Rules
        escalation_rules = [
            EscalationRule(priority="Critical", deadline_hours=4.0, level_1_percent=100.0, level_2_percent=150.0, level_3_percent=200.0),
            EscalationRule(priority="High", deadline_hours=24.0, level_1_percent=100.0, level_2_percent=150.0, level_3_percent=200.0),
            EscalationRule(priority="Medium", deadline_hours=72.0, level_1_percent=100.0, level_2_percent=150.0, level_3_percent=200.0),
            EscalationRule(priority="Low", deadline_hours=168.0, level_1_percent=100.0, level_2_percent=150.0, level_3_percent=200.0)
        ]
        db.add_all(escalation_rules)

        # 4. Demo Users
        hashed_pwd = hash_password("password123")
        admin_user = User(
            email="admin@demo",
            password_hash=hashed_pwd,
            full_name="Dr. Arvind Sharma (Chief Admin)",
            role="admin",
            department_id=None
        )
        handler_user = User(
            email="handler@demo",
            password_hash=hashed_pwd,
            full_name="Rajesh Kumar (Facility Incharge)",
            role="handler",
            department_id=dept_map["Estate & Maintenance"].id
        )
        student_user = User(
            email="student@demo",
            password_hash=hashed_pwd,
            full_name="Priya Verma (Student)",
            role="complainant",
            department_id=None
        )
        db.add_all([admin_user, handler_user, student_user])
        db.flush()

        # 5. 15 Realistic Resolved Incidents across categories
        embedder = get_embedder()
        now = get_current_time()

        resolved_incidents_data = [
            {
                "code": "INC-HIST-001",
                "title": "Main supply pipeline rupture near Hostel Block A lawn",
                "category": "Water & Plumbing",
                "location_id": block_a.id,
                "dept": "Estate & Maintenance",
                "priority": "High",
                "impact_score": 68,
                "resolution_notes": "Excavated line, replaced fractured 4-inch PVC elbow coupling, reinforced clamp bracket and restored full pipeline pressure.",
                "hours_to_resolve": 6.5
            },
            {
                "code": "INC-HIST-002",
                "title": "Drinking water cooler continuous leakage in Central Library",
                "category": "Water & Plumbing",
                "location_id": loc_lib_hall.id,
                "dept": "Estate & Maintenance",
                "priority": "Medium",
                "impact_score": 45,
                "resolution_notes": "Replaced cracked float valve inside storage tank and sealed leaking drainage outlet with Teflon gasket.",
                "hours_to_resolve": 4.0
            },
            {
                "code": "INC-HIST-003",
                "title": "Severe spark and burning smell in Computer Lab 2 main distribution board",
                "category": "Electrical",
                "location_id": loc_lab_2.id,
                "dept": "Electrical & Power",
                "priority": "Critical",
                "impact_score": 82,
                "resolution_notes": "Isolated circuit, replaced damaged 63A three-phase MCCB, re-crimped loose aluminum busbar lugs and verified thermal imaging.",
                "hours_to_resolve": 3.0
            },
            {
                "code": "INC-HIST-004",
                "title": "Corridor lighting blackout across Hostel Block B First Floor",
                "category": "Electrical",
                "location_id": loc_b_first.id,
                "dept": "Electrical & Power",
                "priority": "Medium",
                "impact_score": 52,
                "resolution_notes": "Diagnosed tripped sub-MCB due to a faulty capacitor in fixture #4; replaced ballast and all lamps operational.",
                "hours_to_resolve": 5.5
            },
            {
                "code": "INC-HIST-005",
                "title": "Ceiling fan speed regulator burnt in Academic Block A Ground Floor",
                "category": "Electrical",
                "location_id": loc_a_ground.id,
                "dept": "Electrical & Power",
                "priority": "Low",
                "impact_score": 28,
                "resolution_notes": "Replaced burnt rotary regulator with modular electronic dimmer switch and tested load stability.",
                "hours_to_resolve": 8.0
            },
            {
                "code": "INC-HIST-006",
                "title": "Sewage drain blockage and foul odor overflow in Hostel Block B",
                "category": "Sanitation & Cleanliness",
                "location_id": block_b.id,
                "dept": "Estate & Maintenance",
                "priority": "High",
                "impact_score": 74,
                "resolution_notes": "Sanitation crew deployed mechanized drain auger to clear stubborn grease and plastic obstruction; chlorinated and disinfected sump.",
                "hours_to_resolve": 7.0,
                "days_ago": 16
            },
            {
                "code": "INC-HIST-007",
                "title": "Overflowing waste dumpster near Mess Dining Hall",
                "category": "Sanitation & Cleanliness",
                "location_id": loc_b_mess.id,
                "dept": "Estate & Maintenance",
                "priority": "Medium",
                "impact_score": 48,
                "resolution_notes": "Arranged municipal clearance vehicle for immediate disposal; sanitized container bay and added two segregated 240L bins.",
                "hours_to_resolve": 5.0,
                "days_ago": 9
            },
            {
                "code": "INC-HIST-008",
                "title": "Hostel Block B Second Floor Wi-Fi access point offline",
                "category": "IT & Network",
                "location_id": loc_b_second.id,
                "dept": "IT & Networking",
                "priority": "Medium",
                "impact_score": 55,
                "resolution_notes": "Power-over-Ethernet (PoE) port reset on distribution switch, renewed DHCP lease pool and confirmed 100Mbps coverage.",
                "hours_to_resolve": 4.5
            },
            {
                "code": "INC-HIST-009",
                "title": "Core optical fiber packet drop affecting Computer Lab 2",
                "category": "IT & Network",
                "location_id": loc_lab_2.id,
                "dept": "IT & Networking",
                "priority": "High",
                "impact_score": 71,
                "resolution_notes": "Cleaned LC fiber patch connectors with isopropyl alcohol swabs and replaced degraded SFP+ transceiver module.",
                "hours_to_resolve": 8.5
            },
            {
                "code": "INC-HIST-010",
                "title": "Mess dining water dispenser refrigeration compressor failure",
                "category": "Hostel & Mess",
                "location_id": loc_b_mess.id,
                "dept": "Hostel & Food Services",
                "priority": "High",
                "impact_score": 64,
                "resolution_notes": "HVAC technician recharged R-134a refrigerant gas, replaced starting relay and confirmed chilling to 11 degrees Celsius.",
                "hours_to_resolve": 12.0
            },
            {
                "code": "INC-HIST-011",
                "title": "Washroom floor drain backflow and overflow in Hostel Block B First Floor",
                "category": "Sanitation & Cleanliness",
                "location_id": loc_b_first.id,
                "dept": "Estate & Maintenance",
                "priority": "Medium",
                "impact_score": 45,
                "resolution_notes": "De-silted common drainage branch, replaced defective P-trap seal, and sanitized first floor corridor.",
                "hours_to_resolve": 3.5,
                "days_ago": 3
            },
            {
                "code": "INC-HIST-012",
                "title": "Classroom ceiling projector color distortion in Academic Block A",
                "category": "Classroom & Infrastructure",
                "location_id": loc_a_ground.id,
                "dept": "Academic & Student Affairs",
                "priority": "Low",
                "impact_score": 27,
                "resolution_notes": "Replaced worn 15-meter shielded HDMI cable running through conduit and reset projector color matrix settings.",
                "hours_to_resolve": 14.0
            },
            {
                "code": "INC-HIST-013",
                "title": "Broken wooden writing bench in Academic Block A Ground Floor",
                "category": "Classroom & Infrastructure",
                "location_id": loc_a_ground.id,
                "dept": "Estate & Maintenance",
                "priority": "Low",
                "impact_score": 22,
                "resolution_notes": "Welded broken tubular steel bracket, refastened polished hardwood bench plank with countersunk bolts.",
                "hours_to_resolve": 20.0
            },
            {
                "code": "INC-HIST-014",
                "title": "Perimeter boundary floodlight dark zone near Sports Complex",
                "category": "Safety & Security",
                "location_id": loc_sports.id,
                "dept": "Campus Security & Proctorial",
                "priority": "High",
                "impact_score": 67,
                "resolution_notes": "Replaced damaged 100W IP66 LED flood fixture and repositioned beam angle to eliminate blind spot at boundary fence.",
                "hours_to_resolve": 9.0
            },
            {
                "code": "INC-HIST-015",
                "title": "Hostel caution deposit refund delay in Accounts Office",
                "category": "Administrative",
                "location_id": loc_accounts.id,
                "dept": "Academic & Student Affairs",
                "priority": "Medium",
                "impact_score": 42,
                "resolution_notes": "Audited bank account IFSC discrepancies, reconciled ledger entries and executed batch RTGS credit for 42 student accounts.",
                "hours_to_resolve": 36.0
            }
        ]

        # 37 Realistic Linked Complaints for the 15 Historical Incidents
        historical_complaints_data = [
            # INC-HIST-001 (4 complaints)
            {"inc": "INC-HIST-001", "text": "Water pipeline burst outside Hostel Block A entrance lawn flooding pathway", "lang": "english", "anon": False, "offset_h": 0.2, "aff": 8},
            {"inc": "INC-HIST-001", "text": "Hostel Block A ke garden mein main water line leak ho rahi hai paani jam gaya", "lang": "hinglish", "anon": False, "offset_h": 0.5, "aff": 12},
            {"inc": "INC-HIST-001", "text": "हॉस्टल ब्लॉक ए के मुख्य लॉन में पानी की पाइपलाइन फटी हुई है", "lang": "hindi", "anon": True, "offset_h": 0.8, "aff": 15},
            {"inc": "INC-HIST-001", "text": "High pressure water pipe leaking heavily outside Block A mess path", "lang": "english", "anon": False, "offset_h": 1.2, "aff": 10},

            # INC-HIST-002 (2 complaints)
            {"inc": "INC-HIST-002", "text": "Drinking water cooler overflowing continuously on Reading Hall 1 floor", "lang": "english", "anon": False, "offset_h": 0.3, "aff": 20},
            {"inc": "INC-HIST-002", "text": "लाइब्रेरी के रीडिंग हॉल में वाटर कूलर का पानी बहकर फर्श पर फैल रहा है", "lang": "hindi", "anon": True, "offset_h": 0.7, "aff": 25},

            # INC-HIST-003 (3 complaints)
            {"inc": "INC-HIST-003", "text": "Loud spark and black smoke coming from distribution panel in Computer Lab 2", "lang": "english", "anon": False, "offset_h": 0.1, "aff": 40},
            {"inc": "INC-HIST-003", "text": "Computer Lab 2 ke switch board se spark nikla aur burning smell aa rahi hai", "lang": "hinglish", "anon": False, "offset_h": 0.2, "aff": 35},
            {"inc": "INC-HIST-003", "text": "लैब 2 के मुख्य बिजली बोर्ड में आग की चिंगारी निकली तुरंत बंद करें", "lang": "hindi", "anon": True, "offset_h": 0.4, "aff": 30},

            # INC-HIST-004 (2 complaints)
            {"inc": "INC-HIST-004", "text": "Complete light blackout in Hostel Block B first floor passage", "lang": "english", "anon": False, "offset_h": 0.4, "aff": 18},
            {"inc": "INC-HIST-004", "text": "First floor corridor ki saari lights fuse ho gayi hain andhera hai", "lang": "hinglish", "anon": True, "offset_h": 0.9, "aff": 22},

            # INC-HIST-005 (1 complaint)
            {"inc": "INC-HIST-005", "text": "Ceiling fan regulator burnt and stuck at maximum speed in Ground Floor classroom", "lang": "english", "anon": False, "offset_h": 0.5, "aff": 5},

            # INC-HIST-006 (3 complaints)
            {"inc": "INC-HIST-006", "text": "Sewage backflow and unbearable foul smell from ground floor drainage line in Block B", "lang": "english", "anon": False, "offset_h": 0.3, "aff": 30},
            {"inc": "INC-HIST-006", "text": "Hostel Block B mein ganda paani overflow ho raha hai badboo fail rahi hai", "lang": "hinglish", "anon": False, "offset_h": 0.6, "aff": 28},
            {"inc": "INC-HIST-006", "text": "हॉस्टल ब्लॉक बी के सीवर का पानी बाहर निकल रहा है सफाई जरूरी है", "lang": "hindi", "anon": True, "offset_h": 1.0, "aff": 25},

            # INC-HIST-007 (2 complaints)
            {"inc": "INC-HIST-007", "text": "Garbage dumpster overflowing near Mess entrance dogs scattering trash", "lang": "english", "anon": False, "offset_h": 0.5, "aff": 50},
            {"inc": "INC-HIST-007", "text": "Mess ke bahar kachre ka dher laga hai dustbin pura bhar chuka hai", "lang": "hinglish", "anon": True, "offset_h": 1.1, "aff": 45},

            # INC-HIST-008 (2 complaints)
            {"inc": "INC-HIST-008", "text": "Wi-Fi access point showing red light no internet connectivity in Block B second floor", "lang": "english", "anon": False, "offset_h": 0.4, "aff": 35},
            {"inc": "INC-HIST-008", "text": "Second floor par wifi network disconnect ho gaya signal nahi aa raha", "lang": "hinglish", "anon": False, "offset_h": 0.8, "aff": 40},

            # INC-HIST-009 (2 complaints)
            {"inc": "INC-HIST-009", "text": "Extremely high packet loss and gateway disconnects during lab exam in Lab 2", "lang": "english", "anon": False, "offset_h": 0.2, "aff": 60},
            {"inc": "INC-HIST-009", "text": "कंप्यूटर लैब 2 में इंटरनेट सर्वर कनेक्शन बार-बार कट रहा है", "lang": "hindi", "anon": True, "offset_h": 0.5, "aff": 55},

            # INC-HIST-010 (4 complaints)
            {"inc": "INC-HIST-010", "text": "Water cooler in mess dispensing warm water compressor not humming", "lang": "english", "anon": False, "offset_h": 0.3, "aff": 70},
            {"inc": "INC-HIST-010", "text": "Mess dining hall cooler kharab hai garam paani aa raha hai", "lang": "hinglish", "anon": False, "offset_h": 0.7, "aff": 80},
            {"inc": "INC-HIST-010", "text": "मेस में पीने का ठंडा पानी नहीं मिल रहा मशीन खराब हो गई है", "lang": "hindi", "anon": True, "offset_h": 1.2, "aff": 65},
            {"inc": "INC-HIST-010", "text": "Drinking water chiller failed in student mess hot weather crisis", "lang": "english", "anon": False, "offset_h": 1.8, "aff": 75},

            # INC-HIST-011 (1 complaint)
            {"inc": "INC-HIST-011", "text": "Washroom floor drain backflow causing foul smell and overflow in Hostel Block B First Floor", "lang": "english", "anon": False, "offset_h": 0.4, "aff": 18},

            # INC-HIST-012 (2 complaints)
            {"inc": "INC-HIST-012", "text": "Ceiling projector displaying deep yellow tint impossible to read slide text", "lang": "english", "anon": False, "offset_h": 0.5, "aff": 45},
            {"inc": "INC-HIST-012", "text": "Block A ground floor classroom ka projector color distort kar raha hai", "lang": "hinglish", "anon": True, "offset_h": 1.0, "aff": 40},

            # INC-HIST-013 (1 complaint)
            {"inc": "INC-HIST-013", "text": "Third row wooden desk plank cracked with exposed sharp screw", "lang": "english", "anon": False, "offset_h": 0.6, "aff": 3},

            # INC-HIST-014 (3 complaints)
            {"inc": "INC-HIST-014", "text": "High mast floodlight near sports ground dark complete blind spot at night", "lang": "english", "anon": False, "offset_h": 0.3, "aff": 25},
            {"inc": "INC-HIST-014", "text": "Sports complex ke paas boundary wall par streetlight band rehti hai safety issue", "lang": "hinglish", "anon": True, "offset_h": 0.8, "aff": 30},
            {"inc": "INC-HIST-014", "text": "खेल परिसर की बाउंड्री पर रात को बहुत अंधेरा रहता है सुरक्षा खतरा है", "lang": "hindi", "anon": False, "offset_h": 1.5, "aff": 20},

            # INC-HIST-015 (5 complaints)
            {"inc": "INC-HIST-015", "text": "Caution deposit refund pending past 60 days accounts counter not updating status", "lang": "english", "anon": False, "offset_h": 1.0, "aff": 15},
            {"inc": "INC-HIST-015", "text": "Hostel caution money ka cheque abhi tak nahi mila bar bar chakkar katna pad raha hai", "lang": "hinglish", "anon": False, "offset_h": 2.5, "aff": 12},
            {"inc": "INC-HIST-015", "text": "एडमिन ऑफिस में सिक्योरिटी रिफंड का आवेदन 2 महीने से अटका हुआ है", "lang": "hindi", "anon": True, "offset_h": 4.0, "aff": 18},
            {"inc": "INC-HIST-015", "text": "Multiple outgoing students waiting for hostel clearance security money refund", "lang": "english", "anon": False, "offset_h": 6.0, "aff": 25},
            {"inc": "INC-HIST-015", "text": "Accounts branch ka caution refund batch process delay ho raha hai", "lang": "hinglish", "anon": True, "offset_h": 8.0, "aff": 20},
        ]

        # Map to track created incident objects by code
        incident_by_code: Dict[str, Incident] = {}

        for item in resolved_incidents_data:
            days_ago = item.get("days_ago", 5)
            created_dt = now - timedelta(days=days_ago, hours=item["hours_to_resolve"])
            resolved_dt = created_dt + timedelta(hours=item["hours_to_resolve"])
            
            inc = Incident(
                code=item["code"],
                title=item["title"],
                category=item["category"],
                location_id=item["location_id"],
                department_id=dept_map[item["dept"]].id,
                priority=item["priority"],
                impact_score=item["impact_score"],
                impact_breakdown={
                    "severity": 60,
                    "urgency": 50,
                    "affected": 40,
                    "duration": 30,
                    "raw_hours_open": item["hours_to_resolve"]
                },
                relatedness_confidence=0.9,
                status="Resolved",
                deadline_at=created_dt + timedelta(hours=72),
                escalation_level=0,
                resolution_notes=item["resolution_notes"],
                created_at=created_dt,
                resolved_at=resolved_dt
            )
            db.add(inc)
            db.flush()
            incident_by_code[item["code"]] = inc

        # Insert 37 linked historical complaints
        for idx, c_item in enumerate(historical_complaints_data, start=1):
            inc = incident_by_code[c_item["inc"]]
            c_created = inc.created_at + timedelta(hours=c_item["offset_h"])
            access_hash = hash_access_code(f"HIST{idx:04d}") if c_item["anon"] else None
            
            cmp_hist = Complaint(
                tracking_id=f"CMP-HIST-{idx:03d}",
                complainant_id=None if c_item["anon"] else student_user.id,
                is_anonymous=c_item["anon"],
                access_code_hash=access_hash,
                text=c_item["text"],
                original_language=c_item["lang"],
                category=inc.category,
                category_confidence=0.90,
                priority=inc.priority,
                priority_reasons=[f"Historical verified {inc.category} grievance"],
                location_id=inc.location_id,
                department_id=inc.department_id,
                status="Resolved",
                incident_id=inc.id,
                affected_count=c_item["aff"],
                embedding=embedder.embed(c_item["text"]),
                deadline_at=c_created + timedelta(hours=72.0),
                escalation_level=0,
                created_at=c_created
            )
            db.add(cmp_hist)

        db.commit()

        # 6. Seed the live demo story
        seed_demo_story(db, now)

        print("Database seeded successfully with master data, 15 historical incidents (37 linked complaints), and demo story!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        if close_on_exit:
            db.close()


if __name__ == "__main__":
    seed_database()
