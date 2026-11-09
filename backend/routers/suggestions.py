"""Incident suggestions router for Project Shikayat Karo."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Suggestion, Complaint, Incident, Department, Update, User, Location
from backend.schemas import (
    SuggestionOut, SuggestionConfirm, RemoveComplaintFromGroup,
    IncidentOut, ComplaintOut
)
from backend.routers.auth import require_role, get_current_user
from backend.routers.complaints import serialize_complaint
from backend.ai.impact import calculate_impact
from backend.ai.escalation import calculate_deadline
from backend.clock import get_current_time

router = APIRouter(prefix="/api/suggestions", tags=["suggestions"])


def generate_incident_code(db: Session) -> str:
    """Generates next INC-XXXX code."""
    last = db.query(Incident).order_by(Incident.id.desc()).first()
    next_num = (last.id + 1) if last else 1
    return f"INC-{next_num:03d}"


def serialize_suggestion(sugg: Suggestion, db: Session) -> SuggestionOut:
    """Helper to load linked complaint models and serialize safely."""
    c_ids = sugg.complaint_ids or []
    complaints = db.query(Complaint).filter(Complaint.id.in_(c_ids)).all() if c_ids else []
    complaint_outs = [serialize_complaint(c) for c in complaints]

    return SuggestionOut(
        id=sugg.id,
        complaint_ids=c_ids,
        confidence=sugg.confidence,
        reasons=sugg.reasons,
        status=sugg.status,
        incident_id=sugg.incident_id,
        created_at=sugg.created_at,
        complaints=complaint_outs
    )


@router.get("", response_model=List[SuggestionOut])
def list_suggestions(
    status_filter: Optional[str] = Query("pending", description="Filter by status: pending | confirmed | rejected | all"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists system-generated incident suggestions."""
    query = db.query(Suggestion)
    if status_filter and status_filter.lower() != "all":
        query = query.filter(Suggestion.status == status_filter.lower())
    
    suggestions = query.order_by(Suggestion.confidence.desc(), Suggestion.created_at.desc()).all()
    return [serialize_suggestion(s, db) for s in suggestions]


@router.post("/{id}/confirm")
def confirm_suggestion(
    id: int,
    payload: SuggestionConfirm = SuggestionConfirm(),
    current_user: User = Depends(require_role(["admin", "handler"])),
    db: Session = Depends(get_db)
):
    """Confirms a suggestion, converting clustered complaints into a formal Parent Incident."""
    sugg = db.query(Suggestion).filter(Suggestion.id == id).first()
    if not sugg:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    if sugg.status != "pending":
        raise HTTPException(status_code=400, detail=f"Cannot confirm suggestion with status '{sugg.status}'")

    c_ids = sugg.complaint_ids or []
    complaints = db.query(Complaint).filter(Complaint.id.in_(c_ids)).all()
    if not complaints:
        raise HTTPException(status_code=400, detail="No active complaints found in this suggestion")

    now = get_current_time()
    inc_code = generate_incident_code(db)

    # Determine aggregated category and location
    primary_category = complaints[0].category
    primary_location_id = complaints[0].location_id

    # Determine priority: pick highest among complaints
    prio_order = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
    highest_prio = "Low"
    for c in complaints:
        if prio_order.get(c.priority, 1) > prio_order.get(highest_prio, 1):
            highest_prio = c.priority

    final_priority = payload.priority or highest_prio

    # Calculate transparent impact score
    # Aggregate affected count
    total_affected = sum(c.affected_count for c in complaints)
    # Longest hours open among complaints
    longest_hours_open = max((now - c.created_at).total_seconds() / 3600.0 for c in complaints)

    # Base severity and urgency mapped from priority level
    sev_map = {"Critical": 85.0, "High": 70.0, "Medium": 50.0, "Low": 25.0}
    urg_map = {"Critical": 90.0, "High": 75.0, "Medium": 50.0, "Low": 20.0}

    impact_result = calculate_impact(
        severity=sev_map.get(final_priority, 50.0),
        urgency=urg_map.get(final_priority, 50.0),
        affected_count=max(total_affected, len(complaints)),
        hours_open=longest_hours_open
    )

    # Auto-assign department if not specified
    dept_id = payload.department_id
    if not dept_id:
        dept_match = {
            "Water & Plumbing": "Estate & Maintenance",
            "Electrical": "Electrical & Power",
            "Sanitation & Cleanliness": "Estate & Maintenance",
            "IT & Network": "IT & Networking",
            "Hostel & Mess": "Hostel & Food Services",
            "Safety & Security": "Campus Security & Proctorial",
            "Harassment & Misconduct (confidential)": "Campus Security & Proctorial",
            "Classroom & Infrastructure": "Academic & Student Affairs",
            "Administrative": "Academic & Student Affairs",
        }
        dept_name = dept_match.get(primary_category, "Estate & Maintenance")
        dept = db.query(Department).filter(Department.name == dept_name).first()
        if dept:
            dept_id = dept.id

    # Construct Title
    loc_name = complaints[0].location.name if complaints[0].location else "Campus Area"
    inc_title = payload.title or f"{primary_category} issue near {loc_name} ({len(complaints)} complaints grouped)"

    # Compute parent incident deadline
    deadline = calculate_deadline(db, final_priority, now)

    # Create Parent Incident
    incident = Incident(
        code=inc_code,
        title=inc_title,
        category=primary_category,
        location_id=primary_location_id,
        department_id=dept_id,
        priority=final_priority,
        impact_score=impact_result["impact_score"],
        impact_breakdown=impact_result,
        relatedness_confidence=sugg.confidence,
        status="Assigned" if dept_id else "AI Analysed",
        deadline_at=deadline,
        escalation_level=0,
        resolution_notes=None,
        created_at=now
    )
    db.add(incident)
    db.flush()

    # Link complaints to the parent incident
    for c in complaints:
        c.incident_id = incident.id
        c.department_id = dept_id
        c.status = "Assigned" if dept_id else "AI Analysed"
        c.deadline_at = deadline

    # Update suggestion status
    sugg.status = "confirmed"
    sugg.incident_id = incident.id

    # Audit Update for confirmation
    audit = Update(
        target_type="incident",
        target_id=incident.id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        old_status=None,
        new_status=incident.status,
        remarks=f"Confirmed Suggestion #{sugg.id}. Grouped {len(complaints)} complaints into Parent Incident {incident.code}.",
        event_type="confirmation",
        timestamp=now
    )
    db.add(audit)
    db.commit()

    return {
        "message": f"Suggestion #{sugg.id} confirmed successfully.",
        "incident_id": incident.id,
        "incident_code": incident.code,
        "impact_score": incident.impact_score,
        "grouped_complaint_ids": c_ids
    }


@router.post("/{id}/reject")
def reject_suggestion(
    id: int,
    current_user: User = Depends(require_role(["admin", "handler"])),
    db: Session = Depends(get_db)
):
    """Rejects a system-generated suggestion."""
    sugg = db.query(Suggestion).filter(Suggestion.id == id).first()
    if not sugg:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    sugg.status = "rejected"
    now = get_current_time()

    audit = Update(
        target_type="suggestion",
        target_id=sugg.id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        old_status="pending",
        new_status="rejected",
        remarks=f"Admin rejected incident clustering suggestion #{sugg.id}.",
        event_type="status",
        timestamp=now
    )
    db.add(audit)
    db.commit()

    return {"message": f"Suggestion #{sugg.id} rejected.", "status": "rejected"}


@router.post("/{id}/remove-complaint")
def remove_complaint_from_group(
    id: int,
    payload: RemoveComplaintFromGroup,
    current_user: User = Depends(require_role(["admin", "handler"])),
    db: Session = Depends(get_db)
):
    """Removes a specific complaint from an incident grouping suggestion."""
    sugg = db.query(Suggestion).filter(Suggestion.id == id).first()
    if not sugg:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    c_ids = list(sugg.complaint_ids or [])
    if payload.complaint_id not in c_ids:
        raise HTTPException(status_code=400, detail=f"Complaint #{payload.complaint_id} is not in this suggestion")

    c_ids.remove(payload.complaint_id)
    sugg.complaint_ids = c_ids

    # If only 1 complaint remains, group no longer valid
    if len(c_ids) < 2:
        sugg.status = "rejected"

    db.commit()
    return {
        "message": f"Complaint #{payload.complaint_id} removed from suggestion #{sugg.id}.",
        "remaining_complaints": c_ids,
        "suggestion_status": sugg.status
    }
