#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
to_mermaid.py

将 graph_state.json 转换为 Mermaid 图文本。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _shorten(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + "…"


def _escape_mermaid_label(text: str) -> str:
    return text.replace('"', '\\"')


def graph_to_mermaid(graph: dict[str, Any], max_label_len: int = 40) -> str:
    lines = ["graph TD"]

    nodes = graph.get("nodes", {})
    for nid, node in nodes.items():
        node_type = _escape_mermaid_label(node.get("type", "Unknown"))
        content = _escape_mermaid_label(
            _shorten(node.get("content", ""), max_label_len)
        )

        label = f"{node_type}<br/>{content}"

        if node.get("status") == "superseded":
            lines.append(f'    {nid}["❌ {label}"]:::dead')
        else:
            lines.append(f'    {nid}["{label}"]')

    for e in graph.get("edges", []):
        src = e.get("source") or e.get("from") or e.get("src")
        tgt = e.get("target") or e.get("to") or e.get("dst")
        relation = e.get("relation") or e.get("type") or e.get("edge_type")
        if not src or not tgt or not relation:
            continue
        lines.append(f'    {src} -->|{relation}| {tgt}')

    lines.append("    classDef dead fill:#fdd,stroke:#c33;")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert graph_state.json to Mermaid text")
    parser.add_argument("--graph", required=True, help="Path to graph_state.json")
    parser.add_argument("--out", type=Path, help="Output .mmd file path")
    parser.add_argument("--max-label-len", type=int, default=40, help="Max label length")
    parser.add_argument("--print", action="store_true", dest="print_mermaid", help="Print to stdout")

    args = parser.parse_args()

    with open(args.graph, "r", encoding="utf-8") as f:
        graph = json.load(f)

    mermaid = graph_to_mermaid(graph, max_label_len=args.max_label_len)

    if args.out:
        args.out.write_text(mermaid, encoding="utf-8")
        print(f"Mermaid saved to: {args.out}")

    if args.print_mermaid or not args.out:
        print(mermaid)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
