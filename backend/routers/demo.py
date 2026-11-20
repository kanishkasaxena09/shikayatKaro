"""Demo controls and simulation story router for Project Shikayat Karo.

Controllable via the DEMO_MODE environment variable (default: true for hackathons).
When DEMO_MODE=false, all endpoints in this router return HTTP 403 Forbidden.
"""

import os
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    Complaint, Incident, Suggestion, Update, Notification, User, Location, Department
)
from backend.schemas import AdvanceTimeRequest
from backend.clock import get_current_time, advance_time, reset_time, get_offset_hours
from backend.ai.escalation import check_and_apply_escalations
from backend.seed import seed_demo_story


def is_demo_mode_enabled() -> bool:
    """Returns True if DEMO_MODE is enabled (default: True)."""
    val = os.getenv("DEMO_MODE", "true").lower().strip()
    return val not in ["false", "0", "no", "disabled", "off"]


def require_demo_mode():
    """Dependency that enforces DEMO_MODE.
    
    When DEMO_MODE=false, demo endpoints return HTTP 403 Forbidden.
    """
    if not is_demo_mode_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo endpoints and story simulator are disabled (DEMO_MODE=false)."
        )


router = APIRouter(prefix="/api/demo", tags=["demo"], dependencies=[Depends(require_demo_mode)])


@router.post("/load-story")
def load_demo_story(db: Session = Depends(get_db)):
    """Loads the canonical demo story:
    - 5 complaints about a major water leak at Hostel Block B (EN, HI, Hinglish, Anonymous)
      forming exactly ONE pending Suggestion for admin confirmation.
    - 2 unrelated complaints (Library Wi-Fi, Computer Lab lighting) that correctly do NOT cluster.
    """
    reset_time()
    res = seed_demo_story(db)

    pending_sugg = db.query(Suggestion).filter(Suggestion.status == "pending").order_by(Suggestion.id.desc()).first()
    demo_complaints = db.query(Complaint).filter(Complaint.tracking_id.like("CMP-DEMO-%")).all()

    created_info = []
    for c in demo_complaints:
        created_info.append({
            "tracking_id": c.tracking_id,
            "language": c.original_language,
            "is_anonymous": c.is_anonymous,
            "category": c.category,
            "priority": c.priority,
            "in_suggestion": bool(pending_sugg and c.id in (pending_sugg.complaint_ids or []))
        })

    return {
        "message": "Demo story loaded: 5 clustered complaints at Hostel Block B + 2 unclustered complaints.",
        "location": "Hostel Block B",
        "complaints_created": created_info,
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
    """Resets the virtual clock to 0 and restores the pristine demo story state:
    - 15 historical resolved incidents with 37 linked complaints.
    - 5 complaints at Hostel Block B forming 1 pending AI cluster.
    - 2 unrelated complaints that do NOT cluster.
    """
    reset_time()
    story_res = seed_demo_story(db)

    total_cmp = db.query(Complaint).count()
    total_inc = db.query(Incident).count()
    active_inc = db.query(Incident).filter(Incident.status.notin_(["Resolved", "Closed"])).count()
    resolved_inc = db.query(Incident).filter(Incident.status.in_(["Resolved", "Closed"])).count()
    pending_sugg = db.query(Suggestion).filter(Suggestion.status == "pending").count()

    return {
        "message": "Demo state and virtual clock reset successfully to pristine story.",
        "virtual_time_utc": get_current_time().isoformat(),
        "total_complaints": total_cmp,
        "total_incidents": total_inc,
        "active_incidents": active_inc,
        "resolved_incidents": resolved_inc,
        "pending_suggestions": pending_sugg,
        "pending_suggestion_id": story_res.get("pending_suggestion_id")
    }
