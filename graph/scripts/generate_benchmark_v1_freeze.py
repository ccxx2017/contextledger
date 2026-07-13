#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the benchmark v1 freeze manifest for abu_modern.

Run from repository root. This script only reads existing phase05_v3 artifacts
and writes the freeze manifest; it does not modify trajectories or gold.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT = "abu_modern"
BENCHMARK_VERSION = "phase05_v3"
FREEZE_VERSION = "v1"
FREEZE_DIR = REPO_ROOT / "graph" / "projects" / PROJECT / "benchmark" / "v1_freeze"
MANIFEST_PATH = FREEZE_DIR / "benchmark_v1_freeze_manifest.json"
BENCHMARK_DIR = REPO_ROOT / "graph" / "projects" / PROJECT / "benchmark" / BENCHMARK_VERSION
SCORE_REPORT_PATH = BENCHMARK_DIR / "reports" / "phase05_score_report.json"
METRIC_SCRIPT_PATH = REPO_ROOT / "graph" / "scripts" / "score_phase05.py"

# Explicit, frozen split assignment. Deterministic and reviewed.
SPLITS: dict[str, list[str]] = {
    "development": [
        "tr_full_tkt_005b",
        "tr_syn_partial_policy_clause",
        "tr_syn_conditional_region_exception",
        "tr_syn_revival_feature_flag",
        "tr_alias_workspace_identity",
        "tr_syn_non_invalidation_parallel_targets",
        "tr_syn_out_of_order_inventory_present",
    ],
    "regression": [
        "tr_full_tkt_006",
        "tr_syn_partial_checklist_clause",
        "tr_syn_conditional_window_exception",
        "tr_revival_round5x",
        "tr_alias_quant_tools",
        "tr_syn_out_of_order_price_band_present",
    ],
    "blind_holdout": [
        "tr_decoy_strategy_scripts",
        "tr_alias_tkt_split",
    ],
    "adversarial": [
        "tr_prov_run54b",
        "tr_syn_provenance_conflict",
    ],
}

SPLIT_RULES: dict[str, str] = {
    "development": "Allowed for iterative development, rule tuning, and prompt engineering. Results may be inspected.",
    "regression": "Must pass on every commit that touches reconcile/apply/assembler/resolver. Results may be inspected.",
    "blind_holdout": "Must not be inspected or used for rule design before final evaluation. Used only for generalization check.",
    "adversarial": "Stress-tests for false merge/split, provenance conflict, and adversarial alias traps. May be inspected after initial design.",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_benchmark_dir_hash() -> str:
    h = hashlib.sha256()
    files = sorted(p for p in BENCHMARK_DIR.rglob("*") if p.is_file())
    for p in files:
        rel = p.relative_to(BENCHMARK_DIR).as_posix()
        h.update(rel.encode("utf-8"))
        h.update(sha256_file(p).encode("utf-8"))
    return h.hexdigest()


def build_split_manifest(split_name: str, case_ids: list[str]) -> dict[str, Any]:
    cases = []
    for cid in case_ids:
        traj = BENCHMARK_DIR / "trajectories" / f"{cid}.json"
        gold = BENCHMARK_DIR / "gold" / f"{cid}.gold.json"
        cases.append(
            {
                "case_id": cid,
                "trajectory_path": traj.relative_to(REPO_ROOT).as_posix(),
                "trajectory_sha256": sha256_file(traj),
                "gold_path": gold.relative_to(REPO_ROOT).as_posix(),
                "gold_sha256": sha256_file(gold),
            }
        )
    return {
        "name": split_name,
        "rule": SPLIT_RULES[split_name],
        "case_count": len(cases),
        "case_ids": case_ids,
        "cases": cases,
    }


def load_baselines() -> dict[str, Any]:
    if not SCORE_REPORT_PATH.exists():
        return {}
    data = load_json(SCORE_REPORT_PATH)
    baselines = data.get("baselines", {})
    out: dict[str, Any] = {}
    for name in ["phase0_current", "flat_rag_d1", "flat_rag_d2"]:
        b = baselines.get(name, {})
        m = b.get("metrics", {})
        out[name] = {
            "invalidation_precision": m.get("invalidation_precision"),
            "invalidation_recall": m.get("invalidation_recall"),
            "active_set_set_f1": m.get("active_set_set_f1"),
            "must_include_recall": m.get("must_include_recall"),
            "valid_time_adjudication_accuracy": m.get("valid_time_adjudication_accuracy"),
        }
    return out


def build_manifest() -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    all_case_ids = [cid for case_ids in SPLITS.values() for cid in case_ids]
    return {
        "schema_version": "1.0",
        "freeze_version": FREEZE_VERSION,
        "based_on_benchmark_version": BENCHMARK_VERSION,
        "project_id": PROJECT,
        "generated_at": now.isoformat(),
        "generated_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_path": BENCHMARK_DIR.relative_to(REPO_ROOT).as_posix(),
        "source_dir_sha256": compute_benchmark_dir_hash(),
        "metric_script_path": METRIC_SCRIPT_PATH.relative_to(REPO_ROOT).as_posix(),
        "metric_script_sha256": sha256_file(METRIC_SCRIPT_PATH),
        "score_report_path": SCORE_REPORT_PATH.relative_to(REPO_ROOT).as_posix(),
        "score_report_sha256": sha256_file(SCORE_REPORT_PATH),
        "gold_annotation_schema_version": "phase05_v3",
        "d1_baseline_definition": "Flat RAG with static context window, no invalidation tracking",
        "d2_baseline_definition": "Flat RAG with injected chronological summary, no explicit lifecycle adjudication",
        "splits": [build_split_manifest(name, case_ids) for name, case_ids in SPLITS.items()],
        "total_cases": len(all_case_ids),
        "all_case_ids": all_case_ids,
        "split_overlap_check": len(set(all_case_ids)) == len(all_case_ids),
        "usage_rules": {
            "development": "May be used for tuning and debugging. Inspect freely.",
            "regression": "Must remain green for any candidate replacement of reconcile/apply/assembler/resolver.",
            "blind_holdout": "Never inspect before final evaluation. Do not use for prompt or rule design.",
            "adversarial": "May be inspected, but failures must be treated as high-priority regressions.",
        },
        "update_policy": {
            "versioning": "Semver: MAJOR for split changes, MINOR for new cases, PATCH for metadata fixes.",
            "allowed_changes": [
                "Fix trajectory formatting errors without changing semantics",
                "Add metadata or hashes",
                "Update baseline scores when the old-link implementation changes",
            ],
            "forbidden_changes_without_new_version": [
                "Move a case from blind_holdout to development",
                "Modify gold annotations",
                "Add or remove cases",
                "Change metric scripts",
            ],
        },
        "baselines": load_baselines(),
        "notes": [
            "This freeze separates mechanism correctness (fixtures) from generalization (blind_holdout).",
            "The blind_holdout split must remain uninspected until lifecycle implementation is finalized.",
        ],
    }


def main() -> int:
    manifest = build_manifest()
    FREEZE_DIR.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Wrote {MANIFEST_PATH}")
    print(f"  total cases: {manifest['total_cases']}")
    print(f"  splits: {', '.join(s['name'] + '=' + str(s['case_count']) for s in manifest['splits'])}")
    print(f"  overlap_check: {manifest['split_overlap_check']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
