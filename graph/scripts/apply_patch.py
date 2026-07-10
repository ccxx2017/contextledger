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


def parse_turn_number(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        pass

    text = str(value or "").strip().lower()
    if text.startswith("turn_"):
        text = text.split("_", 1)[1]
    try:
        return int(text)
    except (TypeError, ValueError):
        return None


def require_existing_file(path_str: str, *, role: str, hint: str) -> Path:
    path = Path(path_str)
    if not path.exists():
        raise SystemExit(f"{role} 不存在: {path}。{hint}")
    return path


def validate_apply_preconditions(
    graph: dict[str, Any],
    patch: dict[str, Any],
    *,
    graph_path: Path,
    patch_path: Path,
    expected_turn: Any | None,
) -> tuple[int, int]:
    graph_turn = parse_turn_number(graph.get("turn_counter"))
    if graph_turn is None:
        raise SystemExit(f"{graph_path} 缺少可解析的 turn_counter，拒绝执行 apply。")

    patch_turn = parse_turn_number(patch.get("turn_id"))
    if patch_turn is None:
        raise SystemExit(f"{patch_path} 缺少可解析的 turn_id，拒绝执行 apply。")

    if expected_turn is not None:
        expected = parse_turn_number(expected_turn)
        if expected is None:
            raise SystemExit(f"无法解析 --expected-turn={expected_turn!r}")
        if patch_turn != expected:
            raise SystemExit(
                f"{patch_path} 的 turn_id={patch_turn}，与 --expected-turn=turn_{expected:03d} 不一致。"
                "为避免写入错误轮次，已拒绝执行。"
            )

    # 允许 graph_turn < patch_turn - 1（前面有轮次被 quarantine 跳过），
    # 但不允许 graph_turn >= patch_turn（重复 apply 或乱序）。
    if graph_turn >= patch_turn:
        raise SystemExit(
            f"{graph_path} 的 turn_counter={graph_turn}，但 {patch_path} 的 turn_id={patch_turn}。"
            "graph 已处于或超过本轮状态，拒绝重复/乱序 apply。"
        )
    if graph_turn < patch_turn - 1:
        print(
            f"WARN: {graph_path} 的 turn_counter={graph_turn}，跳过 turn_{graph_turn + 1:03d} ~ turn_{patch_turn - 1:03d}，"
            f"直接应用 turn_{patch_turn:03d}（quarantine 跳过模式）。"
        )

    return graph_turn, patch_turn


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

    turn_id = patch.get("turn_id")
    try:
        patch_turn = int(turn_id) if turn_id is not None else None
    except (TypeError, ValueError):
        patch_turn = None

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
        item = dict(n)
        if patch_turn is not None:
            item.setdefault("created_turn", patch_turn)
        nodes[nid] = item

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
    if patch_turn is not None:
        new_graph["turn_counter"] = max(new_graph.get("turn_counter", 0), patch_turn)

    return new_graph


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply a Graph Patch to graph_state.json")
    parser.add_argument("--graph", required=True, help="Path to graph_state.json")
    parser.add_argument("--patch", required=True, help="Path to patch.json")
    parser.add_argument("--out", help="Output path for new graph_state.json")
    parser.add_argument("--in-place", action="store_true", help="Overwrite the original graph file")
    parser.add_argument("--snapshot-dir", help="Directory to save a turn-numbered snapshot after successful apply")
    parser.add_argument("--expected-turn", help="预期执行的轮次，如 4 或 turn_004")

    args = parser.parse_args()

    graph_path = require_existing_file(
        args.graph,
        role="graph",
        hint="请传入当前权威图或上一轮 run 快照。",
    )
    patch_path = require_existing_file(
        args.patch,
        role="patch",
        hint="请先生成并确认本轮 patch.json。",
    )

    graph = load_json(graph_path)
    patch = load_json(patch_path)
    _, patch_turn = validate_apply_preconditions(
        graph,
        patch,
        graph_path=graph_path,
        patch_path=patch_path,
        expected_turn=args.expected_turn,
    )

    new_graph = apply_patch(graph, patch)

    if args.in_place:
        write_json(graph_path, new_graph)
        print(f"Updated in-place: {graph_path}")
        out_path = graph_path
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
        snap_dir = Path(args.snapshot_dir)
        snap_dir.mkdir(parents=True, exist_ok=True)
        snap_name = f"graph_state.turn_{patch_turn:03d}.json"
        snap_path = snap_dir / snap_name
        if snap_path.exists():
            snap_name = f"graph_state.turn_{patch_turn:03d}.rerun.json"
            snap_path = snap_dir / snap_name
            print(f"[WARN] Snapshot conflict, writing to {snap_path}")
        shutil.copy2(str(out_path), str(snap_path))
        print(f"Snapshot saved: {snap_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
