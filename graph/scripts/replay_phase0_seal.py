#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
replay_phase0_seal.py

turn_005 封板辅助脚本：
1. 从 graph_state.seed.json + patch_001..004 重放整条 patch 链
2. 将重放结果与 run/ 下的 turn 快照逐轮比较
3. 以当前脚本口径重生成 Phase 0 的 canonical bundle / assembly_report
4. 再用 replay 图重新生成一遍，验证 bundle / report 的字节级与语义级一致性
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import apply_patch as apply_mod
import build_context_bundle as bundle_mod


@dataclass(frozen=True)
class BundleSpec:
    turn_id: str
    graph_snapshot_name: str
    bundle_name: str
    report_name: str
    max_nodes: int
    budget_profile: str


BUNDLE_SPECS = [
    BundleSpec(
        turn_id="turn_001",
        graph_snapshot_name="graph_state.turn_001.json",
        bundle_name="context_bundle.turn_001.json",
        report_name="assembly_report.turn_001.json",
        max_nodes=9,
        budget_profile="phase0_turn_001_full_context",
    ),
    BundleSpec(
        turn_id="turn_002",
        graph_snapshot_name="graph_state.turn_002.json",
        bundle_name="context_bundle.turn_002.json",
        report_name="assembly_report.turn_002.json",
        max_nodes=3,
        budget_profile="tight_budget_must_only",
    ),
    BundleSpec(
        turn_id="turn_003",
        graph_snapshot_name="graph_state.turn_003.json",
        bundle_name="context_bundle.turn_003.json",
        report_name="assembly_report.turn_003.json",
        max_nodes=3,
        budget_profile="tight_budget_must_only",
    ),
    BundleSpec(
        turn_id="turn_003_pre_adjudication",
        graph_snapshot_name="graph_state.turn_003.json",
        bundle_name="context_bundle.turn_003_pre_adjudication_budget4.json",
        report_name="assembly_report.turn_003_pre_adjudication_budget4.json",
        max_nodes=4,
        budget_profile="budget4_pre_adjudication",
    ),
    BundleSpec(
        turn_id="turn_004",
        graph_snapshot_name="graph_state.turn_004.json",
        bundle_name="context_bundle.turn_004_budget4.json",
        report_name="assembly_report.turn_004_budget4.json",
        max_nodes=4,
        budget_profile="budget4_post_adjudication",
    ),
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def compare_json_files(left: Path, right: Path) -> bool:
    return apply_mod.load_json(left) == apply_mod.load_json(right)


def ensure_turn001_legacy_backup(reports_dir: Path) -> str | None:
    current = reports_dir / "context_bundle.turn_001.json"
    legacy = reports_dir / "context_bundle.turn_001.legacy_manual.json"
    if legacy.exists():
        return str(legacy)
    if not current.exists():
        return None

    data = apply_mod.load_json(current)
    if data.get("kind") != "context_bundle.phase0_manual.v1":
        return None

    if not legacy.exists():
        shutil.copy2(current, legacy)
    return str(legacy)


def replay_graph_chain(
    *,
    seed_path: Path,
    patch_paths: list[Path],
    replay_run_dir: Path,
    canonical_run_dir: Path,
    phase0_dir: Path,
) -> list[dict[str, Any]]:
    graph = apply_mod.load_json(seed_path)
    results: list[dict[str, Any]] = []

    for index, patch_path in enumerate(patch_paths, start=1):
        patch = apply_mod.load_json(patch_path)
        graph = apply_mod.apply_patch(graph, patch)

        turn_name = f"turn_{index:03d}"
        replay_path = replay_run_dir / f"graph_state.{turn_name}.json"
        canonical_path = canonical_run_dir / f"graph_state.{turn_name}.json"
        apply_mod.write_json(replay_path, graph)

        semantic_equal = canonical_path.exists() and compare_json_files(replay_path, canonical_path)
        sha_equal = canonical_path.exists() and sha256_file(replay_path) == sha256_file(canonical_path)
        current_state_path = phase0_dir / "graph_state.json"
        current_equal = False
        if index == len(patch_paths) and current_state_path.exists():
            current_equal = compare_json_files(replay_path, current_state_path)

        results.append({
            "turn_id": turn_name,
            "patch": str(patch_path),
            "replay_snapshot": str(replay_path),
            "canonical_snapshot": str(canonical_path),
            "semantic_equal": semantic_equal,
            "sha256_equal": sha_equal,
            "matches_current_graph_state": current_equal if index == len(patch_paths) else None,
        })

    return results


def build_and_write_bundle(
    *,
    graph_path: Path,
    bundle_path: Path,
    report_path: Path,
    project_id: str,
    spec: BundleSpec,
) -> None:
    graph = apply_mod.load_json(graph_path)
    bundle, report = bundle_mod.build_bundle(
        graph_state=graph,
        project_id=project_id,
        turn_id=spec.turn_id,
        max_nodes=spec.max_nodes,
        budget_profile=spec.budget_profile,
    )
    bundle_mod.write_json(bundle_path, bundle)
    bundle_mod.write_json(report_path, report)


def replay_and_compare_bundles(
    *,
    project_id: str,
    canonical_run_dir: Path,
    replay_run_dir: Path,
    reports_dir: Path,
    replay_reports_dir: Path,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for spec in BUNDLE_SPECS:
        canonical_graph = canonical_run_dir / spec.graph_snapshot_name
        replay_graph = replay_run_dir / spec.graph_snapshot_name
        canonical_bundle = reports_dir / spec.bundle_name
        canonical_report = reports_dir / spec.report_name
        replay_bundle = replay_reports_dir / spec.bundle_name
        replay_report = replay_reports_dir / spec.report_name

        build_and_write_bundle(
            graph_path=canonical_graph,
            bundle_path=canonical_bundle,
            report_path=canonical_report,
            project_id=project_id,
            spec=spec,
        )
        build_and_write_bundle(
            graph_path=replay_graph,
            bundle_path=replay_bundle,
            report_path=replay_report,
            project_id=project_id,
            spec=spec,
        )

        results.append({
            "turn_id": spec.turn_id,
            "bundle": {
                "canonical_path": str(canonical_bundle),
                "replay_path": str(replay_bundle),
                "semantic_equal": compare_json_files(canonical_bundle, replay_bundle),
                "sha256_equal": sha256_file(canonical_bundle) == sha256_file(replay_bundle),
            },
            "assembly_report": {
                "canonical_path": str(canonical_report),
                "replay_path": str(replay_report),
                "semantic_equal": compare_json_files(canonical_report, replay_report),
                "sha256_equal": sha256_file(canonical_report) == sha256_file(replay_report),
            },
        })

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Seal Phase 0 by replaying patch chain and regenerating canonical bundles.")
    parser.add_argument("--project-id", default="abu_modern")
    args = parser.parse_args()

    root = repo_root()
    phase0_dir = root / "graph" / "projects" / args.project_id / "phase0_manual"
    patches_dir = phase0_dir / "patches"
    reports_dir = phase0_dir / "reports"
    canonical_run_dir = phase0_dir / "run"
    replay_root = reports_dir / "replay_turn_005"
    replay_run_dir = replay_root / "run"
    replay_reports_dir = replay_root / "reports"
    replay_root.mkdir(parents=True, exist_ok=True)
    replay_run_dir.mkdir(parents=True, exist_ok=True)
    replay_reports_dir.mkdir(parents=True, exist_ok=True)

    legacy_backup = ensure_turn001_legacy_backup(reports_dir)

    seed_path = root / "graph" / "graph_state.seed.json"
    patch_paths = [patches_dir / f"patch_{i:03d}.json" for i in range(1, 5)]
    graph_results = replay_graph_chain(
        seed_path=seed_path,
        patch_paths=patch_paths,
        replay_run_dir=replay_run_dir,
        canonical_run_dir=canonical_run_dir,
        phase0_dir=phase0_dir,
    )

    bundle_results = replay_and_compare_bundles(
        project_id=args.project_id,
        canonical_run_dir=canonical_run_dir,
        replay_run_dir=replay_run_dir,
        reports_dir=reports_dir,
        replay_reports_dir=replay_reports_dir,
    )

    ok = all(item["semantic_equal"] and item["sha256_equal"] for item in graph_results)
    ok = ok and all(
        item["bundle"]["semantic_equal"]
        and item["bundle"]["sha256_equal"]
        and item["assembly_report"]["semantic_equal"]
        and item["assembly_report"]["sha256_equal"]
        for item in bundle_results
    )

    report = {
        "kind": "phase0_seal_report.v1",
        "project_id": args.project_id,
        "ok": ok,
        "seed_path": str(seed_path),
        "patch_chain": [str(path) for path in patch_paths],
        "turn001_legacy_backup": legacy_backup,
        "graph_replay": graph_results,
        "bundle_replay": bundle_results,
    }
    write_json(reports_dir / "turn_005_seal_report.json", report)
    print(f"Wrote seal report: {reports_dir / 'turn_005_seal_report.json'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
