"""Nearest-prototype category classification module for Project Shikayat Karo.

Predicts categories based on prototype example embeddings in English, Hindi, and Hinglish.
Categories:
- Water & Plumbing
- Electrical
- Sanitation & Cleanliness
- IT & Network
- Hostel & Mess
- Classroom & Infrastructure
- Safety & Security
- Harassment & Misconduct (confidential)
- Administrative

Outputs:
- Predicted category
- Confidence score (0.0 - 1.0)
- Top-2 alternative categories with scores
- needs_review flag if confidence falls below threshold
"""

from typing import Dict, Any, List, Tuple
from backend.ai.embedder import get_embedder
from backend.ai.relatedness import cosine_similarity

# Confidence threshold below which manual admin review is recommended
CONFIDENCE_THRESHOLD = 0.35

CATEGORY_PROTOTYPES: Dict[str, List[str]] = {
    "Water & Plumbing": [
        "Water leakage from pipe in washroom",
        "Drinking water cooler is leaking and water is overflowing",
        "Washbasin tap broken water flowing continuously",
        "Hostel ground floor mein paani ka pipe phat gaya hai poora paani beh raha hai",
        "Hostel Block B mein paani ka pipe phat gaya hai poora paani beh raha hai",
        "Hostel Block B mein paani ka pipe leak ho raha hai",
        "Paani ka pipe phat gaya hai poora paani beh raha hai",
        "Nal se paani tapak raha hai band nahi ho raha",
        "Hostel bathroom mein geyser se leakage ho rahi hai",
        "पानी का नल टूटा हुआ है और पानी बह रहा है",
        "शौचालय में पाइपलाइन लीक हो रही है",
        "Water supply completely cut off in hostel pipeline"
    ],
    "Electrical": [
        "Electric spark coming from main switchboard in hallway",
        "Ceiling fan is making loud noise and not spinning",
        "Power socket in lab burnt and giving electric shock",
        "Room ka pankha nahi chal raha switch kharab ho gaya",
        "Socket mein se spark nikal raha hai current aa raha hai",
        "Bijli chali gayi hai tube light fuse ho gayi hai",
        "कमरे का पंखा और लाइट काम नहीं कर रहे हैं",
        "बिजली के बोर्ड से स्पार्क निकल रहा है करंट का खतरा है",
        "Corridor lights are flickering and causing complete darkness"
    ],
    "Sanitation & Cleanliness": [
        "Washroom is extremely dirty with choked toilet flush",
        "Garbage bin overflowing in corridor bad smell spreading",
        "Cockroaches and insects infestation in washroom",
        "Bathroom bohot ganda hai flush jam ho gaya hai",
        "Corridor mein kachra pada hai bohot badboo aa rahi hai",
        "Safai nahi hui hai dustbin poora overflow kar raha hai",
        "शौचालय बहुत गंदा है और बदबू आ रही है",
        "कचरा पेटी भरी हुई है और सफाई नहीं हुई है",
        "Floor needs immediate disinfection and deep cleaning"
    ],
    "IT & Network": [
        "Campus Wi-Fi is disconnected and router has no internet signal",
        "Lab computer network cable damaged cannot connect to portal",
        "Internet speed is extremely slow and portal is not opening",
        "Hostel wifi connect nahi ho raha internet band hai",
        "Wifi speed bohot slow hai lab mein net nahi chal raha",
        "Router down hai portal open nahi ho raha network error aa raha",
        "इंटरनेट बिल्कुल नहीं चल रहा है वाईफाई बंद है",
        "लैब का नेटवर्क काम नहीं कर रहा है",
        "Student ERP portal connection timeout and gateway down"
    ],
    "Hostel & Mess": [
        "Mess food quality is poor insect found in daal",
        "Student mess meal unhygienic and cold food served",
        "Hostel bed mattress is torn and cupboard latch broken",
        "Mess ke khane mein daal kacchi hai roti kharab mili",
        "Hostel room cupboard almirah door hinge broken",
        "Hostel room ka bed toota hua hai mattress replace karo",
        "मेस के खाने में कीड़ा निकला और खाना खराब है",
        "कमरे का फर्नीचर और अलमारी टूटी हुई है",
        "Dinner not served properly in student mess dining hall"
    ],
    "Classroom & Infrastructure": [
        "Classroom projector is not turning on and display is blur",
        "Lecture hall benches and desks are broken",
        "Air conditioner in seminar hall is broken and leaking",
        "Classroom ka projector display nahi dikha raha display cut ho raha",
        "Lecture hall ki bench tooti hui hai baithne ki jagah nahi hai",
        "Seminar hall ka AC kharab hai garmi bohot lag rahi hai",
        "कक्षा का प्रोजेक्टर खराब है स्क्रीन नहीं चल रही",
        "क्लासरूम की टेबल और कुर्सियां टूटी हुई हैं",
        "Blackboard broken and ceiling plaster falling down"
    ],
    "Safety & Security": [
        "Bicycle stolen from hostel cycle parking area",
        "Streetlight near boundary wall broken complete dark and unsafe",
        "Unauthorized outsiders entered hostel premises without entry pass",
        "Parking se meri cycle chori ho gayi security guard nahi tha",
        "Raat ko boundary wall ke paas streetlight band rehti hai dar lagta hai",
        "Hostel gate par security check nahi ho raha bahar ke log aa rahe",
        "साइकिल पार्किंग से चोरी हो गई गार्ड मौजूद नहीं था",
        "कैंपस की बाउंड्री पर अंधेरा है सुरक्षा का खतरा है",
        "Suspicious individuals wandering near student residences"
    ],
    "Harassment & Misconduct (confidential)": [
        "Senior students ragging and bullying junior students in hostel",
        "Verbal harassment and inappropriate stalking behavior near library",
        "Threatening and abusive behavior from peers during college hours",
        "Hostel mein seniors ragging le rahe hain dhamki de rahe hain",
        "Library ke paas ladko ne gandi comments ki aur piche piche aaye",
        "Abusive language use ki aur threatening di ja rahi hai",
        "सीनियर छात्रों द्वारा रैगिंग और धमकाने का मामला",
        "परिसर में पीछा करना और गलत व्यवहार करना",
        "Confidential report of intimidation and misconduct"
    ],
    "Administrative": [
        "Fee receipt not updated in accounts office after online payment",
        "Hostel caution money refund pending since three months",
        "Student ID card replacement application delay at admin office",
        "Admin office se fees receipt nahi mili account update nahi hua",
        "Caution money refund nahi aaya bohot din se chakkar kaat rahe",
        "Student ID card request pending hai koi sunwai nahi ho rahi",
        "फीस जमा होने के बाद भी रसीद नहीं दी गई",
        "एडमिन ऑफिस से छात्र पहचान पत्र में देरी हो रही है",
        "Marksheet correction request stuck with examination branch"
    ]
}

# Pre-computed prototype centroid cache
_CATEGORY_CENTROIDS: Dict[str, List[float]] = {}


def _get_category_centroids() -> Dict[str, List[float]]:
    global _CATEGORY_CENTROIDS
    if _CATEGORY_CENTROIDS:
        return _CATEGORY_CENTROIDS

    embedder = get_embedder()
    centroids: Dict[str, List[float]] = {}
    
    for cat, phrases in CATEGORY_PROTOTYPES.items():
        embeddings = embedder.embed_batch(phrases)
        if not embeddings:
            continue
        dim = len(embeddings[0])
        # Average vectors
        centroid = [0.0] * dim
        for emb in embeddings:
            for d in range(dim):
                centroid[d] += emb[d]
        n = float(len(embeddings))
        centroid = [x / n for x in centroid]
        # Normalize
        norm = sum(x * x for x in centroid) ** 0.5
        if norm > 0:
            centroid = [x / norm for x in centroid]
        centroids[cat] = centroid

    _CATEGORY_CENTROIDS = centroids
    return _CATEGORY_CENTROIDS


def classify_complaint(text: str) -> Dict[str, Any]:
    """Classifies complaint text into the most probable category using prototype embeddings.
    
    Returns:
        {
            "category": str,
            "confidence": float,
            "top_alternatives": [{"category": str, "score": float}, ...],
            "needs_review": bool,
            "reasons": List[str]
        }
    """
    if not text or not text.strip():
        return {
            "category": "Administrative",
            "confidence": 0.0,
            "top_alternatives": [],
            "needs_review": True,
            "reasons": ["Empty input text"]
        }

    embedder = get_embedder()
    text_vector = embedder.embed(text)
    centroids = _get_category_centroids()

    # Compute similarity against all prototypes
    scores: List[Tuple[str, float]] = []
    for cat, centroid in centroids.items():
        sim = cosine_similarity(text_vector, centroid)
        scores.append((cat, round(sim, 3)))

    # Sort descending
    scores.sort(key=lambda x: x[1], reverse=True)

    best_cat, best_score = scores[0]
    alternatives = [{"category": c, "score": s} for c, s in scores[1:3]]
    needs_review = best_score < CONFIDENCE_THRESHOLD

    reasons = [
        f"Matched category '{best_cat}' with prototype similarity score {best_score}.",
        f"Alternative 1: {alternatives[0]['category']} ({alternatives[0]['score']})",
        f"Alternative 2: {alternatives[1]['category']} ({alternatives[1]['score']})"
    ]
    if needs_review:
        reasons.append(f"Confidence {best_score} is below threshold {CONFIDENCE_THRESHOLD}; flagged for admin review.")

    return {
        "category": best_cat,
        "confidence": best_score,
        "top_alternatives": alternatives,
        "needs_review": needs_review,
        "reasons": reasons
    }
