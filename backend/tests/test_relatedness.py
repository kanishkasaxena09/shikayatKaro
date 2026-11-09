"""Unit tests for multi-factor relatedness module."""

from datetime import timedelta
from backend.clock import get_current_time
from backend.ai.relatedness import calculate_relatedness, cosine_similarity
from backend.ai.embedder import get_embedder


def test_hard_rule_category_and_location_both_differ():
    """If category AND location both differ, the score must be capped at 0.40."""
    t0 = get_current_time()
    # High text similarity 0.95, same time <= 3h
    # BUT different location (loc_score = 0.0) AND different category (cat_match = 0.0)
    res = calculate_relatedness(
        text_cosine=0.95,
        loc1_id=1,
        loc2_id=2,
        block1_id=10,
        block2_id=20,
        time1=t0,
        time2=t0,
        category1="Water & Plumbing",
        category2="Electrical"
    )
    # Raw would be: 0.45*0.95 + 0.15*1.0 = 0.4275 + 0.15 = 0.5775
    # Capped at 0.40
    assert res["score"] <= 0.40
    assert res["capped_by_hard_rule"] is True
    assert res["band"] == "none"
    assert res["should_suggest"] is False


def test_same_wording_at_different_locations_not_strongly_grouped():
    """Same wording at different campus locations must NOT form a strong suggestion (>= 0.80)."""
    t0 = get_current_time()
    # Identical wording (cosine = 1.0), same category, but different blocks (loc_score = 0.0)
    # and slight time gap 12h (time_score = 0.6)
    res = calculate_relatedness(
        text_cosine=1.0,
        loc1_id=1,
        loc2_id=2,
        block1_id=10,
        block2_id=20,
        time1=t0,
        time2=t0 + timedelta(hours=12),
        category1="Water & Plumbing",
        category2="Water & Plumbing"
    )
    # 0.45*1.0 + 0.25*0.0 + 0.15*0.6 + 0.15*1.0 = 0.45 + 0.09 + 0.15 = 0.69
    assert res["score"] < 0.80
    assert res["band"] != "strong"


def test_differently_worded_complaints_at_same_place_are_grouped():
    """Differently worded complaints at the same location within close time form a strong suggestion (>= 0.80)."""
    embedder = get_embedder()
    text1 = "Severe pipe leakage flooding the corridor floor"
    text2 = "Water overflowing from bathroom pipeline near room entrance"
    
    vec1 = embedder.embed(text1)
    vec2 = embedder.embed(text2)
    cosine = cosine_similarity(vec1, vec2)
    assert cosine > 0.40  # Both relate to water leakage

    t0 = get_current_time()
    res = calculate_relatedness(
        text_cosine=cosine,
        loc1_id=5,
        loc2_id=5,        # Identical location -> 1.0
        block1_id=2,
        block2_id=2,
        time1=t0,
        time2=t0 + timedelta(hours=1), # <= 3h -> 1.0
        category1="Water & Plumbing",
        category2="Water & Plumbing"   # Exact match -> 1.0
    )
    # Score: 0.45*cosine + 0.25*1.0 + 0.15*1.0 + 0.15*1.0 = 0.45*cosine + 0.55
    # If cosine >= 0.56, score >= 0.80
    assert res["score"] >= 0.80
    assert res["band"] == "strong"
    assert res["should_suggest"] is True


def test_hinglish_matches_english_equivalent():
    """A Hinglish complaint matches its English equivalent and clusters appropriately."""
    embedder = get_embedder()
    english = "Water pipe leakage in Hostel Block B ground floor"
    hinglish = "Hostel Block B ground floor mein paani ka pipe leak ho raha hai"

    vec_en = embedder.embed(english)
    vec_hi = embedder.embed(hinglish)
    cosine = cosine_similarity(vec_en, vec_hi)
    assert cosine >= 0.60  # Cross-lingual embedding similarity

    t0 = get_current_time()
    res = calculate_relatedness(
        text_cosine=cosine,
        loc1_id=8,
        loc2_id=8,
        block1_id=2,
        block2_id=2,
        time1=t0,
        time2=t0 + timedelta(minutes=45),
        category1="Water & Plumbing",
        category2="Water & Plumbing"
    )
    assert res["score"] >= 0.80
    assert res["band"] == "strong"
