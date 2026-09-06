#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""失效边差异解释器（工作包 B4，评审 §三：新增/减少失效逐条归因）。

对比两份 graph_state 的 invalidates 边集合，每条新增/消失的失效边输出：
    {edge, direction, causing_rule, adjudication_key, lifecycle_ref, reason}

causing_rule 的归因优先级：
    1. 新节点/旧节点上的 _superseded_reason（adjudicator 决策附带的理由）
    2. 节点上的 _decision.action / _decision.reason
    3. "unattributed" —— 出现该值即视为未解释，B 门不通过

用法：
    python graph/scripts/explain_invalidation_diff.py \
        --before reports/baseline_A/graph_state_frozen.json \
        --after graph/projects/abu_modern/graph_state.json \
        --out reports/lifecycle_B/invalidation_diff.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def invalidation_edges(graph: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    """收集 invalidates 边：{(source, target): edge}。"""
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for edge in graph.get("edges", []):
        if not isinstance(edge, dict):
            continue
        relation = str(edge.get("relation") or edge.get("type") or "").strip().lower()
        if relation != "invalidates":
            continue
        src = str(edge.get("source") or "")
        tgt = str(edge.get("target") or "")
        result[(src, tgt)] = edge
    return result


def attribute_rule(
    graph: dict[str, Any],
    source_id: str,
    target_id: str,
) -> tuple[str, str, str, str]:
    """归因一条失效边 -> (causing_rule, reason, adjudication_key, lifecycle_ref)。"""
    nodes = graph.get("nodes", {})
    source = nodes.get(source_id) or {}
    target = nodes.get(target_id) or {}

    reason = (
        source.get("_superseded_reason")
        or target.get("_superseded_reason")
        or (source.get("_decision") or {}).get("reason")
        or (target.get("_decision") or {}).get("reason")
        or ""
    )
    action = (
        (source.get("_decision") or {}).get("action")
        or (target.get("_decision") or {}).get("action")
        or ""
    )
    if action:
        causing_rule = f"decision:{action}"
    elif reason:
        causing_rule = "decision:patch_mark"
    else:
        causing_rule = "unattributed"
    return causing_rule, str(reason), str(source.get("adjudication_key") or source.get("lifecycle_ref") or source.get("entity_ref") or ""), str(source.get("lifecycle_ref") or "")


def explain_diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_edges = invalidation_edges(before)
    after_edges = invalidation_edges(after)

    added = []
    removed = []
    for key in sorted(after_edges.keys() - before_edges.keys()):
        src, tgt = key
        rule, reason, adj_key, ref = attribute_rule(after, src, tgt)
        added.append({
            "edge": {"source": src, "target": tgt},
            "direction": "added",
            "causing_rule": rule,
            "reason": reason,
            "adjudication_key": adj_key,
            "lifecycle_ref": ref,
        })
    for key in sorted(before_edges.keys() - after_edges.keys()):
        src, tgt = key
        rule, reason, adj_key, ref = attribute_rule(before, src, tgt)
        removed.append({
            "edge": {"source": src, "target": tgt},
            "direction": "removed",
            "causing_rule": rule,
            "reason": reason,
            "adjudication_key": adj_key,
            "lifecycle_ref": ref,
        })

    unattributed = [e for e in added + removed if e["causing_rule"] == "unattributed"]
    return {
        "kind": "invalidation_diff.v1",
        "summary": {
            "before_edge_count": len(before_edges),
            "after_edge_count": len(after_edges),
            "added": len(added),
            "removed": len(removed),
            "unattributed": len(unattributed),
        },
        "added": added,
        "removed": removed,
        "all_attributed": len(unattributed) == 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    diff = explain_diff(load_json(Path(args.before)), load_json(Path(args.after)))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(diff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    s = diff["summary"]
    print(f"invalidation diff: +{s['added']} / -{s['removed']} (unattributed={s['unattributed']})")
    print(f"Wrote {out}")
    return 0 if diff["all_attributed"] else 1


if __name__ == "__main__":
    sys.exit(main())
