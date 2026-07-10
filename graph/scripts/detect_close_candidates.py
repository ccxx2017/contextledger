#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from graph_lint import load_json


def write_json(path: str | Path, obj: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def normalize_text(text: Any) -> str:
    return str(text or "").strip()


def collect_evidence_text(patch: dict[str, Any]) -> str:
    chunks: list[str] = []
    for item in patch.get("new_nodes", []) or []:
        chunks.append(normalize_text(item.get("content")))
        chunks.append(normalize_text(item.get("entity_ref")))

    for item in patch.get("updated_nodes", []) or []:
        chunks.append(normalize_text(item.get("reason")))
        changes = item.get("changes") or {}
        if isinstance(changes, dict):
            chunks.append(normalize_text(changes.get("content")))
            chunks.append(normalize_text(changes.get("entity_ref")))
            chunks.append(normalize_text(changes.get("state")))

    for item in patch.get("new_edges", []) or []:
        chunks.append(normalize_text(item.get("source")))
        chunks.append(normalize_text(item.get("target")))
        chunks.append(normalize_text(item.get("relation")))

    text = "\n".join([c for c in chunks if c])
    return text


def tokenize(text: str) -> set[str]:
    lowered = text.lower()
    tokens = set(re.findall(r"[a-z0-9_./\\:-]{3,}", lowered))
    tokens.update(re.findall(r"tkt-[0-9]{4}-[0-9]{3}(?:~[0-9]{3})?", lowered))
    tokens.update(re.findall(r"n_[0-9]{4}", lowered))
    tokens.update(re.findall(r"[\u4e00-\u9fff]{2,}", text))
    return {t.strip() for t in tokens if t.strip()}


def node_is_open_like(node: dict[str, Any]) -> bool:
    state = str(node.get("state") or "").strip().lower()
    status = str(node.get("status") or "active").strip().lower()
    return status == "active" and state in {"open", "blocked", "in_progress"}


def node_summary(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "node_id": node.get("node_id"),
        "type": node.get("type"),
        "entity_ref": node.get("entity_ref"),
        "state": node.get("state"),
        "status": node.get("status", "active"),
        "priority": node.get("priority"),
        "content": node.get("content"),
    }


def score_candidate(node: dict[str, Any], evidence_text: str, evidence_tokens: set[str]) -> tuple[int, list[str]]:
    matched: list[str] = []
    score = 0

    entity_ref = normalize_text(node.get("entity_ref"))
    if entity_ref:
        if entity_ref in evidence_text:
            score += 10
            matched.append(entity_ref)
        else:
            entity_ref_lower = entity_ref.lower()
            if entity_ref_lower in evidence_text.lower():
                score += 8
                matched.append(entity_ref)

    node_tokens = tokenize(normalize_text(node.get("content"))) | tokenize(entity_ref)
    overlap = sorted(node_tokens & evidence_tokens)
    if overlap:
        score += min(6, len(overlap))
        matched.extend(overlap[:12])

    return score, matched


def main() -> int:
    parser = argparse.ArgumentParser(
        description="召回：可能应被本轮内容关闭/推进，但 patch 未显式 updated 的旧 open 节点候选清单（用于闸门人工核对）。"
    )
    parser.add_argument("--graph", required=True, help="上一态 graph_state.json")
    parser.add_argument("--patch", required=True, help="本轮 patch（reviewed 或 resolved 均可）")
    parser.add_argument("--out", required=True, help="输出报告 JSON 路径")
    parser.add_argument("--min-score", type=int, default=3, help="候选最低分阈值")
    parser.add_argument("--max-candidates", type=int, default=30, help="最多输出候选数量")
    args = parser.parse_args()

    graph_path = Path(args.graph)
    patch_path = Path(args.patch)
    graph = load_json(graph_path)
    patch = load_json(patch_path)

    nodes = graph.get("nodes") or {}
    if not isinstance(nodes, dict):
        raise SystemExit(f"{graph_path} 的 nodes 字段不是 dict，无法扫描。")

    updated_ids = {str(item.get("node_id")) for item in patch.get("updated_nodes", []) or [] if item.get("node_id")}
    evidence_text = collect_evidence_text(patch)
    evidence_tokens = tokenize(evidence_text)

    candidates: list[dict[str, Any]] = []
    for node_id, node in nodes.items():
        if not isinstance(node, dict):
            continue
        nid = str(node.get("node_id") or node_id)
        if nid in updated_ids:
            continue
        if not node_is_open_like(node):
            continue
        score, matched = score_candidate(node, evidence_text, evidence_tokens)
        if score < int(args.min_score):
            continue
        item = node_summary(node)
        item["score"] = score
        item["matched_terms"] = matched[:20]
        candidates.append(item)

    candidates.sort(key=lambda x: (-int(x.get("score") or 0), str(x.get("node_id") or "")))
    candidates = candidates[: int(args.max_candidates)]

    score_hist = Counter(int(item.get("score") or 0) for item in candidates)
    result = {
        "kind": "close_candidates.phase1_gate.v1",
        "graph_path": str(graph_path),
        "patch_path": str(patch_path),
        "threshold": {"min_score": args.min_score, "max_candidates": args.max_candidates},
        "stats": {
            "graph_turn_counter": graph.get("turn_counter"),
            "open_like_nodes_scanned": sum(1 for v in nodes.values() if isinstance(v, dict) and node_is_open_like(v)),
            "updated_nodes_in_patch": len(updated_ids),
            "candidates_found": len(candidates),
            "score_histogram": dict(sorted(score_hist.items(), key=lambda kv: (-kv[0], kv[1]))),
        },
        "candidates": candidates,
    }
    write_json(args.out, result)
    print(f"Wrote close candidates: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

