# Shikayat Karo (शिकायत Karo)
## Intelligent Multi-Organisation Grievance Redressal & Incident Aggregation Platform

Shikayat Karo is an AI-powered grievance intelligence system that transforms individual, multilingual complaints into structured, actionable, and trackable parent incidents. By combining composite multi-factor clustering, transparent rule-based reasoning, and zero-leakage privacy guarantees, it streamlines grievance resolution across campuses and public institutions.

---

## Key Features

- **Multi-Factor Incident Clustering**: Clusters related complaints using **Text (Embeddings) + Spatial Hierarchy (2D Coordinates & Block Ancestry) + Time Proximity + Category Match** (never text alone). Hard rule strictly caps relatedness score at 0.40 if both location and category differ.
- **Multilingual Support**: Real-time detection and processing of grievances in **Hindi** (Devanagari script), **Hinglish** (150+ romanised vocabulary tokens), and **English**.
- **Transparent AI Engine**:
  - `language.py`: High-accuracy language classification.
  - `classifier.py`: Nearest-prototype category prediction across 9 campus infrastructure categories.
  - `priority.py`: 100% deterministic, rule-based priority engine (Critical, High, Medium, Low) with natural-language reason explanations.
  - `impact.py`: Transparent impact formula:
    $$\text{Impact} = 0.35 \cdot \text{Severity} + 0.25 \cdot \text{Urgency} + 0.25 \cdot \text{Affected} + 0.15 \cdot \text{Duration}$$
  - `relatedness.py`: Composite relatedness score:
    $$\text{Score} = 0.45 \cdot \text{Text} + 0.25 \cdot \text{Location} + 0.15 \cdot \text{Time} + 0.15 \cdot \text{Category}$$
  - `escalation.py`: SLA deadline management (Critical 4h, High 24h, Medium 72h, Low 168h) with automated Tier 1 (100%), Tier 2 (150%), and Tier 3 (200%) escalations.
  - `resolution_intel.py`: Recommends similar historical resolved incidents to guide facility handlers.
- **Zero-Leakage Anonymous Reporting**: Public tracking via an 8-character uppercase hex code. Only salted bcrypt hashes are stored in the database. Personal identity is never recorded or exposed.
- **Virtual Clock Simulator**: Deterministic fast-forwarding of time (`/api/demo/advance-time`) for interactive demonstrations and automated SLA testing.
- **Live 2D Spatial Risk Heatmap**: Real-time interactive campus map rendering infrastructure density and grievance severity.

---

## Three Role-Based Interfaces

The application provides three connected, role-guarded user experiences:

1. **Complainant (Student / Citizen)**
   - Multilingual grievance submission with preset shortcuts and optional anonymous mode.
   - Immediate AI analysis modal displaying category confidence, priority reasoning, and access code.
   - Public status tracking (`/track`) without login requirement.
   - Private filing history (`/my-complaints`) and notification center (`/notifications`).

2. **Administrator (Chief Authority)**
   - Unified campus command dashboard (`/`) with KPI cards and 2D spatial grievance heatmap.
   - Incident clustering suggestion review (`/suggestions`): confirm clusters into parent incidents, reject, or remove outliers.
   - Backlog management (`/incidents`) with status, priority, and category filters.
   - Department assignment and re-assignment (`/api/incidents/{id}/assign`).
   - Story simulator and virtual clock controls (`/demo`).

3. **Department Handler (Facility Incharge)**
   - Department-filtered incident backlog (`/incidents`).
   - Incident dossier inspection (`/incidents/{id}`) with complete audit trail, linked individual complaints, and historical resolution intelligence.
   - Workflow status transitions (`Under Investigation` $\rightarrow$ `In Progress` $\rightarrow$ `Resolved` $\rightarrow$ `Closed`).
   - Mandatory resolution notes validation on case resolution.

---

## Technology Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy 2.x, Pydantic v2, PyJWT, Bcrypt, APScheduler, SQLite / PostgreSQL.
- **Frontend**: React 19, Vite 6, Tailwind CSS v4, Axios, React Router v7, Lucide Icons.
- **Deployment**: Render (Backend Web Service), Vercel (Frontend SPA).

---

## Project Structure

```text
shikayatKaro/
├── backend/
│   ├── ai/                         # Transparent AI reasoning modules
│   │   ├── classifier.py           # Prototype category classifier
│   │   ├── embedder.py             # SentenceTransformers / FastEmbed / Fallback embedder
│   │   ├── escalation.py           # SLA calculation & tier escalations
│   │   ├── impact.py               # Impact score formula
│   │   ├── language.py             # Hindi, Hinglish, English detection
│   │   ├── priority.py             # Rule-based priority scoring
│   │   ├── relatedness.py          # Multi-factor composite relatedness
│   │   └── resolution_intel.py     # Past incident similarity recommender
│   ├── routers/                    # FastAPI route controllers
│   │   ├── analytics.py            # Heatmap & KPI counters
│   │   ├── auth.py                 # JWT authentication & role guards
│   │   ├── complaints.py           # Grievance registration & tracking
│   │   ├── demo.py                 # Demo story simulation & clock advance
│   │   ├── incidents.py            # Incident dossier & workflow management
│   │   ├── notifications.py        # User & broadcast alerts
│   │   └── suggestions.py          # Incident clustering approval
│   ├── tests/                      # Unit & integration test suite
│   ├── clock.py                    # Deterministic virtual clock
│   ├── database.py                 # SQLAlchemy session & SQLite WAL pragmas
│   ├── main.py                     # Main application & lifespan
│   ├── models.py                   # Database models
│   ├── requirements.txt            # Python dependencies
│   ├── schemas.py                  # Pydantic schemas
│   └── seed.py                     # Master database seeding
├── frontend/
│   ├── src/
│   │   ├── api/client.js           # Centralized Axios API client
│   │   ├── components/             # Reusable UI components (Navbar, Heatmap, Modals)
│   │   ├── context/                # AuthContext & ToastContext
│   │   ├── pages/                  # 10 role-based pages
│   │   ├── App.jsx                 # Route definitions & protected guards
│   │   └── main.jsx                # React DOM root
│   ├── package.json                # Frontend dependencies
│   ├── vite.config.js              # Vite configuration & development proxy
│   └── vercel.json                 # Vercel SPA routing rules
├── .env.example                    # Environment variable configuration template
├── render.yaml                     # Render Blueprint specification
├── run.py                          # Unified server runner
├── seed.py                         # Master seed entrypoint
└── smoke_test.py                   # Automated end-to-end smoke test
```

---

## Demo Credentials

All test persona accounts use password: `password123`

| Persona | Email | Role | Scope |
| :--- | :--- | :--- | :--- |
| **Chief Administrator** | `admin@demo` | `admin` | Full system oversight & suggestion approvals |
| **Facility Incharge** | `handler@demo` | `handler` | Estate & Maintenance department incidents |
| **Student / Citizen** | `student@demo` | `complainant` | Grievance submission & personal tracking |

*(Note: The sticky top bar in the web UI allows instant 1-click persona switching during demonstrations).*

---

## Quickstart & Local Setup

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 2. Backend Setup
```bash
# Clone the repository
git clone https://github.com/kanishkasaxena09/shikayatKaro.git
cd shikayatKaro

# Create & activate a virtual environment
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Seed initial master data & historical incidents
python seed.py

# Start the backend server (runs on http://127.0.0.1:8000)
python run.py
```
*Interactive Swagger API documentation is available at `http://127.0.0.1:8000/docs`.*

### 3. Frontend Setup
```bash
# Open a new terminal and navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the Vite development server (runs on http://localhost:3000)
npm run dev
```

---

## Testing

### Automated Live Server Verification
To run the automated 13-stage end-to-end test against a live backend instance:
```bash
python smoke_test.py
```

### Frontend Production Build
```bash
cd frontend
npm run build
```

---

## Production Deployment

### Backend on Render
1. Connect your GitHub repository to [Render](https://render.com).
2. Create a new **Web Service** pointing to the repository:
   - **Root Directory**: `.` (leave blank or set to repository root)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `python run.py`
3. Configure Environment Variables:
   - `ENVIRONMENT`: `production`
   - `EMBEDDER`: `fallback` *(or `sentence-transformers` on paid instances with $\ge$ 2GB RAM)*
   - `DATABASE_URL`: `sqlite:///./shikayat_karo.db` *(or PostgreSQL connection string)*
   - `JWT_SECRET`: Random 32+ character string
   - `CORS_ORIGINS`: Your Vercel frontend URL (e.g. `https://shikayatkaro.vercel.app`)
4. Health check path: `/api/health`.

### Frontend on Vercel
1. Import the repository in [Vercel](https://vercel.com).
2. Set **Root Directory** to `frontend`.
3. Framework Preset: **Vite**.
4. Configure Environment Variable:
   - `VITE_API_BASE_URL`: Your deployed Render backend URL (e.g. `https://shikayatkaro-backend.onrender.com`).
5. Deploy. The included [`frontend/vercel.json`](file:///C:/Users/91999/.gemini/antigravity/scratch/shikayatKaro/frontend/vercel.json) handles client-side SPA routing automatically.

---

## Known Limitations

- **Free-Tier Memory Considerations**: Deep neural embeddings via `sentence-transformers` require $\sim 800\text{ MB}$ of memory. On free-tier cloud environments (512MB RAM limits), configure `EMBEDDER=fallback` in environment variables for lightweight, deterministic n-gram semantic hashing without degrading classification capabilities.
- **Ephemeral Storage on SQLite**: When using SQLite on serverless hosts, the database file resets on service restart. For persistent multi-user production data, configure a hosted PostgreSQL database URL in `DATABASE_URL`.
