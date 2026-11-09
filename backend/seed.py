"""Database seeding script for Project Shikayat Karo.

Seeds:
- 1 Organisation / Campus root location
- 6 Departments
- 14 Locations in a campus > block > floor/area tree with 2D grid coordinates
- 3 Demo Users: admin@demo, handler@demo, student@demo (password: password123)
- 4 Escalation rules (Critical 4h, High 24h, Medium 72h, Low 168h)
- 15 Realistic resolved incidents with comprehensive resolution notes
"""

from datetime import datetime, timedelta
import bcrypt

from backend.database import SessionLocal, engine, Base
from backend.models import (
    Department, User, Location, Incident, Complaint, EscalationRule, Update
)
from backend.ai.embedder import get_embedder
from backend.clock import get_current_time


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def seed_database():
    """Seeds the database with required master data and resolved historical records."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(User).filter(User.email == "admin@demo").first():
            print("Database already seeded. Skipping initial seed.")
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
        dept_map = {}
        for d in departments_data:
            dept = Department(**d)
            db.add(dept)
            db.flush()
            dept_map[d["name"]] = dept

        # 2. Locations: Campus > Block > Floor/Area (~14 locations)
        # Root Campus
        campus = Location(
            name="Main Campus (Vidyanagar)",
            parent_id=None,
            type="campus",
            grid_x=50.0,
            grid_y=50.0
        )
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
            # Water & Plumbing
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
            # Electrical
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
            # Sanitation & Cleanliness
            {
                "code": "INC-HIST-006",
                "title": "Sewage drain blockage and foul odor overflow in Hostel Block B",
                "category": "Sanitation & Cleanliness",
                "location_id": block_b.id,
                "dept": "Estate & Maintenance",
                "priority": "High",
                "impact_score": 74,
                "resolution_notes": "Sanitation crew deployed mechanized drain auger to clear stubborn grease and plastic obstruction; chlorinated and disinfected sump.",
                "hours_to_resolve": 7.0
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
                "hours_to_resolve": 5.0
            },
            # IT & Network
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
            # Hostel & Mess
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
                "title": "Hostel room door mortise lock jammed in Block B First Floor",
                "category": "Hostel & Mess",
                "location_id": loc_b_first.id,
                "dept": "Hostel & Food Services",
                "priority": "Low",
                "impact_score": 25,
                "resolution_notes": "Carpenter extracted jammed key fragment, dismantled cylinder lockset, lubricated tumblers and handed over duplicate key set.",
                "hours_to_resolve": 3.5
            },
            # Classroom & Infrastructure
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
            # Safety & Security
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
            # Administrative
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

        for item in resolved_incidents_data:
            created_dt = now - timedelta(days=5, hours=item["hours_to_resolve"])
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

        db.commit()
        print("Database seeded successfully with all required master data!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
