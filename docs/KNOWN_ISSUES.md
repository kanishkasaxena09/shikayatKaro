# Known Issues & Architectural Production Considerations

This document records architectural edge cases, resolved bugs, and production considerations for **Shikayat Karo**. All identified functional bugs discovered during systematic debugging, fuzzing, and concurrency testing have been resolved in the codebase. The items below document system constraints and edge cases to consider when scaling beyond single-instance deployment under heavy production load.

---

## 1. Concurrency & Storage Scalability Under Heavy Load

### SQLite Lock Contention
- **Context**: The application defaults to SQLite (`sqlite:///./shikayat_karo.db`) with `PRAGMA journal_mode=WAL` and `busy_timeout=30.0s`. Thread safety within a single process is enforced via Python `threading.Lock` primitives (`_SUGGESTION_LOCK` and `_INCIDENT_LOCK`).
- **Limitation**: While WAL mode permits multiple concurrent readers and a single concurrent writer, high-frequency simultaneous write spikes (e.g. 50+ concurrent grievance confirmations) will queue on the SQLite database file lock.
- **Production Recommendation**: For campus-wide production deployments with thousands of concurrent active users across multiple application servers, switch to PostgreSQL by providing `DATABASE_URL=postgresql://user:password@host:5432/shikayatkaro`. The SQLAlchemy ORM models and migrations are fully PostgreSQL-compliant.

---

## 2. In-Memory State & Horizontal Scaling

### In-Memory Sliding-Window Rate Limiter
- **Context**: `backend/limiter.py` implements an in-memory sliding-window rate limiter for the login (`POST /api/auth/login`) and anonymous tracking (`GET /api/track`) endpoints.
- **Limitation**:
  1. **Restart Reset**: When the backend server process restarts, in-memory rate-limiting counters are reset.
  2. **Multi-Instance Isolation**: If the backend is deployed as multiple container replicas behind a round-robin load balancer, each container maintains its own in-memory history.
- **Production Recommendation**: In horizontal scaling environments with multiple worker processes or containers, replace `backend/limiter.py` with a Redis-backed sliding-window rate limiter (e.g., Redis `ZADD` / `ZREMRANGEBYSCORE`).

### In-Memory Prototype Centroid & Embedder Caches
- **Context**: Prototype centroids in `backend/ai/classifier.py` and text embedding vectors in `backend/ai/embedder.py` are cached in process memory (`_EMBEDDING_CACHE`, `_CATEGORY_CENTROIDS`).
- **Behavior**: Caches are process-local and warm up dynamically on first use.
- **Production Recommendation**: When deploying with multi-worker Gunicorn/Uvicorn (`uvicorn --workers 4`), each worker initializes its own centroid cache on cold start. In a production deployment using neural models (`EMBEDDER=fastembed`), pre-downloading model weights during Docker container build (`RUN python -c "from fastembed import TextEmbedding; TextEmbedding()"`) ensures zero cold-start download delay.

---

## 3. Virtual Clock & Demonstration Controls

### Virtual Clock Drift in Multi-Process Setups
- **Context**: The virtual clock (`backend/clock.py`) maintains an in-process offset (`_TIME_OFFSET_SECONDS`) for live hackathon demonstrations and SLA escalation testing.
- **Production Setting**: In real production, `DEMO_MODE=false` disables virtual clock alteration endpoints (`/api/demo/*`) with HTTP 403 Forbidden, and all system timestamps derive directly from real UTC system time.
- **JWT `iat` (Issued At) Handling**: When fast-forwarding the virtual clock into the future during demonstrations, JWT tokens are decoded with `options={"verify_iat": False}` to prevent `ImmatureSignatureError` while strictly enforcing standard expiration (`exp`).

---

## 4. Summary of Bugs Fixed During Systematic Verification

| Bug # | Component | Symptom | Root Cause | Fix Applied | Covering Regression Test |
|---|---|---|---|---|---|
| **BUG-01** | `backend/routers/incidents.py` | 422 Unprocessable Entity when accessing incident deep link `/incidents/INC-HIST-002` | Endpoint defined `id: int`, failing on alphanumeric incident codes | Accepted `id: str`, added `find_incident` helper resolving both numeric IDs and codes | `test_api.py`, `frontend/e2e/walkthrough.spec.js` |
| **BUG-02** | `backend/routers/suggestions.py` | Duplicate parent incidents created when two admins confirmed the same suggestion simultaneously | Critical section exited before incident creation; non-atomic check-then-insert | Added `_SUGGESTION_LOCK` wrapping entire transaction and 409 Conflict checks | `test_fuzzing_concurrency.py::test_concurrency_cluster_confirmation` |
| **BUG-03** | `backend/routers/incidents.py` | Lost updates or race conditions during simultaneous handler status transitions | Concurrent updates wrote un-synchronized changes to status and audit log | Added `_INCIDENT_LOCK` wrapping status transition, complaint cascading, and audit commit | `test_fuzzing_concurrency.py::test_concurrency_incident_updates` |
| **BUG-04** | `backend/routers/complaints.py` | Unbounded text and affected count could cause memory or validation issues | Pydantic schema lacked upper bounds (`max_length`, `le`) | Added `max_length=5000` to `text` and `le=100000` to `affected_count` in `ComplaintCreate` | `test_fuzzing_concurrency.py::test_fuzz_submission_text_length`, `test_fuzz_submission_affected_count` |
| **BUG-05** | `backend/routers/complaints.py` | Non-existent `location_id` could create orphaned or invalid foreign keys | Location ID was not validated before persisting record | Added database existence check for `location_id`, returning 400 Bad Request if missing | `test_fuzzing_concurrency.py::test_fuzz_submission_location_validation` |
| **BUG-06** | `backend/routers/complaints.py` | Accidental double-click produced duplicate complaints | No debounce or rapid duplicate check existed on intake endpoint | Added 5-second duplicate submit detection returning 409 Conflict | `test_fuzzing_concurrency.py::test_fuzz_double_submit_guard` |
| **BUG-07** | `backend/routers/auth.py` | Malformed or expired JWT tokens on optional auth endpoints silently failed as anonymous | `get_current_user_optional` swallowed all token decoding exceptions | Raised 401 Unauthorized when an explicit invalid or expired token is provided | `test_fuzzing_concurrency.py::test_fuzz_tracking_and_auth_tokens` |
| **BUG-08** | `backend/main.py` | Direct alias `/api/track` dropped `current_user` dependency | `api_track_alias` called `track_complaint(..., current_user=None)` | Bound `current_user=Depends(auth.get_current_user_optional)` to alias | `test_fuzzing_concurrency.py::test_fuzz_tracking_and_auth_tokens` |
| **BUG-09** | `backend/main.py` | Redundant slow database seeding during test execution | `lifespan` executed `seed_database()` even when `TESTING=1` | Skipped lifespan auto-seeding when `TESTING=1` (deferred to `conftest.py`) | All backend pytest runs (reduced runtime from ~32s to ~4s) |
| **BUG-10** | `backend/main.py` | Standard deployment health checks expecting `/health` received 404 | Health check was only bound to `/api/health` | Added dual route decorator `@app.get("/health")` and `@app.get("/api/health")` | `test_production_simulation.py` |
