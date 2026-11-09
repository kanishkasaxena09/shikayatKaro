"""Embedder interface and implementations for Project Shikayat Karo.

Provides:
- Abstract Embedder interface
- SentenceTransformersEmbedder (default: paraphrase-multilingual-MiniLM-L12-v2)
- FastEmbedder (fallback when EMBEDDER=fastembed)
- FallbackEmbedder (deterministic lightweight fallback for offline/test environments)
- Embedding caching mechanism
"""

import os
import re
import math
import hashlib
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any

# Prevent Hugging Face from making network checks when models are cached locally
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

# In-memory LRU / lookup cache for embeddings
_EMBEDDING_CACHE: Dict[str, List[float]] = {}


class Embedder(ABC):
    """Abstract interface for text embedding models."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Returns the embedding vector dimension."""
        pass

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Generates a normalized embedding vector for a single string."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates normalized embedding vectors for a batch of strings."""
        pass


class SentenceTransformersEmbedder(Embedder):
    """Embedder using sentence-transformers paraphrase-multilingual-MiniLM-L12-v2."""

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self.model_name = model_name
        self._model: Any = None
        self._dim = 384

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except Exception:
                self._model = FallbackEmbedder(self._dim)
        return self._model

    @property
    def dimension(self) -> int:
        return self._dim

    def embed(self, text: str) -> List[float]:
        cleaned = text.strip() if text else ""
        cache_key = f"st:{hashlib.sha256(cleaned.encode('utf-8')).hexdigest()}"
        if cache_key in _EMBEDDING_CACHE:
            return _EMBEDDING_CACHE[cache_key]

        model = self._load_model()
        if isinstance(model, Embedder):
            vec_list = model.embed(cleaned)
            _EMBEDDING_CACHE[cache_key] = vec_list
            return vec_list

        vec = model.encode(cleaned, normalize_embeddings=True)
        vec_list = [float(x) for x in vec]
        _EMBEDDING_CACHE[cache_key] = vec_list
        return vec_list

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        results: List[List[float]] = []
        texts_to_embed = []
        indices_to_embed = []

        for i, text in enumerate(texts):
            cleaned = text.strip() if text else ""
            cache_key = f"st:{hashlib.sha256(cleaned.encode('utf-8')).hexdigest()}"
            if cache_key in _EMBEDDING_CACHE:
                results.append(_EMBEDDING_CACHE[cache_key])
            else:
                results.append([])
                texts_to_embed.append(cleaned)
                indices_to_embed.append(i)

        if texts_to_embed:
            model = self._load_model()
            if isinstance(model, Embedder):
                batch_res = model.embed_batch(texts_to_embed)
                for orig_idx, emb in zip(indices_to_embed, batch_res):
                    results[orig_idx] = emb
                    cache_key = f"st:{hashlib.sha256(texts[orig_idx].strip().encode('utf-8')).hexdigest()}"
                    _EMBEDDING_CACHE[cache_key] = emb
            else:
                embeddings = model.encode(texts_to_embed, normalize_embeddings=True)
                for orig_idx, emb in zip(indices_to_embed, embeddings):
                    vec_list = [float(x) for x in emb]
                    cache_key = f"st:{hashlib.sha256(texts[orig_idx].strip().encode('utf-8')).hexdigest()}"
                    _EMBEDDING_CACHE[cache_key] = vec_list
                    results[orig_idx] = vec_list

        return results


class FastEmbedder(Embedder):
    """Low-memory alternative using fastembed package."""

    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        self.model_name = model_name
        self._model: Any = None
        self._dim = 384

    def _load_model(self):
        if self._model is None:
            try:
                from fastembed import TextEmbedding
                self._model = TextEmbedding(model_name=self.model_name)
            except Exception:
                self._model = FallbackEmbedder(self._dim)
        return self._model

    @property
    def dimension(self) -> int:
        return self._dim

    def embed(self, text: str) -> List[float]:
        cleaned = text.strip() if text else ""
        cache_key = f"fe:{hashlib.sha256(cleaned.encode('utf-8')).hexdigest()}"
        if cache_key in _EMBEDDING_CACHE:
            return _EMBEDDING_CACHE[cache_key]

        model = self._load_model()
        if isinstance(model, Embedder):
            vec_list = model.embed(cleaned)
            _EMBEDDING_CACHE[cache_key] = vec_list
            return vec_list

        embeddings = list(model.embed([cleaned]))
        vec = embeddings[0]
        # Normalize
        norm = math.sqrt(sum(x * x for x in vec))
        vec_list = [float(x / norm) if norm > 0 else 0.0 for x in vec]
        _EMBEDDING_CACHE[cache_key] = vec_list
        return vec_list

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed(t) for t in texts]


class FallbackEmbedder(Embedder):
    """Deterministic, lightweight multilingual semantic embedder.
    
    Used when deep learning wheels are loading, offline, or during fast unit testing.
    Uses subword character n-grams and semantic concept projection so that
    multilingual equivalents (water leak / paani leak / पानी का रिसाव) have high cosine similarity.
    """

    def __init__(self, dim: int = 384):
        self._dim = dim
        self.concepts = {
            "water_plumbing": [
                "water", "tap", "leak", "pipe", "overflow", "drain", "flush", "plumbing",
                "paani", "pani", "nal", "tanki", "motor", "geyser", "sewage", "badboo",
                "पानी", "नल", "पाइप", "टंकी", "रिसाव", "सीवेज", "लीक"
            ],
            "electrical": [
                "electricity", "power", "shock", "spark", "light", "fan", "switch", "socket",
                "bijli", "batti", "current", "pankha", "taar", "fuse", "powercut", "cooler",
                "बिजली", "पंखा", "करंट", "स्पार्क", "लाइट", "तार"
            ],
            "sanitation": [
                "clean", "cleaning", "dirt", "garbage", "trash", "dustbin", "hygiene", "toilet",
                "safai", "kachra", "gandagi", "kooda", "saaf", "cockroach", "keeda",
                "सफाई", "कचरा", "गंदगी", "कूड़ा", "शौचालय"
            ],
            "it_network": [
                "wifi", "internet", "network", "router", "lan", "speed", "server",
                "net", "signal", "connect", "slow", "bandh",
                "वाईफाई", "इंटरनेट", "नेटवर्क"
            ],
            "hostel_mess": [
                "food", "mess", "meal", "hostel", "room", "bed", "warden", "door", "window",
                "khana", "roti", "chawal", "kamra", "darwaza", "khidki", "tala",
                "खाना", "मेस", "कमरा", "हॉस्टल", "दरवाजा"
            ],
            "safety_security": [
                "theft", "stolen", "security", "guard", "harass", "threat", "violence", "fight",
                "chori", "ragging", "ladai", "jhagda", "khatra", "danger",
                "चोरी", "सुरक्षा", "खतरा", "लड़ाई", "धमकी"
            ]
        }

    @property
    def dimension(self) -> int:
        return self._dim

    def embed(self, text: str) -> List[float]:
        cleaned = text.strip() if text else ""
        cache_key = f"fb:{hashlib.sha256(cleaned.encode('utf-8')).hexdigest()}"
        if cache_key in _EMBEDDING_CACHE:
            return _EMBEDDING_CACHE[cache_key]

        vec = [0.0] * self._dim
        text_lower = cleaned.lower()

        # 1. Base hashing on words and character trigrams
        tokens = re.findall(r"\w+", text_lower)
        for tok in tokens:
            h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dim
            sign = 1.0 if (h // self._dim) % 2 == 0 else -1.0
            vec[idx] += 1.0 * sign

        # Trigrams for cross-lingual substring matching
        for i in range(len(text_lower) - 2):
            tri = text_lower[i:i + 3]
            h = int(hashlib.md5(tri.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dim
            vec[idx] += 0.3

        # 2. Semantic concept projection
        for c_idx, (concept, keywords) in enumerate(self.concepts.items()):
            concept_hash = int(hashlib.md5(concept.encode("utf-8")).hexdigest(), 16)
            base_bin = (concept_hash % 64) * 5
            match_weight = 0.0
            for kw in keywords:
                if kw in text_lower:
                    match_weight += 3.0
            if match_weight > 0.0:
                for k in range(24):
                    bin_idx = (base_bin + k) % self._dim
                    vec[bin_idx] += match_weight

        # Normalize vector
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0.0:
            vec = [float(x / norm) for x in vec]
        else:
            vec[0] = 1.0

        _EMBEDDING_CACHE[cache_key] = vec
        return vec

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed(t) for t in texts]


_ACTIVE_EMBEDDER: Optional[Embedder] = None


def get_embedder() -> Embedder:
    """Returns the globally configured Embedder instance."""
    global _ACTIVE_EMBEDDER
    if _ACTIVE_EMBEDDER is not None:
        return _ACTIVE_EMBEDDER

    embedder_env = os.getenv("EMBEDDER", "sentence-transformers").lower().strip()

    if embedder_env == "fastembed":
        try:
            _ACTIVE_EMBEDDER = FastEmbedder()
            return _ACTIVE_EMBEDDER
        except Exception:
            pass

    if embedder_env in ["sentence-transformers", "default", ""]:
        try:
            _ACTIVE_EMBEDDER = SentenceTransformersEmbedder()
            return _ACTIVE_EMBEDDER
        except Exception:
            pass

    # Fallback embedder
    _ACTIVE_EMBEDDER = FallbackEmbedder()
    return _ACTIVE_EMBEDDER
