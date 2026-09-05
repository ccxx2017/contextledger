#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lifecycle 整图 lint 规则（RFC §14 的 8 条必须规则）。

接入方式：graph_lint.lint_graph 末尾调用
    run_lifecycle_lint(graph_state, report, add_issue)
隔离保证：只对携带 lifecycle 语义字段（lifecycle_ref/state_slot/lifecycle_seq）的
节点与 lifecycle 关系边产生 finding；纯 legacy 图零 finding，报告字节不变。
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

from lifecycle_fields import (
    adjudication_key,
    has_lifecycle_semantics,
)

# lifecycle 关系词（归一化：小写）
LIFECYCLE_RELATIONS = {"supercedes", "supersedes", "coexists", "contests", "revives", "unrelated"}


def _nodes(graph_state: dict[str, Any]) -> list[dict[str, Any]]:
    nodes = graph_state.get("nodes", {})
    if isinstance(nodes, dict):
        return [n for n in nodes.values() if isinstance(n, dict)]
    return [n for n in nodes if isinstance(n, dict)]


def _edges(graph_state: dict[str, Any]) -> list[dict[str, Any]]:
    return [e for e in graph_state.get("edges", []) if isinstance(e, dict)]


def _relation(edge: dict[str, Any]) -> str:
    for key in ("relation", "type", "edge_type"):
        value = edge.get(key)
        if value:
            return str(value).strip().lower()
    return ""


def _endpoint(edge: dict[str, Any]) -> tuple[str | None, str | None]:
    src = edge.get("source") or edge.get("from") or edge.get("src")
    tgt = edge.get("target") or edge.get("to") or edge.get("dst")
    return (str(src) if src else None, str(tgt) if tgt else None)


def run_lifecycle_lint(
    graph_state: dict[str, Any],
    report: dict[str, Any],
    add_issue: Callable[..., None],
) -> None:
    """对整图执行 RFC §14 的 8 条 lifecycle lint。纯 legacy 图零干预。"""
    nodes = _nodes(graph_state)
    edges = _edges(graph_state)
    nodes_by_id = {str(n.get("node_id")): n for n in nodes if n.get("node_id")}
    lifecycle_nodes = [n for n in nodes if has_lifecycle_semantics(n)]
    lifecycle_relations = [e for e in edges if _relation(e) in LIFECYCLE_RELATIONS]

    if not lifecycle_nodes and not lifecycle_relations:
        return  # 纯 legacy 图：零干预（字节一致保证）

    # 规则 1：lifecycle_ref 指向多个 canonical entity
    lifecycle_entities: dict[str, set[str]] = defaultdict(set)
    for node in lifecycle_nodes:
        ref = node.get("lifecycle_ref")
        entity = node.get("entity_ref")
        if ref and entity:
            lifecycle_entities[str(ref)].add(str(entity))
    for ref, entities in lifecycle_entities.items():
        if len(entities) > 1:
            add_issue(
                report, "error",
                "LIFECYCLE_REF_MULTI_ENTITY",
                f"lifecycle_ref={ref} 指向多个 canonical entity: {sorted(entities)}。",
                lifecycle_ref=ref, entity_refs=sorted(entities),
            )

    # 规则 2：同一 lifecycle_ref 下 lifecycle_seq 重复
    seqs_by_ref: dict[str, dict[int, str]] = defaultdict(dict)
    for node in lifecycle_nodes:
        ref = node.get("lifecycle_ref")
        seq = node.get("lifecycle_seq")
        if ref and isinstance(seq, int) and not isinstance(seq, bool):
            seqs_by_ref[str(ref)].setdefault(seq, str(node.get("node_id")))
    for node in lifecycle_nodes:
        ref = node.get("lifecycle_ref")
        seq = node.get("lifecycle_seq")
        if ref and isinstance(seq, int) and not isinstance(seq, bool):
            first_owner = seqs_by_ref[str(ref)].get(seq)
            owner_id = str(node.get("node_id"))
            if first_owner and first_owner != owner_id:
                add_issue(
                    report, "error",
                    "LIFECYCLE_SEQ_DUPLICATE",
                    f"lifecycle_ref={ref} 下 lifecycle_seq={seq} 重复（{first_owner} 与 {owner_id}）。",
                    lifecycle_ref=ref, lifecycle_seq=seq, node_ids=[first_owner, owner_id],
                )

    # 规则 3：REVIVES 找不到合法目标
    for edge in edges:
        if _relation(edge) != "revives":
            continue
        src, tgt = _endpoint(edge)
        target = nodes_by_id.get(tgt or "")
        if target is None:
            add_issue(
                report, "error",
                "REVIVES_TARGET_MISSING",
                f"REVIVES 边 {src} -> {tgt} 的目标节点不存在。",
                source=src, target=tgt,
            )
        elif str(target.get("status")) != "superseded":
            add_issue(
                report, "error",
                "REVIVES_TARGET_NOT_SUPERSEDED",
                f"REVIVES 边 {src} -> {tgt} 的目标不是 superseded 节点（revival 只能指向失效点）。",
                source=src, target=tgt, target_status=target.get("status"),
            )

    # 规则 4：partial 缺少原子化或作用域
    for node in lifecycle_nodes:
        if str(node.get("invalidation_kind") or "").lower() != "partial":
            continue
        if not node.get("atomic_claims") and not node.get("scope"):
            add_issue(
                report, "error",
                "PARTIAL_MISSING_ATOMIC_OR_SCOPE",
                f"节点 {node.get('node_id')} 声明 partial，但缺少 atomic_claims 与 scope。",
                node_id=node.get("node_id"),
            )

    # 规则 5：conditional 缺少 condition
    for node in lifecycle_nodes:
        if str(node.get("invalidation_kind") or "").lower() != "conditional":
            continue
        if not node.get("condition"):
            add_issue(
                report, "error",
                "CONDITIONAL_MISSING_CONDITION",
                f"节点 {node.get('node_id')} 声明 conditional，但缺少 condition。",
                node_id=node.get("node_id"),
            )

    # 规则 6：provenance conflict 被直接写成 full invalidation
    for node in lifecycle_nodes:
        if (
            str(node.get("invalidation_kind") or "").lower() == "full"
            and str(node.get("provenance_conflict") or "").lower() in {"true", "1", "yes"}
        ):
            add_issue(
                report, "error",
                "PROVENANCE_CONFLICT_AS_FULL_INVALIDATION",
                f"节点 {node.get('node_id')} 带 provenance_conflict 却声明 full invalidation（§8 禁止）。",
                node_id=node.get("node_id"),
            )

    # 规则 7：adjudication_key 在无授权情况下变化（legacy 与 lifecycle 混挂同一 entity_ref）
    lifecycle_entities_by_ref: dict[str, str] = {}
    for node in lifecycle_nodes:
        entity = str(node.get("entity_ref") or "")
        ref = str(node.get("lifecycle_ref") or "")
        if entity and ref:
            lifecycle_entities_by_ref.setdefault(entity, ref)
    for node in nodes:
        entity = str(node.get("entity_ref") or "")
        if not entity or has_lifecycle_semantics(node) or entity not in lifecycle_entities_by_ref:
            continue
        add_issue(
            report, "warning",
            "ADJUDICATION_KEY_CHANGED_WITHOUT_AUTHORITY",
            (
                f"entity_ref={entity} 同时存在 legacy 记录与 lifecycle_ref="
                f"{lifecycle_entities_by_ref[entity]} 记录，裁定键在无授权情况下变化（§13 迁移需显式声明）。"
            ),
            entity_ref=entity, lifecycle_ref=lifecycle_entities_by_ref[entity],
            node_id=node.get("node_id"),
        )

    # 规则 8：legacy 节点与 lifecycle_v1 节点模糊混裁（同 entity_ref 双活跃）
    legacy_active_entities = {
        str(n.get("entity_ref") or "")
        for n in nodes
        if n.get("status") == "active" and not has_lifecycle_semantics(n) and n.get("entity_ref")
    }
    for node in lifecycle_nodes:
        entity = str(node.get("entity_ref") or "")
        if node.get("status") == "active" and entity in legacy_active_entities:
            add_issue(
                report, "error",
                "LEGACY_LIFECYCLE_AMBIGUOUS_COADJUDICATION",
                (
                    f"entity_ref={entity} 下 legacy 活跃节点与 lifecycle 节点（{node.get('node_id')}）"
                    "可能被模糊混裁，须先完成 §13 迁移。"
                ),
                entity_ref=entity, node_id=node.get("node_id"),
            )
