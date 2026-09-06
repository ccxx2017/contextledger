#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lifecycle A/B 驱动（工作包 B4，B 门的收口证据）。

做三件事并汇总 reports/lifecycle_B/ab_summary.json：
  1. legacy 重放：从 seed + patches/ 全链重放，与冻结基线 graph_state 逐字节比对
     —— "无 lifecycle 字段的旧行为不回归" 的直接证据；
  2. 失效差异解释：explain_invalidation_diff（冻结基线 vs 本轮重放），
     每条新增/消失失效必须可归因（本轮预期为空差异：能力新增、零行为改变）；
  3. shadow 对照：跑 development split（lifecycle 语义已激活的评测链），
     如实记录 gate 状态（stage04c123 封存的已知 BLOCK 不在本轮解决）。

用法：
    python graph/scripts/run_lifecycle_ab.py
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "graph" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

PROJECT_ID = "abu_modern"
PROJECT_DIR = PROJECT_ROOT / "graph" / "projects" / PROJECT_ID
OUT_DIR = PROJECT_ROOT / "reports" / "lifecycle_B"

import apply_patch as apply_mod  # noqa: E402
from explain_invalidation_diff import explain_diff  # noqa: E402


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def git_capture(args: list[str]) -> str:
    return subprocess.run(
        ["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8"
    ).stdout.strip()


def replay_full_chain() -> tuple[dict[str, Any], int]:
    """seed + patch_001..N 全链重放，返回 (最终图, 重放轮数)。"""
    seed = load_json(PROJECT_ROOT / "graph" / "graph_state.seed.json")
    patches = sorted((PROJECT_DIR / "patches").glob("patch_*.json"))
    graph = seed
    for patch_path in patches:
        graph = apply_mod.apply_patch(graph, load_json(patch_path))
    return graph, len(patches)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-shadow", action="store_true", help="跳过 shadow 对照")
    args = parser.parse_args()

    started = datetime.now(timezone.utc)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fatal: list[str] = []

    # 1. legacy 全链重放 + 字节比对
    replayed, patch_count = replay_full_chain()
    frozen = load_json(PROJECT_DIR / "graph_state.json")
    byte_identical = replayed == frozen
    if not byte_identical:
        fatal.append("legacy 全链重放与冻结基线 graph_state 不一致——lifecycle 接入引入了回归")

    # 2. 失效差异解释（预期空差异；一旦非空必须逐条归因）
    diff = explain_diff(frozen, replayed)
    if not diff["all_attributed"]:
        fatal.append("存在无法归因的失效差异（causing_rule=unattributed）")
    diff_path = OUT_DIR / "invalidation_diff.json"
    diff_path.write_text(json.dumps(diff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 3. shadow 对照（lifecycle 语义激活的评测链）
    shadow = {}
    if not args.skip_shadow:
        runner = PROJECT_DIR / "shadow_replay" / "scripts" / "benchmark_shadow_runner.py"
        result = subprocess.run(
            [sys.executable, str(runner), "--split", "development"],
            cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8",
        )
        runs_dir = PROJECT_DIR / "shadow_replay" / "runs" / "stage04b" / "development"
        if runs_dir.exists():
            latest = sorted(runs_dir.iterdir())[-1]
            summary_path = latest / "split_summary.json"
            if summary_path.exists():
                summary = load_json(summary_path)
                shadow = {
                    "split": "development",
                    "gate": summary.get("split_gate_decision"),
                    "aggregate": summary.get("aggregate"),
                    "note": "lifecycle 语义在 shadow 评测链中激活；已知 BLOCK 见 stage04c123 封存报告",
                }

    # 4. 主链 × fixture 交叉核对（B 门最后一项）
    crosscheck_path = OUT_DIR / "mainchain_fixture_crosscheck.json"
    crosscheck = None
    if crosscheck_path.exists():
        payload = load_json(crosscheck_path)
        crosscheck = {
            "path": str(crosscheck_path.relative_to(PROJECT_ROOT)),
            "verdict_counts": payload.get("verdict_counts"),
            "note": "无注记缺口(mainchain_gap)=0 即 B 门通过；规格分歧与文档化偏离逐条带 reason",
        }

    summary = {
        "kind": "lifecycle_ab_summary.v1",
        "generated_at": started.isoformat(),
        "git": {
            "branch": git_capture(["branch", "--show-current"]),
            "commit": git_capture(["rev-parse", "HEAD"]),
        },
        "legacy_replay": {
            "patch_count": patch_count,
            "byte_identical_to_frozen_baseline": byte_identical,
            "meaning": "无 lifecycle 字段的旧行为不回归（B 门第 2 条）",
        },
        "invalidation_diff": {
            "path": str(diff_path.relative_to(PROJECT_ROOT)),
            "summary": diff["summary"],
            "all_attributed": diff["all_attributed"],
            "meaning": "新增/消失失效逐条归因（B 门第 4 条）；空差异=本轮为零行为改变的能力新增",
        },
        "shadow_comparison": shadow,
        "mainchain_fixture_crosscheck": crosscheck,
        "fatal": fatal,
        "ab_gate": "PASS" if not fatal else "BLOCK",
    }
    out_path = OUT_DIR / "ab_summary.json"
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"legacy replay: {patch_count} patches, byte_identical={byte_identical}")
    print(f"invalidation diff: +{diff['summary']['added']} / -{diff['summary']['removed']}")
    print(f"ab_gate: {summary['ab_gate']}")
    print(f"Wrote {out_path}")
    return 0 if not fatal else 1


if __name__ == "__main__":
    sys.exit(main())
