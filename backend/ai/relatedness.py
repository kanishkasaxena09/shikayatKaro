"""Multi-factor relatedness scoring module for Project Shikayat Karo.

Calculates composite similarity using:
  score = 0.45 * text_cosine
        + 0.25 * location_score (same location: 1.0, same block: 0.6, else: 0.0)
        + 0.15 * time_score (<=3h: 1.0, <=24h: 0.6, <=72h: 0.3, else: 0.0)
        + 0.15 * category_match (exact match: 1.0, else: 0.0)

Hard rule:
  If category AND location both differ (category_match == 0 and location_score == 0),
  the score is strictly capped at 0.40.

Bands:
  - >= 0.80: strong suggestion
  - 0.50 - 0.79: low-confidence (flag for admin review)
  - < 0.50: no suggestion

Admin confirmation is ALWAYS required.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import math


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculates cosine similarity between two float vectors, clamped to [0.0, 1.0]."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    val = dot / (norm_a * norm_b)
    return max(0.0, min(1.0, float(val)))


def get_location_score(loc1_id: Optional[int], loc2_id: Optional[int], block1_id: Optional[int], block2_id: Optional[int]) -> float:
    """Returns location match score.
    - 1.0 if identical location
    - 0.6 if both in the same block
    - 0.0 otherwise
    """
    if loc1_id is not None and loc2_id is not None and loc1_id == loc2_id:
        return 1.0
    if block1_id is not None and block2_id is not None and block1_id == block2_id:
        return 0.6
    return 0.0


def get_time_score(time1: datetime, time2: datetime) -> float:
    """Returns time proximity score based on elapsed hours.
    - <= 3h: 1.0
    - <= 24h: 0.6
    - <= 72h: 0.3
    - > 72h: 0.0
    """
    delta_seconds = abs((time1 - time2).total_seconds())
    hours = delta_seconds / 3600.0
    if hours <= 3.0:
        return 1.0
    elif hours <= 24.0:
        return 0.6
    elif hours <= 72.0:
        return 0.3
    return 0.0


def calculate_relatedness(
    text_cosine: float,
    loc1_id: Optional[int],
    loc2_id: Optional[int],
    block1_id: Optional[int],
    block2_id: Optional[int],
    time1: datetime,
    time2: datetime,
    category1: str,
    category2: str,
) -> Dict[str, Any]:
    """Computes transparent composite relatedness score and breakdown."""
    loc_score = get_location_score(loc1_id, loc2_id, block1_id, block2_id)
    t_score = get_time_score(time1, time2)
    cat_match = 1.0 if (category1 and category2 and category1.strip().lower() == category2.strip().lower()) else 0.0

    # Composite weighted formula
    raw_score = (0.45 * text_cosine) + (0.25 * loc_score) + (0.15 * t_score) + (0.15 * cat_match)
    
    # Hard rule: if category AND location both differ, cap score at 0.40
    capped = False
    if cat_match == 0.0 and loc_score == 0.0:
        if raw_score > 0.40:
            final_score = 0.40
            capped = True
        else:
            final_score = raw_score
    else:
        final_score = raw_score

    final_score = round(final_score, 3)

    if final_score >= 0.80:
        band = "strong"
        label = "Strong Suggestion"
        should_suggest = True
    elif final_score >= 0.50:
        band = "review"
        label = "Low Confidence (Admin Review Required)"
        should_suggest = True
    else:
        band = "none"
        label = "No Suggestion"
        should_suggest = False

    reasons = [
        f"Text similarity: {round(text_cosine, 3)} (weight 45% -> {round(0.45 * text_cosine, 3)})",
        f"Location match: {loc_score} ({'Same location' if loc_score == 1.0 else 'Same block' if loc_score == 0.6 else 'Different locations'}) (weight 25% -> {round(0.25 * loc_score, 3)})",
        f"Time proximity: {t_score} ({round(abs((time1 - time2).total_seconds()) / 3600.0, 1)}h apart) (weight 15% -> {round(0.15 * t_score, 3)})",
        f"Category match: {cat_match} ({'Exact match' if cat_match == 1.0 else 'Mismatched categories'}) (weight 15% -> {round(0.15 * cat_match, 3)})"
    ]
    if capped:
        reasons.append("Capped at 0.40 by hard rule: both category and location differ.")

    reasons.append("System suggestion requires admin confirmation.")

    return {
        "score": final_score,
        "band": band,
        "label": label,
        "should_suggest": should_suggest,
        "capped_by_hard_rule": capped,
        "components": {
            "text_cosine": round(text_cosine, 3),
            "location_score": loc_score,
            "time_score": t_score,
            "category_match": cat_match,
        },
        "reasons": reasons
    }
