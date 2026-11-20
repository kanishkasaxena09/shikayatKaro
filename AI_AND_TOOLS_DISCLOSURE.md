# AI & Tools Disclosure

In the spirit of complete transparency, truthful disclosure, and engineering integrity, this document details every third-party library, AI embedding model, evaluation dataset, cloud platform, and AI coding assistant utilized in the design, development, and operation of **Shikayat Karo (शिकायत Karo)**.

---

## 1. Algorithmic Breakdown: Rule-Based vs. Embedding-Based Components

Shikayat Karo does **not** employ opaque Large Language Models (LLMs) or black-box generative models in its core pipeline. Every analytical decision is reproducible, auditable, and categorized below:

### A. Deterministic & Rule-Based Components (No Neural Inference)

| Component | Module | Algorithmic Nature & Logic |
| :--- | :--- | :--- |
| **Priority Scoring** | `backend/ai/priority.py` | **100% Deterministic Rule Engine**. Scans text for high-risk safety hazards (`spark`, `fire`, `gas`, `ragging`, `short circuit` $\rightarrow$ Critical/High), assesses reported citizen impact counts ($\ge 20 \rightarrow$ High, $\ge 5 \rightarrow$ Medium), and extracts Hinglish urgency tokens (`turant`, `jaldi`, `danger`). Accompanied by natural-language reason explanations. |
| **Impact Scoring** | `backend/ai/impact.py` | **Deterministic Linear Formula** mapped to an integer score $[0, 100]$: <br>$$\text{Impact} = 0.35 \cdot \text{Severity} + 0.25 \cdot \text{Urgency} + 0.25 \cdot \text{Affected} + 0.15 \cdot \text{Duration}$$ |
| **SLA Escalations** | `backend/ai/escalation.py` | **Deterministic SLA Timers**. Evaluates elapsed hours against priority rules (Critical 4.0h, High 24.0h, Medium 72.0h, Low 168.0h). Automatically advances escalation tiers: Tier 1 (100% deadline), Tier 2 (150% deadline), and Tier 3 (200% deadline). Awaiting information status pauses the clock. |
| **Language Detection** | `backend/ai/language.py` | **Deterministic Unicode & Vocabulary Heuristic**. Inspects unicode character ranges ($0x0900 - 0x097F$ for Devanagari Hindi) and cross-checks 150+ romanised colloquial Hinglish markers (`paani`, `bijli`, `kharab`, `choke`, `nahi`). Falls back to English. |
| **Recurring Issues** | `backend/ai/recurrence.py` | **Deterministic Spatial-Temporal Heuristic**. Resolves campus block-level hierarchy (`get_block_location`) and flags recurring facility breakdowns when the same category at the same block produces $\ge 3$ distinct parent incidents within 30 days of the virtual clock. Enables scheduling tracked `PermanentFixTask` remediation records. |
| **Zero-Leakage Privacy** | `backend/routers/complaints.py` | **Cryptographic Salted Hash Security**. Generates 8-character uppercase hex access codes for anonymous complainants. Stores only salted `bcrypt` hashes in database. Complainant foreign keys are strictly `NULL`. Single complaint, track, suggestion, and incident APIs strictly sanitize complainant metadata. |

### B. Embedding-Based Components (Vector Similarity)

| Component | Module | Algorithmic Nature & Logic |
| :--- | :--- | :--- |
| **Category Classification** | `backend/ai/classifier.py` | **Nearest-Prototype Cosine Classifier**. Projects input text into vector space and computes cosine similarity against 10 general prototype sentences per category across English, Hindi, and Hinglish (no demo sentences reused). Flags low-confidence predictions ($< 0.35$) for human triage. |
| **Incident Clustering** | `backend/ai/relatedness.py` | **Composite Multi-Factor Relatedness Heuristic** combining text semantics, spatial hierarchy, temporal proximity, and category match: <br>$$\text{Score} = 0.45 \cdot \text{Text} + 0.25 \cdot \text{Location} + 0.15 \cdot \text{Time} + 0.15 \cdot \text{Category}$$ <br>**Hard Negative Guard**: Relatedness score is strictly capped at $0.40$ if both category and location differ. All suggestions are advisory and require human administrator confirmation. |
| **Resolution Intelligence** | `backend/ai/resolution_intel.py` | **Historical Semantic Recommender**. Compares active incident descriptions against past resolved incident dossiers in the database to recommend tested resolution procedures and verified technicians. |

---

## 2. Embedding Models & Environment Configurations

Shikayat Karo supports three interchangeable embedder backends via the `EMBEDDER` environment variable:

```text
EMBEDDER=fastembed | fallback | sentence-transformers
```

| Engine | Technology & Model | Memory Footprint | Accuracy (90 Items) | Clustering F1 | Deployment Environment |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`fastembed`** *(Recommended)* | Quantized ONNX MiniLM (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`) | **~150 MB** | **76.67%** (69/90) | **0.7619** (Recall: 100%, Prec: 61.5%) | **Production Default** (Render Free Tier 512MB RAM) |
| **`fallback`** *(Lightweight)* | Handcrafted concept dictionary (150+ stems) + 3-char n-gram hashing vectorizer | **< 25 MB** | **56.67%** (51/90) | **0.8205** (Recall: 100%, Prec: 69.6%) | **CI / Automated Testing & Offline Environments** |
| **`sentence-transformers`** | PyTorch + Hugging Face Transformers (`paraphrase-multilingual-MiniLM-L12-v2`) | **~850 MB** | ~77% (Equivalent) | ~0.76 (Equivalent) | **High-Memory Dedicated Compute Only** (Causes OOM exit code 137 on 512MB instances; documented limitation) |

> [!NOTE]
> Every clustering suggestion generated by the platform explicitly discloses the active engine (`engine: "neural"` vs `engine: "fallback"`) in its database record, API responses, and administrator review cards.

---

## 3. Evaluation Datasets

To ensure strict zero-leakage benchmark credibility, the evaluation harness in `backend/eval/` utilizes clean datasets with **zero prototype or seed sentence overlap**:

1. **`backend/eval/classification_set.json`**:
   - 90 labeled grievances balanced across all 9 supported campus infrastructure categories.
   - Multilingual composition: 30 English, 30 Hindi (Devanagari), and 30 Hinglish (romanised).
   - Contains colloquial syntax, slang, regional vocabulary, and punctuation variations.

2. **`backend/eval/clustering_pairs.json`**:
   - 60 curated grievance pairs with ground-truth boolean clustering labels (`is_same_incident: true/false`).
   - Includes hard negatives:
     - Identical category, different building/block.
     - Identical building/block, completely different issue (e.g. electrical spark vs water leakage).
     - Differently phrased complaints in different languages describing the exact same underlying incident.

---

## 4. AI Coding Assistants & Development Tools

- **Google Antigravity (Google DeepMind)**: Autonomous agentic software engineering platform used for full-stack codebase architecture, zero-leakage privacy enforcement, deterministic test design, evaluation harness development, production configuration hardening, and end-to-end verification.

---

## 5. Third-Party Backend Libraries (Python 3.10+)

Direct dependencies from `backend/requirements.txt`:

| Package | Version | Purpose |
| :--- | :--- | :--- |
| **`fastapi`** | `>= 0.110.0` | Asynchronous ASGI REST API framework and OpenAPI contract generator |
| **`uvicorn[standard]`** | `>= 0.30.0` | High-performance ASGI production web server |
| **`sqlalchemy`** | `>= 2.0.0` | Object-Relational Mapping (ORM) and SQLite / PostgreSQL query engine |
| **`pydantic`** | `>= 2.7.0` | Strict data validation, request sanitization, and response serialization schemas |
| **`pyjwt`** | `>= 2.8.0` | RFC 7519 JSON Web Token signing, claims encoding, and role-based validation |
| **`bcrypt`** | `>= 4.0.0` | Cryptographic password hashing and anonymous access code salted verification |
| **`apscheduler`** | `>= 3.10.0` | In-process cron scheduler for automated background SLA escalation evaluations |
| **`httpx`** | `>= 0.27.0` | Async HTTP client used by FastAPI TestClient and test harnesses |
| **`python-multipart`** | `>= 0.0.9` | Form data and multipart file parsing support |
| **`psycopg2-binary`** | `>= 2.9.9` | PostgreSQL database adapter for production relational storage |
| **`pytest`** | `>= 8.0.0` | Test framework for unit, integration, boundary, and API tests |
| **`fastembed`** | `>= 0.4.0` | Fast, lightweight ONNX runtime multilingual sentence embedding engine |

---

## 6. Third-Party Frontend Libraries (Node.js 18+)

Direct dependencies from `frontend/package.json`:

| Package | Version | Purpose |
| :--- | :--- | :--- |
| **`react` & `react-dom`** | `^19.3.1` | Declarative reactive UI framework |
| **`react-router-dom`** | `^7.18.5` | Client-side routing, protected route guards, and history navigation |
| **`axios`** | `^1.21.1` | HTTP client with centralized JWT interceptors and error normalization |
| **`lucide-react`** | `^1.70.0` | Clean, accessible SVG iconography |
| **`tailwindcss` & `@tailwindcss/vite`** | `^4.3.5` | Utility-first responsive CSS styling engine |
| **`vite`** | `^6.4.6` | Next-generation frontend build bundler and development proxy |
| **`@playwright/test`** | `^1.65.0` | End-to-end browser automation suite testing full citizen, admin, and handler user journeys |
| **`oxlint`** | `^1.90.0` | High-performance Rust-based JavaScript/JSX code linter |

---

## 7. Cloud Platforms & Hosting

- **Render**: Backend cloud hosting running containerized FastAPI with automatic restarts (`https://shikayatkaro-backend.onrender.com`).
- **Vercel**: Frontend single-page application global CDN hosting with SPA rewrite rules (`https://shikayatkaro.vercel.app`).
- **SQLite (Default)**: Embedded relational database with Write-Ahead Logging (WAL) pragmas.
- **PostgreSQL**: Supported for production persistence via `DATABASE_URL`.
