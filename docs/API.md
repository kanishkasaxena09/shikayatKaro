# Shikayat Karo REST API Reference

This document provides complete, verified endpoint contracts for the **Shikayat Karo** backend. Every request and response schema in this specification is verified against the running application.

---

## 1. Overview & Conventions

- **Base URL**: `http://localhost:8000` (configurable via `HOST` and `PORT`)
- **Interactive Documentation**: `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc` (ReDoc)
- **Authentication**: JWT Bearer token passed in the `Authorization` HTTP header:
  ```http
  Authorization: Bearer <access_token>
  ```
- **Standard Error Format**:
  ```json
  {
    "detail": "Description of error or role requirement"
  }
  ```
- **Rate Limiting**: In-memory sliding-window limiter:
  - `POST /api/auth/login`: Maximum 5 requests/min per IP $\rightarrow$ returns `429 Too Many Requests`.
  - `GET /api/track`: Maximum 10 requests/min per IP $\rightarrow$ returns `429 Too Many Requests`.

---

## 2. Role Matrix

| Method | Endpoint | Allowed Roles | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Public | System and service health check |
| `POST` | `/api/auth/register` | Public | Register new citizen account |
| `POST` | `/api/auth/login` | Public (Rate Limited) | Authenticate user, returns JWT access token |
| `GET` | `/api/auth/me` | Authenticated (All) | Retrieve currently authenticated user profile |
| `POST` | `/api/complaints` | Public / Authenticated | Submit grievance in English, Hindi, or Hinglish |
| `GET` | `/api/complaints/my` | Authenticated (All) | Retrieve grievances submitted by the logged-in user |
| `GET` | `/api/complaints/{id}` | Owner or Staff | Retrieve single complaint (sanitized for anon) |
| `GET` | `/api/track` | Public (Rate Limited) | Public status tracker via tracking ID + optional access code |
| `GET` | `/api/suggestions` | `admin`, `handler` | List AI clustering suggestions (`pending`, `confirmed`, `rejected`) |
| `POST` | `/api/suggestions/{id}/confirm` | `admin`, `handler` | Confirm cluster into a Parent Incident with impact score |
| `POST` | `/api/suggestions/{id}/reject` | `admin`, `handler` | Reject clustering suggestion |
| `POST` | `/api/suggestions/{id}/remove-complaint` | `admin`, `handler` | Remove outlier complaint from candidate cluster |
| `GET` | `/api/incidents` | `admin`, `handler` | List parent incident dossiers with filters |
| `GET` | `/api/incidents/{id}` | `admin`, `handler` | Retrieve parent incident dossier, linked complaints, & similar resolved |
| `POST` | `/api/incidents/{id}/assign` | `admin`, `handler` | Assign incident to department |
| `POST` | `/api/incidents/{id}/status` | `admin`, `handler` | Transition incident status (mandatory resolution notes on `Resolved`) |
| `GET` | `/api/heatmap` | Public / Authenticated | Campus spatial risk heatmap coordinates and impacts |
| `GET` | `/api/dashboard/summary` | Public / Authenticated | High-level platform health metrics & KPI counters |
| `GET` | `/api/analytics/recurring` | Public / Authenticated | Recurring issue patterns ($\ge 3$ incidents in 30 days at same block) |
| `POST` | `/api/analytics/recurring/mark-fix` | `admin`, `handler` | Schedule permanent root-cause remediation task (`PermanentFixTask`) |
| `GET` | `/api/departments` | Public / Authenticated | List all operational campus departments |
| `GET` | `/api/notifications` | Authenticated (All) | List user notifications |
| `POST` | `/api/notifications/{id}/read` | Authenticated (All) | Mark notification as read |
| `POST` | `/api/demo/load-story` | Guarded by `DEMO_MODE` | Ingest canonical 5-complaint demo story |
| `POST` | `/api/demo/advance-time` | Guarded by `DEMO_MODE` | Fast-forward virtual clock by $N$ hours & evaluate SLAs |
| `POST` | `/api/demo/reset` | Guarded by `DEMO_MODE` | Reset virtual clock to 0 and restore benchmark demo state |

---

## 3. Demo Persona Accounts

All demo accounts initialize with password: `password123`:

| Persona Role | Email | System Privileges |
| :--- | :--- | :--- |
| **Chief Administrator** | `admin@demo` | Cluster confirmation, incident assignment, permanent fixes, KPI oversight |
| **Facility Incharge** | `handler@demo` | Estate & Maintenance investigation, incident resolution with mandatory notes |
| **Student / Citizen** | `student@demo` | Grievance submission, personal filing history, tracking |

---

## 4. Endpoints & Verified Request/Response Examples

### 1. Health Check

#### `GET /api/health`
Returns system operational status.

**Response `200 OK`**:
```json
{
  "status": "healthy",
  "service": "Shikayat Karo Backend",
  "version": "1.0.0"
}
```

---

### 2. Authentication

#### `POST /api/auth/login`
Authenticates a user using email and password. Rate-limited to 5 requests/min per IP.

**Request Body**:
```json
{
  "email": "admin@demo",
  "password": "password123"
}
```

**Response `200 OK`**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "admin@demo",
    "full_name": "Dr. Arvind Sharma",
    "role": "admin",
    "department_id": null,
    "created_at": "2026-11-20T03:25:59.320780"
  }
}
```

**Rate Limit Exceeded `429 Too Many Requests`**:
```json
{
  "detail": "Too many login attempts. Please wait 60 seconds before retrying."
}
```

---

### 3. Grievances & Complaints

#### `POST /api/complaints`
Registers a grievance in English, Hindi, or Hinglish with optional zero-knowledge anonymity.

**Request Body**:
```json
{
  "text": "Hostel Block B ground floor ke paas paani ka pipe burst ho gaya hai pura corridor flood ho raha hai",
  "location_id": 2,
  "affected_count": 15,
  "is_anonymous": true
}
```

**Response `201 Created`**:
```json
{
  "complaint": {
    "id": 45,
    "tracking_id": "CMP-0045",
    "is_anonymous": true,
    "text": "Hostel Block B ground floor ke paas paani ka pipe burst ho gaya hai pura corridor flood ho raha hai",
    "original_language": "hinglish",
    "category": "Water & Plumbing",
    "category_confidence": 0.885,
    "priority": "High",
    "priority_reasons": ["Essential utility service disruption affecting multiple students (15 reported affected)"],
    "location_id": 2,
    "location_name": "Hostel Block B",
    "department_id": 1,
    "department_name": "Estate & Maintenance",
    "status": "Submitted",
    "incident_id": null,
    "affected_count": 15,
    "deadline_at": "2026-11-21T03:25:59.320780",
    "escalation_level": 0,
    "created_at": "2026-11-20T03:25:59.320780",
    "complainant": null
  },
  "access_code": "8F2A1C90",
  "suggestion_created": true,
  "suggestion_id": 1,
  "ai_analysis": {
    "language": "hinglish",
    "classification": {
      "category": "Water & Plumbing",
      "confidence": 0.885,
      "needs_review": false
    },
    "priority": {
      "level": "High",
      "reasons": ["Essential utility service disruption affecting multiple students (15 reported affected)"]
    }
  }
}
```

#### `GET /api/track`
Public status tracking endpoint. Rate-limited to 10 requests/min per IP.

**Query Parameters**:
- `tracking_id`: e.g. `CMP-0045` (required)
- `access_code`: e.g. `8F2A1C90` (required for anonymous filings)

**Response `200 OK`**:
```json
{
  "tracking_id": "CMP-0045",
  "status": "Submitted",
  "category": "Water & Plumbing",
  "priority": "High",
  "location_name": "Hostel Block B",
  "department_name": "Estate & Maintenance",
  "is_anonymous": true,
  "created_at": "2026-11-20T03:25:59.320780",
  "deadline_at": "2026-11-21T03:25:59.320780",
  "escalation_level": 0,
  "incident_id": null,
  "timeline": [
    {
      "event_type": "status",
      "old_status": null,
      "new_status": "Submitted",
      "remarks": "Grievance registered and initial priority computed.",
      "timestamp": "2026-11-20T03:25:59.320780"
    }
  ]
}
```

---

### 4. AI Clustering & Suggestions

#### `GET /api/suggestions`
Retrieves candidate grievance clusters for administrator review.

**Headers**: `Authorization: Bearer <admin_or_handler_token>`

**Response `200 OK`**:
```json
[
  {
    "id": 1,
    "complaint_ids": [38, 39, 40, 41, 42],
    "confidence": 0.892,
    "reasons": [
      "Exact building location match (Hostel Block B)",
      "High text semantic similarity across English and Hinglish",
      "Grievances submitted within 3.5 hour burst window"
    ],
    "engine": "fastembed",
    "status": "pending",
    "incident_id": null,
    "created_at": "2026-11-20T02:00:00.000000",
    "complaints": [...]
  }
]
```

#### `POST /api/suggestions/{id}/confirm`
Confirms a suggestion, generating an official Parent Incident dossier with a calculated multi-factor impact score.

**Request Body**:
```json
{
  "title": "Severe Water Main Pipeline Leakage near Hostel Block B Entrance",
  "department_id": 1,
  "priority": "High"
}
```

**Response `200 OK`**:
```json
{
  "message": "Suggestion confirmed and parent incident created successfully.",
  "incident_id": 16,
  "incident_code": "INC-016",
  "impact_score": 78,
  "linked_complaints_count": 5
}
```

---

### 5. Parent Incidents Management

#### `GET /api/incidents/{id}`
Retrieves a full incident dossier with audit updates, linked individual complaints, and historical resolution recommendations.

**Response `200 OK`**:
```json
{
  "id": 16,
  "code": "INC-016",
  "title": "Severe Water Main Pipeline Leakage near Hostel Block B Entrance",
  "category": "Water & Plumbing",
  "location_id": 2,
  "location_name": "Hostel Block B",
  "priority": "High",
  "impact_score": 78,
  "impact_breakdown": {
    "severity": 75,
    "urgency": 65,
    "affected": 82,
    "duration": 40
  },
  "relatedness_confidence": 0.892,
  "status": "Assigned",
  "department_id": 1,
  "department_name": "Estate & Maintenance",
  "deadline_at": "2026-11-21T03:25:59.320780",
  "escalation_level": 0,
  "linked_complaints": [...],
  "similar_resolved": [
    {
      "incident_code": "INC-HIST-001",
      "title": "Water pipeline burst outside Hostel Block A entrance lawn flooding pathway",
      "resolution_notes": "Plumbing crew isolated main butterfly valve, excavated damaged 2.5-inch GI pipe section, installed new PVC union sleeve, and pressure-tested line.",
      "similarity_score": 0.912
    }
  ]
}
```

#### `POST /api/incidents/{id}/status`
Transitions an incident's investigation status.

> [!IMPORTANT]
> Transitioning to `Resolved` or `Closed` **strictly requires** non-empty `resolution_notes` documenting the physical actions taken to fix the issue.

**Request Body**:
```json
{
  "status": "Resolved",
  "resolution_notes": "Replaced ruptured 3-inch inlet flange with new brass gate valve and restored water pressure.",
  "remarks": "Completed work order with campus civil crew."
}
```

**Response `200 OK`**:
```json
{
  "id": 16,
  "code": "INC-016",
  "status": "Resolved",
  "resolution_notes": "Replaced ruptured 3-inch inlet flange with new brass gate valve and restored water pressure.",
  "resolved_at": "2026-11-20T08:30:00.000000"
}
```

---

### 6. Analytics & Recurring Issues

#### `GET /api/analytics/recurring`
Surfaces recurring infrastructure breakdown patterns ($\ge 3$ distinct parent incidents at the same block within 30 days).

**Response `200 OK`**:
```json
[
  {
    "id": "rec-3-sanitation_and_cleanliness",
    "block_id": 3,
    "block_name": "Hostel Block B",
    "category": "Sanitation & Cleanliness",
    "incident_count": 3,
    "incident_ids": [11, 7, 6],
    "incident_codes": ["INC-HIST-011", "INC-HIST-007", "INC-HIST-006"],
    "total_affected": 196,
    "average_resolution_hours": 5.2,
    "last_occurrence_at": "2026-11-17T03:25:59.320780",
    "days_since_last_occurrence": 3.1,
    "has_permanent_fix": false,
    "permanent_fix_task": null
  }
]
```

#### `POST /api/analytics/recurring/mark-fix`
Creates a tracked root-cause remediation task assigned to a department with an SLA due date. Guarded by role `admin` or `handler`.

**Request Body**:
```json
{
  "category": "Sanitation & Cleanliness",
  "location_id": 3,
  "department_id": 1,
  "due_date_days": 14,
  "title": "Complete overhaul of Hostel Block B drainage manifold and grease traps",
  "notes": "Replace worn cast-iron drainage branch with 6-inch UPVC piping to permanently stop chronic choking."
}
```

**Response `200 OK`**:
```json
{
  "id": 1,
  "task_code": "PFIX-001",
  "title": "Complete overhaul of Hostel Block B drainage manifold and grease traps",
  "category": "Sanitation & Cleanliness",
  "location_id": 3,
  "department_id": 1,
  "department_name": "Estate & Maintenance",
  "status": "Scheduled",
  "due_date": "2026-12-04T03:25:59.320780",
  "incident_ids": [11, 7, 6],
  "created_at": "2026-11-20T03:25:59.320780"
}
```

---

### 7. Demo Simulator & Virtual Clock

#### `POST /api/demo/advance-time`
Advances the virtual clock by $N$ hours and triggers automated SLA escalation checks.

**Request Body**:
```json
{
  "hours": 6.5
}
```

**Response `200 OK`**:
```json
{
  "message": "Virtual clock advanced by 6.5 hours.",
  "previous_time": "2026-11-20T03:25:59.320780",
  "new_time": "2026-11-20T09:55:59.320780",
  "total_offset_hours": 6.5,
  "escalations_triggered": [
    {
      "target_type": "incident",
      "id": 16,
      "code": "INC-016",
      "old_level": 1,
      "new_level": 2,
      "overdue_hours": 6.5
    }
  ]
}
```
