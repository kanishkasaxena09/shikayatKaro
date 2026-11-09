"""Impact score calculation module for Project Shikayat Karo.

Scored transparently using weighted components:
- Severity: 35%
- Urgency: 25%
- Affected Users: 25% (min(100, 10 * affected_users))
- Duration: 15% (min(100, (hours_open / 120) * 100))

Impact bands:
- 0-29: Low
- 30-59: Medium
- 60-79: High
- 80-100: Critical
"""

from typing import Dict, Any, Union


def get_impact_band(score: float) -> str:
    """Returns band name for an impact score."""
    if score >= 80:
        return "Critical"
    elif score >= 60:
        return "High"
    elif score >= 30:
        return "Medium"
    else:
        return "Low"


def calculate_impact(
    severity: float,
    urgency: float,
    affected_count: int,
    hours_open: float,
    override_affected_score: Union[float, None] = None,
    override_duration_score: Union[float, None] = None,
) -> Dict[str, Any]:
    """Calculates transparent impact score and detailed breakdown.
    
    Args:
        severity: Score 0-100 representing problem severity.
        urgency: Score 0-100 representing time sensitivity.
        affected_count: Number of affected users.
        hours_open: Total elapsed hours since complaint creation.
        override_affected_score: Optional explicit score (0-100) for testing formulas directly.
        override_duration_score: Optional explicit score (0-100) for testing formulas directly.
        
    Returns:
        dict containing final impact_score (rounded int), band, and component breakdown.
    """
    # Clamp inputs between 0 and 100
    sev_score = max(0.0, min(100.0, float(severity)))
    urg_score = max(0.0, min(100.0, float(urgency)))
    
    if override_affected_score is not None:
        aff_score = max(0.0, min(100.0, float(override_affected_score)))
    else:
        aff_score = min(100.0, max(0.0, 10.0 * float(affected_count)))

    if override_duration_score is not None:
        dur_score = max(0.0, min(100.0, float(override_duration_score)))
    else:
        dur_score = min(100.0, max(0.0, (float(hours_open) / 120.0) * 100.0))

    # Weighted calculation
    score = (0.35 * sev_score) + (0.25 * urg_score) + (0.25 * aff_score) + (0.15 * dur_score)
    final_score = int(round(score))
    band = get_impact_band(final_score)

    return {
        "impact_score": final_score,
        "band": band,
        "formula": "0.35*severity + 0.25*urgency + 0.25*affected + 0.15*duration",
        "breakdown": {
            "severity": round(sev_score, 1),
            "urgency": round(urg_score, 1),
            "affected": round(aff_score, 1),
            "duration": round(dur_score, 1),
            "raw_affected_count": affected_count,
            "raw_hours_open": round(hours_open, 2)
        }
    }
