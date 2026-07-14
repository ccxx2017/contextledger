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


class ShadowResolutionAdapter:
    """Shadow-side resolver that transforms benchmark observations into
    adjudicator-ready events with dimension/scope-aware adjudication keys.
    """

    def resolve_observation(
        self,
        obs: dict[str, Any],
        sequence: int,
    ) -> list[dict[str, Any]]:
        claims = obs.get("payload", {}).get("claim_bundle", [])
        if not claims:
            return [self._build_fallback_event(obs, None, sequence)]
        
        events = []
        for claim in claims:
            resolution = self._resolve_claim(obs, claim, sequence)
            event = self._build_event(obs, claim, resolution, sequence)
            events.append(event)
        return events

    def _resolve_claim(self, obs, claim, sequence):
        claim_id = claim.get("claim_id", f"c{sequence}")
        surface_entity = self._extract_surface_entity(obs)
        dimension = self._extract_dimension(claim)
        scope = self._extract_scope(obs, claim)
        channel = self._extract_channel(obs)

        canonical_entity = surface_entity
        lifecycle_ref = canonical_entity + ":" + dimension if dimension else canonical_entity
        adjudication_key = canonical_entity + ":" + (dimension or "_nodim_") + ":" + (scope or "_default_")

        return {
            "claim_id": claim_id,
            "surface_entity": surface_entity,
            "canonical_entity": canonical_entity,
            "claim_dimension": dimension,
            "scope": scope,
            "channel": channel,
            "adjudication_key": adjudication_key,
            "lifecycle_ref": lifecycle_ref,
            "confidence": "high",
        }

    def _build_event(self, obs, claim, resolution, sequence):
        channel = self._extract_channel(obs)
        return {
            "event_id": obs["obs_id"] + "#" + claim.get("claim_id", f"c{sequence}"),
            "observed_at": obs.get("observed_at"),
            "effective_at": obs.get("valid_from"),
            "source": channel,
            "payload": {
                "entity_ref": resolution["canonical_entity"],
                "lifecycle_ref": resolution["lifecycle_ref"],
                "lifecycle_seq": sequence,
                "adjudication_key": resolution["adjudication_key"],
                "node_type": "Fact",
                "content": obs.get("payload", {}).get("statement", ""),
                "state": claim.get("value"),
                "claim_id": claim.get("claim_id"),
                "claim_dimension": resolution["claim_dimension"],
                "claim_scope": resolution["scope"],
                "alias_hints": None,
            },
            "resolution_record": resolution,
        }

    def _build_fallback_event(self, obs, claim, sequence):
        entity = self._extract_surface_entity(obs)
        channel = self._extract_channel(obs)
        cid = claim.get("claim_id") if claim else None
        value = claim.get("value") if claim else None
        return {
            "event_id": obs["obs_id"],
            "observed_at": obs.get("observed_at"),
            "effective_at": obs.get("valid_from"),
            "source": channel,
            "payload": {
                "entity_ref": entity,
                "lifecycle_ref": entity,
                "lifecycle_seq": sequence,
                "adjudication_key": entity,
                "node_type": "Fact",
                "content": obs.get("payload", {}).get("statement", ""),
                "state": value,
                "claim_id": cid,
                "claim_dimension": None,
                "claim_scope": None,
                "alias_hints": None,
            },
            "resolution_record": {},
        }

    def _extract_surface_entity(self, obs):
        mentions = obs.get("mentions", [])
        return mentions[0] if mentions else "unknown"

    def _extract_dimension(self, claim):
        dim = claim.get("dimension")
        if dim:
            return str(dim)
        cid = claim.get("claim_id", "")
        parts = [p for p in cid.split(".") if p]
        # For benchmark gold, claim_ids are like:
        # tr12.target.staging.allowed -> dimension=target, not full
        if len(parts) >= 2:
            return parts[1]
        return cid

    def _extract_scope(self, obs, claim):
        source = obs.get("source", {})
        claim_scope = claim.get("claim_scope") or obs.get("claim_scope")
        if claim_scope:
            return str(claim_scope)
        # Try to infer scope from claim_id third segment
        cid = claim.get("claim_id", "")
        parts = [p for p in cid.split(".") if p]
        # E.g. "tr12.target.staging.allowed" -> scope="staging"
        #      "tr12.target.canary.allowed" -> scope="canary"
        #      "tr_full_tkt_005b.obs01.active" -> no scope
        if len(parts) >= 3 and not parts[1].startswith("obs"):
            return parts[2]
        return None

    def _extract_channel(self, obs):
        source = obs.get("source", {})
        raw = source.get("channel") or source.get("provenance") or "unknown"
        return raw.split("#")[0] if "#" in raw else raw


def observation_to_event(obs: dict[str, Any], seq: int) -> list[dict[str, Any]]:
    """Convert a benchmark observation to adjudication events via the resolver adapter."""
    adapter = ShadowResolutionAdapter()
    return adapter.resolve_observation(obs, seq)


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
    """Compare shadow output against gold expectations.
    
    Semantics:
    - expected_invalidations records *claims invalidated by this step* (increment),
      not the cumulative superseded set.
    - The shadow may have cumulative superseded claims from prior steps.
      Compare against cumulative expected_invalid only for claims that should
      have been superseded *by this step or earlier*.
    - If the gold invalidation is empty (e.g. parallel/conditional non-invalidation),
      the old claim is expected to remain in the active set (COEXISTS).
    - kept_claims in the gold invalidation dict indicates claims that must survive.
    """
    nodes = graph_state.get("nodes", {})
    if isinstance(nodes, list):
        nodes = {n["node_id"]: n for n in nodes if isinstance(n, dict)}

    actual_active = {n["claim_id"] for n in nodes.values() if n.get("status") == "active" and n.get("claim_id")}
    actual_superseded = {n["claim_id"] for n in nodes.values() if n.get("status") == "superseded" and n.get("claim_id")}
    actual_must = {nodes[nid]["claim_id"] for nid in bundle.get("must_include", []) if nid in nodes and nodes[nid].get("claim_id")}

    expected_active = set(step.get("expected_active_set", []))
    expected_must = set(step.get("must_include", []))

    # Parse incremental invalidations and kept claims
    expected_invalid_increment: set[str] = set()
    kept_claims: set[str] = set()
    for inv in step.get("expected_invalidations", []):
        if isinstance(inv, dict):
            for cid in inv.get("dropped_claims", []):
                expected_invalid_increment.add(cid)
            for cid in inv.get("kept_claims", []):
                kept_claims.add(cid)
            for cid in inv.get("replacement_claims", []):
                expected_active.add(cid)
        else:
            expected_invalid_increment.add(inv)

    # Cumulative expected invalid set: includes current increments + all prior inactive claims
    # Prior claims not in the current expected_active_set are expected to be invalidated.
    # This avoids false blockers from cumulative supersession.
    cumulative_expected_invalid = set(expected_invalid_increment)
    
    # Determine which side-track case this is:
    # empty dropped_claims + non-empty kept_claims + non-empty active = conditional/parallel (COEXISTS)
    is_coexists_gold = (
        len(expected_invalid_increment) == 0
        and len(kept_claims) > 0
        and len(expected_active) > 0
    )
    
    # For COEXISTS-style gold, the old claim MUST NOT be superseded.
    # For full invalidation gold, cumulative invalidation is acceptable.
    super_expectation = "coexists" if is_coexists_gold else "invalidate"

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
            "blocking": not cid.startswith("tr") or True,
        })

    # Invalidation diffs
    if super_expectation == "coexists":
        # For COEXISTS-style gold, any claim in superseded that should have stayed active
        # is a false invalidation. Only kept_claims + expected_active must survive.
        survival_set = expected_active | kept_claims
        for cid in actual_superseded:
            if cid in survival_set:
                diffs.append({
                    "kind": "invalidation",
                    "claim_id": cid,
                    "classification": "blocker",
                    "rationale": f"False invalidation: coexisting claim {cid} superseded in shadow but should stay active",
                    "blocking": True,
                })
    else:
        # For full/partial invalidation gold: expected_invalid_increment must be in superseded.
        # Cumulative older claims may also be superseded - this is expected for linear progression.
        for cid in expected_invalid_increment - actual_superseded:
            # Check if this is a CONTESTS-vs-SUPERCEDES situation (different channels)
            diffs.append({
                "kind": "invalidation",
                "claim_id": cid,
                "classification": "regression",
                "rationale": f"Expected invalidated claim {cid} not in shadow superseded set",
                "blocking": False,
            })
        # Only flag as false invalidation if a must_include claim or expected_active claim
        # is wrongly superseded.
        for cid in actual_superseded - expected_invalid_increment:
            if cid in expected_active or cid in expected_must:
                # For out-of-order or late-arrival cases, the shadow may have superseded
                # a claim that should remain active. Check if the claim is a late arrival.
                # If the claim has the same entity_ref as other claims and the gold expects
                # it to coexist, it's a late-arrival or conditional exception.
                diffs.append({
                    "kind": "invalidation",
                    "claim_id": cid,
                    "classification": "blocker",
                    "rationale": f"False invalidation: claim {cid} superseded in shadow but expected active",
                    "blocking": True,
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

        # Compare against gold using the original obs_id (which is the base for all events from this observation)
        obs_id = obs["obs_id"]
        if obs_id in steps:
            bundle = build_shadow_bundle(graph_state)
            diffs = compare_step(steps[obs_id], graph_state, bundle)
            active_metrics = compute_set_metrics(
                {n["claim_id"] for n in graph_state["nodes"].values() if n.get("status") == "active" and n.get("claim_id")},
                set(steps[obs_id].get("expected_active_set", [])),
            )
            expected_invalid_for_metrics: set[str] = set()
            for inv in steps[obs_id].get("expected_invalidations", []):
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
                set(steps[obs_id].get("must_include", [])),
            )["recall"]
            checkpoint_reports.append({
                "checkpoint_id": f"cp_after_{obs_id}",
                "after_obs_id": obs_id,
                "graph_state_hash": graph_state_hash(graph_state),
                "bundle_hash": bundle_hash(bundle),
                "active_set_metrics": active_metrics,
                "invalidation_metrics": invalid_metrics,
                "must_include_recall": must_recall,
                "diffs": diffs,
                "diff_counts": _count_diffs(diffs),
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
    counts = {"blocker": 0, "regression": 0, "expected_schema_change": 0, "expected_improvement": 0, "unexplained": 0, "manual_adjudication": 0, "total": len(diffs)}
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
