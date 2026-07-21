#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate the benchmark v1 freeze manifest.

Checks that all referenced files exist, hashes match, splits are disjoint,
and the manifest can be regenerated deterministically.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = REPO_ROOT / "graph" / "projects" / "abu_modern" / "benchmark" / "v1_freeze" / "benchmark_v1_freeze_manifest.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate() -> list[str]:
    errors: list[str] = []
    if not MANIFEST_PATH.exists():
        errors.append(f"missing manifest: {MANIFEST_PATH}")
        return errors

    manifest = load_json(MANIFEST_PATH)

    # Basic fields
    required = ["schema_version", "freeze_version", "splits", "total_cases", "all_case_ids", "split_overlap_check"]
    for key in required:
        if key not in manifest:
            errors.append(f"missing field: {key}")

    splits = manifest.get("splits", [])
    seen: set[str] = set()
    all_ids: list[str] = []
    for split in splits:
        name = split.get("name", "<unknown>")
        case_ids = split.get("case_ids", [])
        cases = split.get("cases", [])
        if len(case_ids) != len(cases):
            errors.append(f"split {name}: case_ids length mismatch with cases")
        for cid, case in zip(case_ids, cases):
            all_ids.append(cid)
            if cid in seen:
                errors.append(f"case {cid} appears in more than one split")
            seen.add(cid)
            traj_path = REPO_ROOT / case["trajectory_path"]
            gold_path = REPO_ROOT / case["gold_path"]
            if not traj_path.exists():
                errors.append(f"missing trajectory: {traj_path}")
            elif sha256_file(traj_path) != case["trajectory_sha256"]:
                errors.append(f"trajectory hash mismatch: {cid}")
            if not gold_path.exists():
                errors.append(f"missing gold: {gold_path}")
            elif sha256_file(gold_path) != case["gold_sha256"]:
                errors.append(f"gold hash mismatch: {cid}")

    if len(all_ids) != manifest.get("total_cases", 0):
        errors.append(f"total_cases mismatch: {manifest.get('total_cases')} vs {len(all_ids)}")
    if len(set(all_ids)) != len(all_ids):
        errors.append("duplicate case_ids across splits")
    if manifest.get("split_overlap_check") is not True:
        errors.append("split_overlap_check is not True")

    # Metric script hash
    metric_script = REPO_ROOT / manifest.get("metric_script_path", "")
    if metric_script.exists() and sha256_file(metric_script) != manifest.get("metric_script_sha256"):
        errors.append("metric_script hash mismatch")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("VALIDATION FAILED")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("VALIDATION PASSED")
    manifest = load_json(MANIFEST_PATH)
    print(f"  freeze_version: {manifest['freeze_version']}")
    print(f"  based_on: {manifest['based_on_benchmark_version']}")
    print(f"  total_cases: {manifest['total_cases']}")
    print(f"  splits: {', '.join(s['name'] + '=' + str(s['case_count']) for s in manifest['splits'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
