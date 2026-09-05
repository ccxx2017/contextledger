#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lifecycle 字段语义（RFC: contracts/05_phase1_lifecycle_schema.md §4/§7/§13）。

主链 lifecycle 能力的最小字段层：
- adjudication_key：裁定归属键（lifecycle_ref ?? entity_ref，§4.1）
- state_slot：可替代状态维度；同 lifecycle 下不同 slot 共存，不互相取代
- sequence_sort_key：顺序权威（observed_at -> created_turn -> 节点 id，§7.1）
- legacy 判定与兼容回退（§13）

本模块是纯函数层，不做 IO、不调用 LLM；adjudicator 与 lint 都建立在其上。
"""

from __future__ import annotations

from typing import Any

LIFECYCLE_FIELDS = ("lifecycle_ref", "state_slot", "lifecycle_seq", "observed_at", "effective_at")

VALID_STATUS = {"active", "superseded"}


def has_lifecycle_semantics(payload_or_node: dict[str, Any]) -> bool:
    """载荷/节点是否携带 lifecycle 语义字段（区分 lifecycle 模式与 legacy 模式）。"""
    return any(
        payload_or_node.get(field) is not None
        for field in ("lifecycle_ref", "state_slot", "lifecycle_seq")
    )


def adjudication_key(payload_or_node: dict[str, Any]) -> str | None:
    """裁定归属键：lifecycle_ref 优先，缺失时回退 entity_ref（§4.1 / §13）。

    两者皆缺失时返回 None（由调用方决定保守处置）。
    """
    lifecycle_ref = payload_or_node.get("lifecycle_ref")
    if lifecycle_ref:
        return str(lifecycle_ref)
    entity_ref = payload_or_node.get("entity_ref")
    if entity_ref:
        return str(entity_ref)
    return None


def state_slot_of(payload_or_node: dict[str, Any]) -> str | None:
    slot = payload_or_node.get("state_slot")
    return str(slot) if slot else None


def sequence_sort_key(
    *,
    observed_at: str | None,
    created_turn: int | None,
    node_id: str | None,
) -> tuple[int, str, int, str]:
    """§7.1 顺序权威：observed_at -> created_turn -> 节点 id 稳定排序。

    带 observed_at 的节点按时间排序在前；缺失 observed_at 的节点排在
    同周期之后、按 created_turn 排序；节点 id 做最终稳定键。
    """
    observed_rank = 0 if observed_at else 1
    observed = str(observed_at) if observed_at else ""
    turn = int(created_turn) if created_turn is not None else 0
    return (observed_rank, observed, turn, str(node_id or ""))


def compare_observation_time(
    left: str | None,
    right: str | None,
) -> int | None:
    """比较两个 observed_at。返回 1/0/-1；任一缺失或不可比时返回 None。"""
    if not left or not right:
        return None
    if left == right:
        return 0
    return 1 if left > right else -1


def validate_lifecycle_fields(node: dict[str, Any]) -> list[str]:
    """节点上 lifecycle 字段的机械校验。返回问题清单（空 = 合法）。

    只对携带 lifecycle 语义的节点生效；legacy 节点零干预（§13 兼容）。
    """
    if not has_lifecycle_semantics(node):
        return []
    problems: list[str] = []
    seq = node.get("lifecycle_seq")
    if seq is not None and not isinstance(seq, int) or isinstance(seq, bool):
        problems.append("lifecycle_seq 必须是整数或缺失")
    for field in ("observed_at", "effective_at"):
        value = node.get(field)
        if value is not None and not isinstance(value, str):
            problems.append(f"{field} 必须是字符串或缺失")
    if node.get("lifecycle_ref") is None and node.get("state_slot") is not None:
        problems.append("state_slot 必须与 lifecycle_ref 同时出现（无归属的状态维度不可裁定）")
    return problems


def legacy_adjudication_compatible(node: dict[str, Any]) -> bool:
    """§13：schema_version < lifecycle_v1 的节点走 entity_ref 桶，不参与 lifecycle 裁定。"""
    return not has_lifecycle_semantics(node)
