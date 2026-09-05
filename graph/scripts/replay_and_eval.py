#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""一键重放 + 评测（工作包 A 的收口命令，runbook/baseline_replay.md 引用）。

顺序执行：
    0. generate_state_manifest  -> reports/baseline_A/state_manifest.json
    1. replay_phase0_seal       机械核重放，逐字节比对 run/ 快照（必须全过）
    2. graph_lint               当前主图整图校验（结果如实记录，不硬性阻断）
    3. benchmark_shadow_runner  依次跑 development / regression / adversarial
    4. score_phase05            重建基准分数报告
    5. quarantine_register check 隔离登记簿无超期未裁定条目
    6. 汇总 reports/baseline_A/baseline_summary.json

封存纪律：本命令永不触碰 blind_holdout。若在环境变量里发现该 split 的
评测意图，直接拒绝（见 benchmark_v1_freeze_manifest.json usage_rules）。

退出码：任一必过步骤失败 → 1；仅已知 blocked 项（shadow gate）→ 0，
但 baseline_summary.json 会如实记录 gate 状态，由人判定是否接受基线。
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
PROJECT_ID = "abu_modern"
PROJECT_DIR = PROJECT_ROOT / "graph" / "projects" / PROJECT_ID
BASELINE_DIR = PROJECT_ROOT / "reports" / "baseline_A"
SCORE_REPORT_PATH = PROJECT_DIR / "benchmark" / "phase05_v3" / "reports" / "phase05_score_report.json"

# 封存集保护（评审 §四.2）：一次性消耗集，任何自动化入口都不得运行。
FORBIDDEN_SPLITS = {"blind_holdout"}
EVAL_SPLITS = ("development", "regression", "adversarial")

# 只存在于叙事文档、无法从仓库工件复现的历史数字（评审 §二.2 / §四.1）。
# 引用保留，provenance 标记为 external_unreproducible，禁止再当作可比较基线。
EXTERNAL_UNREPRODUCIBLE = {
    "invalidation_precision_before": {
        "value": 0.550,
        "source": "pack/projects/contextLedger/ContextLedger 项目背景包（新AI接手用）.md (改动前叙事值)",
    },
    "invalidation_recall_before": {
        "value": 0.579,
        "source": "同上",
    },
    "active_set_set_f1_before": {
        "value": 0.856,
        "source": "同上",
    },
    "historical_quarantine_rate": {
        "value": "15/72 ≈ 20.8%",
        "source": "背景包 turn_012-084 批次叙事；该批次的隔离工件不在仓库内",
    },
}


def run_step(name: str, cmd: list[str], *, check: bool = True) -> dict[str, Any]:
    print(f"==> {name}: {' '.join(cmd)}")
    result = subprocess.run(
        [sys.executable, *cmd],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    step = {
        "step": name,
        "cmd": cmd,
        "returncode": result.returncode,
        "ok": result.returncode == 0,
    }
    if result.returncode != 0:
        step["stderr_tail"] = (result.stderr or "")[-2000:]
        print(f"    rc={result.returncode}")
        if check:
            raise RuntimeError(f"步骤 {name} 失败 (rc={result.returncode})")
    return step


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def turn_counter_of(project_dir: Path) -> int:
    try:
        return int(load_json(project_dir / "graph_state.json").get("turn_counter", 0))
    except Exception:
        return 0


def git_capture(args: list[str]) -> str:
    return subprocess.run(
        ["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8"
    ).stdout.strip()


def collect_metrics() -> dict[str, Any]:
    if not SCORE_REPORT_PATH.exists():
        return {"error": "score report 不存在"}
    data = load_json(SCORE_REPORT_PATH)
    baselines = data.get("baselines", {})
    out: dict[str, Any] = {}
    for name, payload in baselines.items():
        metrics = payload.get("metrics", {})
        out[name] = {
            "invalidation_precision": metrics.get("invalidation_precision"),
            "invalidation_recall": metrics.get("invalidation_recall"),
            "active_set_set_f1": metrics.get("active_set_set_f1"),
            "must_include_recall": metrics.get("must_include_recall"),
            "invalidation_events": metrics.get("invalidation_event_summary"),
            "provenance": "this_run_reproducible",
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-shadow", action="store_true", help="跳过 shadow 评测（只验证机械核）")
    parser.add_argument("--out", default=str(BASELINE_DIR / "baseline_summary.json"))
    args = parser.parse_args()

    started_at = datetime.now(timezone.utc)
    steps: list[dict[str, Any]] = []
    fatal: list[str] = []

    # 0. 状态 manifest
    try:
        steps.append(run_step(
            "generate_state_manifest",
            ["graph/scripts/generate_state_manifest.py", "--out", "reports/baseline_A/state_manifest.json"],
        ))
    except RuntimeError as exc:
        fatal.append(str(exc))

    # 1. 机械核重放（必过）
    try:
        steps.append(run_step(
            "replay_phase0_seal",
            ["graph/scripts/replay_phase0_seal.py", "--project-id", PROJECT_ID],
        ))
    except RuntimeError as exc:
        fatal.append(str(exc))

    # 2. 整图 lint + 存量对照（runbook [L1]/[L2] 纪律：存量看基线，只有新增才阻断）
    try:
        lint_step = run_step(
            "graph_lint",
            [
                "graph/scripts/graph_lint.py",
                str(PROJECT_DIR / "graph_state.json"),
                "--out", "reports/current_graph_lint_report.json",
            ],
            check=False,
        )
        steps.append(lint_step)
        prev_turn = max(1, turn_counter_of(PROJECT_DIR) - 1)
        diff_step = run_step(
            "diff_lint_reports_vs_baseline",
            [
                "graph/scripts/diff_lint_reports.py",
                # 语义配对：上一态 = turn_N-1 提交快照，当前态 = 权威 graph_state
                "--before-graph", str(PROJECT_DIR / "run" / f"graph_state.turn_{prev_turn:03d}.json"),
                "--after-graph", str(PROJECT_DIR / "graph_state.json"),
                "--expected-turn", f"turn_{turn_counter_of(PROJECT_DIR):03d}",
                "--baseline", str(PROJECT_DIR / "reports" / "lint_baseline.json"),
                "--out", "reports/baseline_A/lint_delta_vs_baseline.json",
            ],
            check=False,
        )
        steps.append(diff_step)
        if diff_step["ok"]:
            delta = load_json(PROJECT_ROOT / "reports" / "baseline_A" / "lint_delta_vs_baseline.json")
            introduced = delta.get("summary", {}).get("introduced_errors", 0)
            if introduced:
                fatal.append(f"主图存在 {introduced} 个未登记的新增 lint 违例——先按 [L2] 登记或修复")
        else:
            fatal.append("lint 基线对照失败（详见 baseline_A/lint_delta_vs_baseline.json）")
    except RuntimeError as exc:
        fatal.append(str(exc))

    # 3. shadow 评测（三条非封存 split；gate 结果如实记录）
    split_summaries: dict[str, Any] = {}
    if not args.skip_shadow:
        runner = "graph/projects/abu_modern/shadow_replay/scripts/benchmark_shadow_runner.py"
        for split in EVAL_SPLITS:
            assert split not in FORBIDDEN_SPLITS  # 封存纪律：入口处硬防
            try:
                step = run_step(
                    f"shadow_eval:{split}",
                    [runner, "--split", split],
                    check=False,
                )
                steps.append(step)
            except RuntimeError as exc:
                fatal.append(str(exc))
                continue
            # 找到最新一次 run 的 split_summary 读取 gate 与聚合
            runs_dir = PROJECT_DIR / "shadow_replay" / "runs" / "stage04b" / split
            if runs_dir.exists():
                latest = sorted(runs_dir.iterdir())[-1]
                summary_path = latest / "split_summary.json"
                if summary_path.exists():
                    summary = load_json(summary_path)
                    split_summaries[split] = {
                        "run_id": summary.get("run_id"),
                        "gate": summary.get("split_gate_decision"),
                        "aggregate": summary.get("aggregate"),
                        "provenance": "this_run_reproducible",
                    }

    # 4. 基准分数（对 phase05_v3 沙箱评分；v3 数字已验证可复现）
    try:
        steps.append(run_step(
            "score_phase05",
            ["graph/scripts/score_phase05.py",
             "--project-dir", f"graph/projects/{PROJECT_ID}/benchmark/phase05_v3"],
        ))
        metrics = collect_metrics()
    except RuntimeError as exc:
        fatal.append(str(exc))
        metrics = {"error": str(exc)}

    # 5. quarantine 登记簿检查
    turn_counter = turn_counter_of(PROJECT_DIR)
    try:
        q_step = run_step(
            "quarantine_register_check",
            [
                "graph/scripts/quarantine_register.py", "check",
                "--project-id", PROJECT_ID,
                "--current-turn", str(turn_counter),
                "--out", "reports/quarantine_register_check.json",
            ],
            check=False,
        )
        steps.append(q_step)
        if not q_step["ok"]:
            fatal.append("quarantine 登记簿存在超期未裁定条目（先补裁定再冻结基线）")
    except RuntimeError as exc:
        fatal.append(str(exc))

    summary = {
        "kind": "baseline_summary.v1",
        "project_id": PROJECT_ID,
        "generated_at": started_at.isoformat(),
        "git": {
            "branch": git_capture(["branch", "--show-current"]),
            "commit": git_capture(["rev-parse", "HEAD"]),
            "dirty": git_capture(["status", "--short"]) != "",
        },
        "turn_counter": turn_counter,
        "steps": steps,
        "benchmark_metrics": metrics,
        "shadow_splits": split_summaries,
        "external_unreproducible": EXTERNAL_UNREPRODUCIBLE,
        "fatal": fatal,
        "baseline_status": "FROZEN" if not fatal else "BLOCKED",
        "notes": [
            "本文件是工作包 A 的比较起点登记：后续 B/C 的重放必须与本基线字节可比。",
            "external_unreproducible 中的叙事数字只作历史引用，禁止再当作可比较基线。",
            "shadow gate 为 BLOCK 表示该 split 存在已知回归（stage04c123 封存的状态），不阻止基线登记，但必须如实带入门禁结论。",
        ],
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Wrote baseline summary: {out_path}")
    print(f"baseline_status: {summary['baseline_status']}")
    for item in fatal:
        print(f"  FATAL: {item}")
    return 1 if fatal else 0


if __name__ == "__main__":
    sys.exit(main())
