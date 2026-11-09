"""Demo controls and simulation story router for Project Shikayat Karo."""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db, Base, engine
from backend.models import (
    Complaint, Incident, Suggestion, Update, Notification, User, Location, Department
)
from backend.schemas import AdvanceTimeRequest
from backend.clock import get_current_time, advance_time, reset_time, get_offset_hours
from backend.ai.escalation import check_and_apply_escalations
from backend.routers.complaints import submit_complaint, ComplaintCreate
from backend.seed import seed_database

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.post("/load-story")
def load_demo_story(db: Session = Depends(get_db)):
    """Loads the canonical demo story:
    5 complaints about a water leak near Hostel Block B:
    - 2 English
    - 1 Hindi
    - 1 Hinglish
    - 1 Anonymous
    Spaced over a few virtual hours, automatically forming an aggregated Suggestion.
    """
    # Find Hostel Block B location
    block_b = db.query(Location).filter(Location.name == "Hostel Block B").first()
    loc_id = block_b.id if block_b else None

    # Demo student user
    student = db.query(User).filter(User.email == "student@demo").first()

    # Reset clock for clean demonstration timeline
    reset_time()

    story_items = [
        {
            "advance_before": 0.0,
            "text": "Water pipe ruptured outside Hostel Block B entrance, drinking water pipeline leaking heavily onto the pathway",
            "is_anonymous": False,
            "affected_count": 5
        },
        {
            "advance_before": 1.1,
            "text": "Severe water leakage from main supply pipe near Hostel Block B, clean water flowing continuously and flooding the corridor entrance",
            "is_anonymous": False,
            "affected_count": 8
        },
        {
            "advance_before": 0.9,
            "text": "हॉस्टल ब्लॉक बी के मुख्य गेट के पास पानी का पाइप फटा हुआ है और सड़क पर बहुत सारा पानी बह रहा है",
            "is_anonymous": False,
            "affected_count": 12
        },
        {
            "advance_before": 0.8,
            "text": "Hostel Block B ground floor ke paas paani ka pipe leak ho raha hai, nal ka paani waste ho raha hai turant theek kijiye",
            "is_anonymous": False,
            "affected_count": 15
        },
        {
            "advance_before": 0.7,
            "text": "Water pipeline broken near Block B hostel entrance, water logging is blocking student access, please fix urgently",
            "is_anonymous": True,  # Anonymous report
            "affected_count": 20
        }
    ]

    created_complaints: List[Dict[str, Any]] = []

    for item in story_items:
        if item["advance_before"] > 0:
            advance_time(item["advance_before"])

        payload = ComplaintCreate(
            text=item["text"],
            location_id=loc_id,
            affected_count=item["affected_count"],
            is_anonymous=item["is_anonymous"]
        )
        res = submit_complaint(payload=payload, current_user=student, db=db)
        created_complaints.append({
            "tracking_id": res.complaint.tracking_id,
            "language": res.complaint.original_language,
            "is_anonymous": res.complaint.is_anonymous,
            "access_code": res.access_code,
            "category": res.complaint.category,
            "priority": res.complaint.priority,
            "suggestion_created": res.suggestion_created,
            "suggestion_id": res.suggestion_id
        })

    # Retrieve final pending suggestion
    pending_sugg = db.query(Suggestion).filter(Suggestion.status == "pending").order_by(Suggestion.id.desc()).first()

    return {
        "message": "Demo story loaded successfully: 5 complaints submitted across English, Hindi, and Hinglish.",
        "location": "Hostel Block B",
        "complaints_created": created_complaints,
        "pending_suggestion_id": pending_sugg.id if pending_sugg else None,
        "grouped_complaint_count": len(pending_sugg.complaint_ids) if pending_sugg else 0,
        "composite_confidence": pending_sugg.confidence if pending_sugg else 0.0,
        "suggestion_reasons": pending_sugg.reasons if pending_sugg else [],
        "current_virtual_time": get_current_time().isoformat()
    }


@router.post("/advance-time")
def advance_virtual_time(payload: AdvanceTimeRequest, db: Session = Depends(get_db)):
    """Advances the virtual clock by N hours and evaluates escalation rules on demand."""
    prev_time = get_current_time()
    new_time = advance_time(payload.hours)

    # Run escalation checks
    escalation_results = check_and_apply_escalations(db)

    return {
        "message": f"Virtual clock advanced by {payload.hours} hours.",
        "previous_time": prev_time.isoformat(),
        "new_time": new_time.isoformat(),
        "total_offset_hours": get_offset_hours(),
        "escalations_triggered": escalation_results
    }


@router.post("/reset")
def reset_demo_state(db: Session = Depends(get_db)):
    """Resets the virtual clock to 0 and clears demo complaints and suggestions."""
    reset_time()

    # Clear dynamically created complaints, suggestions, notifications, non-historical incidents
    db.query(Complaint).delete()
    db.query(Suggestion).delete()
    db.query(Notification).delete()
    db.query(Update).delete()
    db.query(Incident).filter(Incident.code.notlike("INC-HIST-%")).delete()
    db.commit()

    return {
        "message": "Demo state and virtual clock reset successfully.",
        "virtual_time_utc": get_current_time().isoformat()
    }
