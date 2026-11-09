"""Unit tests for escalation rules and virtual clock advance."""

from datetime import datetime, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import Incident, Complaint, EscalationRule, Update, Notification, User, Department
from backend.clock import get_current_time, advance_time, reset_time
from backend.ai.escalation import check_and_apply_escalations, calculate_deadline


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    # Seed escalation rules
    rules = [
        EscalationRule(priority="Critical", deadline_hours=4.0, level_1_percent=100.0, level_2_percent=150.0, level_3_percent=200.0),
        EscalationRule(priority="High", deadline_hours=24.0, level_1_percent=100.0, level_2_percent=150.0, level_3_percent=200.0),
        EscalationRule(priority="Medium", deadline_hours=72.0, level_1_percent=100.0, level_2_percent=150.0, level_3_percent=200.0),
        EscalationRule(priority="Low", deadline_hours=168.0, level_1_percent=100.0, level_2_percent=150.0, level_3_percent=200.0),
    ]
    db.add_all(rules)

    dept = Department(name="Estate & Maintenance", code="EST", description="Test dept")
    db.add(dept)
    db.flush()

    admin = User(email="admin@test.com", password_hash="hash", full_name="Admin", role="admin")
    handler = User(email="handler@test.com", password_hash="hash", full_name="Handler", role="handler", department_id=dept.id)
    db.add_all([admin, handler])
    db.commit()

    reset_time()
    yield db
    reset_time()
    db.close()


def test_escalation_tiers_progression(test_db):
    t0 = get_current_time()
    # Critical incident: deadline 4.0 hours
    # Level 1 at 100% (4.0h)
    # Level 2 at 150% (6.0h)
    # Level 3 at 200% (8.0h)
    inc = Incident(
        code="INC-TEST-001",
        title="Main gas pipeline leak",
        category="Safety & Security",
        priority="Critical",
        impact_score=90,
        status="Assigned",
        escalation_level=0,
        created_at=t0,
        deadline_at=t0 + timedelta(hours=4.0)
    )
    test_db.add(inc)
    test_db.commit()

    # 1. Advance 2 hours (50%) -> no escalation
    advance_time(2.0)
    res = check_and_apply_escalations(test_db)
    test_db.refresh(inc)
    assert inc.escalation_level == 0
    assert res["incidents_escalated"] == 0

    # 2. Advance another 2.5 hours (total 4.5h > 4.0h -> Level 1)
    advance_time(2.5)
    res = check_and_apply_escalations(test_db)
    test_db.refresh(inc)
    assert inc.escalation_level == 1
    assert res["incidents_escalated"] == 1

    # Verify audit log & notification
    updates = test_db.query(Update).filter(Update.target_id == inc.id, Update.event_type == "escalation").all()
    assert len(updates) == 1
    assert "Level 1" in updates[0].remarks

    # 3. Advance to 6.5 hours (> 150% = 6.0h -> Level 2)
    advance_time(2.0)
    res = check_and_apply_escalations(test_db)
    test_db.refresh(inc)
    assert inc.escalation_level == 2
    assert res["incidents_escalated"] == 1

    # 4. Advance to 9.0 hours (> 200% = 8.0h -> Level 3)
    advance_time(2.5)
    res = check_and_apply_escalations(test_db)
    test_db.refresh(inc)
    assert inc.escalation_level == 3
    assert res["incidents_escalated"] == 1

    # 5. Advance further (e.g. 15 hours) -> Level remains 3, NO DUPLICATE escalations
    advance_time(6.0)
    res = check_and_apply_escalations(test_db)
    test_db.refresh(inc)
    assert inc.escalation_level == 3
    assert res["incidents_escalated"] == 0  # No duplicate escalation


def test_awaiting_info_pauses_clock(test_db):
    t0 = get_current_time()
    inc = Incident(
        code="INC-TEST-002",
        title="Classroom key lost",
        category="Administrative",
        priority="Low",
        status="Awaiting Info",
        escalation_level=0,
        created_at=t0,
        deadline_at=t0 + timedelta(hours=168.0)
    )
    test_db.add(inc)
    test_db.commit()

    # Fast forward 300 hours
    advance_time(300.0)
    res = check_and_apply_escalations(test_db)
    test_db.refresh(inc)
    # Status is Awaiting Info, so escalation is paused!
    assert inc.escalation_level == 0
    assert res["incidents_escalated"] == 0


def test_resolved_incident_stops_escalation(test_db):
    t0 = get_current_time()
    inc = Incident(
        code="INC-TEST-003",
        title="Broken water valve",
        category="Water & Plumbing",
        priority="High",
        status="Resolved",
        escalation_level=0,
        created_at=t0,
        resolved_at=t0 + timedelta(hours=5.0)
    )
    test_db.add(inc)
    test_db.commit()

    # Advance 100 hours
    advance_time(100.0)
    res = check_and_apply_escalations(test_db)
    test_db.refresh(inc)
    assert inc.escalation_level == 0
    assert res["incidents_escalated"] == 0
