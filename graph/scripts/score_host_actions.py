#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""行动收益指标评分器（工作包 D4，评审 §四.4 的主指标）。

只读 traces，不参与运行。成对运行的 trace 契约（paired_trace.v1）：

    traces/<arm>/turn_NNN.json：
    {
      "turn_id": "host-turn-008",
      "arm": "cl_v0" | "baseline",
      "actions": [
        {
          "action_id": "a001",
          "kind": "edit|command|message",
          "entity_refs": [{"entity": "impl-owner", "state_assumed": "agent-wang"}],
          "tokens_in": 0, "tokens_out": 0, "latency_ms": 0, "cost_usd": 0.0
        }
      ],
      "replan": false,
      "cl_snapshot": {                       # 两臂都必须附 CL 事后状态快照
        "state_revision": "0002:ab12cd34ef56",
        "current_states": {"impl-owner": "agent-liu", "...": "..."}
      },
      "cl_verdict": {                        # 仅 cl_v0 臂
        "readiness": "blocked",
        "review_justified": null             # blocked 时由人工事后复核回填 true/false
      },
      "constraint_violations": ["..."]       # 命中预注册 constraints 的说明（人工判定回填）
    }

公式见 paired_run_preregistration.json 的 metric_formulas。

用法：
    python graph/scripts/score_host_actions.py \
        --traces <contextledger-host>/traces/paired_run_001 \
        --preregistration graph/projects/abu_modern/host_integration/paired_run_preregistration.json \
        --out graph/projects/abu_modern/host_integration/paired_run_results.json
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


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def git_capture(args: list[str]) -> str:
    return subprocess.run(
        ["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8"
    ).stdout.strip()


def is_action_stale(action: dict[str, Any], cl_snapshot: dict[str, Any]) -> bool:
    """行动引用的实体状态在行动时点已被 CL 当前态更新 → stale。"""
    current_states = cl_snapshot.get("current_states", {})
    for ref in action.get("entity_refs", []):
        entity = str(ref.get("entity") or "")
        assumed = str(ref.get("state_assumed") or "").strip().lower()
        actual = str(current_states.get(entity) or "").strip().lower()
        if entity and assumed and actual and assumed != actual:
            return True
    return False


def score_arm(turns: list[dict[str, Any]], arm_id: str) -> dict[str, Any]:
    total_actions = 0
    stale_actions = 0
    violated_actions = 0
    replan_turns = 0
    blocked_turns = 0
    needless_blocks = 0
    tokens_in = tokens_out = 0
    latency_ms = 0
    cost_usd = 0.0
    missing_snapshot_turns = 0

    for turn in turns:
        snapshot = turn.get("cl_snapshot") or {}
        if not snapshot.get("current_states"):
            missing_snapshot_turns += 1
        for action in turn.get("actions", []):
            total_actions += 1
            if snapshot.get("current_states") and is_action_stale(action, snapshot):
                stale_actions += 1
            if turn.get("constraint_violations"):
                violated_actions += 1
            tokens_in += int(action.get("tokens_in") or 0)
            tokens_out += int(action.get("tokens_out") or 0)
            latency_ms += int(action.get("latency_ms") or 0)
            cost_usd += float(action.get("cost_usd") or 0.0)
        if turn.get("replan"):
            replan_turns += 1
        verdict = turn.get("cl_verdict") or {}
        if arm_id == "cl_v0" and verdict.get("readiness") == "blocked":
            blocked_turns += 1
            if verdict.get("review_justified") is False:
                needless_blocks += 1

    return {
        "arm": arm_id,
        "turn_count": len(turns),
        "action_count": total_actions,
        "missing_cl_snapshot_turns": missing_snapshot_turns,
        "stale_action_rate": round(stale_actions / total_actions, 4) if total_actions else None,
        "constraint_violation_rate": round(violated_actions / total_actions, 4) if total_actions else None,
        "replan_rate": round(replan_turns / len(turns), 4) if turns else None,
        "needless_block_rate": round(needless_blocks / blocked_turns, 4) if blocked_turns else 0.0,
        "blocked_turns": blocked_turns,
        "cost": {
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "latency_ms": latency_ms,
            "cost_usd": round(cost_usd, 4),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--traces", required=True, help="成对运行 traces 目录（内含 <arm>/turn_*.json）")
    parser.add_argument(
        "--preregistration",
        default="graph/projects/abu_modern/host_integration/paired_run_preregistration.json",
    )
    parser.add_argument(
        "--out",
        default="graph/projects/abu_modern/host_integration/paired_run_results.json",
    )
    args = parser.parse_args()

    traces_dir = Path(args.traces)
    if not traces_dir.exists():
        print(f"traces 目录不存在: {traces_dir}", file=sys.stderr)
        return 2
    prereg = load_json(PROJECT_ROOT / args.preregistration) if not Path(args.preregistration).is_absolute() else load_json(Path(args.preregistration))

    arm_results = []
    for arm_dir in sorted(p for p in traces_dir.iterdir() if p.is_dir()):
        turn_files = sorted(arm_dir.glob("turn_*.json"))
        turns = [load_json(f) for f in turn_files]
        arm_results.append(score_arm(turns, arm_dir.name))

    by_arm = {r["arm"]: r for r in arm_results}
    comparison = None
    if "cl_v0" in by_arm and "baseline" in by_arm:
        cl, base = by_arm["cl_v0"], by_arm["baseline"]
        cl_stale = cl["stale_action_rate"]
        base_stale = base["stale_action_rate"]
        comparison = {
            "stale_action_rate_cl_le_baseline": (
                None if cl_stale is None or base_stale is None else cl_stale <= base_stale
            ),
            "needless_block_rate_cl_v0": cl["needless_block_rate"],
            "cost_delta": {
                "tokens_in": cl["cost"]["tokens_in"] - base["cost"]["tokens_in"],
                "tokens_out": cl["cost"]["tokens_out"] - base["cost"]["tokens_out"],
                "latency_ms": cl["cost"]["latency_ms"] - base["cost"]["latency_ms"],
                "cost_usd": round(cl["cost"]["cost_usd"] - base["cost"]["cost_usd"], 4),
            },
            "honesty_note": "成本差如实呈现；若 CL 臂更贵，不得隐藏",
        }

    results = {
        "kind": "paired_run_results.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "traces_dir": str(traces_dir),
        "preregistration_ref": args.preregistration,
        "preregistration_commit": git_capture(
            ["rev-parse", "HEAD", "--", args.preregistration]
        ).split()[0] if git_capture(["rev-parse", "HEAD"]) else None,
        "scenario_id": prereg.get("scenario_id"),
        "arms": arm_results,
        "comparison": comparison,
        "acceptance_gate": prereg.get("acceptance_gate"),
        "gate_verdict": None,
    }
    if comparison is not None:
        gate = comparison.get("stale_action_rate_cl_le_baseline")
        needless = comparison.get("needless_block_rate_cl_v0", 1.0)
        if gate is None:
            results["gate_verdict"] = "INCOMPLETE_MISSING_SNAPSHOTS"
        else:
            results["gate_verdict"] = "PASS" if (gate and needless <= 0.2) else "FAIL"

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote paired run results: {out}")
    for r in arm_results:
        print(f"  {r['arm']}: stale_action_rate={r['stale_action_rate']} replan_rate={r['replan_rate']} needless_block={r['needless_block_rate']}")
    if results["gate_verdict"]:
        print(f"gate: {results['gate_verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
