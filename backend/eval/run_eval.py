#!/usr/bin/env python3
"""AI Evaluation Script for Project Shikayat Karo.

Runs both classification and clustering benchmarks through the active pipeline
using the specified embedder (fallback, fastembed, or sentence-transformers).

Metrics computed:
- Classification: Overall Accuracy, Per-Category Accuracy & Confusion Summary, Language breakdown
- Clustering / Relatedness: Precision, Recall, F1 Score, Accuracy, Hard-Negatives Breakdown
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.ai.embedder import (
    get_embedder,
    reset_active_embedder,
    FallbackEmbedder,
    FastEmbedder,
    SentenceTransformersEmbedder,
)
from backend.ai.classifier import classify_complaint, reset_category_centroids
from backend.ai.relatedness import calculate_relatedness, cosine_similarity


def configure_embedder(embedder_choice: str):
    """Configures and activates the specified embedder."""
    os.environ["EMBEDDER"] = embedder_choice
    # If the user explicitly asks for fallback or fastembed in this run, clear any TESTING=1 override
    if "TESTING" in os.environ and embedder_choice != "fallback":
        del os.environ["TESTING"]

    reset_active_embedder()
    reset_category_centroids()

    try:
        active = get_embedder()
        print(f"[*] Initialized embedder: {active.model_name} (engine: {active.engine_type})")
        return active
    except Exception as e:
        print(f"[!] Error initializing embedder '{embedder_choice}': {e}")
        sys.exit(1)


def evaluate_classification(dataset_path: Path) -> Dict[str, Any]:
    """Evaluates category classifier against labeled benchmark."""
    with open(dataset_path, "r", encoding="utf-8") as f:
        data: List[Dict[str, Any]] = json.load(f)

    total = len(data)
    correct = 0

    per_category: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"total": 0, "correct": 0, "confusions": defaultdict(int)}
    )
    per_language: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {"total": 0, "correct": 0}
    )

    for item in data:
        text = item["text"]
        expected = item["expected_category"]
        lang = item.get("language", "unknown")

        res = classify_complaint(text)
        predicted = res["category"]
        is_correct = (predicted.strip().lower() == expected.strip().lower())

        if is_correct:
            correct += 1

        per_category[expected]["total"] += 1
        if is_correct:
            per_category[expected]["correct"] += 1
        else:
            per_category[expected]["confusions"][predicted] += 1

        per_language[lang]["total"] += 1
        if is_correct:
            per_language[lang]["correct"] += 1

    accuracy = (correct / total) if total > 0 else 0.0

    return {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "per_category": dict(per_category),
        "per_language": dict(per_language),
    }


def evaluate_clustering(dataset_path: Path, embedder) -> Dict[str, Any]:
    """Evaluates multi-factor relatedness & clustering against labeled pair benchmark."""
    with open(dataset_path, "r", encoding="utf-8") as f:
        pairs: List[Dict[str, Any]] = json.load(f)

    total = len(pairs)
    tp = 0
    fp = 0
    tn = 0
    fn = 0

    pair_type_stats: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {"total": 0, "correct": 0}
    )

    ref_time = datetime(2026, 11, 20, 10, 0, 0)

    for pair in pairs:
        t1 = ref_time
        t2 = ref_time + timedelta(hours=pair.get("hours_apart", 1.0))

        v1 = embedder.embed(pair["text1"])
        v2 = embedder.embed(pair["text2"])
        text_sim = cosine_similarity(v1, v2)

        res = calculate_relatedness(
            text_cosine=text_sim,
            loc1_id=pair.get("loc1_id"),
            loc2_id=pair.get("loc2_id"),
            block1_id=pair.get("block1_id"),
            block2_id=pair.get("block2_id"),
            time1=t1,
            time2=t2,
            category1=pair.get("category1", ""),
            category2=pair.get("category2", ""),
            engine=embedder.engine_type,
        )

        predicted_suggest = res["should_suggest"]
        actual_incident = pair["same_incident"]
        p_type = pair.get("pair_type", "other")

        pair_type_stats[p_type]["total"] += 1

        if predicted_suggest and actual_incident:
            tp += 1
            pair_type_stats[p_type]["correct"] += 1
        elif predicted_suggest and not actual_incident:
            fp += 1
        elif not predicted_suggest and not actual_incident:
            tn += 1
            pair_type_stats[p_type]["correct"] += 1
        elif not predicted_suggest and actual_incident:
            fn += 1

    precision = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    accuracy = ((tp + tn) / total) if total > 0 else 0.0

    return {
        "total": total,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
        "pair_type_stats": dict(pair_type_stats),
    }


def print_evaluation_report(
    embedder_name: str,
    embedder_obj,
    clf_results: Dict[str, Any],
    clu_results: Dict[str, Any],
):
    print("\n" + "=" * 78)
    print(f"SHIKAYAT KARO AI EVALUATION REPORT: {embedder_name.upper()}")
    print("=" * 78)
    print(f"Model Name  : {embedder_obj.model_name}")
    print(f"Engine Type : {embedder_obj.engine_type}")
    print(f"Dimension   : {embedder_obj.dimension}")
    print("-" * 78)

    # Classification Summary
    print("\n[1] CATEGORY CLASSIFICATION BENCHMARK")
    print(f"Total Samples : {clf_results['total']}")
    print(f"Overall Accuracy: {clf_results['correct']}/{clf_results['total']} ({clf_results['accuracy'] * 100:.2f}%)")

    print("\nLanguage Breakdown:")
    for lang, stats in sorted(clf_results["per_language"].items()):
        acc = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0.0
        print(f"  - {lang.upper():8s}: {stats['correct']:2d}/{stats['total']:2d} ({acc:5.1f}%)")

    print("\nPer-Category Breakdown & Confusion Summary:")
    print(f"  {'Category':<36} {'Acc':<12} {'Top Misclassifications'}")
    print("  " + "-" * 74)
    for cat, stats in sorted(clf_results["per_category"].items()):
        acc_str = f"{stats['correct']}/{stats['total']} ({(stats['correct']/stats['total']*100):.1f}%)"
        confusions = stats["confusions"]
        if confusions:
            top_conf = sorted(confusions.items(), key=lambda x: x[1], reverse=True)[:2]
            conf_str = ", ".join(f"{c} ({cnt})" for c, cnt in top_conf)
        else:
            conf_str = "None (100% correct)"
        print(f"  {cat:<36} {acc_str:<12} {conf_str}")

    # Clustering Summary
    print("\n" + "-" * 78)
    print("[2] CLUSTERING & RELATEDNESS BENCHMARK")
    print(f"Total Pairs Evaluated : {clu_results['total']}")
    print(f"True Positives  (TP)  : {clu_results['tp']}")
    print(f"False Positives (FP)  : {clu_results['fp']}")
    print(f"True Negatives  (TN)  : {clu_results['tn']}")
    print(f"False Negatives (FN)  : {clu_results['fn']}")
    print(f"Precision             : {clu_results['precision']:.4f} ({clu_results['precision'] * 100:.2f}%)")
    print(f"Recall                : {clu_results['recall']:.4f} ({clu_results['recall'] * 100:.2f}%)")
    print(f"F1 Score              : {clu_results['f1']:.4f}")
    print(f"Clustering Accuracy   : {clu_results['accuracy']:.4f} ({clu_results['accuracy'] * 100:.2f}%)")

    print("\nBreakdown by Pair Type:")
    for p_type, stats in sorted(clu_results["pair_type_stats"].items()):
        acc = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0.0
        print(f"  - {p_type:<42}: {stats['correct']:2d}/{stats['total']:2d} ({acc:5.1f}%)")

    print("=" * 78 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Evaluate AI classification and clustering pipeline.")
    parser.add_argument(
        "--embedder",
        choices=["fallback", "fastembed", "sentence-transformers"],
        default="fallback",
        help="Embedder engine to evaluate (fallback, fastembed, or sentence-transformers).",
    )
    parser.add_argument(
        "--classification-data",
        type=str,
        default=str(PROJECT_ROOT / "backend" / "eval" / "classification_set.json"),
        help="Path to classification benchmark JSON.",
    )
    parser.add_argument(
        "--clustering-data",
        type=str,
        default=str(PROJECT_ROOT / "backend" / "eval" / "clustering_pairs.json"),
        help="Path to clustering benchmark JSON.",
    )
    args = parser.parse_args()

    clf_path = Path(args.classification_data)
    clu_path = Path(args.clustering_data)

    if not clf_path.exists():
        print(f"Error: Classification dataset not found at {clf_path}")
        sys.exit(1)
    if not clu_path.exists():
        print(f"Error: Clustering dataset not found at {clu_path}")
        sys.exit(1)

    embedder_obj = configure_embedder(args.embedder)

    clf_results = evaluate_classification(clf_path)
    clu_results = evaluate_clustering(clu_path, embedder_obj)

    print_evaluation_report(args.embedder, embedder_obj, clf_results, clu_results)


if __name__ == "__main__":
    main()
