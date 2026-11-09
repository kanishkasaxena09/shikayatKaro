"""Unit tests for language detection module."""

from backend.ai.language import detect_language


def test_detect_hindi():
    hindi_text = "कमरे में बिजली नहीं आ रही है और पंखा बंद पड़ा है"
    assert detect_language(hindi_text) == "hindi"
    # Ensure original text remains unchanged
    assert hindi_text == "कमरे में बिजली नहीं आ रही है और पंखा बंद पड़ा है"


def test_detect_hinglish():
    hinglish_text1 = "Paani ka pipe leak ho raha hai aur paani beh raha hai"
    assert detect_language(hinglish_text1) == "hinglish"

    hinglish_text2 = "Room ka pankha nahi chal raha, bijli chali gayi hai"
    assert detect_language(hinglish_text2) == "hinglish"

    hinglish_text3 = "Bathroom mein safai nahi hui kachra pada hai"
    assert detect_language(hinglish_text3) == "hinglish"


def test_detect_english():
    english_text = "The overhead water tank is overflowing near the cafeteria"
    assert detect_language(english_text) == "english"

    english_text2 = "Classroom projector display is flickering in Hall 102"
    assert detect_language(english_text2) == "english"


def test_edge_cases():
    assert detect_language("") == "english"
    assert detect_language("   ") == "english"
