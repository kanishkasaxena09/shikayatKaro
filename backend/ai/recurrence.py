"""Recurring incident detection module for Project Shikayat Karo.

Definition of a Recurring Issue:
The same category at the same location (or block ancestry) producing
3 or more distinct parent incidents within 30 days of virtual-clock time.

Thresholds are configurable via:
- RECURRING_INCIDENT_THRESHOLD (default: 3)
- RECURRING_WINDOW_DAYS (default: 30)
or via function parameters for testing boundary conditions.
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.models import Incident, Location, Department, PermanentFixTask
from backend.clock import get_current_time

DEFAULT_RECURRING_THRESHOLD = int(os.getenv("RECURRING_INCIDENT_THRESHOLD", "3"))
DEFAULT_RECURRING_WINDOW_DAYS = int(os.getenv("RECURRING_WINDOW_DAYS", "30"))


def get_block_location(loc: Optional[Location]) -> Optional[Location]:
    """Resolves block-level location for spatial ancestry grouping."""
    if not loc:
        return None
    if loc.type == "block":
        return loc
    if loc.parent and loc.parent.type == "block":
        return loc.parent
    return loc


def detect_recurring_issues(
    db: Session,
    min_incidents: Optional[int] = None,
    window_days: Optional[int] = None,
    reference_time: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """Detects recurring infrastructure issues across campus.
    
    A recurring issue occurs when the same category at the same block
    has at least `min_incidents` (default: 3) parent incidents within
    the past `window_days` (default: 30 days).
    """
    threshold = min_incidents if min_incidents is not None else DEFAULT_RECURRING_THRESHOLD
    days = window_days if window_days is not None else DEFAULT_RECURRING_WINDOW_DAYS
    now = reference_time or get_current_time()
    window_start = now - timedelta(days=days)

    # Fetch all parent incidents created within the time window
    incidents = db.query(Incident).filter(
        Incident.created_at >= window_start
    ).order_by(Incident.created_at.desc()).all()

    # Group incidents by (block_id, category)
    groups: Dict[tuple, List[Incident]] = {}
    for inc in incidents:
        block_loc = get_block_location(inc.location)
        block_id = block_loc.id if block_loc else (inc.location_id or 0)
        key = (block_id, inc.category)
        if key not in groups:
            groups[key] = []
        groups[key].append(inc)

    results: List[Dict[str, Any]] = []

    for (block_id, category), inc_list in groups.items():
        if len(inc_list) < threshold:
            continue

        block_loc = db.query(Location).filter(Location.id == block_id).first() if block_id else None
        block_name = block_loc.name if block_loc else "Campus Area"

        # Sort incidents by created_at descending (newest first)
        sorted_incs = sorted(inc_list, key=lambda x: x.created_at, reverse=True)
        latest_inc = sorted_incs[0]
        days_since_last = round((now - latest_inc.created_at).total_seconds() / 86400.0, 1)

        # Total people affected across all incidents in this recurring pattern
        total_affected = 0
        for inc in inc_list:
            if inc.complaints:
                total_affected += sum(c.affected_count for c in inc.complaints)
            elif inc.impact_breakdown and isinstance(inc.impact_breakdown, dict) and "breakdown" in inc.impact_breakdown:
                total_affected += inc.impact_breakdown["breakdown"].get("raw_affected_count", 1)
            else:
                total_affected += 1

        # Average resolution time across resolved incidents in this group
        resolved_with_time = [
            (inc.resolved_at - inc.created_at).total_seconds() / 3600.0
            for inc in inc_list
            if inc.resolved_at and inc.created_at
        ]
        avg_resolution_hours = round(sum(resolved_with_time) / len(resolved_with_time), 1) if resolved_with_time else 0.0

        # Check if an active PermanentFixTask already exists for this block & category
        active_task = db.query(PermanentFixTask).filter(
            PermanentFixTask.location_id == block_id,
            PermanentFixTask.category == category,
            PermanentFixTask.status != "Completed"
        ).order_by(PermanentFixTask.id.desc()).first()

        category_slug = category.lower().replace("&", "and").replace(" ", "_")

        results.append({
            "id": f"rec-{block_id}-{category_slug}",
            "block_id": block_id,
            "block_name": block_name,
            "category": category,
            "incident_count": len(inc_list),
            "incident_ids": [i.id for i in sorted_incs],
            "incident_codes": [i.code for i in sorted_incs],
            "total_affected": total_affected,
            "average_resolution_hours": avg_resolution_hours,
            "last_occurrence_at": latest_inc.created_at.isoformat(),
            "days_since_last_occurrence": max(0.0, days_since_last),
            "has_permanent_fix": active_task is not None,
            "permanent_fix_task": {
                "id": active_task.id,
                "task_code": active_task.task_code,
                "title": active_task.title,
                "status": active_task.status,
                "department_name": active_task.department.name if active_task.department else None,
                "due_date": active_task.due_date.isoformat(),
            } if active_task else None
        })

    # Sort results by incident_count descending, then total_affected descending
    results.sort(key=lambda x: (x["incident_count"], x["total_affected"]), reverse=True)
    return results
