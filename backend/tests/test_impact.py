"""Unit tests for impact calculation module."""

from backend.ai.impact import calculate_impact, get_impact_band


def test_required_impact_specification():
    """Exact test from specification:
    severity 70, urgency 80, affected 50, duration 40 -> 63 (High).
    """
    res = calculate_impact(
        severity=70.0,
        urgency=80.0,
        affected_count=5,  # 5 * 10 = 50
        hours_open=48.0,   # (48 / 120) * 100 = 40.0
        override_affected_score=50.0,
        override_duration_score=40.0
    )
    assert res["impact_score"] == 63
    assert res["band"] == "High"
    assert res["breakdown"]["severity"] == 70.0
    assert res["breakdown"]["urgency"] == 80.0
    assert res["breakdown"]["affected"] == 50.0
    assert res["breakdown"]["duration"] == 40.0


def test_impact_formula_with_raw_inputs():
    """Verify raw affected count and duration scaling."""
    # 5 affected -> 50 affected score
    # 48 hours open -> 48/120 * 100 = 40 duration score
    res = calculate_impact(
        severity=70.0,
        urgency=80.0,
        affected_count=5,
        hours_open=48.0
    )
    assert res["impact_score"] == 63
    assert res["band"] == "High"


def test_impact_bands():
    assert get_impact_band(25) == "Low"
    assert get_impact_band(45) == "Medium"
    assert get_impact_band(65) == "High"
    assert get_impact_band(85) == "Critical"


def test_impact_clamping():
    # Extreme inputs clamped to 0-100 range
    res = calculate_impact(
        severity=200.0,
        urgency=150.0,
        affected_count=50,  # capped at 100
        hours_open=300.0    # capped at 100
    )
    assert res["impact_score"] == 100
    assert res["band"] == "Critical"
