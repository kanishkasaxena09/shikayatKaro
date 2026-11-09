"""Incidents management router for Project Shikayat Karo."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Incident, Complaint, Department, Update, Notification, User
from backend.schemas import (
    IncidentOut, IncidentDetail, IncidentAssign, IncidentStatusUpdate, UpdateOut
)
from backend.routers.auth import require_role, get_current_user
from backend.routers.complaints import serialize_complaint
from backend.ai.resolution_intel import find_similar_resolved_incidents
from backend.clock import get_current_time

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


def serialize_incident_summary(inc: Incident) -> IncidentOut:
    """Builds an IncidentOut model with calculated pending hours and linked complaint counts."""
    now = get_current_time()
    elapsed_hours = (now - inc.created_at).total_seconds() / 3600.0
    if inc.resolved_at:
        pending_hours = (inc.resolved_at - inc.created_at).total_seconds() / 3600.0
    else:
        pending_hours = elapsed_hours

    return IncidentOut(
        id=inc.id,
        code=inc.code,
        title=inc.title,
        category=inc.category,
        location_id=inc.location_id,
        location_name=inc.location.name if inc.location else None,
        priority=inc.priority,
        impact_score=inc.impact_score,
        impact_breakdown=inc.impact_breakdown,
        relatedness_confidence=inc.relatedness_confidence,
        status=inc.status,
        department_id=inc.department_id,
        department_name=inc.department.name if inc.department else None,
        deadline_at=inc.deadline_at,
        escalation_level=inc.escalation_level,
        resolution_notes=inc.resolution_notes,
        created_at=inc.created_at,
        resolved_at=inc.resolved_at,
        linked_complaints_count=len(inc.complaints) if inc.complaints else 0,
        pending_hours=round(pending_hours, 1)
    )


@router.get("", response_model=List[IncidentOut])
def list_incidents(
    status_filter: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = None,
    priority: Optional[str] = None,
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists incidents sorted by impact score descending."""
    query = db.query(Incident)

    if status_filter:
        query = query.filter(Incident.status == status_filter)
    if category:
        query = query.filter(Incident.category == category)
    if priority:
        query = query.filter(Incident.priority == priority)
    if department_id:
        query = query.filter(Incident.department_id == department_id)

    # Handlers can optionally be scoped to their department or view all
    incidents = query.order_by(Incident.impact_score.desc(), Incident.created_at.desc()).all()
    return [serialize_incident_summary(inc) for inc in incidents]


@router.get("/{id}", response_model=IncidentDetail)
def get_incident_detail(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns complete incident details including linked complaints, audit timeline, and resolution intelligence."""
    inc = db.query(Incident).filter(Incident.id == id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    base = serialize_incident_summary(inc)

    # 1. Linked complaints (with guaranteed anonymity protections)
    complaint_outs = [serialize_complaint(c) for c in inc.complaints]

    # 2. Timeline from audit logs
    updates = db.query(Update).filter(
        Update.target_type == "incident",
        Update.target_id == inc.id
    ).order_by(Update.timestamp.asc()).all()
    timeline = [UpdateOut.model_validate(u).model_dump() for u in updates]

    # 3. Resolution Intelligence: similar past resolved incidents
    query_text = f"{inc.title} {inc.category}"
    similar_resolved = find_similar_resolved_incidents(db, query_text, limit=3)

    return IncidentDetail(
        **base.model_dump(),
        linked_complaints=complaint_outs,
        timeline=timeline,
        similar_resolved=similar_resolved
    )


@router.post("/{id}/assign")
def assign_department(
    id: int,
    payload: IncidentAssign,
    current_user: User = Depends(require_role(["admin", "handler"])),
    db: Session = Depends(get_db)
):
    """Assigns an incident to a department and updates status to 'Assigned'."""
    inc = db.query(Incident).filter(Incident.id == id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    dept = db.query(Department).filter(Department.id == payload.department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    old_dept_id = inc.department_id
    old_status = inc.status
    now = get_current_time()

    inc.department_id = dept.id
    if inc.status in ["Submitted", "AI Analysed"]:
        inc.status = "Assigned"

    # Propagate to linked complaints
    for c in inc.complaints:
        c.department_id = dept.id
        if c.status in ["Submitted", "AI Analysed"]:
            c.status = "Assigned"

    # Audit Update
    audit = Update(
        target_type="incident",
        target_id=inc.id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        old_status=old_status,
        new_status=inc.status,
        remarks=payload.remarks or f"Assigned to {dept.name} by {current_user.full_name}.",
        event_type="assignment",
        timestamp=now
    )
    db.add(audit)

    # Notify handlers of that department
    dept_users = db.query(User).filter(User.department_id == dept.id).all()
    for u in dept_users:
        db.add(Notification(
            user_id=u.id,
            title=f"New Assignment: {inc.code}",
            message=f"Incident {inc.code} ({inc.title}) has been assigned to your department.",
            target_type="incident",
            target_id=inc.id,
            is_read=False,
            created_at=now
        ))

    db.commit()
    return {
        "message": f"Incident {inc.code} assigned to {dept.name}.",
        "incident_id": inc.id,
        "department_id": dept.id,
        "status": inc.status
    }


@router.post("/{id}/status")
def update_status(
    id: int,
    payload: IncidentStatusUpdate,
    current_user: User = Depends(require_role(["admin", "handler"])),
    db: Session = Depends(get_db)
):
    """Updates incident status.
    
    Status flow:
    Submitted -> AI Analysed -> Assigned -> Under Investigation -> In Progress -> Resolved -> Closed
    (plus Awaiting Info).
    
    Resolution notes are strictly required when transitioning to 'Resolved' or 'Closed'.
    """
    inc = db.query(Incident).filter(Incident.id == id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    valid_statuses = [
        "Submitted", "AI Analysed", "Assigned", "Under Investigation",
        "In Progress", "Awaiting Info", "Resolved", "Closed"
    ]
    if payload.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{payload.status}'. Allowed: {', '.join(valid_statuses)}"
        )

    # Resolution notes required for Resolved and Closed
    if payload.status in ["Resolved", "Closed"]:
        if not payload.resolution_notes or not payload.resolution_notes.strip():
            raise HTTPException(
                status_code=400,
                detail="Resolution notes are strictly required when setting status to Resolved or Closed."
            )

    old_status = inc.status
    now = get_current_time()

    inc.status = payload.status
    if payload.resolution_notes:
        inc.resolution_notes = payload.resolution_notes.strip()

    if payload.status in ["Resolved", "Closed"] and not inc.resolved_at:
        inc.resolved_at = now

    # Propagate status to linked complaints
    for c in inc.complaints:
        c.status = payload.status

    # Audit Update
    audit = Update(
        target_type="incident",
        target_id=inc.id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        old_status=old_status,
        new_status=payload.status,
        remarks=payload.remarks or payload.resolution_notes or f"Status changed from {old_status} to {payload.status}.",
        event_type="status",
        timestamp=now
    )
    db.add(audit)

    # Notify admins and complainants
    admins = db.query(User).filter(User.role == "admin").all()
    for a in admins:
        db.add(Notification(
            user_id=a.id,
            title=f"Status Update: {inc.code} -> {payload.status}",
            message=f"Incident {inc.code} status changed to {payload.status}.",
            target_type="incident",
            target_id=inc.id,
            is_read=False,
            created_at=now
        ))

    db.commit()
    return {
        "message": f"Incident {inc.code} status updated to {payload.status}.",
        "incident_id": inc.id,
        "old_status": old_status,
        "new_status": payload.status,
        "resolved_at": inc.resolved_at
    }
