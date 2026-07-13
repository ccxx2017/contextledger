#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit benchmark v1 freeze split integrity.

Checks:
- No trajectory case appears in more than one split.
- No complete trajectory is split across development and blind_holdout.
- Template/alias leakage score between blind_holdout and development.
- Mechanism type distribution per split.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SHADOW_ROOT = SCRIPT_DIR.parent
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
    # Extract identifiers, paths, entity refs, and long phrases
    tokens = set(re.findall(r"[a-z0-9_./-]{6,}", text))
    # Also extract quoted strings and content fields
    tokens.update(re.findall(r'"([^"]{10,})"', text))
    return tokens


def compute_leakage_score(holdout_path: Path, dev_paths: list[Path]) -> dict[str, Any]:
    holdout_fingerprints = extract_text_fingerprints(holdout_path)
    if not holdout_fingerprints:
        return {"overlap_count": 0, "overlap_ratio": 0.0, "samples": []}
    dev_union: set[str] = set()
    for p in dev_paths:
        dev_union.update(extract_text_fingerprints(p))
    overlap = holdout_fingerprints & dev_union
    samples = sorted(overlap)[:20]
    return {
        "overlap_count": len(overlap),
        "overlap_ratio": round(len(overlap) / len(holdout_fingerprints), 4),
        "samples": samples,
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

    # Alias leakage: entity-like tokens shared between holdout and development
    dev_tokens: set[str] = set()
    for p in dev_paths:
        dev_tokens.update(extract_text_fingerprints(p))
    alias_leakage: list[dict[str, Any]] = []
    for case in holdout_cases:
        path = REPO_ROOT / case["trajectory_path"]
        holdout_tokens = extract_text_fingerprints(path)
        shared = holdout_tokens & dev_tokens
        alias_leakage.append({
            "case_id": case["case_id"],
            "shared_token_count": len(shared),
            "samples": sorted(shared)[:10],
        })

    return {
        "audit_version": "1.0",
        "freeze_manifest_sha256": hashlib.sha256(FREEZE_MANIFEST_PATH.read_bytes()).hexdigest(),
        "total_cases": manifest.get("total_cases"),
        "duplicated_cases": duplicated,
        "split_integrity_ok": len(duplicated) == 0,
        "mechanism_distribution": distribution,
        "template_alias_leakage": {
            "method": "text fingerprint overlap between blind_holdout and development trajectories",
            "per_case": leakage,
            "alias_per_case": alias_leakage,
        },
        "blind_holdout_rule": "blind_holdout cases must not be inspected or used for rule design; overlap scores below 0.5 are considered acceptable for this audit",
        "conclusion": {
            "no_cross_split_trajectories": len(duplicated) == 0,
            "blind_holdout_isolated_from_development": all(l["leakage_score"]["overlap_ratio"] < 0.5 for l in leakage),
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
    print(f"  blind_holdout_isolated: {report['conclusion']['blind_holdout_isolated_from_development']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
