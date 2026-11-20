"""Analytics, Heatmap, Dashboard summary, and Recurring Issues router for Project Shikayat Karo."""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models import Complaint, Incident, Location, Suggestion, Department, PermanentFixTask, Update, User
from backend.schemas import (
    HeatmapItem, DashboardSummary, RecurringIssueOut, PermanentFixCreate, PermanentFixTaskOut, DepartmentOut
)
from backend.routers.auth import get_current_user, require_role
from backend.clock import get_current_time, get_offset_hours
from backend.ai.recurrence import detect_recurring_issues

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/departments", response_model=List[DepartmentOut])
def list_departments(db: Session = Depends(get_db)):
    """Returns all operational campus departments."""
    return db.query(Department).all()


@router.get("/heatmap", response_model=List[HeatmapItem])
def get_heatmap(
    category: Optional[str] = Query(None, description="Filter by complaint/incident category"),
    date_from: Optional[datetime] = Query(None, description="ISO format start date"),
    date_to: Optional[datetime] = Query(None, description="ISO format end date"),
    db: Session = Depends(get_db)
):
    """Returns spatial grievance heatmap aggregating counts and total impact across campus locations."""
    locations = db.query(Location).filter(Location.type.in_(["block", "floor", "area"])).all()
    results: List[HeatmapItem] = []

    for loc in locations:
        # Complaints at this location
        c_query = db.query(Complaint).filter(Complaint.location_id == loc.id)
        if category:
            c_query = c_query.filter(Complaint.category == category)
        if date_from:
            c_query = c_query.filter(Complaint.created_at >= date_from)
        if date_to:
            c_query = c_query.filter(Complaint.created_at <= date_to)
        complaints = c_query.all()

        # Incidents at this location
        i_query = db.query(Incident).filter(Incident.location_id == loc.id)
        if category:
            i_query = i_query.filter(Incident.category == category)
        if date_from:
            i_query = i_query.filter(Incident.created_at >= date_from)
        if date_to:
            i_query = i_query.filter(Incident.created_at <= date_to)
        incidents = i_query.all()

        c_count = len(complaints)
        i_count = len(incidents)

        total_impact = sum(inc.impact_score for inc in incidents)
        # If no incidents but complaints exist, estimate impact from complaint priorities
        if not incidents and complaints:
            prio_weights = {"Critical": 85, "High": 65, "Medium": 45, "Low": 20}
            total_impact = sum(prio_weights.get(c.priority, 30) for c in complaints)

        total_records = c_count + i_count
        avg_impact = round(total_impact / max(1, i_count or c_count), 1) if total_records > 0 else 0.0

        # Determine primary category at this location
        cat_counts = {}
        for item in complaints + incidents:
            cat = getattr(item, "category", None)
            if cat:
                cat_counts[cat] = cat_counts.get(cat, 0) + 1
        primary_cat = max(cat_counts, key=cat_counts.get) if cat_counts else None

        results.append(HeatmapItem(
            location_id=loc.id,
            location_name=loc.name,
            parent_name=loc.parent.name if loc.parent else None,
            grid_x=loc.grid_x,
            grid_y=loc.grid_y,
            complaint_count=c_count,
            incident_count=i_count,
            total_impact=total_impact,
            average_impact=avg_impact,
            primary_category=primary_cat
        ))

    return results


@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Returns high-level platform health metrics and KPI counters."""
    total_complaints = db.query(Complaint).count()
    total_incidents = db.query(Incident).count()
    pending_suggestions = db.query(Suggestion).filter(Suggestion.status == "pending").count()
    active_incidents = db.query(Incident).filter(Incident.status.notin_(["Resolved", "Closed"])).count()
    resolved_incidents = db.query(Incident).filter(Incident.status.in_(["Resolved", "Closed"])).count()
    critical_incidents = db.query(Incident).filter(Incident.priority == "Critical").count()
    escalated_count = db.query(Incident).filter(Incident.escalation_level > 0).count()

    # Average resolution time in hours
    resolved = db.query(Incident).filter(
        Incident.status.in_(["Resolved", "Closed"]),
        Incident.resolved_at.isnot(None),
        Incident.created_at.isnot(None)
    ).all()

    if resolved:
        total_hours = sum((inc.resolved_at - inc.created_at).total_seconds() / 3600.0 for inc in resolved)
        avg_resolution_hours = round(total_hours / len(resolved), 1)
    else:
        avg_resolution_hours = 0.0

    now = get_current_time()

    from backend.routers.demo import is_demo_mode_enabled

    return DashboardSummary(
        total_complaints=total_complaints,
        total_incidents=total_incidents,
        pending_suggestions=pending_suggestions,
        active_incidents=active_incidents,
        resolved_incidents=resolved_incidents,
        critical_incidents=critical_incidents,
        escalated_count=escalated_count,
        average_resolution_hours=avg_resolution_hours,
        virtual_clock_utc=now.isoformat(),
        virtual_offset_hours=get_offset_hours(),
        demo_mode=is_demo_mode_enabled()
    )


# Category to default Department mapping
CATEGORY_DEPT_FALLBACK = {
    "Water & Plumbing": "Estate & Maintenance",
    "Sanitation & Cleanliness": "Estate & Maintenance",
    "Electrical": "Electrical & Power",
    "IT & Network": "IT & Networking",
    "Hostel & Mess": "Hostel & Food Services",
    "Classroom & Infrastructure": "Estate & Maintenance",
    "Safety & Security": "Campus Security & Proctorial",
    "Administrative": "Academic & Student Affairs",
}


@router.get("/recurring", response_model=List[RecurringIssueOut])
def get_recurring_issues(
    min_incidents: Optional[int] = Query(None, ge=1, description="Minimum incident threshold"),
    window_days: Optional[int] = Query(None, ge=1, description="Time window in days"),
    db: Session = Depends(get_db)
):
    """Surfaces recurring infrastructure issues matching:
    The same category at the same block producing >= 3 parent incidents within 30 days.
    """
    raw_results = detect_recurring_issues(
        db,
        min_incidents=min_incidents,
        window_days=window_days
    )
    return [RecurringIssueOut(**item) for item in raw_results]


@router.post("/recurring/mark-fix", response_model=PermanentFixTaskOut)
def mark_permanent_fix(
    data: PermanentFixCreate,
    current_user: User = Depends(require_role(["admin", "handler"])),
    db: Session = Depends(get_db)
):
    """Creates a permanent infrastructure remediation task for a recurring issue."""
    now = get_current_time()

    loc = db.query(Location).filter(Location.id == data.location_id).first()
    if not loc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location {data.location_id} not found"
        )

    # Resolve department
    dept = None
    if data.department_id:
        dept = db.query(Department).filter(Department.id == data.department_id).first()
        if not dept:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department {data.department_id} not found"
            )
    else:
        dept_name = CATEGORY_DEPT_FALLBACK.get(data.category)
        if dept_name:
            dept = db.query(Department).filter(Department.name == dept_name).first()
        if not dept:
            dept = db.query(Department).first()

    # Generate sequential task code
    last_task = db.query(PermanentFixTask).order_by(PermanentFixTask.id.desc()).first()
    next_num = (last_task.id + 1) if last_task else 1
    task_code = f"PFIX-{next_num:03d}"

    # Calculate due date
    if data.due_date:
        due_date = data.due_date
    else:
        days = data.due_date_days if data.due_date_days is not None else 14
        due_date = now + timedelta(days=days)

    task_title = data.title or f"Permanent Remediation: {data.category} at {loc.name}"
    task_desc = data.description or f"Root-cause engineering overhaul scheduled to remediate recurring {data.category} issues at {loc.name}."

    task = PermanentFixTask(
        task_code=task_code,
        title=task_title,
        description=task_desc,
        category=data.category,
        location_id=loc.id,
        department_id=dept.id if dept else None,
        created_by_id=current_user.id,
        status="Scheduled",
        due_date=due_date,
        incident_ids=data.incident_ids or [],
        notes=data.notes,
        created_at=now
    )
    db.add(task)
    db.flush()

    # Log audit event
    audit_log = Update(
        target_type="permanent_fix",
        target_id=task.id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        old_status=None,
        new_status="Scheduled",
        remarks=f"Admin initiated permanent remediation task {task_code} for recurring {data.category} at {loc.name}.",
        event_type="permanent_fix_created",
        timestamp=now
    )
    db.add(audit_log)
    db.commit()
    db.refresh(task)

    return PermanentFixTaskOut(
        id=task.id,
        task_code=task.task_code,
        title=task.title,
        description=task.description,
        category=task.category,
        location_id=task.location_id,
        department_id=task.department_id,
        department_name=task.department.name if task.department else None,
        created_by_id=task.created_by_id,
        status=task.status,
        due_date=task.due_date,
        incident_ids=task.incident_ids,
        notes=task.notes,
        created_at=task.created_at,
        completed_at=task.completed_at
    )

