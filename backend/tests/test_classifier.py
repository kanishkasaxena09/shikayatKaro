"""Unit tests for category classification module."""

from backend.ai.classifier import classify_complaint


def test_classify_water_complaint_english():
    res = classify_complaint("Water pipe broken in washroom, continuous flooding")
    assert res["category"] == "Water & Plumbing"
    assert res["confidence"] > 0.40
    assert len(res["top_alternatives"]) == 2
    assert res["needs_review"] is False


def test_classify_water_complaint_hinglish():
    res = classify_complaint("Hostel ground floor mein paani ka pipe leak ho raha hai")
    assert res["category"] == "Water & Plumbing"
    assert res["confidence"] > 0.40


def test_classify_electrical_complaint_hindi():
    res = classify_complaint("कमरे में पंखा नहीं चल रहा है और बिजली के स्विच से स्पार्क निकल रहा है")
    assert res["category"] == "Electrical"
    assert res["confidence"] > 0.40


def test_classify_sanitation_complaint():
    res = classify_complaint("Garbage bins overflowing and washroom toilet is completely choked and filthy")
    assert res["category"] == "Sanitation & Cleanliness"
    assert res["confidence"] > 0.40


def test_low_confidence_flags_review():
    # Vague or ambiguous short string
    res = classify_complaint("Something is strange here today")
    # Low confidence or fallback
    assert len(res["top_alternatives"]) == 2
    if res["confidence"] < 0.35:
        assert res["needs_review"] is True
