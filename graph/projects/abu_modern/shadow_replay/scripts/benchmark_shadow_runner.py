#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Frozen benchmark shadow evaluation runner (Stage04-B).

Runs phase05_v3 benchmark trajectories through the shadow lifecycle
adjudication chain and compares outputs against gold annotations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SHADOW_ROOT = SCRIPT_DIR.parent
REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(SCRIPT_DIR))

from shadow_lifecycle_adjudicator import ShadowLifecycleAdjudicator
from shadow_compiler import (
    initialize_shadow_graph_state,
    apply_shadow_patch,
    graph_state_hash,
    write_shadow_json,
)
from shadow_bundle_builder import build_shadow_bundle, bundle_hash
from shadow_resolution_adapter import observation_to_event

FREEZE_MANIFEST_PATH = REPO_ROOT / "graph" / "projects" / "abu_modern" / "benchmark" / "v1_freeze" / "benchmark_v1_freeze_manifest.json"
TRAJECTORY_DIR = REPO_ROOT / "graph" / "projects" / "abu_modern" / "benchmark" / "phase05_v3" / "trajectories"
GOLD_DIR = REPO_ROOT / "graph" / "projects" / "abu_modern" / "benchmark" / "phase05_v3" / "gold"
SHADOW_RUNS_DIR = SHADOW_ROOT / "runs" / "stage04b"
SHADOW_SCRIPTS = [
    SCRIPT_DIR / "shadow_lifecycle_adjudicator.py",
    SCRIPT_DIR / "shadow_compiler.py",
    SCRIPT_DIR / "shadow_bundle_builder.py",
    SCRIPT_DIR / "benchmark_shadow_runner.py",
]
CONTRACTS = [
    REPO_ROOT / "contracts" / "03_graph_schema.md",
    REPO_ROOT / "contracts" / "05_phase1_lifecycle_schema.md",
]

D1_BASELINE = {"must_include_recall": 1.0}
PHASE0_BASELINE = {
    "must_include_recall": 1.0,
    "active_set_set_f1": 0.8979591836734694,
    "invalidation_recall": 0.7368421052631579,
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def runtime_fingerprint() -> dict[str, Any]:
    return {
        "shadow_scripts": {p.name: sha256_file(p) for p in SHADOW_SCRIPTS},
        "contracts": {p.name: sha256_file(p) for p in CONTRACTS},
        "cwd": os.getcwd(),
        "argv": sys.argv,
    }


def compute_set_metrics(actual: set[str], expected: set[str]) -> dict[str, float]:
    tp = len(actual & expected)
    fp = len(actual - expected)
    fn = len(expected - actual)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}


def compare_step(
    step: dict[str, Any],
    graph_state: dict[str, Any],
    bundle: dict[str, Any],
) -> list[dict[str, Any]]:
    nodes = graph_state.get("nodes", {})
    if isinstance(nodes, list):
        nodes = {n["node_id"]: n for n in nodes if isinstance(n, dict)}

    actual_active = {n["claim_id"] for n in nodes.values() if n.get("status") == "active" and n.get("claim_id")}
    actual_superseded = {n["claim_id"] for n in nodes.values() if n.get("status") == "superseded" and n.get("claim_id")}
    actual_must = {nodes[nid]["claim_id"] for nid in bundle.get("must_include", []) if nid in nodes and nodes[nid].get("claim_id")}

    expected_active = set(step.get("expected_active_set", []))
    expected_invalid: set[str] = set()
    for inv in step.get("expected_invalidations", []):
        if isinstance(inv, dict):
            for cid in inv.get("dropped_claims", []):
                expected_invalid.add(cid)
        else:
            expected_invalid.add(inv)
    expected_must = set(step.get("must_include", []))

    diffs: list[dict[str, Any]] = []

    # Active set diffs
    for cid in expected_active - actual_active:
        diffs.append({
            "kind": "active_set",
            "claim_id": cid,
            "classification": "regression",
            "rationale": f"Expected active claim {cid} not in shadow active set",
            "blocking": cid in expected_must,
        })
    for cid in actual_active - expected_active:
        diffs.append({
            "kind": "active_set",
            "claim_id": cid,
            "classification": "regression",
            "rationale": f"Unexpected active claim {cid} in shadow active set",
            "blocking": False,
        })

    # Invalidation diffs (full bidirectional evaluation)
    # Reports all categories: true positive, false positive (unexpected_supersedes), false negative
    for cid in expected_invalid & actual_superseded:
        diffs.append({
            "kind": "invalidation",
            "claim_id": cid,
            "classification": "expected_improvement",
            "rationale": f"True positive invalidation: claim {cid} correctly superseded",
            "blocking": False,
        })
    for cid in expected_invalid - actual_superseded:
        diffs.append({
            "kind": "invalidation",
            "claim_id": cid,
            "classification": "regression",
            "rationale": f"False negative invalidation: expected invalidated claim {cid} not in shadow superseded set",
            "blocking": False,
        })
    for cid in actual_superseded - expected_invalid:
        diffs.append({
            "kind": "invalidation",
            "claim_id": cid,
            "classification": "unexpected_supersedes",
            "rationale": f"Unexpected supersedes: claim {cid} superseded in shadow but not in gold expected_invalidations for this step",
            "blocking": False,
        })

    # must_include diffs
    for cid in expected_must - actual_must:
        diffs.append({
            "kind": "must_include",
            "claim_id": cid,
            "classification": "blocker",
            "rationale": f"Expected must_include claim {cid} missing from shadow bundle",
            "blocking": True,
        })
    for cid in actual_must - expected_must:
        diffs.append({
            "kind": "must_include",
            "claim_id": cid,
            "classification": "expected_schema_change",
            "rationale": f"Shadow bundle includes additional claim {cid}",
            "blocking": False,
        })

    return diffs


def run_trajectory(
    trajectory_path: Path,
    gold_path: Path,
    case_output_dir: Path,
) -> dict[str, Any]:
    trajectory = load_json(trajectory_path)
    gold = load_json(gold_path)
    steps = {step["after_obs_id"]: step for step in gold.get("steps", [])}

    adjudicator = ShadowLifecycleAdjudicator()
    graph_state = initialize_shadow_graph_state()
    checkpoint_reports: list[dict[str, Any]] = []
    patches: list[dict[str, Any]] = []
    logs: list[dict[str, Any]] = []

    for seq, obs in enumerate(trajectory.get("observations", []), start=1):
        events = observation_to_event(obs, seq)
        for event in events:
            result = adjudicator.adjudicate_event(event, graph_state)
            patches.append(result.patch)
            logs.extend(result.log)
            for q in result.quarantine:
                graph_state["quarantine"].append(q)
            graph_state = apply_shadow_patch(graph_state, result.patch)

            if event["event_id"] in steps:
                bundle = build_shadow_bundle(graph_state)
                diffs = compare_step(steps[cp_event_id], graph_state, bundle)
                active_metrics = compute_set_metrics(
                    {n["claim_id"] for n in graph_state["nodes"].values() if n.get("status") == "active" and n.get("claim_id")},
                    set(steps[cp_event_id].get("expected_active_set", [])),
                )
                expected_invalid_for_metrics: set[str] = set()
                for inv in steps[cp_event_id].get("expected_invalidations", []):
                    if isinstance(inv, dict):
                        for cid in inv.get("dropped_claims", []):
                            expected_invalid_for_metrics.add(cid)
                    else:
                        expected_invalid_for_metrics.add(inv)
                invalid_metrics = compute_set_metrics(
                    {n["claim_id"] for n in graph_state["nodes"].values() if n.get("status") == "superseded" and n.get("claim_id")},
                    expected_invalid_for_metrics,
                )
                must_recall = compute_set_metrics(
                    {graph_state["nodes"][nid]["claim_id"] for nid in bundle.get("must_include", []) if nid in graph_state["nodes"] and graph_state["nodes"][nid].get("claim_id")},
                    set(steps[cp_event_id].get("must_include", [])),
                )["recall"]
                checkpoint_reports.append({
                    "checkpoint_id": f"cp_after_{cp_event_id}",
                    "after_obs_id": cp_event_id,
                    "graph_state_hash": graph_state_hash(graph_state),
                    "bundle_hash": bundle_hash(bundle),
                    "active_set_metrics": active_metrics,
                    "invalidation_metrics": invalid_metrics,
                    "must_include_recall": must_recall,
                    "diffs": diffs,
                    "diff_counts": _count_diffs(diffs),
                })


        # After all events for this obs processed, check obs-level checkpoint
        if obs.get("obs_id") and obs["obs_id"] in steps:
            bundle_obs = build_shadow_bundle(graph_state)
            diffs_obs = compare_step(steps[obs["obs_id"]], graph_state, bundle_obs)
            active_metrics_obs = compute_set_metrics(
                {n["claim_id"] for n in graph_state["nodes"].values() if n.get("status") == "active" and n.get("claim_id")},
                set(steps[obs["obs_id"]].get("expected_active_set", [])),
            )
            expected_invalid_obs: set[str] = set()
            for inv in steps[obs["obs_id"]].get("expected_invalidations", []):
                if isinstance(inv, dict):
                    for cid in inv.get("dropped_claims", []):
                        expected_invalid_obs.add(cid)
                else:
                    expected_invalid_obs.add(inv)
            invalid_metrics_obs = compute_set_metrics(
                {n["claim_id"] for n in graph_state["nodes"].values() if n.get("status") == "superseded" and n.get("claim_id")},
                expected_invalid_obs,
            )
            must_recall_obs = compute_set_metrics(
                {graph_state["nodes"][nid]["claim_id"] for nid in bundle_obs.get("must_include", []) if nid in graph_state["nodes"] and graph_state["nodes"][nid].get("claim_id")},
                set(steps[obs["obs_id"]].get("must_include", [])),
            )["recall"]
            checkpoint_reports.append({
                "checkpoint_id": f"cp_after_{obs['obs_id']}",
                "after_obs_id": obs["obs_id"],
                "graph_state_hash": graph_state_hash(graph_state),
                "bundle_hash": bundle_hash(bundle_obs),
                "active_set_metrics": active_metrics_obs,
                "invalidation_metrics": invalid_metrics_obs,
                "must_include_recall": must_recall_obs,
                "diffs": diffs_obs,
                "diff_counts": _count_diffs(diffs_obs),
            })

    final_bundle = build_shadow_bundle(graph_state)
    blocker_count = sum(cp["diff_counts"]["blocker"] for cp in checkpoint_reports)
    regression_count = sum(cp["diff_counts"]["regression"] for cp in checkpoint_reports)
    unexplained_count = sum(cp["diff_counts"].get("unexplained", 0) for cp in checkpoint_reports)
    must_include_recall = min((cp["must_include_recall"] for cp in checkpoint_reports), default=1.0)
    active_set_f1 = min((cp["active_set_metrics"]["f1"] for cp in checkpoint_reports), default=1.0)

    if blocker_count > 0 or regression_count > 0 or unexplained_count > 0:
        gate = "BLOCK"
    else:
        gate = "PASS"

    report = {
        "trajectory_id": trajectory["trajectory_id"],
        "case_output_dir": str(case_output_dir.relative_to(REPO_ROOT)),
        "trajectory_sha256": sha256_file(trajectory_path),
        "gold_sha256": sha256_file(gold_path),
        "checkpoint_count": len(checkpoint_reports),
        "checkpoints": checkpoint_reports,
        "aggregate": {
            "blocker_count": blocker_count,
            "regression_count": regression_count,
            "unexplained_count": unexplained_count,
            "min_must_include_recall": must_include_recall,
            "min_active_set_set_f1": active_set_f1,
        },
        "gate_decision": gate,
        "final_graph_state_hash": graph_state_hash(graph_state),
        "final_bundle_hash": bundle_hash(final_bundle),
        "patch_hash": sha256_text("\n".join(json.dumps(p, sort_keys=True) for p in patches)),
        "quarantine": graph_state["quarantine"],
    }

    write_shadow_json(case_output_dir / "config.json", {"runtime_fingerprint": runtime_fingerprint(), "trajectory_sha256": report["trajectory_sha256"], "gold_sha256": report["gold_sha256"]}, SHADOW_ROOT)
    write_shadow_json(case_output_dir / "shadow_graph_state.json", graph_state, SHADOW_ROOT)
    write_shadow_json(case_output_dir / "shadow_context_bundle.json", final_bundle, SHADOW_ROOT)
    write_shadow_json(case_output_dir / "patches.jsonl", patches, SHADOW_ROOT)
    write_shadow_json(case_output_dir / "diff_report.json", report, SHADOW_ROOT)
    write_shadow_json(case_output_dir / "log.jsonl", logs, SHADOW_ROOT)
    write_shadow_json(case_output_dir / "gate_decision.json", {"gate_decision": gate, "reason": _gate_reason(gate, blocker_count, regression_count, unexplained_count)}, SHADOW_ROOT)

    return report


def _count_diffs(diffs: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"blocker": 0, "regression": 0, "expected_schema_change": 0, "expected_improvement": 0, "unexplained": 0, "manual_adjudication": 0, "unexpected_supersedes": 0, "total": len(diffs)}
    for d in diffs:
        cls = d.get("classification", "unexplained")
        counts[cls] = counts.get(cls, 0) + 1
    return counts


def _gate_reason(gate: str, blockers: int, regressions: int, unexplained: int) -> str:
    if gate == "PASS":
        return "All checkpoints match gold; no blocker, regression, or unexplained diffs."
    reasons: list[str] = []
    if blockers > 0:
        reasons.append(f"{blockers} blocker diff(s)")
    if regressions > 0:
        reasons.append(f"{regressions} regression diff(s)")
    if unexplained > 0:
        reasons.append(f"{unexplained} unexplained diff(s)")
    return "; ".join(reasons)


def run_split(split_name: str) -> dict[str, Any]:
    manifest = load_json(FREEZE_MANIFEST_PATH)
    split = next((s for s in manifest["splits"] if s["name"] == split_name), None)
    if split is None:
        raise ValueError(f"Unknown split: {split_name}")

    now = datetime.now(timezone.utc)
    run_id = f"stage04b_{now.strftime('%Y%m%dT%H%M%S')}_{split_name}"
    split_dir = SHADOW_RUNS_DIR / split_name / run_id
    split_dir.mkdir(parents=True, exist_ok=True)

    case_reports: list[dict[str, Any]] = []
    for case in split["cases"]:
        traj_path = REPO_ROOT / case["trajectory_path"]
        gold_path = GOLD_DIR / f"{case['case_id']}.gold.json"
        case_dir = split_dir / case["case_id"]
        case_dir.mkdir(parents=True, exist_ok=True)
        print(f"  Running {case['case_id']} ...")
        report = run_trajectory(traj_path, gold_path, case_dir)
        # Determinism check: run again and compare hashes
        report2 = run_trajectory(traj_path, gold_path, case_dir)
        report["deterministic"] = report["final_graph_state_hash"] == report2["final_graph_state_hash"] and report["patch_hash"] == report2["patch_hash"]
        if not report["deterministic"]:
            report["gate_decision"] = "BLOCK"
            (case_dir / "gate_decision.json").write_text(
                json.dumps({"gate_decision": "BLOCK", "reason": "determinism check failed"}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        case_reports.append(report)

    all_pass = all(r["gate_decision"] == "PASS" for r in case_reports)
    any_det_fail = any(not r.get("deterministic", True) for r in case_reports)
    min_must_include = min(r["aggregate"]["min_must_include_recall"] for r in case_reports)
    min_active_f1 = min(r["aggregate"]["min_active_set_set_f1"] for r in case_reports)

    summary = {
        "split": split_name,
        "run_id": run_id,
        "run_dir": str(split_dir.relative_to(REPO_ROOT)),
        "generated_at": now.isoformat(),
        "case_count": len(case_reports),
        "cases": case_reports,
        "split_gate_decision": "PASS" if all_pass and not any_det_fail else "BLOCK",
        "aggregate": {
            "min_must_include_recall": min_must_include,
            "min_active_set_set_f1": min_active_f1,
            "total_blockers": sum(r["aggregate"]["blocker_count"] for r in case_reports),
            "total_regressions": sum(r["aggregate"]["regression_count"] for r in case_reports),
            "total_unexplained": sum(r["aggregate"]["unexplained_count"] for r in case_reports),
        },
        "freeze_manifest_sha256": sha256_file(FREEZE_MANIFEST_PATH),
        "runtime_fingerprint": runtime_fingerprint(),
    }

    summary_path = split_dir / "split_summary.json"
    write_shadow_json(summary_path, summary, SHADOW_ROOT)
    print(f"Wrote split summary to {summary_path}")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage04-B frozen benchmark shadow evaluation")
    parser.add_argument("--split", required=True, choices=["development", "regression", "blind_holdout", "adversarial"])
    args = parser.parse_args()

    print(f"Running Stage04-B shadow evaluation for split: {args.split}")
    summary = run_split(args.split)
    print(f"Split gate decision: {summary['split_gate_decision']}")
    print(f"  min must_include_recall: {summary['aggregate']['min_must_include_recall']}")
    print(f"  min active_set_set_f1: {summary['aggregate']['min_active_set_set_f1']}")
    print(f"  total blockers: {summary['aggregate']['total_blockers']}")
    print(f"  total regressions: {summary['aggregate']['total_regressions']}")
    return 0 if summary["split_gate_decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
