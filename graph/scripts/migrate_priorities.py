#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PRIORITIES = {"must_include", "should_include", "optional", "background"}


def load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, obj: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def normalize_state(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def infer_priority(node: dict[str, Any]) -> tuple[str, str]:
    node_type = str(node.get("type") or "").strip()
    state = normalize_state(node.get("state"))
    content = str(node.get("content") or "")
    entity_ref = node.get("entity_ref")

    if node_type == "UserGoal":
        return "must_include", "root_user_goal"

    if node_type == "Constraint":
        return "must_include", "constraint_is_hard_guardrail"

    if state == "resolved":
        return "background", "resolved_items_do_not_compete_for_budget"

    if node_type == "Decision":
        return "should_include", "active_decision"

    if node_type == "Fact":
        return "should_include", "active_fact"

    if node_type == "FileArtifact":
        return "should_include", "artifact_needed_for_execution_context"

    if node_type == "OpenTask":
        if "阶段1" in content or "攻坚点" in content or entity_ref:
            return "should_include", "active_task_with_phase1_or_entity_focus"
        return "optional", "active_task_without_explicit_execution_anchor"

    return "optional", "fallback_default"


def migrate(graph_state: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    migrated = json.loads(json.dumps(graph_state))
    nodes = migrated.get("nodes")
    if not isinstance(nodes, dict):
        raise ValueError("当前脚本要求 graph_state.nodes 为 dict 结构")

    changed = []
    unchanged = 0

    for node_id, node in nodes.items():
        if not isinstance(node, dict):
            continue

        existing = str(node.get("priority") or "").strip().lower()
        if existing in PRIORITIES:
            unchanged += 1
            continue

        priority, reason = infer_priority(node)
        node["priority"] = priority
        node["_priority_migration_reason"] = reason
        changed.append(
            {
                "node_id": node_id,
                "type": node.get("type"),
                "priority": priority,
                "reason": reason,
            }
        )

    report = {
        "kind": "priority_migration.phase1_prep.v1",
        "summary": {
            "changed_nodes": len(changed),
            "unchanged_nodes": unchanged,
            "total_nodes": len(nodes),
        },
        "changed_nodes": changed,
    }
    return migrated, report


def main() -> int:
    parser = argparse.ArgumentParser(description="为主项目 graph_state 迁移 priority 字段")
    parser.add_argument("--graph", required=True)
    parser.add_argument("--out", help="输出路径；缺省时覆盖原文件")
    parser.add_argument("--report-out", required=True)
    parser.add_argument("--in-place", action="store_true", help="显式覆盖原文件")
    args = parser.parse_args()

    graph_state = load_json(args.graph)
    migrated, report = migrate(graph_state)

    if args.out:
        out_path = args.out
    elif args.in_place:
        out_path = args.graph
    else:
        raise ValueError("请使用 --out 或 --in-place")

    write_json(out_path, migrated)
    write_json(args.report_out, report)
    print(f"Wrote migrated graph: {out_path}")
    print(f"Wrote migration report: {args.report_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
