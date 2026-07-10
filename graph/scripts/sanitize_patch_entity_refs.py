#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sanitize_patch_entity_refs.py

Patch 预处理：为包含可识别实体线索但 entity_ref 为 null 的节点自动推断并填充 entity_ref。
推断规则（按优先级）：
1. 内容中的工单号 TKT-YYYY-NNN
2. 内容中的技能/目录路径 openclaw_skills/... 或 aos/... 或 docs/...
3. 内容中提到的已知 Agent/技能名（strategy-researcher, duty-reporter, quant_assistant）
4. 出边指向的已有节点带有 entity_ref，则继承

输出仍是一个合法 patch，供 reconcile/apply 使用。
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, obj: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


TICKET_RE = re.compile(r"TKT-\d{4}-\d+[A-Z]?")
PATH_RE = re.compile(r"\b(openclaw_skills|skills|aos|docs)/[\w\-./]+\b")
API_SERVICE_REFS = [
    (re.compile(r"/backtests/|/runs/|/strategy-builder/|POST /runs|GET /runs"), "aos/services/backtest-api"),
    (re.compile(r"/knowledge/"), "aos/services/knowledge-api"),
]
SKILL_KEYWORDS = {
    "strategy-researcher": "openclaw_skills/strategy-researcher",
    "strategy_researcher": "openclaw_skills/strategy-researcher",
    "duty-reporter": "openclaw_skills/duty-reporter",
    "duty_reporter": "openclaw_skills/duty-reporter",
    "quant_assistant": "openclaw_skills/quant-assistant",
    "quant-assistant": "openclaw_skills/quant-assistant",
}

# 只有内容同时包含技能名和以下“工件/实现/代码”线索时，才允许把技能目录作为 entity_ref
ARTIFACT_INDICATOR_RE = re.compile(
    r"(脚本|script|文件|file|目录|dir|路径|path|api|接口|模块|module|代码|code|"
    r"缺少|缺失|实现|编写|创建|构建|build|skill|技能|artifact|工件)",
    re.IGNORECASE,
)


def normalize_path(path: str) -> str:
    # 如果是文件，向上收敛到技能/模块目录，避免过于细碎的 file-level entity_ref
    parts = path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "openclaw_skills":
        return "/".join(parts[:2])
    return path


def infer_from_content(content: str, node_type: str | None = None) -> str | None:
    if not content:
        return None

    # 文件/目录路径优先级最高：可确定到具体文件时更精确
    path_match = PATH_RE.search(content)
    if path_match:
        return normalize_path(path_match.group(0))

    # API 路径收敛到服务模块
    for api_re, api_ref in API_SERVICE_REFS:
        if api_re.search(content):
            return api_ref

    ticket = TICKET_RE.search(content)
    if ticket:
        return ticket.group(0)

    # Decision 节点通常代表策略/结论，不应直接绑定到技能目录，避免与 FileArtifact 冲突
    if node_type == "Decision":
        return None

    lowered = content.lower()
    has_artifact_clue = ARTIFACT_INDICATOR_RE.search(content) is not None
    for keyword, ref in SKILL_KEYWORDS.items():
        if keyword in lowered and has_artifact_clue:
            return ref

    return None


def build_entity_ref_index(graph: dict[str, Any]) -> dict[str, str]:
    nodes = graph.get("nodes", {})
    edges = graph.get("edges", [])
    index: dict[str, str] = {}
    for edge in edges:
        target = edge.get("target")
        source = edge.get("source")
        if not target or not source:
            continue
        target_ref = nodes.get(target, {}).get("entity_ref")
        if target_ref and source not in index:
            index[source] = target_ref
    return index


def normalize_state(value: Any) -> str | None:
    if value is None:
        return None
    return str(value).strip().lower() or None


def is_entity_ref_occupied(graph: dict[str, Any], ref: str, exclude_node_id: str | None = None,
                           candidate_state: str | None = None) -> bool:
    """若图中已有其他 active 节点以互斥状态占用该 entity_ref，则返回 True，避免冲突。"""
    if not ref:
        return False
    nodes = graph.get("nodes", {})
    candidate_state = normalize_state(candidate_state)
    for nid, node in nodes.items():
        if exclude_node_id and nid == exclude_node_id:
            continue
        if node.get("entity_ref") != ref:
            continue
        status = normalize_state(node.get("status")) or "active"
        if status == "superseded":
            continue
        state = normalize_state(node.get("state"))
        # 若任一方 state 不在互斥集合中（如 Fact 的 null/unknown），允许共享
        if state not in MUTUALLY_EXCLUSIVE_ACTIVE_STATES:
            continue
        if candidate_state not in MUTUALLY_EXCLUSIVE_ACTIVE_STATES:
            continue
        if state != candidate_state:
            return True
    return False


def merge_node(base: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    merged.update(changes)
    return merged


TERMINAL_STATES = {"resolved", "cancelled"}
MUTUALLY_EXCLUSIVE_ACTIVE_STATES = {
    "blocked", "cancelled", "deployed", "implemented", "open", "resolved"
}


def ensure_terminal_opentask_status(node_or_changes: dict[str, Any]) -> None:
    node_type = (node_or_changes.get("type") or "").strip()
    state = (node_or_changes.get("state") or "").strip().lower()
    if node_type == "OpenTask" and state in TERMINAL_STATES:
        status = node_or_changes.get("status")
        if status is None:
            node_or_changes["status"] = "superseded"
            node_or_changes["_status_sanitized"] = True


def sanitize_patch(patch: dict[str, Any], graph: dict[str, Any] | None) -> dict[str, Any]:
    patch = json.loads(json.dumps(patch))  # deep copy
    nodes = graph.get("nodes", {}) if graph else {}
    edge_ref_index = build_entity_ref_index(graph) if graph else {}

    # new_nodes
    for node in patch.get("new_nodes", []):
        ensure_terminal_opentask_status(node)
        if node.get("entity_ref"):
            continue
        content = node.get("content") or ""
        ref = infer_from_content(content, node.get("type"))
        if not ref and node.get("node_id") in edge_ref_index:
            ref = edge_ref_index[node["node_id"]]
        if ref and graph and is_entity_ref_occupied(graph, ref, exclude_node_id=node.get("node_id"), candidate_state=node.get("state")):
            ref = None
        if ref:
            node["entity_ref"] = ref
            node["_entity_ref_sanitized"] = True

    # updated_nodes
    for update in patch.get("updated_nodes", []):
        nid = update.get("node_id")
        changes = update.get("changes", {})
        base = nodes.get(nid, {})
        merged = merge_node(base, changes)
        # 如果 changes 把 OpenTask 推入终态但未给 status，则补 superseded
        if (base.get("type") == "OpenTask" or merged.get("type") == "OpenTask") and "status" not in changes:
            ensure_terminal_opentask_status(merged)
            if merged.get("status") == "superseded":
                changes["status"] = "superseded"
                changes["_status_sanitized"] = True
        # 若本次更新未显式修改 entity_ref，且原节点已有 entity_ref，则保留原值，避免冲突
        if "entity_ref" not in changes and base.get("entity_ref"):
            continue
        if changes.get("entity_ref"):
            continue
        content = merged.get("content") or ""
        ref = infer_from_content(content, merged.get("type"))
        if not ref and nid in edge_ref_index:
            ref = edge_ref_index[nid]
        if ref and graph and is_entity_ref_occupied(graph, ref, exclude_node_id=nid, candidate_state=merged.get("state")):
            ref = None
        if ref:
            changes["entity_ref"] = ref
            changes["_entity_ref_sanitized"] = True

    return patch


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-fill missing entity_ref in patch")
    parser.add_argument("--patch", required=True, help="Input patch JSON")
    parser.add_argument("--graph", help="Current graph_state JSON (optional)")
    parser.add_argument("--out", required=True, help="Output sanitized patch JSON")
    args = parser.parse_args()

    patch = load_json(args.patch)
    graph = load_json(args.graph) if args.graph else None
    sanitized = sanitize_patch(patch, graph)
    write_json(args.out, sanitized)
    print(f"Wrote sanitized patch: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
