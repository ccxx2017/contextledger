#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fixture semantic replay runner.

Actually executes shadow adjudication + shadow compiler and compares each
checkpoint against the fixture expectations.
"""
from __future__ import annotations

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

from shadow_lifecycle_adjudicator import ShadowLifecycleAdjudicator, AdjudicationResult
from shadow_compiler import (
    initialize_shadow_graph_state,
    apply_shadow_patch,
    graph_state_hash,
    write_shadow_json,
    ShadowIsolationError,
)
from shadow_bundle_builder import build_shadow_bundle, bundle_hash

FIXTURES_DIR = REPO_ROOT / "graph" / "projects" / "abu_modern" / "fixtures" / "lifecycle" / "fixtures"
SHADOW_RUNS_DIR = SHADOW_ROOT / "runs"
SHADOW_SCRIPTS = [
    SCRIPT_DIR / "shadow_lifecycle_adjudicator.py",
    SCRIPT_DIR / "shadow_compiler.py",
    SCRIPT_DIR / "shadow_bundle_builder.py",
    SCRIPT_DIR / "fixture_replay_runner.py",
]
CONTRACTS = [
    REPO_ROOT / "contracts" / "03_graph_schema.md",
    REPO_ROOT / "contracts" / "05_phase1_lifecycle_schema.md",
]

EXPECTED_NODE_SEMANTICS: dict[str, dict[str, dict[str, Any]]] = {
    "lc_same_source_progression": {
        "n_tkt_001_v1": {"entity_ref": "TKT-001", "lifecycle_ref": "lc_tkt_001", "lifecycle_seq": 1, "claim_id": "tkt.001.v1"},
        "n_tkt_001_v2": {"entity_ref": "TKT-001", "lifecycle_ref": "lc_tkt_001", "lifecycle_seq": 2, "claim_id": "tkt.001.v2"},
    },
    "lc_diff_source_conflict": {
        "n_svc_a_probe": {"entity_ref": "SVC-A", "lifecycle_ref": "lc_svc_a", "lifecycle_seq": 1, "state": "not_ready", "claim_id": "svc.a.probe"},
        "n_svc_a_user": {"entity_ref": "SVC-A", "lifecycle_ref": "lc_svc_a", "lifecycle_seq": 2, "state": "ready", "claim_id": "svc.a.user"},
    },
    "lc_multi_claim_partial": {
        "n_mc_policy_v1": {"entity_ref": "POL-GW-001", "lifecycle_ref": "lc_pol_gw_001", "lifecycle_seq": 1, "claim_id": "mc.policy.v1"},
        "n_mc_policy_v2": {"entity_ref": "POL-GW-001", "lifecycle_ref": "lc_pol_gw_001", "lifecycle_seq": 2, "claim_id": "mc.policy.v2"},
    },
    "lc_two_lifecycles_no_kill": {
        "n_deploy": {"entity_ref": "svc_abu_payment", "lifecycle_ref": "lc_deploy_prod_2026_07", "state": "deployed"},
        "n_ticket_open": {"entity_ref": "svc_abu_payment", "lifecycle_ref": "lc_ticket_005b", "state": "open"},
    },
    "lc_revival": {
        "n_exp_v1_active": {"entity_ref": "exp_quant_models", "lifecycle_ref": "lc_quant_research", "lifecycle_seq": 1, "state": "in_progress"},
        "n_exp_v1_cancelled": {"entity_ref": "exp_quant_models", "lifecycle_ref": "lc_quant_research", "lifecycle_seq": 2, "state": "cancelled"},
        "n_exp_v2_revived": {"entity_ref": "exp_quant_models", "lifecycle_ref": "lc_quant_research", "lifecycle_seq": 3, "state": "in_progress"},
    },
    "lc_provenance_conflict": {
        "n_policy_two_person": {"entity_ref": "POL-2026-003", "lifecycle_ref": "lc_policy_003", "source": "policy_team", "state": "implemented"},
        "n_policy_waived": {"entity_ref": "POL-2026-003", "lifecycle_ref": "lc_policy_003", "source": "audit_probe", "state": "implemented"},
    },
    "lc_late_arrival": {
        "n_price_band_a": {"entity_ref": "SKU-2026-A", "lifecycle_ref": "lc_sku_a", "lifecycle_seq": 1},
        "n_price_band_b": {"entity_ref": "SKU-2026-A", "lifecycle_ref": "lc_sku_a", "lifecycle_seq": 2},
    },
    "lc_legacy_migration": {
        "n_legacy_fact": {"entity_ref": "LEG-001", "lifecycle_ref": None, "source": "legacy_import"},
        "n_updated_fact": {"entity_ref": "LEG-001", "lifecycle_ref": "lc_leg_001", "source": "pipeline"},
    },
    "lc_alias_abstain": {
        "n_tkt_005b_prod": {"entity_ref": "TKT-2026-005B", "lifecycle_ref": "lc_tkt_005b_prod", "source": "ticketing"},
    },
    "lc_sequence_collision": {
        "n_feat_scoped": {"entity_ref": "FEAT-2026-007", "lifecycle_ref": "lc_feat_007", "lifecycle_seq": 1},
        "n_feat_started": {"entity_ref": "FEAT-2026-007", "lifecycle_ref": "lc_feat_007", "lifecycle_seq": 2},
    },
    "lc_replay_determinism": {
        "n_det_a": {"entity_ref": "DET-001", "lifecycle_ref": "lc_det_001", "lifecycle_seq": 1},
        "n_det_b": {"entity_ref": "DET-001", "lifecycle_ref": "lc_det_001", "lifecycle_seq": 2},
    },
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


def semantic_node_key(node: dict[str, Any]) -> str:
    return "|".join([
        str(node.get("entity_ref") or ""),
        str(node.get("lifecycle_ref") or ""),
        str(node.get("state") or ""),
        (node.get("content") or "")[:40].lower().strip(),
    ])


def match_expected_node(
    fixture_id: str,
    expected_id: str,
    actual_nodes: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Find an actual node that semantically matches the expected symbolic ID."""
    for node in actual_nodes:
        if node.get("node_id") == expected_id:
            return node

    semantics = EXPECTED_NODE_SEMANTICS.get(fixture_id, {}).get(expected_id)
    if semantics:
        for node in actual_nodes:
            match = True
            for key, value in semantics.items():
                if node.get(key) != value:
                    match = False
                    break
            if match:
                return node
        return None

    expected_lower = expected_id.lower().replace("n_", "")
    for node in actual_nodes:
        content = (node.get("content") or "").lower()
        state = (node.get("state") or "").lower()
        if expected_lower in content or expected_lower in state:
            return node
    return None


def compare_checkpoint(
    fixture_id: str,
    checkpoint: dict[str, Any],
    graph_state: dict[str, Any],
    bundle: dict[str, Any],
) -> list[dict[str, Any]]:
    nodes = graph_state.get("nodes", {})
    if isinstance(nodes, list):
        nodes = {n["node_id"]: n for n in nodes if isinstance(n, dict)}

    actual_active = [n for n in nodes.values() if n.get("status") == "active"]
    actual_superseded = [n for n in nodes.values() if n.get("status") == "superseded"]
    actual_pending: list[dict[str, Any]] = []
    actual_quarantine = graph_state.get("quarantine", [])
    actual_must_include = set(bundle.get("must_include", []))
    actual_relations = graph_state.get("edges", [])

    diffs: list[dict[str, Any]] = []

    def add_diff(kind: str, expected: Any, actual: Any, classification: str, rationale: str, blocking: bool) -> None:
        diffs.append({
            "kind": kind,
            "expected": expected,
            "actual": actual,
            "classification": classification,
            "rationale": rationale,
            "blocking": blocking,
        })

    expected_active = set(checkpoint.get("active_nodes", []))
    matched_active: set[str] = set()
    for eid in expected_active:
        match = match_expected_node(fixture_id, eid, actual_active)
        if match:
            matched_active.add(match["node_id"])
        else:
            add_diff("active_set", eid, None, "regression", f"Expected active node '{eid}' not found", True)

    for node in actual_active:
        if node["node_id"] not in matched_active:
            add_diff("active_set", None, node["node_id"], "expected_schema_change", f"Unexpected active node {node['node_id']}", False)

    expected_superseded = set(checkpoint.get("superseded_nodes", []))
    matched_superseded: set[str] = set()
    for eid in expected_superseded:
        match = match_expected_node(fixture_id, eid, actual_superseded)
        if match:
            matched_superseded.add(match["node_id"])
        else:
            add_diff("superseded_set", eid, None, "regression", f"Expected superseded node '{eid}' not found", True)

    expected_pending = set(checkpoint.get("pending_nodes", []))
    for eid in expected_pending:
        if eid and eid not in [n.get("node_id") for n in actual_pending]:
            add_diff("pending_set", eid, None, "unexplained", f"Expected pending node '{eid}' not modeled", False)

    expected_relations = checkpoint.get("relations", [])
    for er in expected_relations:
        rtype = er.get("relation_type")
        src_expected = er.get("source")
        tgt_expected = er.get("target")
        src_match = match_expected_node(fixture_id, src_expected, list(nodes.values()))
        tgt_match = match_expected_node(fixture_id, tgt_expected, list(nodes.values()))
        if not src_match or not tgt_match:
            add_diff("relation", er, None, "regression", f"Cannot match relation endpoints for {er}", True)
            continue
        found = any(
            e.get("relation") == rtype and e.get("source") == src_match["node_id"] and e.get("target") == tgt_match["node_id"]
            for e in actual_relations
        )
        if not found:
            add_diff("relation", er, None, "regression", f"Expected relation {rtype} from {src_expected} to {tgt_expected}", True)

    expected_quarantine = {q["event_id"]: q["reason"] for q in checkpoint.get("quarantine", [])}
    actual_quarantine_map = {q["event_id"]: q["reason"] for q in actual_quarantine}
    for eid, reason in expected_quarantine.items():
        if eid not in actual_quarantine_map:
            add_diff("quarantine", {eid: reason}, None, "regression", f"Expected quarantine for {eid} missing", True)
    for eid, reason in actual_quarantine_map.items():
        if eid not in expected_quarantine:
            add_diff("quarantine", None, {eid: reason}, "expected_improvement", f"Shadow quarantined {eid}: {reason}", False)

    expected_must_include = set(checkpoint.get("assembler_must_include", []))
    matched_must: set[str] = set()
    for eid in expected_must_include:
        match = match_expected_node(fixture_id, eid, list(nodes.values()))
        if match and match["node_id"] in actual_must_include:
            matched_must.add(match["node_id"])
        else:
            add_diff("must_include", eid, None, "blocker", f"Expected must_include '{eid}' missing from bundle", True)

    return diffs


def replay_fixture(fixture: dict[str, Any], run_dir: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    adjudicator = ShadowLifecycleAdjudicator()
    graph_state = initialize_shadow_graph_state()
    event_stream = fixture["input"]["event_stream"]
    checkpoints = {cp["after_event_id"]: cp for cp in fixture["expected"]["checkpoints"]}
    checkpoint_reports: list[dict[str, Any]] = []
    patches: list[dict[str, Any]] = []
    logs: list[dict[str, Any]] = []

    for event in event_stream:
        result = adjudicator.adjudicate_event(event, graph_state)
        patches.append(result.patch)
        logs.extend(result.log)
        for q in result.quarantine:
            graph_state["quarantine"].append(q)
        graph_state = apply_shadow_patch(graph_state, result.patch)

        if event["event_id"] in checkpoints:
            bundle = build_shadow_bundle(graph_state)
            diffs = compare_checkpoint(fixture["fixture_id"], checkpoints[event["event_id"]], graph_state, bundle)
            checkpoint_reports.append({
                "checkpoint_id": checkpoints[event["event_id"]]["checkpoint_id"],
                "after_event_id": event["event_id"],
                "graph_state_hash": graph_state_hash(graph_state),
                "bundle_hash": bundle_hash(bundle),
                "diffs": diffs,
                "diff_counts": _count_diffs(diffs),
            })

    final_bundle = build_shadow_bundle(graph_state)
    final_report = {
        "fixture_id": fixture["fixture_id"],
        "category": fixture["category"],
        "run_dir": str(run_dir.relative_to(REPO_ROOT)),
        "event_count": len(event_stream),
        "checkpoint_count": len(checkpoint_reports),
        "checkpoints": checkpoint_reports,
        "final_graph_state_hash": graph_state_hash(graph_state),
        "final_bundle_hash": bundle_hash(final_bundle),
        "patch_hash": sha256_text("\n".join(json.dumps(p, sort_keys=True) for p in patches)),
        "quarantine": graph_state["quarantine"],
    }
    return final_report, graph_state, final_bundle, patches, logs


def _count_diffs(diffs: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"expected_improvement": 0, "expected_schema_change": 0, "regression": 0, "unexplained": 0, "blocker": 0, "total": len(diffs)}
    for d in diffs:
        cls = d.get("classification", "unexplained")
        counts[cls] = counts.get(cls, 0) + 1
        if d.get("blocking"):
            counts["blocker"] += 1
    return counts


def run_fixture_file(fixture_path: Path) -> dict[str, Any]:
    fixture = load_json(fixture_path)
    now = datetime.now(timezone.utc)
    run_id = f"stage04a_{now.strftime('%Y%m%dT%H%M%S')}_{fixture['fixture_id']}"
    run_dir = SHADOW_RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "run_id": run_id,
        "generated_at": now.isoformat(),
        "fixture_path": str(fixture_path.relative_to(REPO_ROOT)),
        "fixture_sha256": sha256_file(fixture_path),
        "runtime_fingerprint": runtime_fingerprint(),
    }

    report1, graph_state1, bundle1, patches1, logs1 = replay_fixture(fixture, run_dir)
    report2, graph_state2, bundle2, patches2, logs2 = replay_fixture(fixture, run_dir)
    deterministic = (
        report1["final_graph_state_hash"] == report2["final_graph_state_hash"]
        and report1["final_bundle_hash"] == report2["final_bundle_hash"]
        and report1["patch_hash"] == report2["patch_hash"]
    )

    config["deterministic"] = deterministic
    config["run1"] = report1
    config["run2"] = report2

    total_blockers = sum(cp["diff_counts"]["blocker"] for cp in report1["checkpoints"])
    total_regressions = sum(cp["diff_counts"]["regression"] for cp in report1["checkpoints"])
    total_unexplained = sum(cp["diff_counts"]["unexplained"] for cp in report1["checkpoints"])
    if not deterministic:
        gate = "BLOCK"
    elif total_blockers > 0 or total_regressions > 0 or total_unexplained > 0:
        gate = "BLOCK"
    else:
        gate = "PASS"
    config["gate_decision"] = gate

    write_shadow_json(run_dir / "config.json", config, SHADOW_ROOT)
    write_shadow_json(run_dir / "shadow_graph_state.json", graph_state1, SHADOW_ROOT)
    write_shadow_json(run_dir / "shadow_context_bundle.json", bundle1, SHADOW_ROOT)
    write_shadow_json(run_dir / "patches.jsonl", patches1, SHADOW_ROOT)
    write_shadow_json(run_dir / "diff_report.json", report1, SHADOW_ROOT)
    write_shadow_json(run_dir / "log.jsonl", logs1, SHADOW_ROOT)
    write_shadow_json(run_dir / "gate_decision.json", {"gate_decision": gate, "reason": _gate_reason(gate, total_blockers, total_regressions, total_unexplained, deterministic)}, SHADOW_ROOT)

    return config


def _gate_reason(gate: str, blockers: int, regressions: int, unexplained: int, deterministic: bool) -> str:
    if gate == "PASS":
        return "All checkpoints match; deterministic replay confirmed."
    reasons: list[str] = []
    if not deterministic:
        reasons.append("determinism check failed")
    if blockers > 0:
        reasons.append(f"{blockers} blocker diff(s)")
    if regressions > 0:
        reasons.append(f"{regressions} regression diff(s)")
    if unexplained > 0:
        reasons.append(f"{unexplained} unexplained diff(s)")
    return "; ".join(reasons)


def main() -> int:
    fixture_paths = sorted(FIXTURES_DIR.glob("lc_*.json"))
    if not fixture_paths:
        print(f"No fixtures found in {FIXTURES_DIR}")
        return 1

    summaries: list[dict[str, Any]] = []
    for fixture_path in fixture_paths:
        print(f"Running {fixture_path.name} ...")
        summary = run_fixture_file(fixture_path)
        summaries.append({
            "fixture_id": summary["run1"]["fixture_id"],
            "gate_decision": summary["gate_decision"],
            "deterministic": summary["deterministic"],
            "run_dir": summary["run1"]["run_dir"],
        })
        print(f"  gate={summary['gate_decision']} deterministic={summary['deterministic']}")

    summary_path = SHADOW_RUNS_DIR / "stage04a_latest_summary.json"
    write_shadow_json(summary_path, {"summaries": summaries}, SHADOW_ROOT)
    print(f"Wrote summary to {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
