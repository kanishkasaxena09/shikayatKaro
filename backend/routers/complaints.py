"""Complaints management router for Project Shikayat Karo."""

import secrets
from datetime import timedelta
from typing import List, Optional
import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.database import get_db
from backend.models import Complaint, Location, Department, Suggestion, Update, User, Incident
from backend.schemas import ComplaintCreate, ComplaintOut, ComplaintSubmitResponse, UserOut
from backend.routers.auth import get_current_user, get_current_user_optional
from backend.ai.language import detect_language
from backend.ai.classifier import classify_complaint
from backend.ai.priority import calculate_priority
from backend.ai.relatedness import calculate_relatedness, cosine_similarity
from backend.ai.embedder import get_embedder
from backend.ai.escalation import calculate_deadline
from backend.clock import get_current_time

router = APIRouter(prefix="/api/complaints", tags=["complaints"])


def generate_tracking_id(db: Session) -> str:
    """Generates next CMP-XXXX sequential code."""
    last = db.query(Complaint).order_by(Complaint.id.desc()).first()
    next_num = (last.id + 1) if last else 1
    return f"CMP-{next_num:04d}"


def hash_access_code(code: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(code.encode("utf-8"), salt).decode("utf-8")


def verify_access_code(code: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(code.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def get_block_id_for_location(loc: Optional[Location]) -> Optional[int]:
    """Traverses upward to find the block-level ancestor ID."""
    curr = loc
    while curr:
        if curr.type == "block":
            return curr.id
        curr = curr.parent
    return None


def serialize_complaint(cmp: Complaint) -> ComplaintOut:
    """Safely serializes a Complaint model, strictly enforcing anonymity rules."""
    complainant_out = None
    if not cmp.is_anonymous and cmp.complainant:
        complainant_out = UserOut.model_validate(cmp.complainant)

    return ComplaintOut(
        id=cmp.id,
        tracking_id=cmp.tracking_id,
        is_anonymous=cmp.is_anonymous,
        text=cmp.text,
        original_language=cmp.original_language,
        category=cmp.category,
        category_confidence=cmp.category_confidence,
        priority=cmp.priority,
        priority_reasons=cmp.priority_reasons,
        location_id=cmp.location_id,
        location_name=cmp.location.name if cmp.location else None,
        department_id=cmp.department_id,
        department_name=cmp.department.name if cmp.department else None,
        status=cmp.status,
        incident_id=cmp.incident_id,
        affected_count=cmp.affected_count,
        deadline_at=cmp.deadline_at,
        escalation_level=cmp.escalation_level,
        created_at=cmp.created_at,
        complainant=complainant_out
    )


@router.post("", response_model=ComplaintSubmitResponse)
def submit_complaint(
    payload: ComplaintCreate,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Submits a new complaint.
    
    Runs full AI pipeline:
    1. Language detection (Devanagari, Hinglish token list, or English)
    2. Prototype classification with confidence
    3. Rule-based priority scoring with transparent reasons
    4. Text embedding caching
    5. Multi-factor relatedness against existing active complaints
    6. Creates or extends a pending Suggestion if related
    7. Generates 8-char access code if anonymous
    """
    now = get_current_time()
    tracking_id = generate_tracking_id(db)

    # 1. Anonymous handling
    plain_access_code = None
    access_code_hash = None
    complainant_id = None

    if payload.is_anonymous:
        # Generate 8-char uppercase hex code
        plain_access_code = secrets.token_hex(4).upper()
        access_code_hash = hash_access_code(plain_access_code)
        complainant_id = None
    else:
        if current_user:
            complainant_id = current_user.id

    # 2. AI Pipeline
    # Language
    lang = detect_language(payload.text)

    # Classification
    clf_res = classify_complaint(payload.text)
    category = clf_res["category"]
    category_conf = clf_res["confidence"]

    # Priority
    priority, priority_reasons = calculate_priority(
        text=payload.text,
        category=category,
        reported_affected_count=payload.affected_count
    )

    # Embed text
    embedder = get_embedder()
    embedding_vec = embedder.embed(payload.text)

    # Initial deadline
    deadline = calculate_deadline(db, priority, now)

    # Create Complaint record
    complaint = Complaint(
        tracking_id=tracking_id,
        complainant_id=complainant_id,
        is_anonymous=payload.is_anonymous,
        access_code_hash=access_code_hash,
        text=payload.text,
        original_language=lang,
        category=category,
        category_confidence=category_conf,
        priority=priority,
        priority_reasons=priority_reasons,
        location_id=payload.location_id,
        department_id=None,
        status="AI Analysed",
        affected_count=payload.affected_count,
        embedding=embedding_vec,
        deadline_at=deadline,
        escalation_level=0,
        created_at=now
    )
    db.add(complaint)
    db.flush()

    # Audit log
    audit_update = Update(
        target_type="complaint",
        target_id=complaint.id,
        actor_id=complainant_id,
        actor_role="complainant" if complainant_id else "anonymous",
        old_status="Submitted",
        new_status="AI Analysed",
        remarks=f"Complaint analysed by AI engine: category={category} ({category_conf}), priority={priority}.",
        event_type="status",
        timestamp=now
    )
    db.add(audit_update)

    # 3. Relatedness Matching against open complaints from the last 72 hours
    window_start = now - timedelta(hours=72)
    candidate_complaints = db.query(Complaint).filter(
        Complaint.id != complaint.id,
        Complaint.created_at >= window_start,
        Complaint.status.notin_(["Resolved", "Closed"])
    ).all()

    my_loc = complaint.location
    my_block_id = get_block_id_for_location(my_loc)

    best_match_complaint: Optional[Complaint] = None
    best_relatedness: Optional[dict] = None
    highest_score = 0.0

    for other in candidate_complaints:
        other_vec = other.embedding or embedder.embed(other.text)
        cosine = cosine_similarity(embedding_vec, other_vec)

        other_loc = other.location
        other_block_id = get_block_id_for_location(other_loc)

        rel = calculate_relatedness(
            text_cosine=cosine,
            loc1_id=complaint.location_id,
            loc2_id=other.location_id,
            block1_id=my_block_id,
            block2_id=other_block_id,
            time1=complaint.created_at,
            time2=other.created_at,
            category1=complaint.category,
            category2=other.category
        )

        if rel["should_suggest"] and rel["score"] > highest_score:
            highest_score = rel["score"]
            best_match_complaint = other
            best_relatedness = rel

    suggestion_created = False
    suggestion_id = None

    if best_match_complaint and best_relatedness:
        # Check if matched complaint is already in an existing pending Suggestion
        pending_suggestions = db.query(Suggestion).filter(Suggestion.status == "pending").all()
        target_suggestion: Optional[Suggestion] = None

        for sugg in pending_suggestions:
            c_ids = sugg.complaint_ids or []
            if best_match_complaint.id in c_ids:
                target_suggestion = sugg
                break

        if target_suggestion:
            # Extend existing suggestion
            c_ids = list(target_suggestion.complaint_ids or [])
            if complaint.id not in c_ids:
                c_ids.append(complaint.id)
                target_suggestion.complaint_ids = c_ids
                target_suggestion.reasons = list(set((target_suggestion.reasons or []) + best_relatedness["reasons"]))
                target_suggestion.confidence = max(target_suggestion.confidence, best_relatedness["score"])
                db.flush()
                suggestion_id = target_suggestion.id
                suggestion_created = True
        else:
            # Create a new Suggestion grouping the two complaints
            new_sugg = Suggestion(
                complaint_ids=[best_match_complaint.id, complaint.id],
                confidence=best_relatedness["score"],
                reasons=best_relatedness["reasons"],
                status="pending",
                created_at=now
            )
            db.add(new_sugg)
            db.flush()
            suggestion_id = new_sugg.id
            suggestion_created = True

    db.commit()
    db.refresh(complaint)

    ai_analysis = {
        "language": lang,
        "classification": clf_res,
        "priority": {
            "level": priority,
            "reasons": priority_reasons
        },
        "relatedness_match": best_relatedness
    }

    return ComplaintSubmitResponse(
        complaint=serialize_complaint(complaint),
        access_code=plain_access_code,
        suggestion_created=suggestion_created,
        suggestion_id=suggestion_id,
        ai_analysis=ai_analysis
    )


@router.get("/my", response_model=List[ComplaintOut])
def get_my_complaints(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns complaints filed by the currently authenticated user."""
    complaints = db.query(Complaint).filter(
        Complaint.complainant_id == current_user.id,
        Complaint.is_anonymous.is_(False)
    ).order_by(Complaint.created_at.desc()).all()
    return [serialize_complaint(c) for c in complaints]


@router.get("/track", response_model=ComplaintOut)
def track_complaint(
    tracking_id: str = Query(..., description="Complaint tracking code (CMP-XXXX)"),
    access_code: Optional[str] = Query(None, description="8-character access code for anonymous complaints"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Tracks a complaint without requiring login if valid tracking_id and access_code are provided.
    
    Guarantees that no anonymous complaint ever leaks complainant identity.
    """
    complaint = db.query(Complaint).filter(Complaint.tracking_id == tracking_id.strip()).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found with provided tracking ID")

    if complaint.is_anonymous:
        if not access_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access code required for tracking anonymous complaint"
            )
        if not complaint.access_code_hash or not verify_access_code(access_code.strip(), complaint.access_code_hash):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid access code for this complaint"
            )
        # Privacy guarantee: serialize_complaint will return complainant=None
        return serialize_complaint(complaint)

    # For non-anonymous complaints:
    # If anonymous user requested without login, verify if access code matches or requires login
    if current_user:
        # Admin or handler or owner
        if current_user.role in ["admin", "handler"] or complaint.complainant_id == current_user.id:
            return serialize_complaint(complaint)
        raise HTTPException(status_code=403, detail="Not authorized to view this complaint")

    # If unauthenticated tracking non-anonymous complaint with access code
    if access_code and complaint.access_code_hash and verify_access_code(access_code.strip(), complaint.access_code_hash):
        return serialize_complaint(complaint)

    raise HTTPException(status_code=401, detail="Authentication or valid access code required")


@router.get("/{id}", response_model=ComplaintOut)
def get_complaint(
    id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Retrieves a single complaint by ID."""
    complaint = db.query(Complaint).filter(Complaint.id == id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return serialize_complaint(complaint)
