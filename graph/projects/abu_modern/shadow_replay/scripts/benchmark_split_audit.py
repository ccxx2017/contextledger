#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit benchmark v1 freeze split integrity and template/alias leakage.

This audit does NOT execute benchmark trajectories; it only checks split
consistency and textual leakage between splits.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[5]

FREEZE_MANIFEST_PATH = REPO_ROOT / "graph" / "projects" / "abu_modern" / "benchmark" / "v1_freeze" / "benchmark_v1_freeze_manifest.json"
AUDIT_REPORT_PATH = REPO_ROOT / "graph" / "projects" / "abu_modern" / "benchmark" / "v1_freeze" / "split_audit_report.json"

MECHANISM_PREFIXES = [
    ("full", ["tr_full_"]),
    ("partial", ["tr_partial_", "tr_syn_partial_"]),
    ("conditional", ["tr_conditional_", "tr_syn_conditional_"]),
    ("revival", ["tr_revival_", "tr_syn_revival_"]),
    ("alias_trap", ["tr_alias_"]),
    ("provenance_conflict", ["tr_provenance_", "tr_prov_", "tr_syn_provenance_"]),
    ("non_invalidation_decoy", ["tr_non_invalidation_", "tr_decoy_"]),
    ("out_of_order_late", ["tr_out_of_order_", "tr_syn_out_of_order_"]),
]

LEAKAGE_ALGORITHM = {
    "name": "text_fingerprint_overlap",
    "description": "Extract stable phrase-like tokens (identifiers, paths, entity refs, quoted strings >= 10 chars) from each trajectory. Compute overlap between blind_holdout fingerprints and the union of development fingerprints.",
    "threshold": 0.5,
    "threshold_semantics": "overlap_ratio < 0.5 is acceptable; >= 0.5 flags the case for manual review",
    "handling_rule": "If a blind_holdout case has overlap_ratio >= threshold, it must not be used for rule design and must be escalated for review. The case may be moved to regression or removed from holdout.",
}

ALIAS_LEAKAGE_ALGORITHM = {
    "name": "shared_alias_token_ratio",
    "description": "Compute the ratio of text fingerprints shared between each blind_holdout trajectory and the union of development trajectories, relative to the holdout trajectory's total fingerprints. This reduces false positives from shared entity references that appear across many trajectories.",
    "threshold": 0.5,
    "threshold_semantics": "shared_ratio < 0.5 is acceptable; >= 0.5 flags the case for manual review",
    "handling_rule": "If a blind_holdout case shares >= threshold of its fingerprints with development, it must be treated as potentially leaked and excluded from final holdout evaluation until reviewed.",
}


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def classify_mechanism(case_id: str) -> str:
    for mech, prefixes in MECHANISM_PREFIXES:
        if any(case_id.startswith(p) for p in prefixes):
            return mech
    return "unknown"


def extract_text_fingerprints(path: Path) -> set[str]:
    """Extract stable phrase-like tokens for leakage comparison."""
    try:
        text = path.read_text(encoding="utf-8").lower()
    except Exception:
        return set()
    tokens = set(re.findall(r"[a-z0-9_./-]{6,}", text))
    tokens.update(re.findall(r'"([^"]{10,})"', text))
    return tokens


def compute_leakage_score(holdout_path: Path, dev_paths: list[Path]) -> dict[str, Any]:
    holdout_fingerprints = extract_text_fingerprints(holdout_path)
    if not holdout_fingerprints:
        return {
            "overlap_count": 0,
            "overlap_ratio": 0.0,
            "samples": [],
            "hits": [],
            "exceeds_threshold": False,
        }
    dev_union: set[str] = set()
    for p in dev_paths:
        dev_union.update(extract_text_fingerprints(p))
    overlap = holdout_fingerprints & dev_union
    samples = sorted(overlap)[:20]
    ratio = len(overlap) / len(holdout_fingerprints)
    return {
        "overlap_count": len(overlap),
        "overlap_ratio": round(ratio, 4),
        "samples": samples,
        "hits": samples,
        "exceeds_threshold": ratio >= LEAKAGE_ALGORITHM["threshold"],
    }


def audit() -> dict[str, Any]:
    manifest = load_json(FREEZE_MANIFEST_PATH)
    splits = {split["name"]: split for split in manifest["splits"]}

    # Cross-split duplication
    case_to_splits: dict[str, list[str]] = {}
    for split_name, split in splits.items():
        for cid in split["case_ids"]:
            case_to_splits.setdefault(cid, []).append(split_name)
    duplicated = {cid: names for cid, names in case_to_splits.items() if len(names) > 1}

    # Mechanism distribution
    distribution: dict[str, dict[str, int]] = {}
    for split_name, split in splits.items():
        distribution[split_name] = {}
        for cid in split["case_ids"]:
            mech = classify_mechanism(cid)
            distribution[split_name][mech] = distribution[split_name].get(mech, 0) + 1

    # Template/alias leakage: blind_holdout vs development
    dev_cases = splits.get("development", {}).get("cases", [])
    dev_paths = [REPO_ROOT / c["trajectory_path"] for c in dev_cases]
    holdout_cases = splits.get("blind_holdout", {}).get("cases", [])
    leakage: list[dict[str, Any]] = []
    for case in holdout_cases:
        path = REPO_ROOT / case["trajectory_path"]
        score = compute_leakage_score(path, dev_paths)
        leakage.append({
            "case_id": case["case_id"],
            "trajectory_path": case["trajectory_path"],
            "leakage_score": score,
        })

    # Alias leakage
    dev_tokens: set[str] = set()
    for p in dev_paths:
        dev_tokens.update(extract_text_fingerprints(p))
    alias_leakage: list[dict[str, Any]] = []
    for case in holdout_cases:
        path = REPO_ROOT / case["trajectory_path"]
        holdout_tokens = extract_text_fingerprints(path)
        shared = holdout_tokens & dev_tokens
        ratio = len(shared) / len(holdout_tokens) if holdout_tokens else 0.0
        alias_leakage.append({
            "case_id": case["case_id"],
            "shared_token_count": len(shared),
            "holdout_token_count": len(holdout_tokens),
            "shared_ratio": round(ratio, 4),
            "hits": sorted(shared)[:20],
            "exceeds_threshold": ratio >= ALIAS_LEAKAGE_ALGORITHM["threshold"],
        })

    return {
        "audit_version": "2.0",
        "note": "This audit checks split integrity and textual/alias leakage between splits. It does NOT execute benchmark trajectories through any adjudication chain and is therefore not a benchmark replay result.",
        "freeze_manifest_sha256": hashlib.sha256(FREEZE_MANIFEST_PATH.read_bytes()).hexdigest(),
        "total_cases": manifest.get("total_cases"),
        "duplicated_cases": duplicated,
        "split_integrity_ok": len(duplicated) == 0,
        "mechanism_distribution": distribution,
        "template_alias_leakage": {
            "algorithms": {
                "template_leakage": LEAKAGE_ALGORITHM,
                "alias_leakage": ALIAS_LEAKAGE_ALGORITHM,
            },
            "per_case": leakage,
            "alias_per_case": alias_leakage,
        },
        "blind_holdout_rule": "blind_holdout cases must not be inspected or used for rule design. Cases flagged by the leakage algorithms must be escalated before use in final evaluation.",
        "conclusion": {
            "no_cross_split_trajectories": len(duplicated) == 0,
            "template_leakage_acceptable": all(not l["leakage_score"]["exceeds_threshold"] for l in leakage),
            "alias_leakage_acceptable": all(not a["exceeds_threshold"] for a in alias_leakage),
            "blind_holdout_isolated_from_development": all(not l["leakage_score"]["exceeds_threshold"] for l in leakage) and all(not a["exceeds_threshold"] for a in alias_leakage),
        },
    }


def main() -> int:
    report = audit()
    AUDIT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Wrote audit report to {AUDIT_REPORT_PATH}")
    print(f"  split_integrity_ok: {report['split_integrity_ok']}")
    print(f"  template_leakage_acceptable: {report['conclusion']['template_leakage_acceptable']}")
    print(f"  alias_leakage_acceptable: {report['conclusion']['alias_leakage_acceptable']}")
    print(f"  blind_holdout_isolated: {report['conclusion']['blind_holdout_isolated_from_development']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
