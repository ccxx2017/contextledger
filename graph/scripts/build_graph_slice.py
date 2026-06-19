#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


NODE_ID_RE = re.compile(r"\bn_(\d+)\b")
TICKET_RE = re.compile(r"\b[A-Z][A-Z0-9]{1,12}-\d{1,8}\b")
CODE_SPAN_RE = re.compile(r"`([^`\n]{1,120})`")
FILE_RE = re.compile(
    r"\b[\w.-]+\.(?:py|json|md|txt|ya?ml|js|ts|tsx|jsx|html|css|csv|sql|sh)\b"
)
API_ROUTE_RE = re.compile(r"(?<!\w)/(?:api|v\d+|[A-Za-z0-9_.-]+)(?:/[A-Za-z0-9_.:-]+)+")
PATH_RE = re.compile(
    r"(?:^|[\s'\"`])((?:\.{0,2}/)?[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+/?)(?=$|[\s'\"`,，。；;:：)])"
)

OPENISH_STATES = {None, "", "open", "blocked", "in_progress", "pending", "todo", "unknown"}
TERMINAL_STATES = {"implemented", "deployed", "resolved", "cancelled"}

STATE_NORMALIZE = {
    "pending": "open",
    "todo": "open",
    "done": "resolved",
    "closed": "resolved",
    "complete": "resolved",
    "completed": "resolved",
}

STATE_SIGNALS = {
    "deployed": ["已部署", "已上线", "上线了", "落盘", "deployed"],
    "implemented": ["已实现", "实现了", "代码已完成", "implemented"],
    "resolved": ["已完成", "已验证", "解决了", "done", "resolved", "closed"],
    "cancelled": ["取消", "废弃", "不做了", "cancelled"],
    "blocked": ["阻塞", "卡住", "blocked"],
    "in_progress": ["进行中", "正在做", "in progress"],
    "open": ["待办", "未完成", "待实现", "todo", "pending", "open"],
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def get_nodes(graph: dict[str, Any]) -> list[dict[str, Any]]:
    raw = graph.get("nodes")
    if raw is None and isinstance(graph.get("graph"), dict):
        raw = graph["graph"].get("nodes")

    if raw is None:
        return []

    if isinstance(raw, dict):
        nodes = list(raw.values())
    elif isinstance(raw, list):
        nodes = raw
    else:
        nodes = []

    return [n for n in nodes if isinstance(n, dict)]


def get_edges(graph: dict[str, Any]) -> list[dict[str, Any]]:
    raw = graph.get("edges")
    if raw is None and isinstance(graph.get("graph"), dict):
        raw = graph["graph"].get("edges")

    if raw is None:
        return []

    if isinstance(raw, dict):
        edges = list(raw.values())
    elif isinstance(raw, list):
        edges = raw
    else:
        edges = []

    return [e for e in edges if isinstance(e, dict)]


def parse_turn_id(path: Path) -> int | None:
    for pattern in [r"turn[_-]?(\d+)", r"slice[_-]?(\d+)"]:
        m = re.search(pattern, path.stem, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None


def node_num(node_id: str | None) -> int:
    if not node_id:
        return -1
    m = NODE_ID_RE.search(str(node_id))
    return int(m.group(1)) if m else -1


def next_node_id_from_full_graph(nodes: list[dict[str, Any]]) -> str:
    max_num = 0
    max_width = 4

    for n in nodes:
        nid = str(n.get("node_id", ""))
        m = NODE_ID_RE.search(nid)
        if not m:
            continue
        num = int(m.group(1))
        max_num = max(max_num, num)
        max_width = max(max_width, len(m.group(1)))

    return f"n_{max_num + 1:0{max_width}d}"


def normalize_state(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip().lower()
    if not s or s == "null":
        return None
    return STATE_NORMALIZE.get(s, s)


def is_active(node: dict[str, Any]) -> bool:
    return str(node.get("status", "active")).lower() == "active"


def infer_state_signals(text: str) -> set[str]:
    lower = text.lower()
    result: set[str] = set()

    for state, words in STATE_SIGNALS.items():
        for w in words:
            if w.lower() in lower:
                result.add(state)
                break

    return result


def canon(s: Any) -> str:
    return str(s or "").strip().lower()


def is_structured_symbol(s: str) -> bool:
    s = s.strip()
    if len(s) < 2 or len(s) > 120:
        return False

    if NODE_ID_RE.search(s):
        return True
    if TICKET_RE.search(s):
        return True
    if "/" in s:
        return True
    if re.search(r"\.(py|json|md|txt|ya?ml|js|ts|tsx|jsx|html|css|csv|sql|sh)$", s):
        return True
    if re.search(r"[_-]", s):
        return True

    # 允许短的代码符号或模块名，比如 TaskGraph、Extractor
    if " " not in s and re.search(r"[A-Za-z]", s):
        return True

    return False


def extract_symbols(text: str) -> set[str]:
    symbols: set[str] = set()

    for regex in [NODE_ID_RE, TICKET_RE, FILE_RE, API_ROUTE_RE]:
        for m in regex.finditer(text):
            symbols.add(m.group(0))

    for m in PATH_RE.finditer(text):
        symbols.add(m.group(1))

    for m in CODE_SPAN_RE.finditer(text):
        raw = m.group(1).strip()
        if is_structured_symbol(raw):
            symbols.add(raw)

    return {s.strip() for s in symbols if s.strip()}


def extract_explicit_node_ids(text: str) -> set[str]:
    return {m.group(0) for m in NODE_ID_RE.finditer(text)}


def lexical_overlap_score(content: str, symbols: set[str]) -> int:
    c = canon(content)
    score = 0
    for s in symbols:
        ss = canon(s)
        if ss and ss in c:
            score += 20
    return score


def score_node(
    node: dict[str, Any],
    turn_text: str,
    symbols: set[str],
    explicit_node_ids: set[str],
    turn_states: set[str],
) -> int:
    score = 0
    node_id = str(node.get("node_id", ""))
    content = str(node.get("content", ""))
    entity_ref = str(node.get("entity_ref") or "")
    state = normalize_state(node.get("state"))

    lower_turn = turn_text.lower()

    if node_id in explicit_node_ids:
        score += 1000

    if entity_ref:
        entity_lower = entity_ref.lower()
        if entity_lower in lower_turn or entity_ref in symbols:
            score += 500

    score += lexical_overlap_score(content, symbols)

    if entity_ref:
        score += lexical_overlap_score(entity_ref, symbols)

    if turn_states & TERMINAL_STATES and state in OPENISH_STATES:
        if score > 0:
            score += 80

    if "阻塞" in content and ("已实现" in turn_text or "已完成" in turn_text or "已部署" in turn_text):
        if score > 0:
            score += 60

    return score


def compact_node(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "node_id": node.get("node_id"),
        "type": node.get("type"),
        "content": node.get("content"),
        "entity_ref": node.get("entity_ref"),
        "state": node.get("state"),
        "status": node.get("status", "active"),
    }


def compact_edge(edge: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": edge.get("source") or edge.get("from"),
        "target": edge.get("target") or edge.get("to"),
        "relation": edge.get("relation"),
    }


def dedupe_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []

    for n in nodes:
        nid = str(n.get("node_id", ""))
        if not nid or nid in seen:
            continue
        seen.add(nid)
        result.append(n)

    return result


def sort_recent(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(n: dict[str, Any]) -> tuple[int, int]:
        turn = n.get("updated_turn") or n.get("created_turn") or n.get("turn_id") or -1
        try:
            turn_int = int(turn)
        except Exception:
            turn_int = -1
        return (turn_int, node_num(str(n.get("node_id", ""))))

    return sorted(nodes, key=key, reverse=True)


def build_slice(
    graph: dict[str, Any],
    turn_text: str,
    turn_id: int,
    task_id: str,
    source_graph: str,
    source_turn: str,
    limits: dict[str, int],
) -> dict[str, Any]:
    nodes = get_nodes(graph)
    edges = get_edges(graph)

    active_nodes = [n for n in nodes if is_active(n)]

    symbols = extract_symbols(turn_text)
    explicit_node_ids = extract_explicit_node_ids(turn_text)
    turn_states = infer_state_signals(turn_text)

    scores = {
        str(n.get("node_id")): score_node(n, turn_text, symbols, explicit_node_ids, turn_states)
        for n in active_nodes
    }

    root_goals = [
        n for n in active_nodes
        if n.get("type") == "UserGoal"
    ]
    root_goals = sort_recent(root_goals)[: limits["root_goals"]]

    standing_constraints = [
        n for n in active_nodes
        if n.get("type") == "Constraint"
    ]
    standing_constraints = sort_recent(standing_constraints)[: limits["standing_constraints"]]

    active_open_tasks = [
        n for n in active_nodes
        if n.get("type") == "OpenTask"
        and normalize_state(n.get("state")) in OPENISH_STATES
    ]
    active_open_tasks = sorted(
        active_open_tasks,
        key=lambda n: (scores.get(str(n.get("node_id")), 0), node_num(str(n.get("node_id")))),
        reverse=True,
    )[: limits["active_open_tasks"]]

    recent_nodes = sort_recent(active_nodes)[: limits["recent_nodes"]]

    symbol_hits = [
        n for n in active_nodes
        if scores.get(str(n.get("node_id")), 0) >= 20
    ]
    symbol_hits = sorted(
        symbol_hits,
        key=lambda n: (scores.get(str(n.get("node_id")), 0), node_num(str(n.get("node_id")))),
        reverse=True,
    )[: limits["symbol_hits"]]

    conflict_candidates: list[dict[str, Any]] = []
    for n in active_nodes:
        nid = str(n.get("node_id", ""))
        state = normalize_state(n.get("state"))
        score = scores.get(nid, 0)

        same_explicit_id = nid in explicit_node_ids
        same_entity = bool(n.get("entity_ref")) and canon(n.get("entity_ref")) in {
            canon(s) for s in symbols
        }
        possible_state_conflict = bool(turn_states & TERMINAL_STATES) and state in OPENISH_STATES and score > 0

        if same_explicit_id or same_entity or possible_state_conflict:
            conflict_candidates.append(n)

    conflict_candidates = sorted(
        dedupe_nodes(conflict_candidates),
        key=lambda n: (scores.get(str(n.get("node_id")), 0), node_num(str(n.get("node_id")))),
        reverse=True,
    )[: limits["conflict_candidates"]]

    selected_ids: set[str] = set()
    all_selected_nodes: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for group in [
        root_goals,
        standing_constraints,
        active_open_tasks,
        recent_nodes,
        symbol_hits,
        conflict_candidates,
    ]:
        for n in group:
            nid = str(n.get("node_id", ""))
            if nid:
                selected_ids.add(nid)
                if nid not in seen_ids:
                    seen_ids.add(nid)
                    all_selected_nodes.append(compact_node(n))

    recent_edges: list[dict[str, Any]] = []
    for e in edges:
        ce = compact_edge(e)
        src = str(ce.get("source") or "")
        tgt = str(ce.get("target") or "")
        if src in selected_ids and tgt in selected_ids:
            recent_edges.append(ce)

    recent_edges = recent_edges[: limits["recent_edges"]]

    def _ids(group_nodes: list[dict[str, Any]]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for n in group_nodes:
            nid = str(n.get("node_id", ""))
            if nid and nid not in seen:
                seen.add(nid)
                out.append(nid)
        return out

    return {
        "task_id": task_id,
        "turn_id": turn_id,
        "nodes": all_selected_nodes,
        "group_node_ids": {
            "root_goals": _ids(root_goals),
            "standing_constraints": _ids(standing_constraints),
            "active_open_tasks": _ids(active_open_tasks),
            "recent_nodes": _ids(recent_nodes),
            "symbol_hits": _ids(symbol_hits),
            "conflict_candidates": _ids(conflict_candidates),
        },
        "recent_edges": recent_edges,
        "retrieval_trace": {
            "explicit_node_ids": sorted(explicit_node_ids),
            "mentioned_symbols": sorted(symbols),
            "turn_state_signals": sorted(turn_states),
            "total_nodes": len(nodes),
            "active_nodes": len(active_nodes),
            "selected_node_ids": sorted(selected_ids),
        },
        "_runtime": {
            "next_node_id": next_node_id_from_full_graph(nodes),
            "source_graph": source_graph,
            "source_turn": source_turn,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", default="graph_state.json")
    parser.add_argument("--turn", required=True)
    parser.add_argument("--out")
    parser.add_argument("--task-id")
    parser.add_argument("--turn-id", type=int)

    parser.add_argument("--root-goals", type=int, default=5)
    parser.add_argument("--standing-constraints", type=int, default=8)
    parser.add_argument("--active-open-tasks", type=int, default=12)
    parser.add_argument("--recent-nodes", type=int, default=16)
    parser.add_argument("--symbol-hits", type=int, default=16)
    parser.add_argument("--conflict-candidates", type=int, default=16)
    parser.add_argument("--recent-edges", type=int, default=30)

    args = parser.parse_args()

    graph_path = Path(args.graph)
    turn_path = Path(args.turn)

    graph = load_json(graph_path)
    turn_text = turn_path.read_text(encoding="utf-8")

    turn_id = args.turn_id if args.turn_id is not None else parse_turn_id(turn_path)
    if turn_id is None:
        print("ERROR: cannot infer turn_id. Use --turn-id.", file=sys.stderr)
        sys.exit(1)

    task_id = args.task_id or graph.get("task_id") or "task_default"

    if args.out:
        out_path = Path(args.out)
    else:
        out_path = Path("graph_slices") / f"slice_{turn_id:03d}.json"

    limits = {
        "root_goals": args.root_goals,
        "standing_constraints": args.standing_constraints,
        "active_open_tasks": args.active_open_tasks,
        "recent_nodes": args.recent_nodes,
        "symbol_hits": args.symbol_hits,
        "conflict_candidates": args.conflict_candidates,
        "recent_edges": args.recent_edges,
    }

    slice_json = build_slice(
        graph=graph,
        turn_text=turn_text,
        turn_id=turn_id,
        task_id=task_id,
        source_graph=str(graph_path),
        source_turn=str(turn_path),
        limits=limits,
    )

    save_json(out_path, slice_json)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()