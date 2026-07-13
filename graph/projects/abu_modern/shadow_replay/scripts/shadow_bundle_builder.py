#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shadow context bundle builder.

Builds a minimal context bundle from the shadow graph state for replay comparison.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shadow_compiler import graph_state_hash


def build_shadow_bundle(graph_state: dict[str, Any], budget: int = 8192) -> dict[str, Any]:
    """Return a context bundle containing active nodes and must_include set."""
    nodes = graph_state.get("nodes", {})
    if isinstance(nodes, list):
        nodes = {n["node_id"]: n for n in nodes if isinstance(n, dict)}

    active_nodes = [n for n in nodes.values() if n.get("status") == "active"]
    active_nodes.sort(key=lambda n: (n.get("observed_at") or "", n.get("node_id") or ""))

    # Simple token budget: count characters / 4 as rough tokens
    included: list[dict[str, Any]] = []
    tokens_used = 0
    for node in active_nodes:
        text = f"{node.get('node_type', '')}: {node.get('content', '')}"
        node_tokens = max(1, len(text) // 4)
        if tokens_used + node_tokens > budget and included:
            break
        included.append(node)
        tokens_used += node_tokens

    must_include = [n["node_id"] for n in included]

    return {
        "project_id": graph_state.get("project_id"),
        "turn_counter": graph_state.get("turn_counter"),
        "budget": budget,
        "tokens_used": tokens_used,
        "included_node_count": len(included),
        "must_include": must_include,
        "nodes": included,
    }


def bundle_hash(bundle: dict[str, Any]) -> str:
    serialized = json.dumps(bundle, sort_keys=True, ensure_ascii=False)
    import hashlib
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
