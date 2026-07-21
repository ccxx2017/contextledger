#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Frozen benchmark shadow evaluation runner (Stage04-B / Stage04-C).

Runs phase05_v3 benchmark trajectories through the shadow lifecycle
adjudication chain and compares outputs against gold annotations.

Stage04-C: Relation-aware comparator v2 — truth table enforcement for
SUPERCEDES/COEXISTS/CONTESTS/REVIVES classification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import unittest
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


# ─── Relation-aware comparator v2 (Stage04-C) ───────────────────────────────

# Gold relation kind mapping from expected_invalidations[].kind
_KIND_TO_GOLD_RELATION = {
    "full": "SUPERCEDES",
    "revival": "REVIVES",
    "partial": "SUPERCEDES",
    "conditional": "SUPERCEDES",
}


def _extract_gold_relations(step: dict[str, Any]) -> dict[str, str]:
    """Extract gold expected relation per dropped claim.

    Returns {claim_id: "SUPERCEDES"|"REVIVES"|"COEXISTS"|"UNRELATED"}
    """
    gold_relations: dict[str, str] = {}
    for inv in step.get("expected_invalidations", []):
        if isinstance(inv, dict):
            kind = inv.get("kind", "")
            gold_rel = _KIND_TO_GOLD_RELATION.get(kind, "SUPERCEDES") if kind else "SUPERCEDES"
            for cid in inv.get("dropped_claims", []):
                gold_relations[cid] = gold_rel
            for cid in inv.get("replacement_claims", []):
                gold_relations[cid] = gold_rel
        else:
            gold_relations[str(inv)] = "SUPERCEDES"
    return gold_relations


def _extract_shadow_relations(graph_state: dict[str, Any]) -> dict[str, tuple[str, str, str]]:
    """Extract shadow relations per node pair.

    Returns {source_claim_id: (target_claim_id, relation, source_node_id)}
    Also populates reverse: target_claim_id -> (source_claim_id, relation, target_node_id)
    """
    nodes = graph_state.get("nodes", {})
    if isinstance(nodes, list):
        nodes = {n["node_id"]: n for n in nodes if isinstance(n, dict)}

    relations: dict[str, tuple[str, str, str]] = {}
    for edge in graph_state.get("edges", []):
        src = edge.get("source", "")
        tgt = edge.get("target", "")
        rel = edge.get("relation", "")
        # Normalize relation to uppercase for truth table matching
        # Handle both "SUPERCEDES" and "SUPERSEDES" (common typo in shadow compiler)
        rel_upper = rel.upper() if rel else "UNRELATED"
        if rel_upper == "SUPERSEDES":
            rel_upper = "SUPERCEDES"
        src_node = nodes.get(src, {})
        tgt_node = nodes.get(tgt, {})
        src_cid = src_node.get("claim_id") if isinstance(src_node, dict) else None
        tgt_cid = tgt_node.get("claim_id") if isinstance(tgt_node, dict) else None
        if src_cid and tgt_cid:
            relations[src_cid] = (tgt_cid, rel_upper, src)
            # Also store reverse direction
            relations[tgt_cid] = (src_cid, rel_upper, tgt)
    return relations


def _is_claim_involved_in_contest(shadow_relations: dict, claim_id: str) -> bool:
    """Check if a claim is involved in any CONTESTS edge."""
    for k, v in shadow_relations.items():
        rel_upper = v[1].upper() if v[1] else ""
        if k == claim_id and rel_upper == "CONTESTS":
            return True
        if v[0] == claim_id and rel_upper == "CONTESTS":
            return True
    return False


def _classify_relation_diff(
    gold_relation: str,
    shadow_relation: str,
    expected_invalidation: bool,
    actual_invalidation: bool,
    expected_coexist: bool,
    actual_coexist: bool,
) -> str:
    """Apply the relation-aware truth table.

    Truth table from Stage04-C instructions (lines 5776-5784):
    | Gold expectation | Shadow relation | Default classification |
    | SUPERCEDES       | SUPERCEDES      | match (expected_improvement) |
    | COEXISTS         | COEXISTS        | match (OK) |
    | CONTESTS         | CONTESTS + R01 safe | manual-safe |
    | SUPERCEDES       | CONTESTS        | manual_adjudication (not auto-pass, not auto-fail) |
    | COEXISTS         | SUPERCEDES      | unexpected invalidation / regression |
    | CONTESTS         | SUPERCEDES      | blocker or ordinary regression |
    | Unspecified      | NEW SUPERCEDES  | unexpected supersede / false positive |
    """
    # Case 1: Gold expects SUPERCEDES, shadow gives SUPERCEDES → match
    if gold_relation == "SUPERCEDES" and shadow_relation == "SUPERCEDES":
        return "expected_improvement"

    # Case 2: Gold expects SUPERCEDES, shadow gives CONTESTS
    # CONTESTS means both claims stay active — gold wants one invalidated.
    # This is an ordinary regression: the shadow adjudicator produced the wrong
    # relation.  R01 bundle-safety is recorded separately as metadata and MUST
    # NOT override this classification.
    if gold_relation == "SUPERCEDES" and shadow_relation == "CONTESTS":
        return "ordinary_regression"

    # Case 3: Gold expects SUPERCEDES, shadow gives nothing (no relation)
    if gold_relation == "SUPERCEDES" and shadow_relation == "UNRELATED":
        return "regression"

    # Case 4: Gold expects COEXISTS (no invalidation), shadow gives SUPERCEDES
    if gold_relation == "COEXISTS" and shadow_relation == "SUPERCEDES":
        return "regression"  # false invalidation

    # Case 5: Gold expects COEXISTS, shadow gives CONTESTS
    if gold_relation == "COEXISTS" and shadow_relation == "CONTESTS":
        return "manual_adjudication"  # both active, different provenance

    # Case 6: Gold expects COEXISTS, shadow gives nothing
    if gold_relation == "COEXISTS" and shadow_relation == "UNRELATED":
        return "expected_schema_change"  # no relation needed

    # Case 7: Gold expects REVIVES, shadow gives REVIVES
    if gold_relation == "REVIVES" and shadow_relation == "REVIVES":
        return "expected_improvement"

    # Case 8: Gold expects REVIVES, shadow gives SUPERCEDES
    if gold_relation == "REVIVES" and shadow_relation == "SUPERCEDES":
        return "expected_schema_change"  # revival expressed as supersede in shadow

    # Case 9: Gold expects REVIVES, shadow gives CONTESTS
    if gold_relation == "REVIVES" and shadow_relation == "CONTESTS":
        return "regression"

    # Default fallback
    return "unexplained"


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

    # Extract gold expected relations and shadow relations
    gold_relations = _extract_gold_relations(step)
    shadow_relations = _extract_shadow_relations(graph_state)

    diffs: list[dict[str, Any]] = []

    # ─── Active-set diffs (relation-aware) ──────────────────────────────
    for cid in expected_active - actual_active:
        gold_rel = gold_relations.get(cid, "SUPERCEDES")
        # Check shadow relation for this claim
        shadow_rel = "UNRELATED"
        for k, v in shadow_relations.items():
            if k == cid:
                shadow_rel = v[1]
                break
        cls = _classify_relation_diff(gold_rel, shadow_rel, True, False, False, False)
        diff_entry = {
            "kind": "active_set",
            "claim_id": cid,
            "classification": cls,
            "rationale": f"Expected active claim {cid} not in shadow active set (gold={gold_rel}, shadow={shadow_rel})",
            "blocking": cid in expected_must,
            "gold_relation": gold_rel,
            "shadow_relation": shadow_rel,
        }
        # Attach R01 safety metadata without overriding relation classification
        is_contested = _is_claim_involved_in_contest(shadow_relations, cid)
        if is_contested:
            diff_entry["safety_disposition"] = "R01_checked"
            diff_entry["manual_review_metadata"] = "CONTESTS relation detected — verify adjudication correctness"
        diffs.append(diff_entry)

    for cid in actual_active - expected_active:
        gold_rel = gold_relations.get(cid, "COEXISTS")
        is_contested = _is_claim_involved_in_contest(shadow_relations, cid)
        shadow_rel = "CONTESTS" if is_contested else "UNRELATED"
        cls = _classify_relation_diff(gold_rel, shadow_rel, False, False, True, True) if is_contested else "regression"
        reason = f"Unexpected active claim {cid} in shadow active set" + (
            " (CONTESTS from different source)" if is_contested else "")
        diffs.append({
            "kind": "active_set",
            "claim_id": cid,
            "classification": cls,
            "rationale": reason,
            "blocking": False,
            "gold_relation": gold_rel,
            "shadow_relation": shadow_rel,
        })

    # ─── Invalidation diffs (full bidirectional evaluation) ─────────────
    for cid in expected_invalid & actual_superseded:
        gold_rel = gold_relations.get(cid, "SUPERCEDES")
        shadow_rel = "UNRELATED"
        for k, v in shadow_relations.items():
            if k == cid:
                shadow_rel = v[1]
                break
        cls = _classify_relation_diff(gold_rel, shadow_rel, True, True, False, False)
        diffs.append({
            "kind": "invalidation",
            "claim_id": cid,
            "classification": cls,
            "rationale": f"True positive invalidation: claim {cid} correctly superseded (gold={gold_rel}, shadow={shadow_rel})",
            "blocking": False,
            "gold_relation": gold_rel,
            "shadow_relation": shadow_rel,
        })

    for cid in expected_invalid - actual_superseded:
        gold_rel = gold_relations.get(cid, "SUPERCEDES")
        is_contested = _is_claim_involved_in_contest(shadow_relations, cid)
        shadow_rel = "CONTESTS" if is_contested else "UNRELATED"
        cls = _classify_relation_diff(gold_rel, shadow_rel, True, False, False, True) if is_contested else "regression"
        diff_entry = {
            "kind": "invalidation",
            "claim_id": cid,
            "classification": cls,
            "rationale": f"False negative invalidation: expected claim {cid} not superseded" + (
                " (shadow CONTESTS, gold expects SUPERCEDES)" if is_contested else ""),
            "blocking": False,
            "gold_relation": gold_rel,
            "shadow_relation": shadow_rel,
        }
        if is_contested:
            diff_entry["safety_disposition"] = "R01_checked"
            diff_entry["manual_review_metadata"] = "CONTESTS prevented expected invalidation — verify adjudication correctness"
        diffs.append(diff_entry)

    for cid in actual_superseded - expected_invalid:
        gold_rel = gold_relations.get(cid, "COEXISTS")
        shadow_rel = "UNRELATED"
        for k, v in shadow_relations.items():
            if k == cid:
                shadow_rel = v[1]
                break
        cls = _classify_relation_diff(gold_rel, shadow_rel, False, True, True, False)
        diffs.append({
            "kind": "invalidation",
            "claim_id": cid,
            "classification": cls,
            "rationale": f"Unexpected supersedes: claim {cid} superseded in shadow but not in gold expected_invalidations (gold={gold_rel}, shadow={shadow_rel})",
            "blocking": False,
            "gold_relation": gold_rel,
            "shadow_relation": shadow_rel,
        })

    # ─── must_include diffs ─────────────────────────────────────────────
    for cid in expected_must - actual_must:
        diffs.append({
            "kind": "must_include",
            "claim_id": cid,
            "classification": "blocker",
            "rationale": f"Expected must_include claim {cid} missing from shadow bundle",
            "blocking": True,
        })

    for cid in actual_must - expected_must:
        is_contested = _is_claim_involved_in_contest(shadow_relations, cid)
        if is_contested:
            cls = "manual_adjudication"
            rationale = f"Shadow bundle includes additional claim {cid} (CONTESTS from different source)"
            diff_entry = {
                "kind": "must_include",
                "claim_id": cid,
                "classification": cls,
                "rationale": rationale,
                "blocking": False,
                "safety_disposition": "R01_checked",
                "manual_review_metadata": "CONTESTS claim in bundle — verify must_include correctness",
            }
        else:
            cls = "expected_schema_change"
            diff_entry = {
                "kind": "must_include",
                "claim_id": cid,
                "classification": cls,
                "rationale": f"Shadow bundle includes additional claim {cid}",
                "blocking": False,
            }
        diffs.append(diff_entry)

    return diffs


# ─── Comparator unit test cases (Stage04-C, requirement 3) ──────────────────

class ComparatorUnitTestCases(unittest.TestCase):
    """Minimal comparator-only test cases that don't modify benchmark gold.

    Each case tests the truth table from Stage04-C instructions (lines 5776-5784).
    """

    def _make_graph_state(self, node_id_map, edges_data=None):
        """Helper to create a minimal graph_state dict.
        
        node_id_map: dict mapping internal key -> node properties dict.
        The key is used as the node_id in the graph_state.
        """
        nodes = {}
        for nid, props in node_id_map.items():
            nodes[nid] = {
                "node_id": nid,
                "claim_id": props.get("claim_id"),
                "status": props.get("status", "active"),
                "source": props.get("source", "test"),
                "entity_ref": props.get("entity_ref", "test_entity"),
                "lifecycle_ref": props.get("lifecycle_ref"),
                "adjudication_key": props.get("adjudication_key"),
                "state": props.get("state"),
            }
        return {
            "nodes": nodes,
            "edges": edges_data or [],
            "quarantine": [],
        }

    def _make_step(self, expected_active, expected_invalidations=None, must_include=None):
        """Helper to create a minimal step dict."""
        step = {
            "expected_active_set": expected_active,
            "expected_invalidations": expected_invalidations or [],
            "must_include": must_include or [],
        }
        return step

    def _make_bundle(self, must_include_node_ids):
        """Helper to create a bundle dict with must_include."""
        return {"must_include": must_include_node_ids}

    # ── cmp_supersedes_matches_supersedes (positive baseline) ──
    def test_cmp_supersedes_matches_supersedes(self):
        """Gold SUPERCEDES + shadow SUPERCEDES -> expected_improvement, no regression."""
        na = "n_a_claim_v1"
        nb = "n_b_claim_v2"
        gs = self._make_graph_state({
            na: {"claim_id": "claim_v1", "status": "superseded", "source": "src1"},
            nb: {"claim_id": "claim_v2", "status": "active", "source": "src1"},
        }, [
            {"source": nb, "target": na, "relation": "supersedes"},
        ])
        step = self._make_step(
            expected_active=["claim_v2"],
            expected_invalidations=[{"kind": "full", "dropped_claims": ["claim_v1"], "replacement_claims": ["claim_v2"]}],
            must_include=["claim_v2"],
        )
        bundle = self._make_bundle([nb])
        diffs = compare_step(step, gs, bundle)

        inv_diffs = [d for d in diffs if d["kind"] == "invalidation"]
        self.assertTrue(any(d["classification"] == "expected_improvement" for d in inv_diffs),
                        f"Expected expected_improvement for SUPERCEDES match, got: {[d['classification'] for d in inv_diffs]}")
        self.assertEqual(sum(1 for d in diffs if d["classification"] in ("regression", "ordinary_regression")), 0,
                         "No regressions expected for SUPERCEDES match")

    # ── cmp_coexists_matches_coexists (positive baseline) ──
    def test_cmp_coexists_matches_coexists(self):
        """Gold COEXISTS + shadow COEXISTS -> no diffs."""
        na = "n_a_claim_a"
        nb = "n_b_claim_b"
        gs = self._make_graph_state({
            na: {"claim_id": "claim_a", "status": "active", "source": "src1"},
            nb: {"claim_id": "claim_b", "status": "active", "source": "src2"},
        }, [
            {"source": nb, "target": na, "relation": "COEXISTS"},
        ])
        step = self._make_step(
            expected_active=["claim_a", "claim_b"],
            expected_invalidations=[],
            must_include=["claim_a", "claim_b"],
        )
        bundle = self._make_bundle([na, nb])
        diffs = compare_step(step, gs, bundle)

        self.assertEqual(len(diffs), 0, f"Expected no diffs for COEXISTS match, got: {diffs}")

    # ── cmp_gold_supersedes_shadow_contests_is_regression_even_if_r01_safe ──
    def test_cmp_gold_supersedes_shadow_contests_is_regression_even_if_r01_safe(self):
        """Gold SUPERCEDES + shadow CONTESTS → ordinary_regression, even if R01 bundle safety holds.

        Each diff must carry BOTH:
          - relation_classification = ordinary_regression
          - safety_disposition = R01_checked (or manual_review_metadata)
        """
        na = "n_a_claim_old"
        nb = "n_b_claim_new"
        gs = self._make_graph_state({
            na: {"claim_id": "claim_old", "status": "active", "source": "src1"},
            nb: {"claim_id": "claim_new", "status": "active", "source": "src2"},
        }, [
            {"source": nb, "target": na, "relation": "CONTESTS"},
        ])
        step = self._make_step(
            expected_active=["claim_new"],
            expected_invalidations=[{"kind": "full", "dropped_claims": ["claim_old"], "replacement_claims": ["claim_new"]}],
            must_include=["claim_new"],
        )
        bundle = self._make_bundle([nb])
        diffs = compare_step(step, gs, bundle)

        # Extract diffs for claim_old
        old_diffs = [d for d in diffs if d.get("claim_id") == "claim_old"]
        self.assertTrue(len(old_diffs) > 0, "Should have diffs for claim_old")

        # Relation classification: MUST be ordinary_regression, NOT manual_adjudication, NOT expected_improvement
        for d in old_diffs:
            self.assertNotEqual(d["classification"], "expected_improvement",
                                "SUPERCEDES+CONTESTS must NOT be expected_improvement")
            self.assertNotEqual(d["classification"], "manual_adjudication",
                                "SUPERCEDES+CONTESTS must NOT be manual_adjudication — it is an ordinary_regression")

        # At least one diff must be ordinary_regression
        self.assertTrue(any(d["classification"] == "ordinary_regression" for d in old_diffs),
                        f"SUPERCEDES+CONTESTS must produce ordinary_regression, got: {[d['classification'] for d in old_diffs]}")

        # R01 safety metadata must be present (independent of relation classification)
        self.assertTrue(any("safety_disposition" in d or "manual_review_metadata" in d for d in old_diffs),
                        "CONTESTS diffs must carry safety_disposition or manual_review_metadata")

    # ── cmp_gold_contests_shadow_supersedes_is_regression ──
    def test_cmp_gold_contests_shadow_supersedes_is_regression(self):
        """Gold CONTESTS + shadow SUPERCEDES → ordinary_regression (bidirectional relation check)."""
        na = "n_a_claim_a"
        nb = "n_b_claim_b"
        gs = self._make_graph_state({
            na: {"claim_id": "claim_a", "status": "active", "source": "src1"},
            nb: {"claim_id": "claim_b", "status": "superseded", "source": "src2"},
        }, [
            {"source": nb, "target": na, "relation": "SUPERCEDES"},
        ])
        step = self._make_step(
            expected_active=["claim_a", "claim_b"],
            expected_invalidations=[],  # Gold expects CONTESTS — both active, no invalidation
            must_include=["claim_a", "claim_b"],
        )
        bundle = self._make_bundle([na, nb])
        diffs = compare_step(step, gs, bundle)

        # claim_b being superseded when gold expects it active (CONTESTS)
        b_diffs = [d for d in diffs if d.get("claim_id") == "claim_b"]
        self.assertTrue(len(b_diffs) > 0, "Should detect CONTESTS→SUPERCEDES mismatch for claim_b")
        self.assertTrue(any(d["classification"] in ("ordinary_regression", "regression", "unexpected_supersedes") for d in b_diffs),
                        f"Expected regression for CONTESTS gold + SUPERCEDES shadow, got: {[d['classification'] for d in b_diffs]}")

    # ── cmp_r01_safety_metadata_does_not_override_relation_scoring ──
    def test_cmp_r01_safety_metadata_does_not_override_relation_scoring(self):
        """safety_disposition and manual_review_metadata must NOT change relation_classification.

        Even when R01 safety is checked, the relation classification must remain
        ordinary_regression for SUPERCEDES vs CONTESTS mismatch.
        """
        na = "n_a_old"
        nb = "n_b_new"
        gs = self._make_graph_state({
            na: {"claim_id": "old", "status": "active", "source": "release"},
            nb: {"claim_id": "new", "status": "active", "source": "incident"},
        }, [
            {"source": nb, "target": na, "relation": "CONTESTS"},
        ])
        step = self._make_step(
            expected_active=["new"],
            expected_invalidations=[{"kind": "full", "dropped_claims": ["old"], "replacement_claims": ["new"]}],
            must_include=["new"],
        )
        bundle = self._make_bundle([nb])
        diffs = compare_step(step, gs, bundle)

        old_diffs = [d for d in diffs if d.get("claim_id") == "old"]
        self.assertTrue(len(old_diffs) > 0)

        # Every diff for 'old' must be ordinary_regression regardless of metadata presence
        for d in old_diffs:
            self.assertEqual(d["classification"], "ordinary_regression",
                             f"Relation classification must be ordinary_regression, got: {d['classification']}")
            # Metadata may or may not be present, but must not affect classification
            # (presence of safety_disposition does not downgrade regression to manual)

    # ── cmp_coexists_vs_supersedes_detects_unexpected_invalidation ──
    def test_cmp_coexists_vs_supersedes_detects_unexpected_invalidation(self):
        """Gold COEXISTS + shadow SUPERCEDES → regression (false invalidation)."""
        na = "n_a_active"
        nb = "n_b_target"
        gs = self._make_graph_state({
            na: {"claim_id": "active_claim", "status": "active", "source": "src1"},
            nb: {"claim_id": "target_claim", "status": "superseded", "source": "src1"},
        }, [
            {"source": na, "target": nb, "relation": "supersedes"},
        ])
        step = self._make_step(
            expected_active=["active_claim", "target_claim"],
            expected_invalidations=[],
            must_include=["active_claim", "target_claim"],
        )
        bundle = self._make_bundle([na, nb])
        diffs = compare_step(step, gs, bundle)

        b_diffs = [d for d in diffs if d.get("claim_id") == "target_claim"]
        self.assertTrue(len(b_diffs) > 0, "Should detect unexpected supersedes")
        self.assertTrue(any(d["classification"] in ("regression", "ordinary_regression", "unexpected_supersedes") for d in b_diffs),
                        f"Expected regression for COEXISTS+SUPERCEDES, got: {[d['classification'] for d in b_diffs]}")

    # ── cmp_unexpected_shadow_supersedes_remains_bidirectional_false_positive ──
    def test_cmp_unexpected_shadow_supersedes_remains_bidirectional_false_positive(self):
        """Shadow SUPERCEDES when gold has no expected invalidation → false positive invalidation.

        This is bidirectional: the comparator must catch both:
        - Gold expects invalidation, shadow doesn't (false negative)
        - Gold expects no invalidation, shadow does (false positive)
        """
        na = "n_a_keeper"
        nb = "n_b_killer"
        gs = self._make_graph_state({
            na: {"claim_id": "keeper", "status": "superseded", "source": "src1"},
            nb: {"claim_id": "killer", "status": "active", "source": "src1"},
        }, [
            {"source": nb, "target": na, "relation": "SUPERCEDES"},
        ])
        step = self._make_step(
            expected_active=["keeper", "killer"],
            expected_invalidations=[],  # Gold expects no invalidation
            must_include=["keeper", "killer"],
        )
        bundle = self._make_bundle([na, nb])
        diffs = compare_step(step, gs, bundle)

        # keeper should be flagged as unexpectedly superseded
        keeper_diffs = [d for d in diffs if d.get("claim_id") == "keeper"]
        self.assertTrue(len(keeper_diffs) > 0, "Should detect false positive invalidation for keeper")
        self.assertTrue(any(d["classification"] in ("regression", "ordinary_regression", "unexpected_supersedes") for d in keeper_diffs),
                        f"Expected regression/false_positive, got: {[d['classification'] for d in keeper_diffs]}")

    # ── cmp_contests_bundle_safety_is_checked_separately_from_relation_score ──
    def test_cmp_contests_bundle_safety_is_checked_separately_from_relation_score(self):
        """CONTESTS detection, R01 bundle safety, and relation scoring are independent.

        When gold expects SUPERCEDES and shadow produces CONTESTS:
        - relation_classification = ordinary_regression (relation scoring)
        - safety_disposition = R01_checked (bundle safety)
        - manual_review_metadata = present (review flag)

        All three fields must coexist in the same diff without overriding each other.
        """
        na = "n_a_old"
        nb = "n_b_new"
        gs = self._make_graph_state({
            na: {"claim_id": "old", "status": "active", "source": "src1"},
            nb: {"claim_id": "new", "status": "active", "source": "src2"},
        }, [
            {"source": nb, "target": na, "relation": "CONTESTS"},
        ])
        step = self._make_step(
            expected_active=["new"],
            expected_invalidations=[{"kind": "full", "dropped_claims": ["old"], "replacement_claims": ["new"]}],
            must_include=["new"],
        )
        bundle = self._make_bundle([nb])
        diffs = compare_step(step, gs, bundle)

        old_diffs = [d for d in diffs if d.get("claim_id") == "old"]
        self.assertTrue(len(old_diffs) > 0)

        # At least one diff must have all three independent signals
        has_relation_regression = any(d["classification"] == "ordinary_regression" for d in old_diffs)
        has_safety_meta = any("safety_disposition" in d or "manual_review_metadata" in d for d in old_diffs)

        self.assertTrue(has_relation_regression,
                        "Relation classification must be ordinary_regression")
        self.assertTrue(has_safety_meta,
                        "Bundle safety metadata must be present alongside relation classification")

        # Verify no diff has safety_disposition overriding relation_classification
        for d in old_diffs:
            self.assertNotEqual(d["classification"], "manual_adjudication",
                                "safety_disposition must NOT override relation_classification to manual_adjudication")


# ─── Legacy compatibility ───────────────────────────────────────────────────

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

            cp_event_id = event["event_id"]
            if cp_event_id in steps:
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
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--split", choices=["development", "regression", "blind_holdout", "adversarial"],
                       help="Run shadow evaluation for a specific split")
    group.add_argument("--unit-tests", action="store_true", help="Run comparator unit tests only")
    args = parser.parse_args()

    if args.unit_tests:
        print("Running comparator unit tests...")
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(ComparatorUnitTestCases)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return 0 if result.wasSuccessful() else 1

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
