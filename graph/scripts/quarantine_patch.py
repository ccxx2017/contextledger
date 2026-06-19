#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
quarantine_patch.py

最小隔离辅助脚本：
当 reconcile_patch.py 或 graph_lint.py 失败时，
将 patch 移入 quarantine/ 目录并写入失败记录。

用法示例：
  python scripts/reconcile_patch.py graph.json patch.json --out report.json
  if ($LASTEXITCODE -ne 0) {
      python scripts/quarantine_patch.py --turn 6 --patch patch.json --report report.json --stage reconcile
  }
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, obj: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Quarantine a failed patch.")
    parser.add_argument("--turn", type=int, required=True, help="Turn ID")
    parser.add_argument("--patch", required=True, help="Path to the failed patch JSON")
    parser.add_argument("--report", help="Path to the failure report JSON (from reconcile or lint)")
    parser.add_argument("--stage", required=True, choices=["reconcile", "lint", "apply"], help="Failure stage")
    parser.add_argument("--reason", default="failed after max retries or manual review required")
    parser.add_argument("--max-retries", type=int, default=3, help="Max retry count")
    parser.add_argument("--quarantine-dir", default="quarantine", help="Quarantine directory")

    args = parser.parse_args()

    quarantine_dir = Path(args.quarantine_dir)
    quarantine_dir.mkdir(parents=True, exist_ok=True)

    # 移动 patch 到隔离区
    patch_path = Path(args.patch)
    quarantine_patch_path = quarantine_dir / f"turn_{args.turn:03d}_failed_patch.json"
    if patch_path.exists():
        shutil.copy2(patch_path, quarantine_patch_path)

    # 读取报告
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    if args.report:
        try:
            report = load_json(args.report)
            errors = report.get("errors", [])
            warnings = report.get("warnings", [])
        except Exception:
            pass

    record = {
        "turn_id": args.turn,
        "patch_path": str(quarantine_patch_path),
        "original_patch": str(args.patch),
        "stage": args.stage,
        "errors": errors,
        "warnings": warnings,
        "max_retries": args.max_retries,
        "decision": "not_applied",
        "reason": args.reason,
        "quarantined_at": datetime.now(timezone.utc).isoformat(),
    }

    record_path = quarantine_dir / f"turn_{args.turn:03d}_failed.json"
    write_json(record_path, record)

    print(f"Quarantined to: {record_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
