"""SQLAlchemy database models for Project Shikayat Karo."""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, JSON, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship

from backend.database import Base
from backend.clock import get_current_time


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    users = relationship("User", back_populates="department")
    complaints = relationship("Complaint", back_populates="department")
    incidents = relationship("Incident", back_populates="department")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default="complainant")  # complainant | handler | admin
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    created_at = Column(DateTime, default=get_current_time)

    department = relationship("Department", back_populates="users")
    complaints = relationship("Complaint", back_populates="complainant")
    notifications = relationship("Notification", back_populates="user")


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    type = Column(String(20), nullable=False)  # campus | block | floor | area
    grid_x = Column(Float, nullable=False, default=0.0)
    grid_y = Column(Float, nullable=False, default=0.0)

    parent = relationship("Location", remote_side=[id], backref="children")
    complaints = relationship("Complaint", back_populates="location")
    incidents = relationship("Incident", back_populates="location")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), unique=True, index=True, nullable=False)  # INC-001
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    priority = Column(String(20), nullable=False, default="Medium")  # Critical | High | Medium | Low
    impact_score = Column(Integer, nullable=False, default=0)
    impact_breakdown = Column(JSON, nullable=True)
    relatedness_confidence = Column(Float, nullable=False, default=0.0)
    status = Column(String(30), nullable=False, default="Submitted")
    # Submitted -> AI Analysed -> Assigned -> Under Investigation -> In Progress -> Resolved -> Closed
    # Also: Awaiting Info (pauses clock)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    deadline_at = Column(DateTime, nullable=True)
    escalation_level = Column(Integer, nullable=False, default=0)  # 0, 1, 2, 3
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_current_time)
    resolved_at = Column(DateTime, nullable=True)

    location = relationship("Location", back_populates="incidents")
    department = relationship("Department", back_populates="incidents")
    complaints = relationship("Complaint", back_populates="incident")


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    tracking_id = Column(String(30), unique=True, index=True, nullable=False)  # CMP-0001
    complainant_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_anonymous = Column(Boolean, nullable=False, default=False)
    access_code_hash = Column(String(255), nullable=True)
    text = Column(Text, nullable=False)
    original_language = Column(String(20), nullable=False, default="english")  # hindi | hinglish | english
    category = Column(String(100), nullable=False)
    category_confidence = Column(Float, nullable=False, default=0.0)
    priority = Column(String(20), nullable=False, default="Medium")
    priority_reasons = Column(JSON, nullable=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    status = Column(String(30), nullable=False, default="Submitted")
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    affected_count = Column(Integer, nullable=False, default=1)
    embedding = Column(JSON, nullable=True)  # cached vector
    deadline_at = Column(DateTime, nullable=True)
    escalation_level = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=get_current_time)

    complainant = relationship("User", back_populates="complaints")
    location = relationship("Location", back_populates="complaints")
    department = relationship("Department", back_populates="complaints")
    incident = relationship("Incident", back_populates="complaints")


class Suggestion(Base):
    __tablename__ = "suggestions"

    id = Column(Integer, primary_key=True, index=True)
    complaint_ids = Column(JSON, nullable=False)  # List[int]
    confidence = Column(Float, nullable=False, default=0.0)
    reasons = Column(JSON, nullable=True)  # List[str]
    status = Column(String(20), nullable=False, default="pending")  # pending | confirmed | rejected
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    created_at = Column(DateTime, default=get_current_time)


class Update(Base):
    """Audit log: target, actor, old_status, new_status, remarks, event_type, timestamp."""
    __tablename__ = "updates"

    id = Column(Integer, primary_key=True, index=True)
    target_type = Column(String(30), nullable=False)  # complaint | incident | suggestion
    target_id = Column(Integer, nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    actor_role = Column(String(30), nullable=True)
    old_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=True)
    remarks = Column(Text, nullable=True)
    event_type = Column(String(30), nullable=False)  # status | assignment | escalation | confirmation
    timestamp = Column(DateTime, default=get_current_time)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    target_type = Column(String(30), nullable=True)
    target_id = Column(Integer, nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=get_current_time)

    user = relationship("User", back_populates="notifications")


class EscalationRule(Base):
    __tablename__ = "escalation_rules"

    id = Column(Integer, primary_key=True, index=True)
    priority = Column(String(20), unique=True, nullable=False)  # Critical | High | Medium | Low
    deadline_hours = Column(Float, nullable=False)
    level_1_percent = Column(Float, nullable=False, default=100.0)
    level_2_percent = Column(Float, nullable=False, default=150.0)
    level_3_percent = Column(Float, nullable=False, default=200.0)
