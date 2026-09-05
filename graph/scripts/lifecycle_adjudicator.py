#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""主链 Lifecycle 裁决器（RFC §8/§7/§9 —— 从 shadow 决策表移植重实现）。

来源与隔离纪律：决策表移植自 shadow_replay 的 shadow_lifecycle_adjudicator.py，
但这里是【重新实现】而非 import——shadow 是评测 oracle，与主链必须保持隔离，
不得让主链依赖评测工件（stage04b2 确立的边界）。

裁决阶梯（按序判定，命中即返回）：
  1. duplicate_noop   事件 id 已在图中（幂等）
  2. legacy 回退       载荷无任何 lifecycle 字段 -> 完全保持既有 entity_ref 行为（§13）
  3. alias abstain     声明的别名提示在图中无法解析且无 lifecycle_ref -> 保守弃权
  4. 无同键 active 节点：有同键 superseded 节点 -> revives；否则 append
  5. 有同键 active 节点：
     5a. state_slot 不同（双方都声明）      -> append（COEXISTS，维度共存）
     5b. lifecycle_seq 碰撞（<= 已有）      -> quarantine（保守隔离）
     5c. observed_at 严格更早（晚到旧事件） -> quarantine（不得覆盖较新状态）
     5d. 无法建立"严格更新"（缺 seq 且时间打平/不可比） -> abstain（保守弃权）
     5e. 来源冲突（双方 source 不同且非空） -> contests（CONTESTS，不静默取代）
     5f. 其余                               -> supersede（SUPERSEDES）

行动 -> patch 的物化：supersede/append/contests/revives 产出可应用的 patch；
quarantine/abstain/duplicate_noop 产出空 patch（当前态零改动）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from lifecycle_fields import (
    adjudication_key,
    compare_observation_time,
    has_lifecycle_semantics,
    state_slot_of,
)

SUPERSEDE = "supersede"
APPEND = "append"
CONTESTS = "contests"
REVIVES = "revives"
ABSTAIN = "abstain"
QUARANTINE = "quarantine"
DUPLICATE_NOOP = "duplicate_noop"

# 产出当前态变更的行动（其余行动为保守不动）
STATE_CHANGING_ACTIONS = {SUPERSEDE, APPEND, CONTESTS, REVIVES}

# 终态语义（移植 shadow 决策表）：携带终态 state 的事件节点落地即非活跃，
# 不进入当前态集合——"取消"本身不是一个可持续的状态。
TERMINAL_STATES = {"cancelled", "canceled", "rejected", "withdrawn", "abandoned", "closed"}


@dataclass
class Decision:
    action: str
    reason: str
    superseded_node_ids: list[str] = field(default_factory=list)
    relates_to_node_id: str | None = None  # CONTESTS / REVIVES 的对象节点
    detail: dict[str, Any] = field(default_factory=dict)


def _iter_nodes(graph: dict[str, Any]) -> list[dict[str, Any]]:
    nodes = graph.get("nodes", {})
    if isinstance(nodes, dict):
        return [n for n in nodes.values() if isinstance(n, dict)]
    return [n for n in nodes if isinstance(n, dict)]


def _node_key(node: dict[str, Any]) -> str | None:
    return adjudication_key(node)


def _event_id_of(node: dict[str, Any]) -> str | None:
    value = node.get("_event_id")
    return str(value) if value else None


def find_active_by_key(graph: dict[str, Any], key: str, slot: str | None = None) -> dict[str, Any] | None:
    for node in _iter_nodes(graph):
        if node.get("status") != "active":
            continue
        if _node_key(node) != key:
            continue
        if slot is not None and state_slot_of(node) is not None and state_slot_of(node) != slot:
            continue
        if slot is not None and state_slot_of(node) is None:
            # legacy 节点无 slot 概念：不视为同维度，避免 lifecycle 事件误取代 legacy 节点
            continue
        return node
    return None


def find_superseded_by_key(graph: dict[str, Any], key: str) -> dict[str, Any] | None:
    """同键最近的 superseded 节点（revival 目标）。"""
    candidates = [
        n for n in _iter_nodes(graph)
        if n.get("status") == "superseded" and _node_key(n) == key
    ]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda n: (
            str(n.get("observed_at") or ""),
            int(n.get("created_turn") or 0),
            str(n.get("node_id") or ""),
        ),
    )


def _alias_resolves(graph: dict[str, Any], entity_ref: str, alias_hints: list[str]) -> bool:
    """别名提示是否能在图中解析出同键节点（最小实现：entity_ref 或既有别名互认）。"""
    surface_keys = {str(h) for h in alias_hints}
    surface_keys.add(str(entity_ref))
    for node in _iter_nodes(graph):
        if node.get("entity_ref") in surface_keys:
            return True
        registered = node.get("alias_hints") or []
        if isinstance(registered, list) and surface_keys & {str(a) for a in registered}:
            return True
    return False


def adjudicate_event(event: dict[str, Any], graph: dict[str, Any]) -> Decision:
    """对单条事件做出裁决。事件结构：{event_id, observed_at, effective_at, source, payload{...}}。"""
    payload = event.get("payload") or {}
    event_id = str(event.get("event_id") or "")
    key = adjudication_key(payload)
    slot = state_slot_of(payload)
    source = event.get("source") or payload.get("source")

    # 1. 幂等：事件已在图中
    for node in _iter_nodes(graph):
        if _event_id_of(node) == event_id and event_id:
            return Decision(
                action=DUPLICATE_NOOP,
                reason=f"event_id {event_id} 已存在于节点 {node.get('node_id')}，幂等跳过",
                relates_to_node_id=node.get("node_id"),
            )

    if key is None:
        return Decision(action=ABSTAIN, reason="payload 缺少 entity_ref 与 lifecycle_ref，无法归属，保守弃权")

    # 2. legacy 回退：无任何 lifecycle 字段 -> 保持既有 entity_ref 行为
    if not has_lifecycle_semantics(payload):
        legacy = find_active_by_key(graph, key)
        if legacy is None:
            return Decision(action=APPEND, reason="legacy 模式：无同 entity_ref 活跃节点，直接新增")
        return Decision(
            action=SUPERSEDE,
            reason="legacy 模式：同 entity_ref 活跃节点被新观测取代（保持既有行为，§13）",
            superseded_node_ids=[str(legacy.get("node_id"))],
            relates_to_node_id=legacy.get("node_id"),
            detail={"legacy": True},
        )

    # 3. alias abstain：带别名提示但图中完全无法解析，且事件自身未提供 lifecycle_ref
    alias_hints = payload.get("alias_hints") or []
    if alias_hints and payload.get("lifecycle_ref") is None and not _alias_resolves(graph, str(payload.get("entity_ref")), alias_hints):
        return Decision(
            action=QUARANTINE,
            reason="resolver_abstain_alias_mismatch：别名提示在图中无法解析，归属不明，保守隔离",
        )

    # 4. 无同键活跃节点：revival 或新增
    active = find_active_by_key(graph, key, slot)
    if active is None:
        superseded = find_superseded_by_key(graph, key)
        if superseded is not None:
            return Decision(
                action=REVIVES,
                reason=f"同键 {key} 无活跃节点但存在历史节点 {superseded.get('node_id')}：revival 落在新节点 + REVIVES 边",
                relates_to_node_id=superseded.get("node_id"),
                detail={"revival_target": str(superseded.get("node_id"))},
            )
        return Decision(action=APPEND, reason=f"同键 {key} 无活跃节点，新增当前态节点")

    # 5. 与同键活跃节点裁决
    prev_id = str(active.get("node_id"))
    prev_seq = active.get("lifecycle_seq")
    event_seq = payload.get("lifecycle_seq")

    # 5a. state_slot 不同 -> 维度共存
    prev_slot = state_slot_of(active)
    if slot is not None and prev_slot is not None and slot != prev_slot:
        return Decision(
            action=APPEND,
            reason=f"同 lifecycle 不同 state_slot（{prev_slot} vs {slot}）：维度共存，互不取代",
        )

    # 5b. lifecycle_seq 碰撞
    if event_seq is not None and isinstance(event_seq, int) and isinstance(prev_seq, int) and event_seq <= prev_seq:
        return Decision(
            action=QUARANTINE,
            reason=f"lifecycle_seq 碰撞：事件 seq={event_seq} <= 既有 seq={prev_seq}，保守隔离",
        )

    # 5c/5d. 时序权威：observed_at 比较
    time_cmp = compare_observation_time(
        event.get("observed_at"), active.get("observed_at")
    )
    if time_cmp == -1:
        return Decision(
            action=QUARANTINE,
            reason=(
                f"晚到旧事件：observed_at {event.get('observed_at')} 早于既有 "
                f"{active.get('observed_at')}，不得覆盖较新状态（§7.2）"
            ),
        )
    if time_cmp is None and event_seq is None:
        return Decision(
            action=ABSTAIN,
            reason="无法建立严格更新：事件缺 lifecycle_seq 且 observed_at 打平或不可比，保守弃权",
        )
    if time_cmp == 0 and event_seq is None:
        return Decision(
            action=ABSTAIN,
            reason="observed_at 与既有节点打平且缺 lifecycle_seq，顺序无法判定，保守弃权",
        )

    # 5e. 来源冲突
    prev_source = active.get("source")
    if source and prev_source and str(source) != str(prev_source):
        return Decision(
            action=CONTESTS,
            reason=(
                f"provenance conflict：同键同槽位来源冲突（{prev_source} vs {source}），"
                "CONTESTS 而非静默取代（§8）"
            ),
            relates_to_node_id=prev_id,
        )

    # 5f. 合法推进
    return Decision(
        action=SUPERSEDE,
        reason=f"同键同槽位合法单流推进（seq {prev_seq} -> {event_seq}）",
        superseded_node_ids=[prev_id],
        relates_to_node_id=prev_id,
    )


def _node_from_event(event: dict[str, Any], node_id: str) -> dict[str, Any]:
    payload = event.get("payload") or {}
    state = payload.get("state")
    is_terminal = str(state or "").strip().lower() in TERMINAL_STATES
    node: dict[str, Any] = {
        "node_id": node_id,
        "entity_ref": payload.get("entity_ref"),
        "content": payload.get("content"),
        "node_type": payload.get("node_type") or "Fact",
        "status": "superseded" if is_terminal else "active",
    }
    if is_terminal:
        node["_terminal_state"] = str(state)
    if payload.get("state") is not None:
        node["state"] = payload["state"]
    if payload.get("lifecycle_ref") is not None:
        node["lifecycle_ref"] = payload["lifecycle_ref"]
    if payload.get("state_slot") is not None:
        node["state_slot"] = payload["state_slot"]
    if payload.get("lifecycle_seq") is not None:
        node["lifecycle_seq"] = payload["lifecycle_seq"]
    if event.get("observed_at") is not None:
        node["observed_at"] = event["observed_at"]
    if event.get("effective_at") is not None:
        node["effective_at"] = event["effective_at"]
    if event.get("source") is not None:
        node["source"] = event["source"]
    if event.get("event_id"):
        node["_event_id"] = event["event_id"]
    if payload.get("alias_hints"):
        node["alias_hints"] = payload["alias_hints"]
    return node


def decision_to_patch(
    decision: Decision,
    event: dict[str, Any],
    *,
    node_id: str,
) -> dict[str, Any]:
    """把裁决物化为主链 patch（reconcile 复核后交 apply_patch 应用）。

    保守行动（quarantine/abstain/duplicate_noop）产出空 patch：当前态零改动。
    """
    if decision.action == SUPERSEDE:
        return {
            "turn_id": None,
            "new_nodes": [_node_from_event(event, node_id)],
            "superseded_nodes": [
                {"node_id": nid, "reason": decision.reason}
                for nid in decision.superseded_node_ids
            ],
            "new_edges": [
                {"source": node_id, "target": nid, "relation": "invalidates"}
                for nid in decision.superseded_node_ids
            ],
            "_decision": {"action": decision.action, "reason": decision.reason},
        }
    if decision.action == APPEND:
        return {
            "turn_id": None,
            "new_nodes": [_node_from_event(event, node_id)],
            "superseded_nodes": [],
            "new_edges": [],
            "_decision": {"action": decision.action, "reason": decision.reason},
        }
    if decision.action == CONTESTS:
        edges = []
        if decision.relates_to_node_id:
            edges.append({
                "source": node_id,
                "target": decision.relates_to_node_id,
                "relation": "CONTESTS",
            })
        return {
            "turn_id": None,
            "new_nodes": [_node_from_event(event, node_id)],
            "superseded_nodes": [],
            "new_edges": edges,
            "_decision": {"action": decision.action, "reason": decision.reason},
        }
    if decision.action == REVIVES:
        edges = []
        if decision.relates_to_node_id:
            edges.append({
                "source": node_id,
                "target": decision.relates_to_node_id,
                "relation": "REVIVES",
            })
        return {
            "turn_id": None,
            "new_nodes": [_node_from_event(event, node_id)],
            "superseded_nodes": [],
            "new_edges": edges,
            "_decision": {"action": decision.action, "reason": decision.reason},
        }
    # QUARANTINE / ABSTAIN / DUPLICATE_NOOP：保守不动当前态
    return {
        "turn_id": None,
        "new_nodes": [],
        "superseded_nodes": [],
        "new_edges": [],
        "_decision": {"action": decision.action, "reason": decision.reason},
    }
