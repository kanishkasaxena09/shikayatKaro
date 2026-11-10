"""Main FastAPI application for Project Shikayat Karo.

Aggregates individual complaints into structured, trackable, actionable incidents.
"""

import os
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from backend.database import engine, Base, SessionLocal, get_db
from backend.seed import seed_database
from backend.ai.escalation import check_and_apply_escalations
from backend.routers import auth, complaints, suggestions, incidents, analytics, notifications, demo

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # 1. Initialize database tables
    Base.metadata.create_all(bind=engine)
    # 2. Seed initial master data if needed
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
cors_origins_env = os.getenv("CORS_ORIGINS")
origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()] if cors_origins_env else ["*"]

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
    tracking_id: str,
    access_code: str = None,
    db=Depends(get_db)
):
    """Direct alias for GET /api/track?tracking_id=&access_code="""
    from backend.routers.complaints import track_complaint
    return track_complaint(tracking_id=tracking_id, access_code=access_code, current_user=None, db=db)


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


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Shikayat Karo Backend",
        "version": "1.0.0"
    }
