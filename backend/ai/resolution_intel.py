"""Resolution intelligence module for Project Shikayat Karo.

Finds top 3 similar past Resolved or Closed incidents to suggest actionable
resolution pathways to department handlers and administrators.
These are suggestions only and are NEVER auto-applied.
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session

from backend.models import Incident
from backend.ai.embedder import get_embedder
from backend.ai.relatedness import cosine_similarity


def find_similar_resolved_incidents(
    db: Session,
    query_text: str,
    limit: int = 3
) -> List[Dict[str, Any]]:
    """Embeds query text and compares against past Resolved/Closed incidents.
    
    Returns top similar incidents with similarity score, past resolution notes,
    department responsible, and elapsed hours to resolution.
    Suggestions only, never auto-applied.
    """
    if not query_text or not query_text.strip():
        return []

    embedder = get_embedder()
    query_vec = embedder.embed(query_text)

    # Fetch resolved or closed incidents having resolution notes
    resolved_incidents = db.query(Incident).filter(
        Incident.status.in_(["Resolved", "Closed"]),
        Incident.resolution_notes.isnot(None)
    ).all()

    if not resolved_incidents:
        return []

    candidates: List[Dict[str, Any]] = []

    for inc in resolved_incidents:
        # Build text representation of past incident and its solution
        doc_text = f"{inc.title}. Category: {inc.category}. Resolution: {inc.resolution_notes}"
        inc_vec = embedder.embed(doc_text)
        sim = cosine_similarity(query_vec, inc_vec)

        # Calculate time to resolve
        if inc.resolved_at and inc.created_at:
            delta_hours = max(0.1, (inc.resolved_at - inc.created_at).total_seconds() / 3600.0)
        else:
            delta_hours = 24.0

        candidates.append({
            "incident_id": inc.id,
            "incident_code": inc.code,
            "title": inc.title,
            "category": inc.category,
            "department_id": inc.department_id,
            "department_name": inc.department.name if inc.department else "General Admin",
            "resolution_notes": inc.resolution_notes,
            "similarity": round(sim, 3),
            "hours_to_resolve": round(delta_hours, 1),
            "system_suggestion_only": True
        })

    # Sort descending by similarity score
    candidates.sort(key=lambda x: x["similarity"], reverse=True)
    return candidates[:limit]
