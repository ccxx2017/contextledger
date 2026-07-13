#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_TAGS = [
    "full",
    "partial",
    "conditional",
    "revival",
    "alias_trap",
    "provenance_conflict",
    "non_invalidation_decoy",
    "out_of_order_late",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_exact(text: str) -> str:
    return " ".join(str(text).strip().lower().split())


def f1_score(predicted: set[str], expected: set[str]) -> float:
    if not predicted and not expected:
        return 1.0
    precision = len(predicted & expected) / len(predicted) if predicted else 0.0
    recall = len(predicted & expected) / len(expected) if expected else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def collect_benchmark_mentions(trajectories: list[dict[str, Any]], golds: dict[str, dict[str, Any]]) -> set[str]:
    mentions: set[str] = set()
    for trajectory in trajectories:
        for observation in trajectory.get("observations", []):
            for mention in observation.get("mentions", []):
                mentions.add(normalize_exact(mention))
    for gold in golds.values():
        for step in gold.get("steps", []):
            for cluster in step.get("entity_clusters", []):
                for mention in cluster.get("mentions", []):
                    mentions.add(normalize_exact(mention))
    return mentions


def build_resolver(project_root: Path, benchmark_mentions: set[str]) -> tuple[dict[str, str], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    register = load_json(project_root / "pending_merge" / "pending_merge_register.json")
    covered_items: list[dict[str, Any]] = []
    for item in register.get("items", []):
        raw_ref = normalize_exact(str(item.get("raw_entity_ref", "")))
        canonical_ref = normalize_exact(str(item.get("canonical_entity_ref", "")))
        if raw_ref in benchmark_mentions or canonical_ref in benchmark_mentions:
            covered_items.append(item)

    direct_map: dict[str, str] = {}
    covered_resolved: list[dict[str, Any]] = []
    covered_tracked: list[dict[str, Any]] = []
    for item in covered_items:
        raw_ref = normalize_exact(str(item.get("raw_entity_ref", "")))
        resolution = item.get("resolution")
        if not resolution:
            covered_tracked.append(item)
            continue
        covered_resolved.append(item)
        if resolution == "kept_distinct":
            direct_map[raw_ref] = raw_ref
        else:
            direct_map[raw_ref] = normalize_exact(str(item.get("canonical_entity_ref", "")))

    cache: dict[str, str] = {}

    def resolve(entity_ref: str) -> str:
        key = normalize_exact(entity_ref)
        if key in cache:
            return cache[key]
        trail: set[str] = set()
        current = key
        while current in direct_map and current not in trail:
            trail.add(current)
            next_key = direct_map[current]
            if next_key == current:
                break
            current = next_key
        cache[key] = current
        return current

    mismatches: list[dict[str, Any]] = []
    for item in covered_resolved:
        raw_ref = normalize_exact(str(item.get("raw_entity_ref", "")))
        resolution = str(item.get("resolution"))
        expected = raw_ref if resolution == "kept_distinct" else resolve(str(item.get("canonical_entity_ref", "")))
        actual = resolve(raw_ref)
        if actual != expected:
            mismatches.append(
                {
                    "raw_entity_ref": str(item.get("raw_entity_ref", "")),
                    "canonical_entity_ref": str(item.get("canonical_entity_ref", "")),
                    "resolution": resolution,
                    "expected_resolved_key": expected,
                    "actual_resolved_key": actual,
                    "resolution_note": str(item.get("resolution_note", "")),
                }
            )

    final_map = {key: resolve(key) for key in direct_map}
    return final_map, covered_resolved, covered_tracked, mismatches


def predicted_entities_d2(observations: list[dict[str, Any]], step_index: int) -> set[str]:
    latest_by_surface: dict[str, dict[str, Any]] = {}
    for observation in observations[: step_index + 1]:
        mentions = observation.get("mentions", [])
        entity_key = normalize_exact(mentions[0]) if mentions else ""
        latest_by_surface[entity_key] = observation
    return set(latest_by_surface.keys())


def predicted_entities_cl_resolved(observations: list[dict[str, Any]], step_index: int, resolver_map: dict[str, str]) -> set[str]:
    latest_by_resolved: dict[str, dict[str, Any]] = {}
    for observation in observations[: step_index + 1]:
        mentions = observation.get("mentions", [])
        entity_key = normalize_exact(mentions[0]) if mentions else ""
        entity_key = resolver_map.get(entity_key, entity_key)
        latest_by_resolved[entity_key] = observation
    return set(latest_by_resolved.keys())


def expected_entities_from_gold(gold_step: dict[str, Any], resolver_map: dict[str, str]) -> set[str]:
    expected: set[str] = set()
    for cluster in gold_step.get("entity_clusters", []):
        mentions = [resolver_map.get(normalize_exact(m), normalize_exact(m)) for m in cluster.get("mentions", [])]
        mentions = [m for m in mentions if m]
        if not mentions:
            continue
        expected.add(sorted(mentions)[0])
    return expected


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 0.5 entity-set Set-F1 diagnostic (resolved CL vs D2).")
    parser.add_argument("--project-dir", required=True, help="Phase 0.5 benchmark directory (contains trajectories/gold/reports).")
    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    trajectories_dir = project_dir / "trajectories"
    gold_dir = project_dir / "gold"
    reports_dir = project_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    trajectories = [load_json(path) for path in sorted(trajectories_dir.glob("*.json"))]
    golds = {
        path.name.replace(".gold", "").replace(".json", ""): load_json(path)
        for path in sorted(gold_dir.glob("*.gold.json"))
    }

    benchmark_mentions = collect_benchmark_mentions(trajectories, golds)
    project_root = project_dir.parents[1]
    resolver_map, covered_resolved, covered_tracked, mismatches = build_resolver(project_root, benchmark_mentions)
    if mismatches:
        raise SystemExit(f"resolver reconciliation failed: mismatch_count={len(mismatches)}")

    per_tag_steps: dict[str, list[tuple[float, float]]] = {tag: [] for tag in REQUIRED_TAGS}
    per_traj: dict[str, Any] = {}

    for trajectory in trajectories:
        tid = str(trajectory["trajectory_id"])
        tags = [tag for tag in trajectory.get("coverage_tags", []) if tag in set(REQUIRED_TAGS)]
        obs = list(trajectory.get("observations", []))
        gold = golds[tid]
        gold_steps = list(gold.get("steps", []))

        rows: list[dict[str, Any]] = []
        for idx, gold_step in enumerate(gold_steps):
            expected = expected_entities_from_gold(gold_step, resolver_map)
            cl = predicted_entities_cl_resolved(obs, idx, resolver_map)
            d2 = predicted_entities_d2(obs, idx)
            cl_f1 = f1_score(cl, expected)
            d2_f1 = f1_score(d2, expected)
            for tag in tags:
                per_tag_steps[tag].append((cl_f1, d2_f1))
            rows.append(
                {
                    "after_obs_id": str(gold_step.get("after_obs_id")),
                    "expected_entities": sorted(expected),
                    "cl_entities": sorted(cl),
                    "d2_entities": sorted(d2),
                    "cl_entity_set_f1": round(cl_f1, 4),
                    "d2_entity_set_f1": round(d2_f1, 4),
                }
            )

        per_traj[tid] = {"tags": tags, "steps": rows}

    lines: list[str] = [
        "# Phase 0.5 v3 Entity-Set Set-F1 (Resolved Harness)",
        "",
        "本报告用于验证 `phase05_v3` 中的 resolved harness 是否真正测到了 resolver 的收益。",
        "",
        "## 对账状态",
        "",
        f"- benchmark mentions 数量：`{len(benchmark_mentions)}`",
        f"- 覆盖到的 pending_merge 项数：`{len(covered_resolved) + len(covered_tracked)}`",
        f"- 已 resolved 项数：`{len(covered_resolved)}`",
        f"- 仍 tracked 项数：`{len(covered_tracked)}`",
        f"- mismatch 数量：`{len(mismatches)}`",
        "",
        "## 口径",
        "",
        "- `D2`：exact surface last-write-wins（以 `normalize_exact(mentions[0])` 为 entity key）。",
        "- `CL(resolved)`：使用 `pending_merge_register` 中已 resolved 的真实 batch 决策做实体归并；对仍 `tracked` 的候选项不强行 merge。",
        "- `expected`：gold 的 `entity_clusters` 先经过同一套 resolved key 映射，再计算 entity-set Set-F1。",
        "",
        "## Per-Category 汇总",
        "",
        "| category | steps | CL(resolved) entity-set Set-F1 | D2 entity-set Set-F1 | delta(CL-D2) |",
        "|---|---:|---:|---:|---:|",
    ]

    for tag in REQUIRED_TAGS:
        samples = per_tag_steps[tag]
        if not samples:
            continue
        cl_avg = sum(x[0] for x in samples) / len(samples)
        d2_avg = sum(x[1] for x in samples) / len(samples)
        lines.append(f"| {tag} | {len(samples)} | {cl_avg:.3f} | {d2_avg:.3f} | {(cl_avg - d2_avg):.3f} |")

    lines.extend(
        [
            "",
            "## Per-Trajectory 明细",
            "",
        ]
    )

    for tid in sorted(per_traj.keys()):
        lines.append(f"### {tid}")
        lines.append("")
        lines.append("| after_obs_id | CL F1 | D2 F1 | expected_entities | CL_entities | D2_entities |")
        lines.append("|---|---:|---:|---|---|---|")
        for row in per_traj[tid]["steps"]:
            lines.append(
                f"| {row['after_obs_id']} | {row['cl_entity_set_f1']:.3f} | {row['d2_entity_set_f1']:.3f} | "
                f"{', '.join(row['expected_entities'])} | {', '.join(row['cl_entities'])} | {', '.join(row['d2_entities'])} |"
            )
        lines.append("")

    out_path = reports_dir / "phase05_v3_entity_set_breakdown.md"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote entity-set breakdown: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

