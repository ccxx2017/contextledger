#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
apply_patch.py

最小 patch 应用脚本：
1. 读取旧 graph_state.json
2. 读取 patch.json
3. 添加 new_nodes
4. 应用 updated_nodes
5. 对 superseded_nodes 中的旧节点设置 status: "superseded"
6. 添加 new_edges
7. 输出新的 graph 文件
8. 默认不覆盖原图，除非显式传入 --in-place
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, obj: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def apply_patch(graph: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    # 深拷贝避免修改原图
    new_graph = json.loads(json.dumps(graph))

    nodes = new_graph.setdefault("nodes", {})
    if isinstance(nodes, list):
        nodes = {n["node_id"]: n for n in nodes if isinstance(n, dict) and n.get("node_id")}
        new_graph["nodes"] = nodes

    edges = new_graph.setdefault("edges", [])
    if not isinstance(edges, list):
        edges = []
        new_graph["edges"] = edges

    # 1. 应用 updated_nodes
    for u in patch.get("updated_nodes", []):
        if not isinstance(u, dict):
            continue
        nid = u.get("node_id")
        if not nid or nid not in nodes:
            continue
        changes = u.get("changes", {})
        for key, value in changes.items():
            nodes[nid][key] = value
        if "reason" in u:
            nodes[nid]["_update_reason"] = u["reason"]

    # 2. 应用 superseded_nodes
    for s in patch.get("superseded_nodes", []):
        if not isinstance(s, dict):
            continue
        nid = s.get("node_id")
        if not nid or nid not in nodes:
            continue
        nodes[nid]["status"] = "superseded"
        if "reason" in s:
            nodes[nid]["_superseded_reason"] = s["reason"]

    # 3. 添加 new_nodes
    for n in patch.get("new_nodes", []):
        if not isinstance(n, dict):
            continue
        nid = n.get("node_id")
        if not nid:
            continue
        if nid in nodes:
            raise ValueError(f"new_node node_id 已存在: {nid}")
        nodes[nid] = dict(n)

    # 4. 添加 new_edges
    for e in patch.get("new_edges", []):
        if not isinstance(e, dict):
            continue
        src = e.get("source") or e.get("from") or e.get("src")
        tgt = e.get("target") or e.get("to") or e.get("dst")
        relation = e.get("relation") or e.get("type") or e.get("edge_type")
        if not src or not tgt or not relation:
            continue
        edges.append({
            "source": src,
            "target": tgt,
            "relation": relation,
        })

    # 更新 turn_counter
    turn_id = patch.get("turn_id")
    if turn_id is not None:
        new_graph["turn_counter"] = max(new_graph.get("turn_counter", 0), int(turn_id))

    return new_graph


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply a Graph Patch to graph_state.json")
    parser.add_argument("--graph", required=True, help="Path to graph_state.json")
    parser.add_argument("--patch", required=True, help="Path to patch.json")
    parser.add_argument("--out", help="Output path for new graph_state.json")
    parser.add_argument("--in-place", action="store_true", help="Overwrite the original graph file")
    parser.add_argument("--snapshot-dir", help="Directory to save a turn-numbered snapshot after successful apply")

    args = parser.parse_args()

    graph = load_json(args.graph)
    patch = load_json(args.patch)

    new_graph = apply_patch(graph, patch)

    if args.in_place:
        write_json(args.graph, new_graph)
        print(f"Updated in-place: {args.graph}")
        out_path = Path(args.graph)
    elif args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(out_path, new_graph)
        print(f"Wrote {out_path}")
    else:
        print(json.dumps(new_graph, ensure_ascii=False, indent=2))
        return 0

    # Save snapshot if requested
    if args.snapshot_dir:
        turn_id = patch.get("turn_id")
        if turn_id is not None:
            snap_dir = Path(args.snapshot_dir)
            snap_dir.mkdir(parents=True, exist_ok=True)
            snap_name = f"graph_state.turn_{int(turn_id):03d}.json"
            snap_path = snap_dir / snap_name
            if snap_path.exists():
                snap_name = f"graph_state.turn_{int(turn_id):03d}.rerun.json"
                snap_path = snap_dir / snap_name
                print(f"[WARN] Snapshot conflict, writing to {snap_path}")
            shutil.copy2(str(out_path), str(snap_path))
            print(f"Snapshot saved: {snap_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
