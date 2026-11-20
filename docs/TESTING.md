# Shikayat Karo Testing & Quality Verification Report

This document details the test strategy, execution instructions, real benchmark results, and automated verification suites for **Shikayat Karo**.

---

## 1. Test Architecture & Overview

The test architecture ensures zero dependencies on pre-existing disk state, honest AI evaluation, and robust end-to-end browser automation:

```text
Test Suites
├── Backend Unit & Integration Tests (pytest)
│   ├── In-memory SQLite session with StaticPool
│   ├── Automatic virtual clock and rate-limiter resets between runs
│   ├── 51 comprehensive tests covering anonymity, RBAC, impact, SLA, and recurrence
├── AI Benchmark Evaluation (run_eval.py)
│   ├── Zero prototype or seed overlap on 90 evaluation complaints
│   ├── Precision, Recall, and F1 metrics for clustering
│   ├── Per-category confusion matrix and multilingual breakdown
└── Frontend End-to-End User Journeys (Playwright)
    ├── Multi-role browser automation (Citizen, Chief Admin, Facility Handler)
    ├── English and Hinglish grievance submission with AI diagnostic inspection
    ├── Anonymous submission with 8-character hex code and public tracking
    ├── Suggestion clustering confirmation into parent incident
    ├── Facility Handler resolution with mandatory resolution notes validation
    ├── Virtual-clock SLA escalation trigger
    └── Desktop (1280x800) and Mobile (393x851) screenshot captures
```

---

## 2. Backend Test Suite Execution

### Command
```bash
# Activate virtual environment
.venv\Scripts\activate

# Run complete pytest test suite
python -m pytest -v
```

### Real Pytest Run Output (51 Passed)
```text
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.2.0, pluggy-1.7.0 -- .venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\91999\.gemini\antigravity\scratch\shikayatKaro
configfile: pytest.ini
testpaths: backend/tests
plugins: anyio-4.16.0
collected 51 items

backend/tests/test_anonymity.py::test_anonymous_submission_privacy PASSED [  1%]
backend/tests/test_anonymity.py::test_anonymous_tracking_without_login PASSED [  3%]
backend/tests/test_anonymity.py::test_logged_in_user_submitting_anonymously_remains_anonymous PASSED [  5%]
backend/tests/test_api.py::test_auth_and_roles PASSED                    [  7%]
backend/tests/test_api.py::test_complaint_to_incident_lifecycle PASSED   [  9%]
backend/tests/test_api.py::test_virtual_clock_advance_and_escalation PASSED [ 11%]
backend/tests/test_classifier.py::test_classify_water_complaint_english PASSED [ 13%]
backend/tests/test_classifier.py::test_classify_water_complaint_hinglish PASSED [ 15%]
backend/tests/test_classifier.py::test_classify_electrical_complaint_hindi PASSED [ 17%]
backend/tests/test_classifier.py::test_classify_sanitation_complaint PASSED [ 19%]
backend/tests/test_classifier.py::test_low_confidence_flags_review PASSED [ 21%]
backend/tests/test_demo_story.py::test_demo_story_clustering_and_isolation PASSED [ 23%]
backend/tests/test_demo_story.py::test_confirm_suggestion_lifecycle_impact_and_sla PASSED [ 25%]
backend/tests/test_demo_story.py::test_kpi_dashboard_metrics_coherence PASSED [ 27%]
backend/tests/test_demo_story.py::test_anonymous_submissions_zero_leakage PASSED [ 29%]
backend/tests/test_escalation.py::test_escalation_tiers_progression PASSED [ 31%]
backend/tests/test_escalation.py::test_awaiting_info_pauses_clock PASSED [ 33%]
backend/tests/test_escalation.py::test_resolved_incident_stops_escalation PASSED [ 35%]
backend/tests/test_impact.py::test_required_impact_specification PASSED  [ 37%]
backend/tests/test_impact.py::test_impact_formula_with_raw_inputs PASSED [ 39%]
backend/tests/test_impact.py::test_impact_bands PASSED                   [ 41%]
backend/tests/test_impact.py::test_impact_clamping PASSED                [ 43%]
backend/tests/test_language.py::test_detect_hindi PASSED                 [ 45%]
backend/tests/test_language.py::test_detect_hinglish PASSED              [ 47%]
backend/tests/test_language.py::test_detect_english PASSED               [ 49%]
backend/tests/test_language.py::test_edge_cases PASSED                   [ 50%]
backend/tests/test_priority.py::test_safety_hazard_priority PASSED       [ 52%]
backend/tests/test_priority.py::test_essential_service_with_multiple_affected PASSED [ 54%]
backend/tests/test_priority.py::test_affected_count_text_extraction PASSED [ 56%]
backend/tests/test_priority.py::test_routine_maintenance_low_priority PASSED [ 58%]
backend/tests/test_priority.py::test_hinglish_urgency_detection PASSED   [ 60%]
backend/tests/test_production_config.py::test_production_refuses_startup_without_jwt_secret PASSED [ 62%]
backend/tests/test_production_config.py::test_production_refuses_startup_with_old_default_jwt_secret PASSED [ 64%]
backend/tests/test_production_config.py::test_production_accepts_strong_jwt_secret PASSED [ 66%]
backend/tests/test_development_generates_random_secret_and_logs_warning PASSED [ 68%]
backend/tests/test_production_config.py::test_production_refuses_wildcard_or_missing_cors PASSED [ 70%]
backend/tests/test_login_rate_limiting PASSED                            [ 72%]
backend/tests/test_production_config.py::test_anonymous_tracking_rate_limiting PASSED [ 74%]
backend/tests/test_production_config.py::test_student_role_guards PASSED [ 76%]
backend/tests/test_production_config.py::test_demo_endpoints_return_403_when_demo_mode_false PASSED [ 78%]
backend/tests/test_production_config.py::test_demo_endpoints_succeed_when_demo_mode_true PASSED [ 80%]
backend/tests/test_recurrence.py::test_boundary_incident_count_two_vs_three PASSED [ 82%]
backend/tests/test_recurrence.py::test_boundary_time_window_31_vs_29_days PASSED [ 84%]
backend/tests/test_recurrence.py::test_configurable_thresholds PASSED    [ 86%]
backend/tests/test_recurrence.py::test_api_recurring_issues_and_mark_permanent_fix PASSED [ 88%]
backend/tests/test_relatedness.py::test_hard_rule_category_and_location_both_differ PASSED [ 90%]
backend/tests/test_relatedness.py::test_same_wording_at_different_locations_not_strongly_grouped PASSED [ 92%]
backend/tests/test_relatedness.py::test_differently_worded_complaints_at_same_place_are_grouped PASSED [ 94%]
backend/tests/test_relatedness.py::test_hinglish_matches_english_equivalent PASSED [ 96%]
backend/tests/test_resolution_intel.py::test_find_similar_resolved_water_incident PASSED [ 98%]
backend/tests/test_resolution_intel.py::test_resolution_intel_empty_query PASSED [100%]

======================= 51 passed, 1 warning in 25.25s ========================
```

---

## 3. AI Evaluation Harness & Benchmarks

The evaluation harness evaluates nearest-prototype category classification and multi-factor incident clustering against fresh, non-overlapping ground-truth sets.

### Commands
```bash
# Run evaluation with fallback embedder (lightweight dictionary + n-grams)
python backend/eval/run_eval.py --embedder fallback

# Run evaluation with recommended production embedder (quantized ONNX MiniLM)
python backend/eval/run_eval.py --embedder fastembed
```

### Real Execution Benchmark Results

#### A. FastEmbed (Quantized ONNX MiniLM - Production Default)
```text
==============================================================================
SHIKAYAT KARO AI EVALUATION REPORT: FASTEMBED
==============================================================================
Model Name  : sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
Engine Type : neural
Dimension   : 384
------------------------------------------------------------------------------

[1] CATEGORY CLASSIFICATION BENCHMARK
Total Samples : 90
Overall Accuracy: 69/90 (76.67%)

Language Breakdown:
  - EN      : 29/36 ( 80.6%)
  - HI      : 20/27 ( 74.1%)
  - HINGLISH: 20/27 ( 74.1%)

Per-Category Breakdown:
  Administrative                       :  8/10 (80.0%)
  Classroom & Infrastructure           :  8/10 (80.0%)
  Electrical                           :  8/10 (80.0%)
  Harassment & Misconduct              :  9/10 (90.0%)
  Hostel & Mess                        :  7/10 (70.0%)
  IT & Network                         :  9/10 (90.0%)
  Safety & Security                    :  4/10 (40.0%)
  Sanitation & Cleanliness             :  7/10 (70.0%)
  Water & Plumbing                     :  9/10 (90.0%)

------------------------------------------------------------------------------
[2] CLUSTERING & RELATEDNESS BENCHMARK
Total Pairs Evaluated : 66
Precision             : 0.6154 (61.54%)
Recall                : 1.0000 (100.00%)
F1 Score              : 0.7619
Clustering Accuracy   : 0.6970 (69.70%)
==============================================================================
```

#### B. Fallback Embedder (Lightweight Concept Dictionary)
```text
==============================================================================
SHIKAYAT KARO AI EVALUATION REPORT: FALLBACK
==============================================================================
Model Name  : fallback-concept-projection-384d
Engine Type : fallback
Dimension   : 384
------------------------------------------------------------------------------

[1] CATEGORY CLASSIFICATION BENCHMARK
Total Samples : 90
Overall Accuracy: 51/90 (56.67%)

Language Breakdown:
  - EN      : 18/36 ( 50.0%)
  - HI      : 16/27 ( 59.3%)
  - HINGLISH: 17/27 ( 63.0%)

------------------------------------------------------------------------------
[2] CLUSTERING & RELATEDNESS BENCHMARK
Total Pairs Evaluated : 66
Precision             : 0.6957 (69.57%)
Recall                : 1.0000 (100.00%)
F1 Score              : 0.8205
Clustering Accuracy   : 0.7879 (78.79%)
==============================================================================
```

---

## 4. Frontend End-to-End Testing (Playwright)

### Setup & Commands
```bash
# Navigate to frontend
cd frontend

# Run complete Playwright end-to-end verification
npm run e2e
```

### Covered Journeys & Assertions:
1. **Journey 1: Student Grievance Filing (English & Hinglish)**:
   - Fills grievance text in English (`Water pipe leaking...`), selects campus location, submits, verifies AI diagnosis modal displaying category and priority.
   - Repeats with Hinglish grievance (`Hostel Block B ground floor ke paas paani ka pipe leak ho raha hai`), asserts AI pipeline correctly identifies Hinglish language and routes to `Water & Plumbing`.
2. **Journey 2: Anonymous Filing & Zero-Login Status Tracking**:
   - Submits grievance with `is_anonymous = true`.
   - Captures 8-character secret access code from success modal.
   - Navigates to public `/track` without logging in, inputs tracking ID and access code, verifies tracking progress bar renders without exposing citizen identity.
3. **Journey 3: Chief Admin Cluster Confirmation**:
   - Switches to `Chief Admin` persona, opens `/suggestions`.
   - Reviews multi-factor cluster reasons and engine tag (`fastembed` / `fallback`).
   - Confirms cluster into a Parent Incident, asserts redirect to `/incidents/{id}` with impact score and SLA deadline.
4. **Journey 4: Facility Handler Redressal with Mandatory Notes**:
   - Switches to `Facility Handler` persona, opens active incident dossier.
   - Verifies historical resolution intelligence recommendations.
   - Attempts resolution without notes $\rightarrow$ asserts validation block.
   - Submits detailed resolution notes $\rightarrow$ asserts state updates to `Resolved`.
5. **Journey 5: Virtual-Clock Fast-Forward & SLA Escalation**:
   - Opens `/demo` simulator, fast-forwards virtual clock by +6 hours.
   - Verifies automated SLA escalation tier advancement.
6. **Journey 6: Recurring-Issue Detection & Root-Cause Remediation**:
   - Opens Dashboard, asserts Recurring Infrastructure Issues card renders with location, category, incident count ($\ge 3$), and direct links to incident dossiers.
   - Clicks "Needs Permanent Fix", fills remediation scope, and schedules `PermanentFixTask`.
7. **Visual Regression & Screenshots**:
   - Automatically saves desktop (1280x800) and mobile (393x851) screenshots to `frontend/e2e/screenshots/`.
