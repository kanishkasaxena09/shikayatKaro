"""Unit tests for resolution intelligence module."""

from backend.database import SessionLocal
from backend.ai.resolution_intel import find_similar_resolved_incidents


def test_find_similar_resolved_water_incident():
    db = SessionLocal()
    try:
        # Search for water leakage issue
        results = find_similar_resolved_incidents(
            db,
            query_text="Water pipeline leakage and water cooler tap broken in library",
            limit=3
        )
        assert len(results) > 0
        assert len(results) <= 3

        top = results[0]
        assert "similarity" in top
        assert "resolution_notes" in top
        assert "department_name" in top
        assert "hours_to_resolve" in top
        assert top["system_suggestion_only"] is True
        assert top["category"] == "Water & Plumbing"
        assert top["hours_to_resolve"] > 0
    finally:
        db.close()


def test_resolution_intel_empty_query():
    db = SessionLocal()
    try:
        assert find_similar_resolved_incidents(db, "") == []
    finally:
        db.close()
