# Project "Shikayat Karo" — Backend

Grievance Redressal Platform that transforms individual complaints into structured, trackable, actionable incidents.

---

## Key Features

- **Multi-Factor Incident Clustering**: Clusters related complaints using **Text (Embeddings) + Location Hierarchy + Time Proximity + Category Match** (never text alone). Hard rule caps score at 0.40 if both location and category differ.
- **Multilingual Support**: Detects and processes complaints in **Hindi** (Devanagari script), **Hinglish** (romanised Hindi vocabulary), and **English**.
- **Transparent AI Engine (`backend/ai/`)**:
  - `embedder.py`: Embeddings with `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2`) and `fastembed` fallback.
  - `language.py`: Hindi (Devanagari ratio), Hinglish (150+ romanised token vocabulary), English fallback.
  - `classifier.py`: Nearest-prototype category prediction across 9 campus categories.
  - `priority.py`: 100% rule-based priority reasoning (Critical, High, Medium, Low) with human-readable rationale strings.
  - `relatedness.py`: Composite relatedness formula:
    $$\text{Score} = 0.45 \cdot \text{Text} + 0.25 \cdot \text{Location} + 0.15 \cdot \text{Time} + 0.15 \cdot \text{Category}$$
  - `impact.py`: Transparent impact formula:
    $$\text{Impact} = 0.35 \cdot \text{Severity} + 0.25 \cdot \text{Urgency} + 0.25 \cdot \text{Affected} + 0.15 \cdot \text{Duration}$$
  - `escalation.py`: Deadlines (Critical 4h, High 24h, Medium 72h, Low 168h) with Level 1 (100%), Level 2 (150%), Level 3 (200%) escalation tiers.
  - `resolution_intel.py`: Suggests similar past resolved incidents.
- **Zero-Leakage Anonymous Reporting**: Anonymous grievances store no user identity. An 8-character access code is generated, and only its salted bcrypt hash is stored. Public tracking (`GET /api/track`) works without authentication and never leaks user identity.
- **Virtual Clock**: Fast-forward time deterministically for demonstrations (`POST /api/demo/advance-time`).

---

## Demo Credentials

All demo accounts use password: `password123`

- **Administrator**: `admin@demo` (Role: `admin`)
- **Department Handler**: `handler@demo` (Role: `handler`, Estate & Maintenance)
- **Student**: `student@demo` (Role: `complainant`)

---

## Quickstart

### 1. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 2. Seed Database
```bash
python seed.py
```
Seeds 6 departments, 14 campus locations with 2D grid coordinates, 3 demo users, and 15 realistic historical resolved incidents.

### 3. Run All Unit & Integration Tests
```bash
python -m pytest backend/tests/
```
33 unit and integration tests covering:
- Hindi, Hinglish, and English language detection
- Nearest-prototype classification
- Rule-based priority detection
- Multi-factor relatedness (different locations are NOT grouped; differently worded complaints at the same place ARE grouped; Hinglish matches English)
- Impact formula (70, 80, 50, 40 -> 63 High)
- SLA escalation tiers (Level 1, 2, 3)
- Strict anonymous reporting privacy
- End-to-end API workflows

### 4. Run Full Demo Story Smoke Test
```bash
python smoke_test.py
```
Runs the 5-complaint Block B water leak demo story across languages, clusters them into an incident suggestion, confirms it as admin, tests anonymous tracking, advances time by 6 hours to trigger escalations, and resolves the incident.

### 5. Start the Live Server
```bash
python run.py
# Or:
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive API documentation (Swagger UI) is available at:
`http://127.0.0.1:8000/docs`
