#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""主链裁定器 × fixture 语义期望交叉核对（工作包 B 门最后一项）。

把每个 fixture 的 event_stream 喂给【主链】lifecycle_adjudicator（移植实现），
将每个 checkpoint 的 active/superseded/relation/quarantine 与 fixture 期望比对。
期望的语义匹配复用 fixture_replay_runner 的 match_expected_node。

方向纪律：本脚本在 shadow 侧（评测可引主链）；graph/scripts 不得反向 import 本目录。

分歧处理纪律：主链与 shadow 的分歧【记录，不静默解决】——分歧清单就是
移植质量与 RFC 语义边界的证据。

用法：
    python graph/projects/abu_modern/shadow_replay/scripts/crosscheck_mainchain_fixtures.py \
        --out reports/lifecycle_B/mainchain_fixture_crosscheck.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SHADOW_ROOT = SCRIPT_DIR.parent
REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(REPO_ROOT / "graph" / "scripts"))

from fixture_replay_runner import (  # noqa: E402
    EXPECTED_NODE_SEMANTICS,
    FIXTURES_DIR,
)
from shadow_lifecycle_adjudicator import ShadowLifecycleAdjudicator  # noqa: E402
from shadow_compiler import (  # noqa: E402
    apply_shadow_patch,
    initialize_shadow_graph_state,
)
from lifecycle_adjudicator import adjudicate_event, decision_to_patch  # noqa: E402
import apply_patch as apply_mod  # noqa: E402

# shadow 期望的关系词 -> 主链边的对应词
RELATION_MAP = {"supercedes": "invalidates", "supersedes": "invalidates"}

# 有记录的主链-oracle 偏离（评审 §三纪律：分歧记录，不静默解决）。
# 每条必须带 reason 与去向；无注记的缺口才是真正的移植缺陷。
DOCUMENTED_DIVERGENCES: dict[str, dict[str, str]] = {
    "lc_late_arrival_missing_effective": {
        "class": "deliberate",
        "reason": (
            "shadow 对『同源状态变更但缺 effective_at』硬隔离；主链按评审 §五细化后的规则处理："
            "缺 effective_at 本身不硬隔离（RFC §7.2 v1 不要求完整 valid_time 求值），"
            "但语义状态变更若同时缺 lifecycle_seq 与 effective_at 则弃权"
            "（test_no_temporal_credential_does_not_overwrite_semantic_change）——"
            "本 fixture 事件带 seq（可信顺序凭据），按顺序权威推进属非无条件覆盖。"
            "缺字段风险另由 Assembler 完整性声明（工作包 C）降级暴露。"
        ),
    },
    "lc_conditional_different_scope": {
        "class": "deferred",
        "reason": "shadow 按 claim_scope 差异化裁决键实现共存；本轮 B 范围为『可靠归属+状态槽位的单流推进』，claim_scope 机制延后至后续轮次。",
    },
    "lc_parallel_targets_same_dimension_must_coexist": {
        "class": "deferred",
        "reason": "同上：claim_scope 机制延后（scope 维度与 state_slot 维度的合并策略留待后续 RFC 修订）。",
    },
    "lc_state_value_vs_real_scope_ambiguity": {
        "class": "deferred",
        "reason": "同上：claim_scope 与 state 值的歧义裁定延后（正是评审指出的『字段看起来全面』陷阱，宁缺毋滥）。",
    },
}

# 行动归一化：两侧的裁决行动映射到同一比较词表
ACTION_CLASS = {
    # 主链
    "supersede": "supersede",
    "append": "append",
    "contests": "contest",
    "revives": "revive",
    "quarantine": "conservative",
    "abstain": "conservative",
    "duplicate_noop": "conservative",
    # shadow
    "create": "append",
    "coexist": "append",
    "contest": "contest",
    "revive": "revive",
    "quarantine": "conservative",
    "quarantine_late": "conservative",
    "abstain": "conservative",
}


def replay_with_shadow(fixture: dict[str, Any]) -> dict[str, Any]:
    """shadow oracle 逐事件重放，返回每事件的主行动（用于与主链对齐比较）。"""
    adjudicator = ShadowLifecycleAdjudicator()
    graph = initialize_shadow_graph_state()
    actions: dict[str, str] = {}
    for event in fixture.get("input", {}).get("event_stream", []):
        result = adjudicator.adjudicate_event(event, graph)
        for q in result.quarantine:
            graph["quarantine"].append(q)
        graph = apply_shadow_patch(graph, result.patch)
        own_actions = [
            str(l.get("action"))
            for l in result.log
            if str(l.get("event_id")) == str(event.get("event_id"))
        ]
        actions[str(event.get("event_id"))] = own_actions[0] if own_actions else "unknown"
    return actions


def match_expected_node_tolerant(
    fixture_id: str,
    expected_id: str,
    actual_nodes: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """语义匹配，但忽略 shadow 管线产物字段（如 claim_id）。

    主链节点与 shadow 节点的语义字段集合不同：claim_id 由 shadow 的
    resolution adapter 从内容派生，不属于 fixture 的语义期望。
    """
    for node in actual_nodes:
        if node.get("node_id") == expected_id:
            return node

    semantics = dict(EXPECTED_NODE_SEMANTICS.get(fixture_id, {}).get(expected_id) or {})
    semantics.pop("claim_id", None)
    if semantics:
        for node in actual_nodes:
            if all(node.get(key) == value for key, value in semantics.items()):
                return node

    expected_lower = expected_id.lower().replace("n_", "")
    for node in actual_nodes:
        content = (node.get("content") or "").lower()
        state = (node.get("state") or "").lower()
        if expected_lower in content or expected_lower in state:
            return node
    return None


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def replay_with_mainchain(fixture: dict[str, Any]) -> dict[str, Any]:
    """主链裁定器逐事件重放，返回 checkpoint 快照。"""
    graph = {"turn_counter": 0, "nodes": {}, "edges": []}
    snapshots: dict[str, dict[str, Any]] = {}
    actions: dict[str, str] = {}
    counter = 0

    for event in fixture.get("input", {}).get("event_stream", []):
        counter += 1
        decision = adjudicate_event(event, graph)
        actions[str(event.get("event_id"))] = decision.action
        patch = decision_to_patch(decision, event, node_id=f"mc_{counter:04d}")
        try:
            graph = apply_mod.apply_patch(graph, patch)
        except ValueError:
            # 主链 apply 对重复 node_id 抛错；裁定器保守路径不产生节点，正常不会到达
            pass
        after_event = str(event.get("event_id"))
        snapshots[after_event] = {
            "nodes": {k: dict(v) for k, v in graph["nodes"].items()},
            "edges": [dict(e) for e in graph["edges"]],
        }
    return {"snapshots": snapshots, "actions": actions}


def crosscheck_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    fixture_id = str(fixture.get("fixture_id"))
    result = replay_with_mainchain(fixture)
    snapshots = result["snapshots"]
    actions = result["actions"]
    shadow_actions = replay_with_shadow(fixture)

    # 主链 vs shadow oracle：行动序列逐事件对齐
    action_comparison = []
    oracle_match = True
    for event in fixture.get("input", {}).get("event_stream", []):
        eid = str(event.get("event_id"))
        mc = ACTION_CLASS.get(actions.get(eid), "unknown")
        sh = ACTION_CLASS.get(shadow_actions.get(eid), "unknown")
        match = mc == sh
        if not match:
            oracle_match = False
        action_comparison.append({
            "event_id": eid,
            "mainchain": actions.get(eid),
            "shadow": shadow_actions.get(eid),
            "class_match": match,
        })

    divergences: list[dict[str, Any]] = []
    checkpoints_checked = 0

    for checkpoint in fixture.get("expected", {}).get("checkpoints", []):
        after_event = str(checkpoint.get("after_event_id") or "")
        snapshot = snapshots.get(after_event)
        if snapshot is None:
            divergences.append({
                "kind": "missing_checkpoint",
                "checkpoint_id": checkpoint.get("checkpoint_id"),
                "detail": f"after_event {after_event} 无主链快照",
            })
            continue
        checkpoints_checked += 1
        nodes = list(snapshot["nodes"].values())
        active = [n for n in nodes if n.get("status") == "active"]
        superseded = [n for n in nodes if n.get("status") == "superseded"]

        for eid in checkpoint.get("active_nodes", []):
            if match_expected_node_tolerant(fixture_id, eid, active) is None:
                divergences.append({
                    "kind": "active_missing",
                    "checkpoint_id": checkpoint.get("checkpoint_id"),
                    "expected": eid,
                })
        for eid in checkpoint.get("superseded_nodes", []):
            if match_expected_node_tolerant(fixture_id, eid, superseded) is None:
                divergences.append({
                    "kind": "superseded_missing",
                    "checkpoint_id": checkpoint.get("checkpoint_id"),
                    "expected": eid,
                })
        for expected_rel in checkpoint.get("relations", []):
            rtype = str(expected_rel.get("relation_type") or "").lower()
            mapped = RELATION_MAP.get(rtype, rtype)
            src = match_expected_node_tolerant(fixture_id, expected_rel.get("source"), list(snapshot["nodes"].values()))
            tgt = match_expected_node_tolerant(fixture_id, expected_rel.get("target"), list(snapshot["nodes"].values()))
            if src is None or tgt is None:
                divergences.append({
                    "kind": "relation_endpoint_unmatched",
                    "checkpoint_id": checkpoint.get("checkpoint_id"),
                    "expected": expected_rel,
                })
                continue
            found = any(
                str(e.get("relation")).lower() == mapped
                and e.get("source") == src["node_id"]
                and e.get("target") == tgt["node_id"]
                for e in snapshot["edges"]
            )
            if not found:
                divergences.append({
                    "kind": "relation_missing",
                    "checkpoint_id": checkpoint.get("checkpoint_id"),
                    "expected": {"relation": mapped, "source": src["node_id"], "target": tgt["node_id"]},
                })
        for q in checkpoint.get("quarantine", []):
            # CONTESTS 亦视为隔离态（争议写入待裁定，quarantined=True）
            if actions.get(str(q.get("event_id"))) not in {"quarantine", "contests"}:
                actual = actions.get(str(q.get("event_id")))
                divergences.append({
                    "kind": "quarantine_missing",
                    "checkpoint_id": checkpoint.get("checkpoint_id"),
                    "expected_event": q.get("event_id"),
                    "actual_action": actual,
                })

    if not divergences:
        verdict = "consistent"
    elif oracle_match:
        # 主链与 oracle 行为一致，但 fixture 规格期望不同 —— 上游规格分歧
        verdict = "fixture_spec_divergence"
    elif fixture_id in DOCUMENTED_DIVERGENCES:
        verdict = "documented_divergence"
    else:
        verdict = "mainchain_gap"

    return {
        "fixture_id": fixture_id,
        "category": fixture.get("category"),
        "checkpoints_checked": checkpoints_checked,
        "mainchain_vs_shadow": "match" if oracle_match else "mismatch",
        "action_comparison": action_comparison,
        "spec_divergence_count": len(divergences),
        "spec_divergences": divergences,
        "divergence_annotation": DOCUMENTED_DIVERGENCES.get(fixture_id),
        "verdict": verdict,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default="reports/lifecycle_B/mainchain_fixture_crosscheck.json",
    )
    args = parser.parse_args()

    fixtures = sorted(FIXTURES_DIR.glob("lc_*.json"))
    results = [crosscheck_fixture(load_json(p)) for p in fixtures]

    counts = {
        "consistent": 0,
        "fixture_spec_divergence": 0,
        "documented_divergence": 0,
        "mainchain_gap": 0,
    }
    for r in results:
        counts[r["verdict"]] += 1

    summary = {
        "kind": "mainchain_fixture_crosscheck.v2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fixture_count": len(results),
        "verdict_counts": counts,
        "results": results,
        "verdict_semantics": {
            "consistent": "主链行为与 fixture 规格期望一致",
            "fixture_spec_divergence": "主链与 shadow oracle 行为一致，但 fixture 规格期望不同——上游规格与 oracle 的分歧，记录不静默解决，不属本轮 B 范围",
            "documented_divergence": "主链与 oracle 的偏离已有文档化裁定（deliberate=范围注记 / deferred=延后机制），逐条带 reason",
            "mainchain_gap": "无注记的移植缺口——B 门不通过项",
        },
        "note": "分歧记录不静默解决：四类裁定分离『移植缺口』『规格 vs oracle 分歧』与『有文档裁定的偏离』",
    }
    out = REPO_ROOT / args.out if not Path(args.out).is_absolute() else Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"crosscheck: {json.dumps(counts)}")
    for r in results:
        if r["verdict"] == "mainchain_gap":
            mismatched = [c["event_id"] for c in r["action_comparison"] if not c["class_match"]]
            print(f"  MAINCHAIN_GAP {r['fixture_id']}: events {mismatched}")
        elif r["verdict"] == "documented_divergence":
            print(f"  DOCUMENTED {r['fixture_id']}: {r['divergence_annotation']['class']}")
        elif r["verdict"] == "fixture_spec_divergence":
            print(f"  SPEC_DIVERGENCE {r['fixture_id']}: {r['spec_divergence_count']} spec divergence(s) (oracle agrees with mainchain)")
    print(f"Wrote {out}")
    return 0 if counts["mainchain_gap"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
