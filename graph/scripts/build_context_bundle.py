#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
build_context_bundle.py

最小确定性 Assembler（Phase 0 专用）：
1. 只读取 graph_state.json，不依赖 LLM
2. 当前态成员资格只按 status=active 判断
3. 按 priority 分层装配：must_include -> should_include -> optional -> background
4. 预算不足时拒绝静默丢弃 must_include
5. 输出机械生成的 context_bundle 与 assembly_report
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PRIORITY_ORDER = {
    "must_include": 0,
    "should_include": 1,
    "optional": 2,
    "background": 3,
}


class AssemblyRejectedError(Exception):
    def __init__(self, message: str, report: dict[str, Any]) -> None:
        super().__init__(message)
        self.report = report


def load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, obj: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def normalize_status(value: Any) -> str:
    if value is None:
        return "active"
    return str(value).strip().lower()


def normalize_priority(value: Any) -> str:
    if value is None:
        return "optional"
    text = str(value).strip().lower()
    if text not in PRIORITY_ORDER:
        return "optional"
    return text


def normalize_state(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def sort_key(node: dict[str, Any]) -> tuple[int, str]:
    created_turn = node.get("created_turn")
    try:
        created_turn_int = int(created_turn)
    except (TypeError, ValueError):
        created_turn_int = 0
    node_id = str(node.get("node_id", ""))
    return created_turn_int, node_id


def backfill_sort_key(node: dict[str, Any]) -> tuple[int, str]:
    created_turn, node_id = sort_key(node)
    return (-created_turn, node_id)


def is_pending_open_candidate(node: dict[str, Any]) -> bool:
    if normalize_status(node.get("status")) != "active":
        return False
    if normalize_state(node.get("state")) != "open":
        return False
    if str(node.get("type")) != "OpenTask":
        return False

    content = str(node.get("content", ""))
    signals = (
        "待定",
        "待裁定",
        "待最终裁定",
        "仍需最终裁定",
        "当前推荐",
    )
    return any(signal in content for signal in signals)


def extract_nodes(graph_state: dict[str, Any]) -> list[dict[str, Any]]:
    nodes = graph_state.get("nodes", {})
    if isinstance(nodes, dict):
        result = []
        for node_id, node in nodes.items():
            if not isinstance(node, dict):
                continue
            item = dict(node)
            item.setdefault("node_id", node_id)
            result.append(item)
        return result
    if isinstance(nodes, list):
        return [dict(node) for node in nodes if isinstance(node, dict)]
    raise ValueError("graph_state.nodes 既不是 dict 也不是 list")


def build_rejection_report(
    *,
    graph_state: dict[str, Any],
    project_id: str,
    turn_id: str,
    budget_profile: str,
    max_nodes: int,
    all_nodes: list[dict[str, Any]],
    active_nodes: list[dict[str, Any]],
    superseded_nodes: list[dict[str, Any]],
    must_nodes: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "kind": "assembly_report.phase0_mechanical.v1",
        "project_id": project_id,
        "turn_id": turn_id,
        "result": "rejected",
        "input_graph_turn_counter": graph_state.get("turn_counter"),
        "policy": {
            "current_membership_field": "status",
            "state_participates_in_current_membership": True,
            "priority_order": [
                "must_include",
                "should_include",
                "optional",
                "background",
            ],
            "backfill_order": "created_turn desc, node_id asc",
            "budget_profile": budget_profile,
            "max_nodes": max_nodes,
            "overflow_rule": "never_drop_must_include",
        },
        "summary": {
            "all_nodes": len(all_nodes),
            "active_nodes": len(active_nodes),
            "superseded_nodes": len(superseded_nodes),
            "active_must_include_nodes": len(must_nodes),
            "selected_nodes": 0,
        },
        "rejection": {
            "code": "MUST_INCLUDE_OVER_BUDGET",
            "message": (
                f"装配预算不足：active must_include={len(must_nodes)} 超过 max_nodes={max_nodes}，"
                "根据规则拒绝装配，避免静默丢弃 must_include。"
            ),
            "active_must_include_node_ids": [
                str(node.get("node_id"))
                for node in sorted(must_nodes, key=sort_key)
            ],
        },
        "excluded_due_to_status": [
            {
                "node_id": node.get("node_id"),
                "status": normalize_status(node.get("status")),
            }
            for node in sorted(superseded_nodes, key=sort_key)
        ],
        "excluded_due_to_state": [],
    }


def build_bundle(
    graph_state: dict[str, Any],
    project_id: str,
    turn_id: str,
    max_nodes: int,
    budget_profile: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    all_nodes = extract_nodes(graph_state)
    active_nodes: list[dict[str, Any]] = []
    superseded_nodes: list[dict[str, Any]] = []
    excluded_due_to_state: list[dict[str, Any]] = []

    for node in all_nodes:
        status = normalize_status(node.get("status"))
        if status == "active":
            if is_pending_open_candidate(node):
                excluded_due_to_state.append(node)
            else:
                active_nodes.append(node)
        else:
            superseded_nodes.append(node)

    grouped: dict[str, list[dict[str, Any]]] = {
        "must_include": [],
        "should_include": [],
        "optional": [],
        "background": [],
    }

    for node in active_nodes:
        grouped[normalize_priority(node.get("priority"))].append(node)

    for key in grouped:
        if key == "must_include":
            grouped[key] = sorted(grouped[key], key=sort_key)
        else:
            grouped[key] = sorted(grouped[key], key=backfill_sort_key)

    must_nodes = grouped["must_include"]
    if len(must_nodes) > max_nodes:
        report = build_rejection_report(
            graph_state=graph_state,
            project_id=project_id,
            turn_id=turn_id,
            budget_profile=budget_profile,
            max_nodes=max_nodes,
            all_nodes=all_nodes,
            active_nodes=active_nodes,
            superseded_nodes=superseded_nodes,
            must_nodes=must_nodes,
        )
        raise AssemblyRejectedError(report["rejection"]["message"], report)

    selected: list[dict[str, Any]] = []
    for key in ("must_include", "should_include", "optional", "background"):
        for node in grouped[key]:
            if len(selected) >= max_nodes:
                break
            selected.append(node)
        if len(selected) >= max_nodes:
            break

    selected_ids = {str(node.get("node_id")) for node in selected}

    def slim(node: dict[str, Any]) -> dict[str, Any]:
        item = {
            "node_id": node.get("node_id"),
            "type": node.get("type"),
            "content": node.get("content"),
            "priority": normalize_priority(node.get("priority")),
        }
        entity_ref = node.get("entity_ref")
        if entity_ref is not None:
            item["entity_ref"] = entity_ref
        return item

    selected_by_priority = {
        key: [slim(node) for node in grouped[key] if str(node.get("node_id")) in selected_ids]
        for key in ("must_include", "should_include", "optional", "background")
    }

    active_focus = [
        str(node.get("node_id"))
        for node in selected
        if str(node.get("type")) in {"OpenTask", "Decision"}
    ]

    bundle = {
        "kind": "context_bundle.phase0_mechanical.v1",
        "project_id": project_id,
        "turn_id": turn_id,
        "goal": "基于 graph_state 机械生成当前态上下文包，用于验证 supersede 与预算规则的装配结果。",
        "source_graph": "graph/projects/abu_modern/phase0_manual/graph_state.json",
        "authority": {
            "mode": "graph_only",
            "current_state_field": "status",
            "state_gate_field": "state",
            "priority_field": "priority",
        },
        "assembly": {
            "generated_by": "graph/scripts/build_context_bundle.py",
            "selection_rule": (
                "status=active -> exclude pending open-task candidates with state=open "
                "-> priority order -> greedy within budget"
            ),
            "budget_profile": budget_profile,
            "max_nodes": max_nodes,
            "selected_node_ids": [str(node.get("node_id")) for node in selected],
        },
        "l1_baseline": {
            "selection_basis": (
                "status=active AND not(state=open on pending open-task candidate) "
                "AND priority ordered packing"
            ),
            "must_include": selected_by_priority["must_include"],
            "should_include": selected_by_priority["should_include"],
            "optional": selected_by_priority["optional"],
            "background": selected_by_priority["background"],
        },
        "l2_task_state": {
            "assembler_profile": budget_profile,
            "active_focus": active_focus,
            "immediate_actions": [],
            "active_node_count": len(active_nodes),
            "bundled_node_count": len(selected),
        },
        "budget_policy": {
            "overflow_rule": "never_drop_must_include",
            "phase": "phase0_manual",
            "owner": "mechanical-assembler",
            "budget_profile": budget_profile,
        },
        "provenance": [
            {
                "node_id": node.get("node_id"),
                "raw_id": (node.get("source") or {}).get("raw_id"),
                "span": (node.get("source") or {}).get("span"),
            }
            for node in selected
            if isinstance(node.get("source"), dict)
        ],
    }

    non_selected_active = [
        {
            "node_id": node.get("node_id"),
            "priority": normalize_priority(node.get("priority")),
            "reason": "budget_exhausted",
        }
        for node in active_nodes
        if str(node.get("node_id")) not in selected_ids
    ]

    report = {
        "kind": "assembly_report.phase0_mechanical.v1",
        "project_id": project_id,
        "turn_id": turn_id,
        "result": "assembled",
        "input_graph_turn_counter": graph_state.get("turn_counter"),
        "policy": {
            "current_membership_field": "status",
            "state_participates_in_current_membership": True,
            "priority_order": [
                "must_include",
                "should_include",
                "optional",
                "background",
            ],
            "backfill_order": "created_turn desc, node_id asc",
            "budget_profile": budget_profile,
            "max_nodes": max_nodes,
            "overflow_rule": "never_drop_must_include",
        },
        "summary": {
            "all_nodes": len(all_nodes),
            "active_nodes": len(active_nodes),
            "superseded_nodes": len(superseded_nodes),
            "excluded_due_to_state_nodes": len(excluded_due_to_state),
            "active_must_include_nodes": len(must_nodes),
            "selected_nodes": len(selected),
        },
        "selected_node_ids": [str(node.get("node_id")) for node in selected],
        "selected_by_priority": {
            key: [str(node.get("node_id")) for node in grouped[key] if str(node.get("node_id")) in selected_ids]
            for key in ("must_include", "should_include", "optional", "background")
        },
        "excluded_due_to_status": [
            {
                "node_id": node.get("node_id"),
                "status": normalize_status(node.get("status")),
            }
            for node in sorted(superseded_nodes, key=sort_key)
        ],
        "excluded_due_to_state": [
            {
                "node_id": node.get("node_id"),
                "type": node.get("type"),
                "state": normalize_state(node.get("state")),
                "reason": "state_open_pending_candidate",
            }
            for node in sorted(excluded_due_to_state, key=sort_key)
        ],
        "excluded_due_to_budget": sorted(
            non_selected_active,
            key=lambda item: (PRIORITY_ORDER[item["priority"]], item["node_id"]),
        ),
    }

    return bundle, report


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic context bundle from graph_state.json")
    parser.add_argument("--graph", required=True, help="Path to graph_state.json")
    parser.add_argument("--project-id", required=True, help="Project id")
    parser.add_argument("--turn-id", required=True, help="Turn id such as turn_002")
    parser.add_argument("--out", required=True, help="Path to output context bundle json")
    parser.add_argument("--report-out", required=True, help="Path to output assembly report json")
    parser.add_argument("--max-nodes", type=int, required=True, help="Maximum nodes allowed in bundle")
    parser.add_argument("--budget-profile", default="tight_budget_must_only", help="Budget profile label")
    args = parser.parse_args()

    graph_state = load_json(args.graph)
    try:
        bundle, report = build_bundle(
            graph_state=graph_state,
            project_id=args.project_id,
            turn_id=args.turn_id,
            max_nodes=args.max_nodes,
            budget_profile=args.budget_profile,
        )
    except AssemblyRejectedError as exc:
        write_json(args.report_out, exc.report)
        print(exc)
        print(f"Wrote rejection report: {args.report_out}")
        return 2

    write_json(args.out, bundle)
    write_json(args.report_out, report)
    print(f"Wrote bundle: {args.out}")
    print(f"Wrote assembly report: {args.report_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
