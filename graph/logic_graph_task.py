"""
logic_graph_task.py

注意：
本文件不负责把自然语言转换成 Graph Patch。
自然语言到 Patch 的转换由 Graph Extractor Prompt + LLM 完成。

本文件只做四件事：
1. 接收用户手动提供的一个 Graph Patch
2. 读取已有 TaskGraph 状态；如果没有，则创建新的 TaskGraph
3. 将当前 Patch 合并进 TaskGraph
4. 保存更新后的 TaskGraph，并可选输出 Mermaid 图

重要原则：
- 每次运行只 apply 一个 patch
- Patch 是增量，不是完整图
- TaskGraph 才是完整状态
- 每轮 apply_patch() 后必须保存 TaskGraph
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional


# ---------------- 数据结构 ----------------

@dataclass
class Node:
    node_id: str
    type: str
    content: str
    created_at_turn: int
    status: str = "active"   # active / superseded / resolved


@dataclass
class Edge:
    source: str
    target: str
    relation: str


@dataclass
class TaskGraph:
    task_id: str
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    turn_counter: int = 0

    def next_node_id(self) -> str:
        i = len(self.nodes) + 1
        while True:
            candidate = f"n_{i:04d}"
            if candidate not in self.nodes:
                return candidate
            i += 1

    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "turn_counter": self.turn_counter,
            "nodes": {
                nid: asdict(node)
                for nid, node in self.nodes.items()
            },
            "edges": [
                asdict(edge)
                for edge in self.edges
            ],
        }

    @staticmethod
    def from_dict(data: Dict) -> "TaskGraph":
        nodes = {
            nid: Node(**node_data)
            for nid, node_data in data.get("nodes", {}).items()
        }
        edges = [
            Edge(**edge_data)
            for edge_data in data.get("edges", [])
        ]

        return TaskGraph(
            task_id=data["task_id"],
            nodes=nodes,
            edges=edges,
            turn_counter=data.get("turn_counter", 0),
        )


# ---------------- 去重 ----------------

class Deduplicator:
    """简单基于 type + content 归一化的去重"""

    @staticmethod
    def find_existing(
        graph: TaskGraph,
        node_type: str,
        content: str,
    ) -> Optional[str]:
        key = (node_type, content.strip().lower())

        for nid, node in graph.nodes.items():
            current_key = (node.type, node.content.strip().lower())
            if current_key == key and node.status == "active":
                return nid

        return None


# ---------------- Patch 合并器 ----------------

class GraphUpdater:
    """把一个 Patch 合并进当前 TaskGraph"""

    @staticmethod
    def apply_patch(
        graph: TaskGraph,
        patch: Dict,
        strict_turn: bool = True,
        strict_refs: bool = True,
    ) -> None:
        turn = int(patch["turn_id"])

        if strict_turn and turn != graph.turn_counter + 1:
            raise ValueError(
                f"turn_id 不连续：当前 TaskGraph turn_counter={graph.turn_counter}，"
                f"但输入 patch turn_id={turn}。"
                f"正确流程应该是每轮只 apply 下一个 patch。"
            )

        # 1. 处理 superseded_nodes
        for item in patch.get("superseded_nodes", []):
            nid = item["node_id"]

            if nid not in graph.nodes:
                if strict_refs:
                    raise ValueError(
                        f"superseded_nodes 引用了不存在的节点：{nid}"
                    )
                continue

            graph.nodes[nid].status = "superseded"

        # 2. 处理 new_nodes，并建立 id_remap
        id_remap = {}

        for n in patch.get("new_nodes", []):
            original_id = n["node_id"]

            existing = Deduplicator.find_existing(
                graph,
                n["type"],
                n["content"],
            )

            if existing:
                id_remap[original_id] = existing
                continue

            new_id = (
                original_id
                if original_id not in graph.nodes
                else graph.next_node_id()
            )

            id_remap[original_id] = new_id

            graph.nodes[new_id] = Node(
                node_id=new_id,
                type=n["type"],
                content=n["content"],
                created_at_turn=turn,
                status=n.get("status", "active"),
            )

        # 3. 处理 updated_nodes
        for u in patch.get("updated_nodes", []):
            original_id = u["node_id"]
            nid = id_remap.get(original_id, original_id)

            if nid not in graph.nodes:
                if strict_refs:
                    raise ValueError(
                        f"updated_nodes 引用了不存在的节点：{nid}"
                    )
                continue

            # 支持新版 schema：{"changes": {...}}
            changes = u.get("changes", {})

            # 兼容旧版 schema：{"content": "..."}
            if "content" in u and "content" not in changes:
                changes["content"] = u["content"]

            if "content" in changes:
                graph.nodes[nid].content = changes["content"]

            if "status" in changes:
                graph.nodes[nid].status = changes["status"]

        # 4. 处理 new_edges
        for e in patch.get("new_edges", []):
            src = id_remap.get(e["source"], e["source"])
            tgt = id_remap.get(e["target"], e["target"])
            relation = e["relation"]

            if strict_refs:
                missing = [
                    nid for nid in [src, tgt]
                    if nid not in graph.nodes
                ]

                if missing:
                    raise ValueError(
                        f"new_edges 引用了不存在的节点：{missing}。"
                        f"这通常说明你没有先 apply 前一轮 patch，"
                        f"或者当前 patch 不是基于最新 TaskGraph 生成的。"
                    )

            already_exists = any(
                edge.source == src
                and edge.target == tgt
                and edge.relation == relation
                for edge in graph.edges
            )

            if not already_exists:
                graph.edges.append(
                    Edge(
                        source=src,
                        target=tgt,
                        relation=relation,
                    )
                )

        graph.turn_counter = turn


# ---------------- Mermaid 输出，仅用于教学观察 ----------------

def _shorten(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + "…"


def _escape_mermaid_label(text: str) -> str:
    return text.replace('"', '\\"')


def to_mermaid(graph: TaskGraph, max_label_len: int = 40) -> str:
    lines = ["graph TD"]

    for nid, node in graph.nodes.items():
        node_type = _escape_mermaid_label(node.type)
        content = _escape_mermaid_label(
            _shorten(node.content, max_label_len)
        )

        label = f"{node_type}<br/>{content}"

        if node.status == "superseded":
            lines.append(f'    {nid}["❌ {label}"]:::dead')
        else:
            lines.append(f'    {nid}["{label}"]')

    for e in graph.edges:
        lines.append(f'    {e.source} -->|{e.relation}| {e.target}')

    lines.append("    classDef dead fill:#fdd,stroke:#c33;")

    return "\n".join(lines)


# ---------------- 文件读写 ----------------

def read_json_file(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json_file(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
        )


def load_patch_from_stdin() -> Dict:
    if sys.stdin.isatty():
        print(
            "请粘贴 Graph Patch JSON，结束后按 Ctrl-D；"
            "Windows 下通常是 Ctrl-Z 后回车。",
            file=sys.stderr,
        )

    text = sys.stdin.read().strip()

    if not text:
        raise ValueError("没有从 stdin 读取到 patch JSON。")

    return json.loads(text)


def validate_patch(patch: Dict) -> None:
    if not isinstance(patch, dict):
        raise ValueError("Patch 必须是 JSON object。")

    if "turn_id" not in patch:
        raise ValueError("Patch 缺少 turn_id。")

    for key in [
        "new_nodes",
        "updated_nodes",
        "superseded_nodes",
        "new_edges",
    ]:
        if key in patch and not isinstance(patch[key], list):
            raise ValueError(f"Patch 字段 {key} 必须是 list。")


def load_or_create_graph(
    state_path: Path,
    patch: Dict,
    task_id: Optional[str],
    reset: bool,
) -> TaskGraph:
    if state_path.exists() and not reset:
        data = read_json_file(state_path)
        return TaskGraph.from_dict(data)

    actual_task_id = task_id or patch.get("task_id") or "task_001"

    return TaskGraph(task_id=actual_task_id)


# ---------------- 命令行入口 ----------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "每次接收一个 Graph Patch，合并进 TaskGraph，"
            "并保存更新后的 TaskGraph。"
        )
    )

    patch_source = parser.add_mutually_exclusive_group(required=True)

    patch_source.add_argument(
        "--patch",
        type=Path,
        help="当前轮 Graph Patch 的 JSON 文件路径。",
    )

    patch_source.add_argument(
        "--stdin",
        action="store_true",
        help="从标准输入读取当前轮 Graph Patch JSON。",
    )

    parser.add_argument(
        "--state",
        type=Path,
        default=Path("graph_state.json"),
        help="TaskGraph 状态文件路径。默认：graph_state.json",
    )

    parser.add_argument(
        "--task-id",
        type=str,
        default=None,
        help="首次创建 TaskGraph 时使用的 task_id。",
    )

    parser.add_argument(
        "--mermaid",
        type=Path,
        default=None,
        help="可选：输出 Mermaid 文件路径，仅用于教学观察。",
    )

    parser.add_argument(
        "--print-mermaid",
        action="store_true",
        help="可选：在终端打印 Mermaid 内容。",
    )

    parser.add_argument(
        "--max-label-len",
        type=int,
        default=40,
        help="Mermaid 节点内容最大显示长度。默认：40",
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="忽略已有 state 文件，重新创建 TaskGraph。只建议第1轮或重新开始时使用。",
    )

    parser.add_argument(
        "--allow-task-id-mismatch",
        action="store_true",
        help="允许 patch.task_id 与 TaskGraph.task_id 不一致。不建议默认使用。",
    )

    parser.add_argument(
        "--allow-nonsequential-turn",
        action="store_true",
        help="允许 turn_id 不连续。不建议默认使用。",
    )

    args = parser.parse_args()

    # 1. 读取用户手动提供的 patch
    if args.patch:
        patch = read_json_file(args.patch)
    else:
        patch = load_patch_from_stdin()

    validate_patch(patch)

    # 2. 读取或创建 TaskGraph
    graph = load_or_create_graph(
        state_path=args.state,
        patch=patch,
        task_id=args.task_id,
        reset=args.reset,
    )

    # 3. 校验 task_id
    patch_task_id = patch.get("task_id")

    if (
        patch_task_id
        and patch_task_id != graph.task_id
        and not args.allow_task_id_mismatch
    ):
        raise ValueError(
            f"patch.task_id={patch_task_id} 与 "
            f"TaskGraph.task_id={graph.task_id} 不一致。"
        )

    before_nodes = len(graph.nodes)
    before_edges = len(graph.edges)
    before_turn = graph.turn_counter

    # 4. 合并当前 patch
    GraphUpdater.apply_patch(
        graph,
        patch,
        strict_turn=not args.allow_nonsequential_turn,
        strict_refs=True,
    )

    # 5. 保存完整 TaskGraph
    write_json_file(args.state, graph.to_dict())

    # 6. 可选输出 Mermaid
    mermaid_text = to_mermaid(
        graph,
        max_label_len=args.max_label_len,
    )

    if args.mermaid:
        args.mermaid.parent.mkdir(parents=True, exist_ok=True)
        args.mermaid.write_text(
            mermaid_text,
            encoding="utf-8",
        )

    if args.print_mermaid:
        print("\n====== Mermaid ======")
        print(mermaid_text)

    # 7. 打印摘要
    print("\n====== Apply Patch Done ======")
    print(f"TaskGraph: {graph.task_id}")
    print(f"Turn: {before_turn} -> {graph.turn_counter}")
    print(f"Nodes: {before_nodes} -> {len(graph.nodes)}")
    print(f"Edges: {before_edges} -> {len(graph.edges)}")
    print(f"State saved to: {args.state}")

    if args.mermaid:
        print(f"Mermaid saved to: {args.mermaid}")


if __name__ == "__main__":
    main()