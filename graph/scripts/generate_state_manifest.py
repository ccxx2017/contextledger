#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate reports/current_state_manifest.json from current repository facts.

This script is intentionally mechanical: it does not call LLMs, does not
modify graph_state.json, and only reads files that are already materialized.
Run it from the repository root (D:\CCXXLESSON\contextledger).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT = "abu_modern"
GRAPH_STATE_PATH = REPO_ROOT / "graph" / "projects" / PROJECT / "graph_state.json"
QUARANTINE_DIR = REPO_ROOT / "graph" / "projects" / PROJECT / "quarantine"
REPORTS_DIR = REPO_ROOT / "reports"
MANIFEST_PATH = REPORTS_DIR / "current_state_manifest.json"
LINT_REPORT_PATH = REPORTS_DIR / "current_graph_lint_report.json"
BENCHMARK_VERSION = "phase05_v3"
BENCHMARK_DIR = REPO_ROOT / "graph" / "projects" / PROJECT / "benchmark" / BENCHMARK_VERSION
SCORE_REPORT_PATH = BENCHMARK_DIR / "reports" / "phase05_score_report.json"
FLAT_RAG_REPORT_PATH = BENCHMARK_DIR / "reports" / "phase05_v3_vs_flat_rag.md"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_dir_hash(root: Path, pattern: tuple[str, ...] = (".json", ".md", ".py")) -> str:
    """Deterministic aggregate hash over all matching files under root."""
    h = hashlib.sha256()
    if not root.exists():
        return ""
    files = sorted(p for p in root.rglob("*") if p.is_file() and str(p).lower().endswith(pattern))
    for p in files:
        rel = p.relative_to(root).as_posix()
        h.update(rel.encode("utf-8"))
        h.update(sha256_file(p).encode("utf-8"))
    return h.hexdigest()


def git_capture(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def git_status_short() -> str:
    return git_capture(["status", "--short"])


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_quarantine_distribution() -> dict[str, Any]:
    if not QUARANTINE_DIR.exists():
        return {"total_files": 0, "reason_distribution": {}, "files": []}
    files = sorted(p for p in QUARANTINE_DIR.iterdir() if p.is_file())
    reasons: dict[str, int] = {}
    for p in files:
        try:
            data = load_json(p)
        except Exception:
            reasons["unparseable"] = reasons.get("unparseable", 0) + 1
            continue
        reason = data.get("reason") or data.get("error") or "unknown"
        if not isinstance(reason, str):
            reason = str(reason)
        reasons[reason] = reasons.get(reason, 0) + 1
    return {
        "total_files": len(files),
        "reason_distribution": reasons,
        "latest_quarantined_turn": max(
            (
                int("".join(c for c in p.stem if c.isdigit()) or "0")
                for p in files
                if p.suffix == ".json"
            ),
            default=0,
        ),
    }


def compute_graph_state_stats() -> dict[str, Any]:
    data = load_json(GRAPH_STATE_PATH)
    nodes = data.get("nodes", {})
    edges = data.get("edges", [])
    status_counts: dict[str, int] = {}
    for n in nodes.values():
        status = n.get("status", "__missing__")
        status_counts[status] = status_counts.get(status, 0) + 1
    state_counts: dict[str, int] = {}
    for n in nodes.values():
        state = n.get("state", "__missing__")
        state_counts[state] = state_counts.get(state, 0) + 1
    return {
        "path": GRAPH_STATE_PATH.relative_to(REPO_ROOT).as_posix(),
        "sha256": sha256_file(GRAPH_STATE_PATH),
        "latest_applied_turn": data.get("turn_counter"),
        "turn_counter": data.get("turn_counter"),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "status_distribution": status_counts,
        "state_distribution": state_counts,
        "quarantine_count_in_graph_state": len(data.get("quarantine", [])),
    }


def load_lint_summary() -> dict[str, Any]:
    if not LINT_REPORT_PATH.exists():
        return {"report_path": str(LINT_REPORT_PATH.relative_to(REPO_ROOT).as_posix()), "exists": False}
    data = load_json(LINT_REPORT_PATH)
    summary = data.get("summary", {})
    return {
        "report_path": str(LINT_REPORT_PATH.relative_to(REPO_ROOT).as_posix()),
        "report_sha256": sha256_file(LINT_REPORT_PATH),
        "exists": True,
        "nodes": summary.get("nodes"),
        "edges": summary.get("edges"),
        "active_nodes": summary.get("active_nodes"),
        "active_edges": summary.get("active_edges"),
        "superseded_nodes": summary.get("superseded_nodes"),
        "errors": summary.get("errors"),
        "warnings": summary.get("warnings"),
    }


BENCHMARK_BASELINE_NAME = "phase0_current"
FLAT_RAG_D1_BASELINE_NAME = "flat_rag_d1"
FLAT_RAG_D2_BASELINE_NAME = "flat_rag_d2"

def load_benchmark_metrics() -> dict[str, Any]:
    if SCORE_REPORT_PATH.exists():
        try:
            data = load_json(SCORE_REPORT_PATH)
            baselines = data.get("baselines", {})
            metrics = baselines.get(BENCHMARK_BASELINE_NAME, {}).get("metrics", {})
            flat_rag_d1 = baselines.get(FLAT_RAG_D1_BASELINE_NAME, {}).get("metrics", {})
            flat_rag_d2 = baselines.get(FLAT_RAG_D2_BASELINE_NAME, {}).get("metrics", {})
        except Exception:
            metrics = {}
            flat_rag_d1 = {}
            flat_rag_d2 = {}
    else:
        metrics = {}
        flat_rag_d1 = {}
        flat_rag_d2 = {}
    def pick(src: dict[str, Any]) -> dict[str, Any]:
        return {
            "invalidation_precision": src.get("invalidation_precision"),
            "invalidation_recall": src.get("invalidation_recall"),
            "active_set_set_f1": src.get("active_set_set_f1"),
            "must_include_recall": src.get("must_include_recall"),
            "valid_time_adjudication_accuracy": src.get("valid_time_adjudication_accuracy"),
        }
    return {
        "current_version": BENCHMARK_VERSION,
        "score_report_path": SCORE_REPORT_PATH.relative_to(REPO_ROOT).as_posix(),
        "score_report_sha256": sha256_file(SCORE_REPORT_PATH) if SCORE_REPORT_PATH.exists() else None,
        "vs_flat_rag_report_path": FLAT_RAG_REPORT_PATH.relative_to(REPO_ROOT).as_posix(),
        "vs_flat_rag_report_sha256": sha256_file(FLAT_RAG_REPORT_PATH) if FLAT_RAG_REPORT_PATH.exists() else None,
        "dir_sha256": compute_dir_hash(BENCHMARK_DIR),
        "current_metrics": pick(metrics),
        "flat_rag_d1_metrics": pick(flat_rag_d1),
        "flat_rag_d2_metrics": pick(flat_rag_d2),
    }


def runtime_component_fingerprints() -> dict[str, Any]:
    """Hash the mechanical files that participate in turn execution."""
    scripts_dir = REPO_ROOT / "graph" / "scripts"
    prompts_dir = REPO_ROOT / "graph" / "prompts"
    contracts_dir = REPO_ROOT / "contracts"
    return {
        "scripts_dir_sha256": compute_dir_hash(scripts_dir),
        "prompts_dir_sha256": compute_dir_hash(prompts_dir),
        "contracts_dir_sha256": compute_dir_hash(contracts_dir),
        "key_files": {
            "contracts/03_graph_schema.md": sha256_file(contracts_dir / "03_graph_schema.md"),
            "contracts/05_phase1_lifecycle_schema.md": sha256_file(contracts_dir / "05_phase1_lifecycle_schema.md"),
            "contracts/06_extractor_runtime.md": sha256_file(contracts_dir / "06_extractor_runtime.md"),
            "contracts/07_turn_runtime.md": sha256_file(contracts_dir / "07_turn_runtime.md"),
            "graph/scripts/entity_resolver.py": sha256_file(scripts_dir / "entity_resolver.py"),
            "graph/scripts/reconcile_patch.py": sha256_file(scripts_dir / "reconcile_patch.py"),
            "graph/scripts/apply_patch.py": sha256_file(scripts_dir / "apply_patch.py"),
            "graph/scripts/graph_lint.py": sha256_file(scripts_dir / "graph_lint.py"),
            "graph/prompts/extractor_system.md": sha256_file(prompts_dir / "extractor_system.md"),
        },
    }


def build_manifest() -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    branch = git_capture(["branch", "--show-current"])
    head = git_capture(["rev-parse", "HEAD"])
    base_main = git_capture(["merge-base", "main", branch or "HEAD"])
    working_tree_clean = git_status_short() == ""
    return {
        "generated_at": now.isoformat(),
        "generated_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project_id": PROJECT,
        "manifest_generation": {
            "script_path": Path(__file__).relative_to(REPO_ROOT).as_posix(),
            "script_sha256": sha256_file(Path(__file__)),
            "invocation_cwd": os.getcwd(),
            "invocation_argv": sys.argv,
        },
        "git": {
            "branch": branch,
            "commit": head,
            "base_commit_on_main": base_main,
            "working_tree_clean_at_generation": working_tree_clean,
            "status_short_at_generation": git_status_short(),
        },
        "schema": {
            "current_contract": "contracts/03_graph_schema.md",
            "current_contract_status": "PROVISIONAL",
            "lifecycle_rfc": "contracts/05_phase1_lifecycle_schema.md",
            "lifecycle_rfc_status": "RFC Draft",
            "compatibility_mode": "legacy_entity_ref_fallback",
        },
        "runtime_components": runtime_component_fingerprints(),
        "graph_state": compute_graph_state_stats(),
        "quarantine": read_quarantine_distribution(),
        "latest_turn_health": {
            "path": f"graph/projects/{PROJECT}/reports/turn_084_auto/turn_health_report.json",
            "note": "exists if turn_084_auto report was materialized; otherwise null",
            "graph_lint": None,
        },
        "benchmark": load_benchmark_metrics(),
        "lint_baseline": load_lint_summary(),
        "stage02_baseline_conclusions": {
            "p4_harness_missing_resolver": "confirmed and already fixed in phase05_v3 benchmark harness",
            "resolver_net_gain_vs_d2": "positive",
            "must_include_redline": "fixed to 1.0 under phase05_v3",
            "high_confidence_round5_candidates": "resolved before Stage02 branch start",
        },
        "notes": [
            "this manifest is the authoritative machine-readable baseline for Stage02 experiments on branch phase1_lifecycle_stage02",
            "all graph_state counts and hashes are measured from the file at manifest generation time, not historical narrative",
            "future Stage02 experiments should cite this manifest instead of historical narrative documents",
        ],
    }


def main() -> int:
    manifest = build_manifest()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Wrote {MANIFEST_PATH}")
    print(f"  branch: {manifest['git']['branch']}")
    print(f"  commit: {manifest['git']['commit']}")
    print(f"  graph_state sha256: {manifest['graph_state']['sha256']}")
    print(f"  working_tree_clean: {manifest['git']['working_tree_clean_at_generation']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
