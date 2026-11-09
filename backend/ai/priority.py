"""Rule-based priority scoring module for Project Shikayat Karo.

Transparently determines priority (Critical, High, Medium, Low) based on:
1. Category base level
2. Urgency keywords (English, Hindi, Hinglish)
3. Essential services disrupted (water, power, network, toilets)
4. Safety / hazard words
5. Extracted or reported affected count
6. Count of linked complaints
"""

import re
from typing import Tuple, List, Dict, Any


ESSENTIAL_SERVICES = {
    "water": [
        "water", "drinking water", "supply", "tap", "pipeline", "pipe",
        "paani", "pani", "nal", "tanki", "motor", "leak", "leakage", "overflow"
    ],
    "power": [
        "electricity", "power", "powercut", "blackout", "light", "current",
        "bijli", "batti", "voltage", "fuse", "transformer", "wire", "taar"
    ],
    "sanitation": [
        "toilet", "washroom", "restroom", "flush", "choked", "sewage",
        "safai", "kachra", "badboo", "smell", "gandagi", "hygiene"
    ],
    "network": [
        "wifi", "internet", "network", "lan", "connection", "server", "router"
    ]
}

SAFETY_HAZARD_KEYWORDS = [
    "shock", "electric shock", "spark", "sparking", "fire", "aag", "smoke",
    "dhuan", "hazard", "danger", "khatra", "collapse", "collapsed", "blast",
    "injured", "chot", "bleeding", "assault", "ragging", "threat", "harass",
    "harassment", "violence", "chori", "theft", "unauthorized entry"
]

URGENCY_KEYWORDS = [
    "urgent", "urgently", "immediately", "emergency", "turant", "jaldi",
    "critical", "severe", "asap", "unusable", "impossible", "blocked",
    "flooded", "overflowing", "kab se band", "jaldi theek karo"
]


def extract_affected_count_hint(text: str) -> int:
    """Extracts affected count clues from text such as '20 students', '5 rooms'."""
    text_lower = text.lower()
    
    # Check for large scale phrases
    if any(k in text_lower for k in ["entire campus", "whole campus", "entire hostel", "whole hostel"]):
        return 100
    if any(k in text_lower for k in ["entire block", "whole block", "entire floor", "whole floor", "entire wing"]):
        return 40
    if any(k in text_lower for k in ["all students", "all rooms", "all residents", "sab log", "sabhi"]):
        return 25
    if any(k in text_lower for k in ["multiple students", "several students", "many rooms", "multiple rooms"]):
        return 10

    # Pattern: 15 students, 20 people, 4 rooms, etc.
    patterns = [
        r"(\d+)\s*(?:students?|people|persons?|users?|residents?|hostelites?|log|bachhe|vidyarthi)",
        r"(\d+)\s*(?:rooms?|kamre|floors?|flats?|labs?|classrooms?)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                count = int(match.group(1))
                if count > 0:
                    return count
            except ValueError:
                pass
                
    return 1


def calculate_priority(
    text: str,
    category: str,
    linked_complaints_count: int = 0,
    reported_affected_count: int = 1
) -> Tuple[str, List[str]]:
    """Determines priority level (Critical, High, Medium, Low) and reasons.
    
    Returns:
        (priority_str, reasons_list)
    """
    reasons: List[str] = []
    text_lower = text.lower()
    
    # Extract affected count
    hinted_count = extract_affected_count_hint(text)
    effective_affected = max(hinted_count, reported_affected_count, linked_complaints_count)

    # 1. Safety & hazard check
    has_safety_hazard = any(word in text_lower for word in SAFETY_HAZARD_KEYWORDS)
    if has_safety_hazard:
        reasons.append("safety hazard or physical danger detected")

    # 2. Category sensitivity
    is_sensitive_category = category in [
        "Safety & Security",
        "Harassment & Misconduct (confidential)"
    ]
    if is_sensitive_category:
        reasons.append(f"sensitive domain ({category})")

    # 3. Essential service check
    disrupted_services = []
    for service, keywords in ESSENTIAL_SERVICES.items():
        if any(kw in text_lower for kw in keywords):
            disrupted_services.append(service)
    
    if category in ["Water & Plumbing", "Electrical", "Sanitation & Cleanliness", "IT & Network"]:
        if category not in disrupted_services:
            disrupted_services.append(category.split("&")[0].strip().lower())
            
    if disrupted_services:
        reasons.append("essential service disrupted (" + ", ".join(disrupted_services) + ")")

    # 4. Urgency keywords check
    has_urgency = any(kw in text_lower for kw in URGENCY_KEYWORDS)
    if has_urgency:
        reasons.append("high-urgency language present")

    # 5. Scale / Affected count
    if effective_affected >= 20:
        reasons.append(f"widespread impact (approx {effective_affected} people/units)")
    elif effective_affected >= 5 or linked_complaints_count >= 3:
        reasons.append(f"multiple users affected ({effective_affected} affected, {linked_complaints_count} linked)")
    elif linked_complaints_count >= 2:
        reasons.append(f"multiple linked complaints ({linked_complaints_count} reports)")

    # Decision Matrix
    # CRITICAL:
    # - Direct safety hazard with physical danger or harassment
    # - Essential service disruption with widespread impact (>= 20 affected)
    # - Linked complaints >= 5 on essential service
    if has_safety_hazard and (is_sensitive_category or has_urgency or effective_affected >= 5):
        return "Critical", reasons or ["direct safety risk"]
    
    if (disrupted_services and effective_affected >= 20) or linked_complaints_count >= 5:
        return "Critical", reasons or ["widespread essential service outage"]
    
    if has_safety_hazard:
        return "Critical", reasons or ["safety hazard detected"]

    # HIGH:
    # - Essential service disrupted with multiple users affected (>= 3 or >= 2 linked complaints)
    # - Sensitive category (Safety & Security, Harassment)
    # - Essential service disruption + urgency words
    # - Any issue affecting >= 10 people
    if is_sensitive_category:
        return "High", reasons or [f"priority category {category}"]

    if disrupted_services and (effective_affected >= 3 or linked_complaints_count >= 2 or has_urgency):
        return "High", reasons or ["essential service disrupted for multiple users"]

    if effective_affected >= 10:
        return "High", reasons or [f"affects {effective_affected} users"]

    if disrupted_services:
        # Single user essential service (e.g. room fan, one tap)
        return "Medium", reasons or ["essential service maintenance required"]

    if has_urgency:
        return "Medium", reasons or ["urgent request noted"]

    # Routine infrastructure or administrative
    if category in ["Administrative", "Classroom & Infrastructure", "Hostel & Mess"]:
        if effective_affected >= 5:
            return "Medium", reasons or ["affects multiple users"]
        return "Low", reasons or ["routine request / standard maintenance"]

    return "Medium", reasons or ["standard evaluation"]
