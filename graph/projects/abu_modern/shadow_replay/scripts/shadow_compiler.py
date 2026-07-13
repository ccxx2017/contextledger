#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shadow compiler: apply shadow patches to an isolated shadow graph state.

Does not write to the formal main graph.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def initialize_shadow_graph_state(project_id: str = "abu_modern") -> dict[str, Any]:
    return {
        "project_id": project_id,
        "turn_counter": 0,
        "schema_version": "lifecycle_v1_shadow",
        "nodes": {},
        "edges": [],
        "quarantine": [],
    }


def apply_shadow_patch(graph_state: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """Return a new graph state with the patch applied.

    Patch keys: new_nodes, updated_nodes, superseded_nodes, new_edges.
    """
    new_graph = json.loads(json.dumps(graph_state))
    nodes = new_graph.setdefault("nodes", {})
    if isinstance(nodes, list):
        nodes = {n["node_id"]: n for n in nodes if isinstance(n, dict)}
        new_graph["nodes"] = nodes

    for node in patch.get("new_nodes", []):
        node_id = node["node_id"]
        nodes[node_id] = json.loads(json.dumps(node))

    for update in patch.get("updated_nodes", []):
        node_id = update.get("node_id")
        if node_id and node_id in nodes:
            nodes[node_id].update(update)

    for node_id in patch.get("superseded_nodes", []):
        if node_id in nodes:
            nodes[node_id]["status"] = "superseded"
            nodes[node_id]["active"] = False

    for edge in patch.get("new_edges", []):
        new_graph["edges"].append(json.loads(json.dumps(edge)))

    turn_id = patch.get("turn_id")
    if turn_id:
        new_graph["turn_counter"] = new_graph.get("turn_counter", 0) + 1
        new_graph["last_applied_turn_id"] = turn_id

    return new_graph


def graph_state_hash(graph_state: dict[str, Any]) -> str:
    serialized = json.dumps(graph_state, sort_keys=True, ensure_ascii=False)
    import hashlib
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def ensure_shadow_path(path: Path, shadow_root: Path) -> Path:
    """Raise if path escapes the shadow root."""
    resolved = path.resolve()
    root = shadow_root.resolve()
    if not (resolved == root or resolved.is_relative_to(root)):
        raise ShadowIsolationError(f"Refusing to write outside shadow root: {path}")
    return resolved


class ShadowIsolationError(Exception):
    pass


def write_shadow_json(path: Path, obj: Any, shadow_root: Path) -> None:
    ensure_shadow_path(path, shadow_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")
