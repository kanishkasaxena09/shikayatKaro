"""Unit tests for rule-based priority module."""

from backend.ai.priority import calculate_priority, extract_affected_count_hint


def test_safety_hazard_priority():
    # Spark / shock hazard triggers Critical
    prio, reasons = calculate_priority(
        text="Spark coming from switchboard, current is leaking, electric shock danger",
        category="Electrical"
    )
    assert prio == "Critical"
    assert any("safety" in r.lower() or "danger" in r.lower() for r in reasons)


def test_essential_service_with_multiple_affected():
    # Water leak affecting multiple people triggers High
    prio, reasons = calculate_priority(
        text="Water pipeline broken near hostel block B, 15 students facing water cut",
        category="Water & Plumbing",
        reported_affected_count=15
    )
    assert prio in ["High", "Critical"]
    assert any("essential service" in r.lower() for r in reasons)


def test_affected_count_text_extraction():
    # Extracted numbers from text
    assert extract_affected_count_hint("Water is stopped for 25 students") == 25
    assert extract_affected_count_hint("Bijli chali gayi hai in 8 rooms") == 8
    assert extract_affected_count_hint("Entire block has no water") == 40
    assert extract_affected_count_hint("Single tap leaking in room 12") == 1


def test_routine_maintenance_low_priority():
    prio, reasons = calculate_priority(
        text="Desk scratch in lecture room 3 needs polishing during holidays",
        category="Classroom & Infrastructure",
        reported_affected_count=1
    )
    assert prio == "Low"
    assert any("routine" in r.lower() or "standard" in r.lower() for r in reasons)


def test_hinglish_urgency_detection():
    prio, reasons = calculate_priority(
        text="Bhaiya turant aao paani poora beh raha hai emergency hai",
        category="Water & Plumbing"
    )
    assert prio in ["High", "Critical"]
    assert any("urgency" in r.lower() or "essential" in r.lower() for r in reasons)
