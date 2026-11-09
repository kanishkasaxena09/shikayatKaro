"""Analytics, Heatmap, and Dashboard summary router for Project Shikayat Karo."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models import Complaint, Incident, Location, Suggestion
from backend.schemas import HeatmapItem, DashboardSummary
from backend.routers.auth import get_current_user
from backend.clock import get_current_time, get_offset_hours

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


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
        virtual_offset_hours=get_offset_hours()
    )
