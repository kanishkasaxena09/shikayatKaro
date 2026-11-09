"""Language detection module for Project Shikayat Karo.

Detects 'hindi' (Devanagari script), 'hinglish' (romanised Hindi), or 'english'.
Original text is preserved unchanged.
"""

import re
from typing import Set

# ~150 common romanised Hindi words across complaints, amenities, and campus contexts.
# Strictly non-English Hindi transliterations to avoid colliding with common English words (like 'the', 'he', 'to').
HINGLISH_VOCABULARY: Set[str] = {
    # Water & Plumbing in Roman Hindi
    "paani", "pani", "nal", "tanki", "motor", "tuta", "toota", "badboo",
    "beh", "bahaav", "ganda", "gandi", "tapka", "tapko", "risav", "chhat",
    
    # Electrical in Roman Hindi
    "bijli", "batti", "pankha", "taar", "andhera", "jhatka",
    
    # Cleanliness & Sanitation in Roman Hindi
    "safai", "kachra", "kooda", "gandagi", "saaf", "keeda", "keede",
    "chooha", "chuha", "makdi", "jaala", "peshab", "dhoop",
    
    # Hostel & Mess in Roman Hindi
    "khana", "daal", "dal", "roti", "chawal", "kamra", "kamre", "bistar",
    "almari", "khidki", "darwaza", "tala", "chabi", "nashta", "thali", "chammach",
    
    # Common functional verbs, pronouns, question/state words in Roman Hindi
    "nahi", "nahin", "nai", "hai", "hain", "tha", "thi",
    "raha", "rahi", "rahe", "hua", "hui", "hue", "karo", "kijiye",
    "kardo", "karna", "bahut", "bohot", "sabko", "kuch", "kuchh",
    "pura", "poora", "yahan", "yaha", "wahan", "waha", "idhar", "udhar",
    "jaldi", "turant", "aaj", "kal", "abhi", "kaise", "kyun", "kyu",
    "yeh", "woh", "apna", "apni", "dikkat", "samsya", "samasya",
    "theek", "thik", "kharab", "toot", "jala", "bandh",
    "aana", "aata", "aati", "gira", "mein",
    "wala", "wali", "wale", "kripya", "chahiye", "dekho", "bhaiya"
}


def detect_language(text: str) -> str:
    """Detects if text is 'hindi', 'hinglish', or 'english'.
    
    - 'hindi': significant ratio of Devanagari script characters.
    - 'hinglish': Latin script with significant romanised Hindi vocabulary.
    - 'english': default fallback.
    The input text is never altered.
    """
    if not text or not text.strip():
        return "english"

    # Count Devanagari characters: \u0900 - \u097F
    devanagari_chars = len(re.findall(r"[\u0900-\u097F]", text))
    letters = len(re.findall(r"[A-Za-z\u0900-\u097F]", text))
    
    if letters > 0 and (devanagari_chars / letters) > 0.15:
        return "hindi"

    # Tokenize words in lowercase alphanumeric
    tokens = re.findall(r"[a-z]+", text.lower())
    if not tokens:
        return "english"

    matching_tokens = [tok for tok in tokens if tok in HINGLISH_VOCABULARY]
    hinglish_count = len(matching_tokens)
    
    # If 2 or more Hinglish tokens, definitely Hinglish
    if hinglish_count >= 2:
        return "hinglish"
    
    # 1 strong Hindi marker
    strong_hinglish_markers = {
        "paani", "pani", "bijli", "kharab", "safai", "kachra", "gandagi",
        "pankha", "nahin", "nahi", "toota", "tuta", "darwaza",
        "samasya", "dikkat", "badboo", "turant", "kijiye"
    }
    if hinglish_count == 1 and any(tok in strong_hinglish_markers for tok in tokens):
        return "hinglish"

    return "english"
