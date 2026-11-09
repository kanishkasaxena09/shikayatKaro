"""Escalation management module for Project Shikayat Karo.

Rules:
- Deadlines: Critical 4h, High 24h, Medium 72h, Low 168h
- Escalation tiers:
  - Level 1: 100% of deadline elapsed -> Department Head
  - Level 2: 150% of deadline elapsed -> Admin
  - Level 3: 200% of deadline elapsed -> Senior Authority
- Deadlines are tracked on parent incidents when complaints are linked.
- Status 'Awaiting Info' pauses the clock.
- 'Resolved' and 'Closed' cease escalation.
- Audit Updates and Notifications are emitted with no duplicates.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from backend.models import Complaint, Incident, EscalationRule, Update, Notification, User
from backend.clock import get_current_time

DEFAULT_DEADLINES: Dict[str, float] = {
    "Critical": 4.0,
    "High": 24.0,
    "Medium": 72.0,
    "Low": 168.0
}


def get_deadline_for_priority(db: Session, priority: str) -> float:
    """Fetches configured deadline hours from DB EscalationRule, or default."""
    rule = db.query(EscalationRule).filter(EscalationRule.priority == priority).first()
    if rule:
        return float(rule.deadline_hours)
    return DEFAULT_DEADLINES.get(priority, 72.0)


def calculate_deadline(db: Session, priority: str, start_time: datetime) -> datetime:
    """Computes initial deadline timestamp from creation time and priority."""
    hours = get_deadline_for_priority(db, priority)
    return start_time + timedelta(hours=hours)


def check_and_apply_escalations(db: Session) -> Dict[str, int]:
    """Checks all active incidents and complaints and applies escalation tiers.
    
    Can be run from APScheduler or triggered synchronously after advance_time.
    Returns:
        {"incidents_escalated": int, "complaints_escalated": int}
    """
    now = get_current_time()
    incidents_escalated = 0
    complaints_escalated = 0

    # 1. Process active Incidents
    active_incidents = db.query(Incident).filter(
        Incident.status.notin_(["Resolved", "Closed", "Awaiting Info"])
    ).all()

    for inc in active_incidents:
        if not inc.deadline_at:
            inc.deadline_at = calculate_deadline(db, inc.priority, inc.created_at)

        deadline_hours = get_deadline_for_priority(db, inc.priority)
        elapsed_seconds = (now - inc.created_at).total_seconds()
        elapsed_hours = elapsed_seconds / 3600.0

        ratio = elapsed_hours / max(0.1, deadline_hours)

        target_level = inc.escalation_level
        level_name = ""
        recipient_role = ""

        if ratio >= 2.0 and inc.escalation_level < 3:
            target_level = 3
            level_name = "Level 3 (Senior Authority)"
            recipient_role = "admin"
        elif ratio >= 1.5 and inc.escalation_level < 2:
            target_level = 2
            level_name = "Level 2 (Admin)"
            recipient_role = "admin"
        elif ratio >= 1.0 and inc.escalation_level < 1:
            target_level = 1
            level_name = "Level 1 (Department Head)"
            recipient_role = "handler"

        if target_level > inc.escalation_level:
            old_level = inc.escalation_level
            inc.escalation_level = target_level
            incidents_escalated += 1

            remarks = (
                f"Incident {inc.code} escalated from Level {old_level} to {level_name}. "
                f"Elapsed: {round(elapsed_hours, 1)}h (Deadline: {deadline_hours}h, {round(ratio * 100, 1)}%)."
            )

            # Record audit update
            update = Update(
                target_type="incident",
                target_id=inc.id,
                actor_id=None,
                actor_role="system",
                old_status=inc.status,
                new_status=inc.status,
                remarks=remarks,
                event_type="escalation",
                timestamp=now
            )
            db.add(update)

            # Target notification users
            query = db.query(User)
            if recipient_role == "handler" and inc.department_id:
                users_to_notify = query.filter(
                    User.department_id == inc.department_id,
                    User.role.in_(["handler", "admin"])
                ).all()
            else:
                users_to_notify = query.filter(User.role == "admin").all()

            for user in users_to_notify:
                db.add(Notification(
                    user_id=user.id,
                    title=f"ESCALATION: {inc.code} -> {level_name}",
                    message=remarks,
                    target_type="incident",
                    target_id=inc.id,
                    is_read=False,
                    created_at=now
                ))

    # 2. Process Standalone Complaints (not yet linked to any incident)
    standalone_complaints = db.query(Complaint).filter(
        Complaint.incident_id.is_(None),
        Complaint.status.notin_(["Resolved", "Closed", "Awaiting Info"])
    ).all()

    for cmp in standalone_complaints:
        if not cmp.deadline_at:
            cmp.deadline_at = calculate_deadline(db, cmp.priority, cmp.created_at)

        deadline_hours = get_deadline_for_priority(db, cmp.priority)
        elapsed_seconds = (now - cmp.created_at).total_seconds()
        elapsed_hours = elapsed_seconds / 3600.0
        ratio = elapsed_hours / max(0.1, deadline_hours)

        target_level = cmp.escalation_level
        level_name = ""

        if ratio >= 2.0 and cmp.escalation_level < 3:
            target_level = 3
            level_name = "Level 3 (Senior Authority)"
        elif ratio >= 1.5 and cmp.escalation_level < 2:
            target_level = 2
            level_name = "Level 2 (Admin)"
        elif ratio >= 1.0 and cmp.escalation_level < 1:
            target_level = 1
            level_name = "Level 1 (Department Head)"

        if target_level > cmp.escalation_level:
            old_level = cmp.escalation_level
            cmp.escalation_level = target_level
            complaints_escalated += 1

            remarks = (
                f"Complaint {cmp.tracking_id} escalated from Level {old_level} to {level_name}. "
                f"Elapsed: {round(elapsed_hours, 1)}h (Deadline: {deadline_hours}h)."
            )

            db.add(Update(
                target_type="complaint",
                target_id=cmp.id,
                actor_id=None,
                actor_role="system",
                old_status=cmp.status,
                new_status=cmp.status,
                remarks=remarks,
                event_type="escalation",
                timestamp=now
            ))

            # Notify admins
            admins = db.query(User).filter(User.role == "admin").all()
            for admin_user in admins:
                db.add(Notification(
                    user_id=admin_user.id,
                    title=f"ESCALATION: {cmp.tracking_id} -> {level_name}",
                    message=remarks,
                    target_type="complaint",
                    target_id=cmp.id,
                    is_read=False,
                    created_at=now
                ))

    db.commit()
    return {
        "incidents_escalated": incidents_escalated,
        "complaints_escalated": complaints_escalated
    }
