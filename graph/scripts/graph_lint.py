#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
graph_lint.py

Graph Lint:
- 在 patch 应用后运行
- 不调用 LLM
- 检查全图结构与语义不变量
- 默认遇到 error 返回非零退出码，适合接 CI
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REQUIRED_RELATIONS = {
    "refines",
    "depends_on",
    "supports",
    "invalidates",
    "implements",
    "serves",
    "produces",
    "derived_from",
}

DEFAULT_ALLOWED_RELATIONS = set(REQUIRED_RELATIONS)

MINIMAL_STATE_ENUM = {
    "open",
    "blocked",
    "in_progress",
    "implemented",
    "deployed",
    "resolved",
    "cancelled",
    "unknown",
}

MUTUALLY_EXCLUSIVE_ACTIVE_STATES = {
    "open",
    "blocked",
    "implemented",
    "deployed",
    "resolved",
    "cancelled",
}

ENTITY_REF_RECOMMENDED_TYPES = {
    "opentask",
    "fact",
    "constraint",
}

SOURCE_KEYS = (
    "source",
    "source_id",
    "source_node_id",
    "from",
    "from_id",
    "from_node_id",
    "src",
)

TARGET_KEYS = (
    "target",
    "target_id",
    "target_node_id",
    "to",
    "to_id",
    "to_node_id",
    "dst",
)

RELATION_KEYS = (
    "relation",
    "type",
    "edge_type",
    "label",
    "predicate",
    "name",
)

NODE_ID_KEYS = (
    "node_id",
    "id",
)


def load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, obj: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def normalize_ws(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_lower(value: Any) -> str:
    return normalize_ws(value).lower()


def normalize_relation(value: Any) -> str:
    return normalize_lower(value)


def normalize_state(value: Any) -> str:
    return normalize_lower(value)


def normalize_entity_ref(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_node_type(value: Any) -> str:
    return normalize_lower(value).replace("_", "").replace("-", "")


def node_id(node: dict[str, Any]) -> str:
    for key in NODE_ID_KEYS:
        value = node.get(key)
        if isinstance(value, (str, int)):
            return str(value).strip()
    return ""


def edge_id(edge: dict[str, Any], index: int) -> str:
    for key in ("edge_id", "id"):
        value = edge.get(key)
        if isinstance(value, (str, int)):
            return str(value).strip()
    return f"edge[{index}]"


def is_active_node(node: dict[str, Any]) -> bool:
    if node.get("active") is False:
        return False

    status = normalize_lower(node.get("status", "active"))
    return status == "active"


def is_active_edge(edge: dict[str, Any]) -> bool:
    if edge.get("active") is False:
        return False

    status = normalize_lower(edge.get("status", "active"))
    return status == "active"


def is_superseded_node(node: dict[str, Any]) -> bool:
    status = normalize_lower(node.get("status"))
    if status == "superseded":
        return True

    if node.get("superseded") is True:
        return True

    return False


def extract_nodes_from_container(data: Any) -> list[dict[str, Any]]:
    """
    支持常见结构：

    1. {"nodes": [...]}
    2. {"graph": {"nodes": [...]}}
    3. {"graph_state": {"nodes": [...]}}
    4. {"memory_graph": {"nodes": [...]}}
    5. {"nodes": {"n_0001": {...}}}
    6. 直接是节点 list
    """
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]

    if not isinstance(data, dict):
        raise ValueError("graph_state.json must be a dict or a list")

    candidate_paths = [
        ("nodes",),
        ("graph", "nodes"),
        ("graph_state", "nodes"),
        ("memory_graph", "nodes"),
    ]

    for path in candidate_paths:
        cur = data
        ok = True

        for key in path:
            if not isinstance(cur, dict) or key not in cur:
                ok = False
                break
            cur = cur[key]

        if not ok:
            continue

        if isinstance(cur, list):
            return [x for x in cur if isinstance(x, dict)]

        if isinstance(cur, dict):
            result: list[dict[str, Any]] = []
            for k, v in cur.items():
                if isinstance(v, dict):
                    item = dict(v)
                    item.setdefault("node_id", str(k))
                    result.append(item)
            return result

    raise ValueError("Cannot find nodes in graph_state.json")


def extract_edges_from_container(data: Any) -> list[dict[str, Any]]:
    """
    支持常见结构：

    1. {"edges": [...]}
    2. {"graph": {"edges": [...]}}
    3. {"graph_state": {"edges": [...]}}
    4. {"memory_graph": {"edges": [...]}}
    5. {"edges": {"e_0001": {...}}}
    """
    if not isinstance(data, dict):
        return []

    candidate_paths = [
        ("edges",),
        ("graph", "edges"),
        ("graph_state", "edges"),
        ("memory_graph", "edges"),
    ]

    for path in candidate_paths:
        cur = data
        ok = True

        for key in path:
            if not isinstance(cur, dict) or key not in cur:
                ok = False
                break
            cur = cur[key]

        if not ok:
            continue

        if isinstance(cur, list):
            return [x for x in cur if isinstance(x, dict)]

        if isinstance(cur, dict):
            result: list[dict[str, Any]] = []
            for k, v in cur.items():
                if isinstance(v, dict):
                    item = dict(v)
                    item.setdefault("edge_id", str(k))
                    result.append(item)
            return result

    return []


def extract_declared_relation_enum(data: Any) -> set[str] | None:
    """
    如果 graph_state 里显式声明了 relation enum，则读取并校验。
    如果没有声明，则使用 DEFAULT_ALLOWED_RELATIONS。
    """
    if not isinstance(data, dict):
        return None

    candidate_paths = [
        ("relation_enum",),
        ("allowed_relations",),
        ("schema", "relation_enum"),
        ("schema", "relations"),
        ("graph_schema", "relation_enum"),
        ("graph_schema", "relations"),
    ]

    for path in candidate_paths:
        cur = data
        ok = True

        for key in path:
            if not isinstance(cur, dict) or key not in cur:
                ok = False
                break
            cur = cur[key]

        if not ok:
            continue

        if isinstance(cur, list):
            return {normalize_relation(x) for x in cur if normalize_relation(x)}

        if isinstance(cur, dict):
            return {normalize_relation(k) for k in cur.keys() if normalize_relation(k)}

    return None


def extract_endpoint(edge: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = edge.get(key)

        if isinstance(value, (str, int)):
            return str(value).strip()

        if isinstance(value, dict):
            nested = node_id(value)
            if nested:
                return nested

    return ""


def extract_relation(edge: dict[str, Any]) -> str:
    for key in RELATION_KEYS:
        if key not in edge:
            continue

        value = edge.get(key)
        relation = normalize_relation(value)

        if relation:
            return relation

    return ""


def add_issue(
    report: dict[str, Any],
    level: str,
    code: str,
    message: str,
    **extra: Any,
) -> None:
    item = {
        "level": level,
        "code": code,
        "message": message,
    }
    item.update(extra)

    if level == "error":
        report["errors"].append(item)
    elif level == "warning":
        report["warnings"].append(item)
    else:
        raise ValueError(f"Unknown issue level: {level}")


def content_has_ticket_id(content: str) -> bool:
    patterns = [
        r"\b[A-Z]{2,12}(?:-\d{2,}){1,4}\b",       # TKT-2026-003, PROJ-123
        r"\b(?:ticket|issue|bug|task)[\s:#-]*\d+\b",
        r"#\d{2,}\b",
    ]
    return any(re.search(p, content, flags=re.IGNORECASE) for p in patterns)


def content_has_file_path(content: str) -> bool:
    patterns = [
        r"(?<!\w)(?:\.{1,2}/|/)[A-Za-z0-9_.\-/{}/]+(?:\.[A-Za-z0-9]{1,12})\b",
        r"\b[A-Za-z]:\\[^\s]+",
        r"\b[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-/{}/]+(?:\.[A-Za-z0-9]{1,12})\b",
    ]
    return any(re.search(p, content) for p in patterns)


def content_has_api_path(content: str) -> bool:
    patterns = [
        r"\b(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+/[A-Za-z0-9_.~:/?#\[\]@!$&'()*+,;=%{}-]+",
        r"(?<!\w)/api(?:/[A-Za-z0-9_.:{}-]+)+",
        r"(?<!\w)/v\d+(?:/[A-Za-z0-9_.:{}-]+)+",
    ]
    return any(re.search(p, content, flags=re.IGNORECASE) for p in patterns)


def entity_ref_evidence(content: str) -> list[str]:
    evidence: list[str] = []

    if content_has_ticket_id(content):
        evidence.append("ticket_id")

    if content_has_file_path(content):
        evidence.append("file_path")

    if content_has_api_path(content):
        evidence.append("api_path")

    return evidence


def content_obviously_completed(content: str) -> bool:
    text = normalize_lower(content)

    negative_patterns = [
        r"未完成",
        r"尚未完成",
        r"还未完成",
        r"没有完成",
        r"未实现",
        r"尚未实现",
        r"未部署",
        r"尚未部署",
        r"未解决",
        r"尚未解决",
        r"\bnot\s+done\b",
        r"\bnot\s+completed\b",
        r"\bnot\s+implemented\b",
        r"\bnot\s+deployed\b",
        r"\bnot\s+resolved\b",
        r"\bblocked\b",
    ]

    if any(re.search(p, text, flags=re.IGNORECASE) for p in negative_patterns):
        return False

    positive_patterns = [
        r"已完成",
        r"已经完成",
        r"完成了",
        r"已实现",
        r"已经实现",
        r"已部署",
        r"已经部署",
        r"已解决",
        r"已经解决",
        r"已关闭",
        r"已上线",
        r"已交付",
        r"\bdone\b",
        r"\bcompleted\b",
        r"\bimplemented\b",
        r"\bdeployed\b",
        r"\bresolved\b",
        r"\bclosed\b",
        r"\bfixed\b",
        r"\bshipped\b",
    ]

    return any(re.search(p, text, flags=re.IGNORECASE) for p in positive_patterns)


def lint_graph(graph_state: dict[str, Any]) -> dict[str, Any]:
    nodes = extract_nodes_from_container(graph_state)
    edges = extract_edges_from_container(graph_state)

    declared_relations = extract_declared_relation_enum(graph_state)
    allowed_relations = declared_relations or DEFAULT_ALLOWED_RELATIONS

    report: dict[str, Any] = {
        "ok": True,
        "summary": {
            "nodes": len(nodes),
            "edges": len(edges),
            "active_nodes": 0,
            "active_edges": 0,
            "errors": 0,
            "warnings": 0,
        },
        "relation_enum": sorted(allowed_relations),
        "minimal_state_enum": sorted(MINIMAL_STATE_ENUM),
        "errors": [],
        "warnings": [],
    }

    # 2. relation enum 必须包含指定 relation
    missing_required_relations = sorted(REQUIRED_RELATIONS - allowed_relations)
    if missing_required_relations:
        add_issue(
            report,
            "error",
            "RELATION_ENUM_MISSING_REQUIRED_VALUES",
            "relation 枚举缺少必需值。",
            missing_relations=missing_required_relations,
            required_relations=sorted(REQUIRED_RELATIONS),
        )

    nodes_by_id: dict[str, dict[str, Any]] = {}
    active_nodes_by_id: dict[str, dict[str, Any]] = {}

    for node in nodes:
        nid = node_id(node)

        if not nid:
            add_issue(
                report,
                "error",
                "NODE_MISSING_ID",
                "存在缺少 node_id/id 的节点。",
                node=node,
            )
            continue

        if nid in nodes_by_id:
            add_issue(
                report,
                "error",
                "DUPLICATE_NODE_ID",
                f"图中存在重复 node_id: {nid}",
                node_id=nid,
            )

        nodes_by_id[nid] = node

        if is_active_node(node):
            active_nodes_by_id[nid] = node

    report["summary"]["active_nodes"] = len(active_nodes_by_id)

    active_degree: dict[str, int] = {nid: 0 for nid in active_nodes_by_id}
    active_entity_state_index: dict[str, dict[str, list[str]]] = {}

    # 节点状态枚举 lint
    for nid, node in nodes_by_id.items():
        state = normalize_state(node.get("state"))

        if state and state not in MINIMAL_STATE_ENUM:
            add_issue(
                report,
                "warning",
                "UNKNOWN_STATE_VALUE",
                f"节点 {nid} 使用了最小状态枚举之外的 state: {state}",
                node_id=nid,
                state=state,
                allowed_states=sorted(MINIMAL_STATE_ENUM),
            )

    # 1. 不允许未知 relation
    # 同时做基础 endpoint 检查、active degree 统计、invalidates 目标检查
    for idx, edge in enumerate(edges):
        eid = edge_id(edge, idx)

        relation = extract_relation(edge)
        source = extract_endpoint(edge, SOURCE_KEYS)
        target = extract_endpoint(edge, TARGET_KEYS)

        if is_active_edge(edge):
            report["summary"]["active_edges"] += 1

        if not relation:
            add_issue(
                report,
                "error",
                "EDGE_MISSING_RELATION",
                f"边 {eid} 缺少 relation/type。",
                edge_id=eid,
                edge=edge,
            )
        elif relation not in allowed_relations:
            add_issue(
                report,
                "error",
                "UNKNOWN_RELATION",
                f"边 {eid} 使用了未知 relation: {relation}",
                edge_id=eid,
                relation=relation,
                allowed_relations=sorted(allowed_relations),
            )

        if not source:
            add_issue(
                report,
                "error",
                "EDGE_MISSING_SOURCE",
                f"边 {eid} 缺少 source。",
                edge_id=eid,
                relation=relation,
            )
        elif source not in nodes_by_id:
            add_issue(
                report,
                "error",
                "EDGE_SOURCE_NOT_FOUND",
                f"边 {eid} 的 source 不存在: {source}",
                edge_id=eid,
                source=source,
                relation=relation,
            )

        if not target:
            add_issue(
                report,
                "error",
                "EDGE_MISSING_TARGET",
                f"边 {eid} 缺少 target。",
                edge_id=eid,
                relation=relation,
            )
        elif target not in nodes_by_id:
            add_issue(
                report,
                "error",
                "EDGE_TARGET_NOT_FOUND",
                f"边 {eid} 的 target 不存在: {target}",
                edge_id=eid,
                target=target,
                relation=relation,
            )

        if is_active_edge(edge):
            if source in active_degree:
                active_degree[source] += 1
            if target in active_degree:
                active_degree[target] += 1

        # 4. 被 invalidates 指向的节点应该是 superseded
        if relation == "invalidates" and target:
            target_node = nodes_by_id.get(target)

            if target_node is None:
                add_issue(
                    report,
                    "error",
                    "INVALIDATES_TARGET_NOT_FOUND",
                    f"invalidates 边 {eid} 指向不存在的节点 {target}。",
                    edge_id=eid,
                    source=source,
                    target=target,
                )
            elif not is_superseded_node(target_node):
                add_issue(
                    report,
                    "error",
                    "INVALIDATES_TARGET_NOT_SUPERSEDED",
                    f"invalidates 边 {eid} 指向的节点 {target} 未标记为 superseded。",
                    edge_id=eid,
                    source=source,
                    target=target,
                    target_status=target_node.get("status"),
                    target_active=target_node.get("active"),
                )

    # 3. 除根 UserGoal 外，不允许 active 孤立节点
    for nid, node in active_nodes_by_id.items():
        degree = active_degree.get(nid, 0)

        if degree > 0:
            continue

        node_type = normalize_node_type(node.get("type"))

        if node_type == "usergoal":
            continue

        add_issue(
            report,
            "error",
            "ACTIVE_ISOLATED_NODE",
            f"active 节点 {nid} 是孤立节点；除根 UserGoal 外不允许 active 孤立节点。",
            node_id=nid,
            node_type=node.get("type"),
        )

    # 5. 相同 entity_ref 下，不应同时存在互斥 active state
    for nid, node in active_nodes_by_id.items():
        entity_ref = normalize_entity_ref(node.get("entity_ref"))
        if not entity_ref:
            continue

        state = normalize_state(node.get("state"))
        if state not in MUTUALLY_EXCLUSIVE_ACTIVE_STATES:
            continue

        active_entity_state_index.setdefault(entity_ref, {}).setdefault(state, []).append(nid)

    for entity_ref, states in active_entity_state_index.items():
        if len(states) <= 1:
            continue

        add_issue(
            report,
            "error",
            "CONFLICTING_ACTIVE_STATES_FOR_ENTITY_REF",
            (
                f"相同 entity_ref={entity_ref} 下同时存在多个互斥 active state: "
                f"{', '.join(sorted(states.keys()))}"
            ),
            entity_ref=entity_ref,
            states={state: ids for state, ids in sorted(states.items())},
            mutually_exclusive_states=sorted(MUTUALLY_EXCLUSIVE_ACTIVE_STATES),
        )

    # 6. OpenTask 如果已经完成，应为 resolved，不要继续 active
    for nid, node in active_nodes_by_id.items():
        node_type = normalize_node_type(node.get("type"))
        if node_type != "opentask":
            continue

        state = normalize_state(node.get("state"))
        content = normalize_ws(node.get("content"))

        if state in {"implemented", "deployed"}:
            add_issue(
                report,
                "error",
                "COMPLETED_OPEN_TASK_USES_NON_RESOLVED_STATE",
                (
                    f"OpenTask {nid} 的 state={state}，但完成后的 OpenTask 应使用 resolved，"
                    f"不应继续作为 active 任务存在。"
                ),
                node_id=nid,
                state=state,
            )

        if state == "resolved":
            add_issue(
                report,
                "error",
                "RESOLVED_OPEN_TASK_STILL_ACTIVE",
                f"OpenTask {nid} 已是 resolved，但仍为 active；完成任务不应继续 active。",
                node_id=nid,
                state=state,
                status=node.get("status"),
            )

        if content_obviously_completed(content) and state != "resolved":
            add_issue(
                report,
                "warning",
                "OPEN_TASK_CONTENT_LOOKS_COMPLETED",
                (
                    f"OpenTask {nid} 的内容看起来已经完成，但 state 不是 resolved。"
                    f"该判断基于关键词启发式，只作为 warning。"
                ),
                node_id=nid,
                state=state or None,
            )

    # 7. OpenTask / Fact / Constraint 中明显包含工单号、文件路径、API 路径，但缺 entity_ref
    for nid, node in nodes_by_id.items():
        node_type = normalize_node_type(node.get("type"))

        if node_type not in ENTITY_REF_RECOMMENDED_TYPES:
            continue

        entity_ref = normalize_entity_ref(node.get("entity_ref"))
        if entity_ref:
            continue

        content = normalize_ws(node.get("content"))
        evidence = entity_ref_evidence(content)

        if evidence:
            add_issue(
                report,
                "warning",
                "MISSING_ENTITY_REF_FOR_IDENTIFIABLE_CONTENT",
                (
                    f"节点 {nid} 类型为 {node.get('type')}，内容中包含可识别实体线索，"
                    f"但缺少 entity_ref。"
                ),
                node_id=nid,
                node_type=node.get("type"),
                evidence=evidence,
            )

    report["summary"]["errors"] = len(report["errors"])
    report["summary"]["warnings"] = len(report["warnings"])
    report["ok"] = len(report["errors"]) == 0

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint graph_state.json after patch application.")
    parser.add_argument("graph_state", help="Path to graph_state.json")
    parser.add_argument("--out", help="Optional output path for lint report JSON")
    parser.add_argument("--no-fail", action="store_true", help="Always exit 0 even if errors exist")
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Exit non-zero when warnings exist",
    )

    args = parser.parse_args()

    graph_state = load_json(args.graph_state)
    report = lint_graph(graph_state)

    if args.out:
        write_json(args.out, report)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.no_fail:
        return 0

    if report["errors"]:
        return 1

    if args.fail_on_warning and report["warnings"]:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())