"""Pydantic schemas for request validation and response serialization.

Ensures strict privacy: anonymous complaints NEVER expose complainant details.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ---------------- Auth Schemas ----------------
class UserBase(BaseModel):
    email: str = Field(..., min_length=3)
    full_name: str
    role: str = "complainant"
    department_id: Optional[int] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: str
    department_id: Optional[int] = None
    created_at: Optional[datetime] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None


# ---------------- Department & Location Schemas ----------------
class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    description: Optional[str] = None


class LocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: Optional[int] = None
    type: str
    grid_x: float
    grid_y: float


# ---------------- Complaint Schemas ----------------
class ComplaintCreate(BaseModel):
    text: str = Field(..., min_length=5)
    location_id: Optional[int] = None
    affected_count: int = Field(default=1, ge=1)
    is_anonymous: bool = False


class ComplaintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tracking_id: str
    is_anonymous: bool
    text: str
    original_language: str
    category: str
    category_confidence: float
    priority: str
    priority_reasons: Optional[List[str]] = None
    location_id: Optional[int] = None
    location_name: Optional[str] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    status: str
    incident_id: Optional[int] = None
    affected_count: int
    deadline_at: Optional[datetime] = None
    escalation_level: int = 0
    created_at: datetime
    complainant: Optional[UserOut] = None


class ComplaintSubmitResponse(BaseModel):
    complaint: ComplaintOut
    access_code: Optional[str] = None
    suggestion_created: bool = False
    suggestion_id: Optional[int] = None
    ai_analysis: Dict[str, Any]


# ---------------- Incident Schemas ----------------
class IncidentCreate(BaseModel):
    title: str
    category: str
    location_id: Optional[int] = None
    department_id: Optional[int] = None
    priority: str = "Medium"
    complaint_ids: List[int] = []


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    title: str
    category: str
    location_id: Optional[int] = None
    location_name: Optional[str] = None
    priority: str
    impact_score: int
    impact_breakdown: Optional[Dict[str, Any]] = None
    relatedness_confidence: float
    status: str
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    deadline_at: Optional[datetime] = None
    escalation_level: int
    resolution_notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    linked_complaints_count: int = 0
    pending_hours: float = 0.0


class IncidentDetail(IncidentOut):
    linked_complaints: List[ComplaintOut] = []
    timeline: List[Dict[str, Any]] = []
    escalation_rules: Optional[Dict[str, Any]] = None
    similar_resolved: List[Dict[str, Any]] = []


class IncidentAssign(BaseModel):
    department_id: int
    remarks: Optional[str] = None


class IncidentStatusUpdate(BaseModel):
    status: str
    resolution_notes: Optional[str] = None
    remarks: Optional[str] = None


# ---------------- Suggestion Schemas ----------------
class SuggestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    complaint_ids: List[int]
    confidence: float
    reasons: Optional[List[str]] = None
    status: str
    incident_id: Optional[int] = None
    created_at: datetime
    complaints: List[ComplaintOut] = []


class SuggestionConfirm(BaseModel):
    title: Optional[str] = None
    department_id: Optional[int] = None
    priority: Optional[str] = None


class RemoveComplaintFromGroup(BaseModel):
    complaint_id: int


# ---------------- Update Audit Log Schemas ----------------
class UpdateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target_type: str
    target_id: int
    actor_id: Optional[int] = None
    actor_role: Optional[str] = None
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    remarks: Optional[str] = None
    event_type: str
    timestamp: datetime


# ---------------- Notification Schemas ----------------
class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    title: str
    message: str
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    is_read: bool
    created_at: datetime


# ---------------- Analytics & Heatmap Schemas ----------------
class HeatmapItem(BaseModel):
    location_id: int
    location_name: str
    parent_name: Optional[str] = None
    grid_x: float
    grid_y: float
    complaint_count: int
    incident_count: int
    total_impact: int
    average_impact: float
    primary_category: Optional[str] = None


class DashboardSummary(BaseModel):
    total_complaints: int
    total_incidents: int
    pending_suggestions: int
    active_incidents: int
    resolved_incidents: int
    critical_incidents: int
    escalated_count: int
    average_resolution_hours: float
    virtual_clock_utc: str
    virtual_offset_hours: float


# ---------------- Demo Schemas ----------------
class AdvanceTimeRequest(BaseModel):
    hours: float = Field(..., gt=0)
