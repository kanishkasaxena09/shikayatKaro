"""Main FastAPI application for Project Shikayat Karo.

Aggregates individual complaints into structured, trackable, actionable incidents.
"""

import os
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from backend.database import engine, Base, SessionLocal, get_db, ensure_database_schema
from backend.seed import seed_database
from backend.ai.escalation import check_and_apply_escalations
from backend.routers import auth, complaints, suggestions, incidents, analytics, notifications, demo
from backend.schemas import LocationOut, PermanentFixCreate, PermanentFixTaskOut

from backend.models import User

# Background APScheduler job for escalation evaluations
scheduler = BackgroundScheduler()


def run_scheduled_escalations():
    """Runs periodic escalation checks every 60s."""
    db = SessionLocal()
    try:
        check_and_apply_escalations(db)
    except Exception as e:
        print(f"[Scheduler Error] Escalation check failed: {e}")
    finally:
        db.close()


def validate_production_config():
    """Validates security requirements in production environment.
    
    Refuses startup if:
    1. JWT_SECRET is missing or equals the insecure default.
    2. CORS_ORIGINS is missing, empty, or contains '*' wildcard.
    """
    env = os.getenv("ENVIRONMENT", "development").lower().strip()
    if env == "production":
        # 1. Enforce strong JWT secret
        auth.get_jwt_secret()

        # 2. Enforce explicit CORS origins without wildcard
        cors_env = os.getenv("CORS_ORIGINS", "").strip()
        if not cors_env or cors_env == "*":
            raise RuntimeError(
                "Production startup failed: In production (ENVIRONMENT=production), CORS_ORIGINS must be set "
                "to explicit allowed frontend domains (e.g. 'https://shikayatkaro.vercel.app') and cannot be empty or '*'."
            )
        origins = [o.strip() for o in cors_env.split(",") if o.strip()]
        if "*" in origins or not origins:
            raise RuntimeError(
                "Production startup failed: In production, CORS_ORIGINS cannot contain '*' wildcard."
            )


def get_cors_origins() -> List[str]:
    """Computes allowed CORS origins based on environment."""
    env = os.getenv("ENVIRONMENT", "development").lower().strip()
    cors_origins_env = os.getenv("CORS_ORIGINS", "")

    if env == "production":
        validate_production_config()
        return [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]

    # Development & Testing safe defaults
    if cors_origins_env and cors_origins_env.strip() != "*":
        return [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]

    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # 0. Validate production environment configuration
    validate_production_config()

    # 1. Initialize database tables & master data if not in test suite
    if not os.getenv("TESTING"):
        Base.metadata.create_all(bind=engine)
        ensure_database_schema(engine)
        try:
            seed_database()
        except Exception as e:
            print(f"Seed warning: {e}")

    # 3. Start APScheduler if not running in pytest/testing
    if not os.getenv("TESTING"):
        scheduler.add_job(run_scheduled_escalations, "interval", seconds=60, id="escalation_job")
        scheduler.start()
        print("[APScheduler] Escalation background job started (interval: 60s).")

    yield

    # Shutdown
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("[APScheduler] Escalation background job stopped.")


app = FastAPI(
    title="Shikayat Karo API",
    description="Intelligent Grievance Redressal and Incident Aggregation Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
origins = get_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(auth.router)
app.include_router(complaints.router)
app.include_router(suggestions.router)
app.include_router(incidents.router)
app.include_router(analytics.router)
app.include_router(notifications.router)
app.include_router(demo.router)

# Direct Aliases for convenience matching prompt specifications
@app.get("/api/track", tags=["complaints"])
def api_track_alias(
    request: Request,
    tracking_id: str = Query(..., min_length=1, max_length=50),
    access_code: Optional[str] = Query(None, max_length=50),
    current_user: Optional[User] = Depends(auth.get_current_user_optional),
    db=Depends(get_db)
):
    """Direct alias for GET /api/track?tracking_id=&access_code="""
    from backend.routers.complaints import track_complaint
    return track_complaint(tracking_id=tracking_id, access_code=access_code, request=request, current_user=current_user, db=db)


@app.get("/api/heatmap", tags=["analytics"])
def api_heatmap_alias(
    category: Optional[str] = Query(None, description="Filter by complaint/incident category"),
    date_from: Optional[datetime] = Query(None, description="ISO format start date"),
    date_to: Optional[datetime] = Query(None, description="ISO format end date"),
    db=Depends(get_db)
):
    """Direct alias for GET /api/heatmap"""
    from backend.routers.analytics import get_heatmap
    return get_heatmap(category=category, date_from=date_from, date_to=date_to, db=db)


@app.get("/api/dashboard/summary", tags=["analytics"])
def api_dashboard_summary_alias(db=Depends(get_db)):
    """Direct alias for GET /api/dashboard/summary"""
    from backend.routers.analytics import get_dashboard_summary
    return get_dashboard_summary(db=db)


@app.get("/api/recurring", tags=["analytics"])
def api_recurring_alias(min_incidents: Optional[int] = None, window_days: Optional[int] = None, db=Depends(get_db)):
    """Direct alias for GET /api/recurring"""
    from backend.routers.analytics import get_recurring_issues
    return get_recurring_issues(min_incidents=min_incidents, window_days=window_days, db=db)


@app.get("/api/departments", tags=["departments"])
def api_departments_alias(db=Depends(get_db)):
    """Direct alias for GET /api/departments"""
    from backend.models import Department
    return db.query(Department).all()


@app.get("/api/locations", tags=["locations"], response_model=List[LocationOut])
def api_locations_alias(db=Depends(get_db)):
    """Direct alias for GET /api/locations"""
    from backend.models import Location
    return db.query(Location).all()


@app.post("/api/recurring/mark-fix", tags=["analytics"], response_model=PermanentFixTaskOut)
def api_recurring_mark_fix_alias(
    data: PermanentFixCreate,
    current_user: User = Depends(auth.require_role(["admin", "handler"])),
    db=Depends(get_db)
):
    """Direct alias for POST /api/recurring/mark-fix"""
    from backend.routers.analytics import mark_permanent_fix
    return mark_permanent_fix(data=data, current_user=current_user, db=db)


@app.get("/api/health")
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Shikayat Karo Backend",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }
