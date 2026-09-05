#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lifecycle 边界测试（工作包 B，评审 §三.放行条件 —— 测试先于实现）。

十个场景一一对应 GPT-6 评审为 lifecycle schema 实施列出的放行测试：
每个测试方法名即场景名。测试驱动【真实】主链模块：
lifecycle_adjudicator 产出决策 -> decision_to_patch 物化为 patch
-> reconcile_patch.reconcile 机械复核 -> apply_patch.apply_patch 应用，
再对最终节点状态断言。

实现顺序纪律：本文件先于 lifecycle_fields.py / lifecycle_adjudicator.py 提交；
提交本文件时测试必须失败（ImportError），由 check_test_commit_ordering.py 取证。
"""

from __future__ import annotations

import sys
import unittest
from typing import Any

from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import apply_patch as apply_mod  # noqa: E402
import reconcile_patch as reconcile_mod  # noqa: E402
from lifecycle_adjudicator import adjudicate_event, decision_to_patch  # noqa: E402
from lifecycle_fields import adjudication_key  # noqa: E402


# ---------------------------------------------------------------- 帮助函数


def make_event(
    event_id: str,
    observed_at: str,
    entity_ref: str,
    content: str,
    *,
    lifecycle_ref: str | None = None,
    state_slot: str | None = None,
    lifecycle_seq: int | None = None,
    effective_at: str | None = None,
    source: str | None = "user",
    state: str | None = None,
    alias_hints: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "event_id": event_id,
        "observed_at": observed_at,
        "effective_at": effective_at,
        "source": source,
        "payload": {
            "entity_ref": entity_ref,
            "lifecycle_ref": lifecycle_ref,
            "state_slot": state_slot,
            "lifecycle_seq": lifecycle_seq,
            "node_type": "Fact",
            "content": content,
            "state": state,
            "alias_hints": alias_hints,
        },
    }


def make_node(
    node_id: str,
    entity_ref: str,
    content: str,
    *,
    lifecycle_ref: str | None = None,
    state_slot: str | None = None,
    lifecycle_seq: int | None = None,
    observed_at: str | None = None,
    state: str = "open",
    status: str = "active",
    created_turn: int = 1,
    source: str | None = "user",
) -> dict[str, Any]:
    node: dict[str, Any] = {
        "node_id": node_id,
        "entity_ref": entity_ref,
        "lifecycle_ref": lifecycle_ref,
        "state_slot": state_slot,
        "content": content,
        "node_type": "Fact",
        "state": state,
        "status": status,
        "created_turn": created_turn,
        "source": source,
    }
    if lifecycle_seq is not None:
        node["lifecycle_seq"] = lifecycle_seq
    if observed_at is not None:
        node["observed_at"] = observed_at
    return node


def make_graph(nodes: list[dict[str, Any]], turn_counter: int = 1) -> dict[str, Any]:
    return {
        "turn_counter": turn_counter,
        "nodes": {n["node_id"]: dict(n) for n in nodes},
        "edges": [],
    }


def node_status(graph: dict[str, Any], node_id: str) -> str:
    return graph["nodes"][node_id]["status"]


def run_decision(
    graph: dict[str, Any],
    event: dict[str, Any],
    *,
    next_node_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """adjudicate -> 物化 patch -> reconcile 复核 -> apply 应用。返回 (新图, 决策)。"""
    decision = adjudicate_event(event, graph)
    patch = decision_to_patch(decision, event, node_id=next_node_id)
    report = reconcile_mod.reconcile(graph, patch)
    if not report.get("ok"):
        raise AssertionError(f"reconcile 拒绝了合法决策的 patch: {report['errors']}")
    new_graph = apply_mod.apply_patch(graph, patch)
    return new_graph, decision


# ---------------------------------------------------------------- 十个边界场景


class LifecycleBoundaryTest(unittest.TestCase):
    def test_same_lifecycle_legal_progression_supersedes(self):
        """同 lifecycle 的合法单流推进：新状态取代旧状态。"""
        graph = make_graph([
            make_node("n_0001", "plan-A", "执行方案A v1", lifecycle_ref="lc-plan-a", state_slot="execution_status"),
        ])
        event = make_event(
            "ev_002", "2026-09-05T10:00:00Z", "plan-A", "执行方案A v2（已部署）",
            lifecycle_ref="lc-plan-a", state_slot="execution_status", lifecycle_seq=2,
        )
        new_graph, decision = run_decision(graph, event, next_node_id="n_0002")

        self.assertEqual(decision.action, "supersede")
        self.assertEqual(node_status(new_graph, "n_0001"), "superseded")
        self.assertEqual(node_status(new_graph, "n_0002"), "active")

    def test_same_lifecycle_different_state_slots_coexist(self):
        """同 lifecycle 的不同状态维度共存：执行状态与产物位置互不取代。"""
        graph = make_graph([
            make_node("n_0001", "build-job", "构建进行中", lifecycle_ref="lc-build-7", state_slot="execution_status"),
        ])
        event = make_event(
            "ev_002", "2026-09-05T10:00:00Z", "build-job", "产物输出到 dist/v2",
            lifecycle_ref="lc-build-7", state_slot="output_path", lifecycle_seq=1,
        )
        new_graph, decision = run_decision(graph, event, next_node_id="n_0002")

        self.assertEqual(decision.action, "append")
        self.assertEqual(node_status(new_graph, "n_0001"), "active", "不同 state_slot 不得被取代")
        self.assertEqual(node_status(new_graph, "n_0002"), "active")

    def test_different_lifecycles_no_crosstalk(self):
        """不同 lifecycle 不串扰：同实体的新计划不得取代旧计划。"""
        graph = make_graph([
            make_node("n_0001", "quant-assistant", "采用方案A", lifecycle_ref="lc-round-5", state_slot="execution_status"),
        ])
        event = make_event(
            "ev_002", "2026-09-05T10:00:00Z", "quant-assistant", "新周期采用方案B",
            lifecycle_ref="lc-round-6", state_slot="execution_status", lifecycle_seq=1,
        )
        new_graph, decision = run_decision(graph, event, next_node_id="n_0002")

        self.assertEqual(decision.action, "append")
        self.assertEqual(node_status(new_graph, "n_0001"), "active", "跨 lifecycle 禁止失效")
        self.assertEqual(node_status(new_graph, "n_0002"), "active")

    def test_alias_change_same_lifecycle_keeps_adjudication_key(self):
        """别名变化但 lifecycle 不变：归属不变，正常推进。"""
        graph = make_graph([
            make_node("n_0001", "strategy-researcher", "调研中 v1", lifecycle_ref="lc-sr-1", state_slot="execution_status"),
        ])
        event = make_event(
            "ev_002", "2026-09-05T10:00:00Z", "strategy_researcher", "调研完成 v2",
            lifecycle_ref="lc-sr-1", state_slot="execution_status", lifecycle_seq=2,
        )
        self.assertEqual(
            adjudication_key(event["payload"]),
            adjudication_key({"lifecycle_ref": "lc-sr-1", "entity_ref": "strategy-researcher"}),
            "lifecycle_ref 存在时 adjudication_key 必须取 lifecycle_ref，与 surface 别名无关",
        )
        new_graph, _ = run_decision(graph, event, next_node_id="n_0002")

        self.assertEqual(node_status(new_graph, "n_0001"), "superseded")
        self.assertEqual(node_status(new_graph, "n_0002"), "active")

    def test_legacy_record_without_lifecycle_ref_falls_back_to_entity_ref(self):
        """旧记录无 lifecycle、新记录也无 lifecycle：回退 entity_ref 桶，旧行为不变。"""
        graph = make_graph([
            make_node("n_0001", "duty-reporter", "周报 v1"),
        ])
        assert adjudication_key({"entity_ref": "duty-reporter"}) == "duty-reporter"
        event = make_event("ev_002", "2026-09-05T10:00:00Z", "duty-reporter", "周报 v2")
        new_graph, decision = run_decision(graph, event, next_node_id="n_0002")

        self.assertEqual(decision.action, "supersede")
        self.assertEqual(node_status(new_graph, "n_0001"), "superseded")
        self.assertEqual(node_status(new_graph, "n_0002"), "active")

    def test_late_arriving_old_event_respects_sequence_authority(self):
        """晚到旧事件：observed_at 早于已处理事件的同槽位事件不得覆盖较新状态。"""
        graph = make_graph([
            make_node(
                "n_0001", "plan-A", "方案A 已取消", lifecycle_ref="lc-plan-a",
                state_slot="execution_status", observed_at="2026-09-05T12:00:00Z",
            ),
        ])
        stale_event = make_event(
            "ev_late", "2026-09-05T09:00:00Z", "plan-A", "方案A 执行中（晚到三小时的旧观测）",
            lifecycle_ref="lc-plan-a", state_slot="execution_status", lifecycle_seq=1,
        )
        new_graph, decision = run_decision(graph, stale_event, next_node_id="n_0002")

        self.assertEqual(decision.action, "quarantine", "晚到旧事件必须进入保守隔离分支")
        self.assertEqual(node_status(new_graph, "n_0001"), "active", "取消状态不得被晚到旧观测覆盖")
        self.assertNotIn("n_0002", new_graph["nodes"], "保守隔离不落新节点")

    def test_duplicate_event_is_idempotent(self):
        """重复事件：同 event_id 重放不产生新节点、不产生新失效。"""
        graph = make_graph([
            make_node("n_0001", "plan-A", "方案A v1", lifecycle_ref="lc-plan-a", state_slot="execution_status"),
        ])
        event = make_event(
            "ev_002", "2026-09-05T10:00:00Z", "plan-A", "方案A v2",
            lifecycle_ref="lc-plan-a", state_slot="execution_status", lifecycle_seq=2,
        )
        once_graph, _ = run_decision(graph, event, next_node_id="n_0002")
        twice_graph, decision = run_decision(once_graph, event, next_node_id="n_0003")

        self.assertEqual(decision.action, "duplicate_noop", "重复 event_id 必须幂等跳过")
        self.assertEqual(
            len(twice_graph["nodes"]),
            len(once_graph["nodes"]),
            "重复事件不得新增节点",
        )

    def test_provenance_conflict_yields_contests_not_silent_overwrite(self):
        """provenance 冲突：同 key 同槽位、来源冲突且语义互斥、无明确时间推进时 CONTESTS。"""
        graph = make_graph([
            make_node("n_0001", "price-band", "区间 50-60", lifecycle_ref="lc-price",
                      state_slot="band", state="band-50-60", source="tool:pricing-api"),
        ])
        event = make_event(
            "ev_002", "2026-09-05T10:00:00Z", "price-band", "区间 55-65",
            lifecycle_ref="lc-price", state_slot="band", lifecycle_seq=2,
            state="band-55-65", source="tool:market-feed",
        )
        new_graph, decision = run_decision(graph, event, next_node_id="n_0002")

        self.assertEqual(decision.action, "contests")
        self.assertEqual(node_status(new_graph, "n_0001"), "active", "冲突双方都必须留在当前态等待裁定")
        self.assertEqual(node_status(new_graph, "n_0002"), "active")

    def test_revival_preserves_interpretable_history(self):
        """revival 后历史仍可解释：恢复方案 A 不得抹去 A 曾失效的事实。"""
        graph = make_graph([
            make_node("n_0001", "plan-A", "采用方案A", lifecycle_ref="lc-plan-a", state_slot="execution_status"),
            make_node(
                "n_0002", "plan-B", "改用方案B", lifecycle_ref="lc-plan-b",
                state_slot="execution_status",
            ),
        ])
        # 终态事件（cancelled）：落地即为非活跃，当前态被清空
        graph, _ = run_decision(graph, make_event(
            "ev_kill_a", "2026-09-05T10:00:00Z", "plan-A", "取消方案A",
            lifecycle_ref="lc-plan-a", state_slot="execution_status", lifecycle_seq=2,
            state="cancelled",
        ), next_node_id="n_0003")
        self.assertEqual(node_status(graph, "n_0001"), "superseded")
        self.assertEqual(node_status(graph, "n_0003"), "superseded", "终态事件节点落地即非活跃")

        revive_event = make_event(
            "ev_revive", "2026-09-05T14:00:00Z", "plan-A", "恢复方案A（新决策）",
            lifecycle_ref="lc-plan-a", state_slot="execution_status", lifecycle_seq=3,
        )
        revived_graph, decision = run_decision(graph, revive_event, next_node_id="n_0004")

        self.assertEqual(decision.action, "revives")
        self.assertEqual(node_status(revived_graph, "n_0001"), "superseded", "旧节点不得被重新激活")
        self.assertEqual(node_status(revived_graph, "n_0004"), "active", "revival 落在新节点上")
        relations = [
            (e["relation"], e["source"], e["target"]) for e in revived_graph["edges"]
        ]
        revive_edges = [r for r in relations if r[0] == "REVIVES" and r[1] == "n_0004"]
        self.assertTrue(
            revive_edges,
            "revival 必须以 REVIVES 边连接新节点与失效点，保留可解释历史",
        )

    def test_insufficient_fields_abstains_conservatively(self):
        """字段不足时保守失败：无法确定顺序的同槽位事件弃权，不猜测。"""
        graph = make_graph([
            make_node("n_0001", "plan-A", "方案A 状态未知时点", lifecycle_ref="lc-plan-a",
                      state_slot="execution_status", observed_at="2026-09-05T10:00:00Z"),
        ])
        ambiguous = make_event(
            "ev_amb", "2026-09-05T10:00:00Z", "plan-A", "同时点观测但缺 lifecycle_seq",
            lifecycle_ref="lc-plan-a", state_slot="execution_status", lifecycle_seq=None,
        )
        new_graph, decision = run_decision(graph, ambiguous, next_node_id="n_0002")

        self.assertEqual(decision.action, "abstain", "无法判定顺序时必须弃权")
        self.assertEqual(node_status(new_graph, "n_0001"), "active", "弃权不得改变当前态")
        self.assertNotIn("n_0002", new_graph["nodes"], "弃权不落新节点")


if __name__ == "__main__":
    unittest.main()
