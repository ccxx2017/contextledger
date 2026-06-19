#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
reconcile_patch.py

Reconciliation Pass:
- 输入 graph_state.json 和 patch.json
- 不调用 LLM
- 基于完整图做机械一致性检查
- entity_ref 精确相等是强判定
- 无 entity_ref 时只做弱兜底 warning
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


SOURCE_KEYS = (
    "source",
    "source_id",
    "source_node_id",
    "from",
    "from_id",
    "from_node_id",
    "src",
    "new_node_id",
)

TARGET_KEYS = (
    "target",
    "target_id",
    "target_node_id",
    "to",
    "to_id",
    "to_node_id",
    "dst",
    "old_node_id",
    "invalidated_node_id",
)

ID_KEYS = (
    "node_id",
    "id",
    "old_node_id",
    "target_node_id",
    "target",
    "node",
)


def load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, obj: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def normalize_ws(text: Any) -> str:
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def normalize_content(text: Any) -> str:
    return normalize_ws(text).lower()


def normalize_type(value: Any) -> str:
    return normalize_ws(value).lower()


def normalize_state(value: Any) -> str:
    return normalize_ws(value).lower()


def normalize_entity_ref(value: Any) -> str:
    # 注意：这里不做语义归一化，只做首尾空白清理。
    # entity_ref 的“同一实体”判定依赖精确相等。
    if value is None:
        return ""
    return str(value).strip()


def node_id(node: dict[str, Any]) -> str:
    return str(node.get("node_id") or node.get("id") or "").strip()


def is_active(node: dict[str, Any]) -> bool:
    if node.get("active") is False:
        return False
    status = normalize_state(node.get("status", "active"))
    return status == "active"


def extract_nodes_from_container(data: Any) -> list[dict[str, Any]]:
    """
    兼容几种常见 graph_state 结构：

    1. {"nodes": [...]}
    2. {"graph": {"nodes": [...]}}
    3. {"graph_state": {"nodes": [...]}}
    4. {"nodes": {"n_0001": {...}}}
    5. 直接是 [...]
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
            nodes: list[dict[str, Any]] = []
            for k, v in cur.items():
                if isinstance(v, dict):
                    item = dict(v)
                    item.setdefault("node_id", str(k))
                    nodes.append(item)
            return nodes

    raise ValueError("Cannot find nodes in graph_state.json")


def extract_patch_new_nodes(patch: dict[str, Any]) -> list[dict[str, Any]]:
    raw = patch.get("new_nodes", [])

    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]

    if isinstance(raw, dict):
        result: list[dict[str, Any]] = []
        for k, v in raw.items():
            if isinstance(v, dict):
                item = dict(v)
                item.setdefault("node_id", str(k))
                result.append(item)
        return result

    return []


def extract_id_from_item(item: Any) -> str:
    if item is None:
        return ""

    if isinstance(item, (str, int)):
        return str(item).strip()

    if isinstance(item, dict):
        for key in ID_KEYS:
            value = item.get(key)
            if isinstance(value, (str, int)):
                return str(value).strip()
            if isinstance(value, dict):
                nested = extract_id_from_item(value)
                if nested:
                    return nested

    return ""


def extract_id_by_keys(obj: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = obj.get(key)
        if isinstance(value, (str, int)):
            return str(value).strip()
        if isinstance(value, dict):
            nested = extract_id_from_item(value)
            if nested:
                return nested
    return ""


def is_invalidates_edge(edge: dict[str, Any]) -> bool:
    for key in ("type", "edge_type", "relation", "label", "predicate", "name"):
        value = normalize_state(edge.get(key))
        if value == "invalidates":
            return True
    return False


def parse_reconciliation_marks(
    patch: dict[str, Any],
    new_nodes: list[dict[str, Any]],
) -> tuple[set[str], set[tuple[str, str]], set[str]]:
    """
    返回：
    - superseded_old_ids
    - invalidates_pairs: {(new_node_id, old_node_id)}
    - invalidated_old_ids: {old_node_id}

    兼容这些写法：

    {
      "superseded_nodes": ["n_0045"]
    }

    {
      "new_edges": [
        {
          "source": "n_0047",
          "target": "n_0045",
          "type": "invalidates"
        }
      ]
    }

    或：

    {
      "invalidates": [
        {
          "new_node_id": "n_0047",
          "old_node_id": "n_0045"
        }
      ]
    }

    或 node 内部：

    {
      "new_nodes": [
        {
          "node_id": "n_0047",
          "invalidates": ["n_0045"]
        }
      ]
    }
    """
    superseded_old_ids: set[str] = set()
    invalidates_pairs: set[tuple[str, str]] = set()
    invalidated_old_ids: set[str] = set()

    for key in ("superseded_nodes", "supersedes", "superseded"):
        for item in as_list(patch.get(key)):
            old_id = extract_id_from_item(item)
            if old_id:
                superseded_old_ids.add(old_id)

    for item in as_list(patch.get("invalidates")):
        if isinstance(item, dict):
            src = extract_id_by_keys(item, SOURCE_KEYS)
            dst = extract_id_by_keys(item, TARGET_KEYS)

            if not dst:
                dst = extract_id_from_item(item)

            if dst:
                invalidated_old_ids.add(dst)

            if src and dst:
                invalidates_pairs.add((src, dst))
        else:
            old_id = extract_id_from_item(item)
            if old_id:
                invalidated_old_ids.add(old_id)

    for edge in as_list(patch.get("new_edges")):
        if not isinstance(edge, dict):
            continue

        if not is_invalidates_edge(edge):
            continue

        src = extract_id_by_keys(edge, SOURCE_KEYS)
        dst = extract_id_by_keys(edge, TARGET_KEYS)

        if dst:
            invalidated_old_ids.add(dst)

        if src and dst:
            invalidates_pairs.add((src, dst))

    for new_node in new_nodes:
        new_id = node_id(new_node)
        if not new_id:
            continue

        for item in as_list(new_node.get("invalidates")):
            old_id = extract_id_from_item(item)
            if old_id:
                invalidates_pairs.add((new_id, old_id))
                invalidated_old_ids.add(old_id)

        for item in as_list(new_node.get("supersedes")):
            old_id = extract_id_from_item(item)
            if old_id:
                superseded_old_ids.add(old_id)

    return superseded_old_ids, invalidates_pairs, invalidated_old_ids


def tokenize_for_weak_match(text: str) -> set[str]:
    text = normalize_content(text)
    tokens: set[str] = set()

    for token in re.findall(r"[a-z0-9]+(?:[-_][a-z0-9]+)*", text):
        if len(token) >= 2:
            tokens.add(token)

    cjk_chunks = re.findall(r"[\u4e00-\u9fff]+", text)
    for chunk in cjk_chunks:
        if len(chunk) <= 2:
            tokens.add(chunk)
        else:
            for i in range(len(chunk) - 1):
                tokens.add(chunk[i : i + 2])

    return tokens


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def content_similarity(a: str, b: str) -> float:
    a = normalize_content(a)
    b = normalize_content(b)

    if not a or not b:
        return 0.0

    return SequenceMatcher(None, a, b).ratio()


def cosine_similarity(a: Any, b: Any) -> float | None:
    if not isinstance(a, list) or not isinstance(b, list):
        return None

    if len(a) != len(b) or not a:
        return None

    try:
        av = [float(x) for x in a]
        bv = [float(x) for x in b]
    except Exception:
        return None

    dot = sum(x * y for x, y in zip(av, bv))
    na = sum(x * x for x in av) ** 0.5
    nb = sum(y * y for y in bv) ** 0.5

    if na == 0 or nb == 0:
        return None

    return dot / (na * nb)


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


def has_invalidates(
    new_id: str,
    old_id: str,
    invalidates_pairs: set[tuple[str, str]],
    invalidated_old_ids: set[str],
) -> bool:
    return (new_id, old_id) in invalidates_pairs or old_id in invalidated_old_ids


def reconcile(
    graph_state: dict[str, Any],
    patch: dict[str, Any],
    *,
    weak_content_threshold: float = 0.88,
    weak_keyword_threshold: float = 0.65,
    embedding_threshold: float = 0.90,
) -> dict[str, Any]:
    graph_nodes = extract_nodes_from_container(graph_state)
    active_old_nodes = [n for n in graph_nodes if is_active(n)]

    new_nodes = extract_patch_new_nodes(patch)

    superseded_old_ids, invalidates_pairs, invalidated_old_ids = parse_reconciliation_marks(
        patch,
        new_nodes,
    )

    report: dict[str, Any] = {
        "ok": True,
        "summary": {
            "graph_nodes": len(graph_nodes),
            "active_graph_nodes": len(active_old_nodes),
            "new_nodes": len(new_nodes),
            "errors": 0,
            "warnings": 0,
        },
        "errors": [],
        "warnings": [],
        "resolved_conflicts": [],
        "entity_ref_matches": [],
        "weak_matches": [],
    }

    old_by_id: dict[str, dict[str, Any]] = {}
    for old in graph_nodes:
        old_id = node_id(old)
        if old_id:
            old_by_id[old_id] = old

    active_by_entity_ref: dict[str, list[dict[str, Any]]] = {}
    for old in active_old_nodes:
        entity_ref = normalize_entity_ref(old.get("entity_ref"))
        if entity_ref:
            active_by_entity_ref.setdefault(entity_ref, []).append(old)

    seen_new_ids: set[str] = set()

    for new in new_nodes:
        new_id = node_id(new)

        if not new_id:
            add_issue(
                report,
                "error",
                "NEW_NODE_MISSING_ID",
                "new_nodes 中存在缺少 node_id 的节点。",
                new_node=new,
            )
            continue

        if new_id in seen_new_ids:
            add_issue(
                report,
                "error",
                "DUPLICATE_NEW_NODE_ID_IN_PATCH",
                f"patch.new_nodes 内部存在重复 node_id: {new_id}",
                new_node_id=new_id,
            )
        seen_new_ids.add(new_id)

        if new_id in old_by_id:
            add_issue(
                report,
                "error",
                "NODE_ID_COLLISION_WITH_GRAPH",
                f"新节点 {new_id} 的 node_id 已存在于 graph_state.json。",
                new_node_id=new_id,
            )

        new_content = normalize_content(new.get("content"))
        new_type = normalize_type(new.get("type"))
        new_state = normalize_state(new.get("state"))
        new_entity_ref = normalize_entity_ref(new.get("entity_ref"))

        # 1. 检查新节点是否和全图 active 节点精确重复
        for old in active_old_nodes:
            old_id = node_id(old)
            old_content = normalize_content(old.get("content"))
            old_type = normalize_type(old.get("type"))
            old_state = normalize_state(old.get("state"))

            if (
                new_content
                and new_content == old_content
                and new_type == old_type
                and new_state == old_state
            ):
                add_issue(
                    report,
                    "error",
                    "EXACT_ACTIVE_DUPLICATE",
                    f"新节点 {new_id} 与 active 旧节点 {old_id} 内容、type、state 完全重复。",
                    new_node_id=new_id,
                    old_node_id=old_id,
                )

        # 2/3/5. entity_ref 强判定
        if new_entity_ref:
            same_entity_old_nodes = active_by_entity_ref.get(new_entity_ref, [])

            for old in same_entity_old_nodes:
                old_id = node_id(old)
                old_state = normalize_state(old.get("state"))

                report["entity_ref_matches"].append(
                    {
                        "entity_ref": new_entity_ref,
                        "new_node_id": new_id,
                        "old_node_id": old_id,
                        "new_state": new_state,
                        "old_state": old_state,
                    }
                )

                if new_state and old_state and new_state != old_state:
                    missing_supersede = old_id not in superseded_old_ids
                    missing_invalidates = not has_invalidates(
                        new_id,
                        old_id,
                        invalidates_pairs,
                        invalidated_old_ids,
                    )

                    if missing_supersede:
                        add_issue(
                            report,
                            "error",
                            "STATE_CONFLICT_MISSING_SUPERSEDE",
                            (
                                f"新节点 {new_id} 与旧节点 {old_id} 指向同一 entity_ref={new_entity_ref}，"
                                f"但 state 冲突：new={new_state}, old={old_state}；"
                                f"patch 缺少 superseded_nodes 对 {old_id} 的声明。"
                            ),
                            entity_ref=new_entity_ref,
                            new_node_id=new_id,
                            old_node_id=old_id,
                            new_state=new_state,
                            old_state=old_state,
                        )

                    if missing_invalidates:
                        add_issue(
                            report,
                            "error",
                            "STATE_CONFLICT_MISSING_INVALIDATES",
                            (
                                f"新节点 {new_id} 与旧节点 {old_id} 指向同一 entity_ref={new_entity_ref}，"
                                f"但 state 冲突：new={new_state}, old={old_state}；"
                                f"patch 缺少 {new_id} invalidates {old_id}。"
                            ),
                            entity_ref=new_entity_ref,
                            new_node_id=new_id,
                            old_node_id=old_id,
                            new_state=new_state,
                            old_state=old_state,
                        )

                    if not missing_supersede and not missing_invalidates:
                        report["resolved_conflicts"].append(
                            {
                                "entity_ref": new_entity_ref,
                                "new_node_id": new_id,
                                "old_node_id": old_id,
                                "new_state": new_state,
                                "old_state": old_state,
                            }
                        )

                elif new_state and old_state and new_state == old_state:
                    sim = content_similarity(new.get("content", ""), old.get("content", ""))

                    if sim >= 0.90:
                        add_issue(
                            report,
                            "warning",
                            "SAME_ENTITY_SAME_STATE_POTENTIAL_DUPLICATE",
                            (
                                f"新节点 {new_id} 与旧节点 {old_id} 指向同一 entity_ref={new_entity_ref}，"
                                f"且 state 相同、内容高度相似，可能是重复写入。"
                            ),
                            entity_ref=new_entity_ref,
                            new_node_id=new_id,
                            old_node_id=old_id,
                            state=new_state,
                            content_similarity=round(sim, 4),
                        )

            continue

        # 4. 无 entity_ref：弱兜底，只 warning
        new_tokens = tokenize_for_weak_match(str(new.get("content", "")))
        weak_hits: list[dict[str, Any]] = []

        for old in active_old_nodes:
            old_id = node_id(old)

            sim = content_similarity(new.get("content", ""), old.get("content", ""))

            old_tokens = tokenize_for_weak_match(str(old.get("content", "")))
            kw_score = jaccard(new_tokens, old_tokens)

            emb_score = cosine_similarity(
                new.get("embedding") or new.get("_embedding"),
                old.get("embedding") or old.get("_embedding"),
            )

            methods: list[str] = []

            if sim >= weak_content_threshold:
                methods.append("content_similarity")

            if kw_score >= weak_keyword_threshold:
                methods.append("keyword_match")

            if emb_score is not None and emb_score >= embedding_threshold:
                methods.append("embedding_similarity")

            if not methods:
                continue

            score = max(sim, kw_score, emb_score or 0.0)

            weak_hits.append(
                {
                    "old_node_id": old_id,
                    "score": round(score, 4),
                    "content_similarity": round(sim, 4),
                    "keyword_score": round(kw_score, 4),
                    "embedding_similarity": None if emb_score is None else round(emb_score, 4),
                    "methods": methods,
                    "old_state": normalize_state(old.get("state")),
                }
            )

        weak_hits.sort(key=lambda x: x["score"], reverse=True)

        for hit in weak_hits[:5]:
            old_state = hit.get("old_state", "")
            state_changed = bool(new_state and old_state and new_state != old_state)

            code = (
                "WEAK_POTENTIAL_CONFLICT_NO_ENTITY_REF"
                if state_changed
                else "WEAK_POTENTIAL_DUPLICATE_NO_ENTITY_REF"
            )

            msg = (
                f"新节点 {new_id} 没有 entity_ref，但与 active 旧节点 {hit['old_node_id']} "
                f"存在弱匹配；该判断只作为 warning，不作为强保证。"
            )

            if state_changed:
                msg += f" 两者 state 可能冲突：new={new_state}, old={old_state}。"

            add_issue(
                report,
                "warning",
                code,
                msg,
                new_node_id=new_id,
                old_node_id=hit["old_node_id"],
                new_state=new_state,
                old_state=old_state,
                weak_match=hit,
            )

            report["weak_matches"].append(
                {
                    "new_node_id": new_id,
                    **hit,
                }
            )

    report["summary"]["errors"] = len(report["errors"])
    report["summary"]["warnings"] = len(report["warnings"])
    report["ok"] = len(report["errors"]) == 0

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Mechanical reconciliation pass for graph patches.")
    parser.add_argument("graph_state", help="Path to graph_state.json")
    parser.add_argument("patch", help="Path to patch.json")
    parser.add_argument("--out", help="Optional output path for reconciliation report JSON")
    parser.add_argument("--no-fail", action="store_true", help="Always exit 0 even if errors exist")

    parser.add_argument("--weak-content-threshold", type=float, default=0.88)
    parser.add_argument("--weak-keyword-threshold", type=float, default=0.65)
    parser.add_argument("--embedding-threshold", type=float, default=0.90)

    args = parser.parse_args()

    graph_state = load_json(args.graph_state)
    patch = load_json(args.patch)

    report = reconcile(
        graph_state,
        patch,
        weak_content_threshold=args.weak_content_threshold,
        weak_keyword_threshold=args.weak_keyword_threshold,
        embedding_threshold=args.embedding_threshold,
    )

    if args.out:
        write_json(args.out, report)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if report["errors"] and not args.no_fail:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())