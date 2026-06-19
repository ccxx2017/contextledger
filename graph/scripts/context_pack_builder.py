import json
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# =========================
# 数据结构
# =========================

@dataclass
class Node:
    node_id: str
    type: str
    content: str
    created_at_turn: int
    status: str = "active"


@dataclass
class Edge:
    source: str
    target: str
    relation: str


@dataclass
class TaskGraph:
    task_id: str
    turn_counter: int = 0
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)


# =========================
# 从 graph_state.json 读取 TaskGraph
# =========================

def load_task_graph_from_json(path: str) -> TaskGraph:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    graph = TaskGraph(
        task_id=raw["task_id"],
        turn_counter=raw.get("turn_counter", 0),
    )

    graph.nodes = {
        node_id: Node(
            node_id=node_data["node_id"],
            type=node_data["type"],
            content=node_data["content"],
            created_at_turn=node_data["created_at_turn"],
            status=node_data.get("status", "active"),
        )
        for node_id, node_data in raw.get("nodes", {}).items()
    }

    graph.edges = [
        Edge(
            source=edge["source"],
            target=edge["target"],
            relation=edge["relation"],
        )
        for edge in raw.get("edges", [])
    ]

    return graph


# =========================
# 基础查询函数
# =========================

def latest_active_open_task(graph: TaskGraph) -> Optional[Node]:
    candidates = [
        node for node in graph.nodes.values()
        if node.type == "OpenTask" and node.status == "active"
    ]

    if not candidates:
        return None

    return sorted(
        candidates,
        key=lambda n: (n.created_at_turn, n.node_id)
    )[-1]


def outgoing_edges(
    graph: TaskGraph,
    node_id: str,
    allowed_relations: Optional[Set[str]] = None
) -> List[Edge]:
    result = []

    for edge in graph.edges:
        if edge.source != node_id:
            continue

        if allowed_relations is not None and edge.relation not in allowed_relations:
            continue

        result.append(edge)

    return result


def incoming_edges(
    graph: TaskGraph,
    node_id: str,
    allowed_relations: Optional[Set[str]] = None
) -> List[Edge]:
    result = []

    for edge in graph.edges:
        if edge.target != node_id:
            continue

        if allowed_relations is not None and edge.relation not in allowed_relations:
            continue

        result.append(edge)

    return result


# =========================
# 读取相关子图
# =========================

def trace_upstream(graph: TaskGraph, start_id: str) -> Set[str]:
    """
    从当前焦点出发，沿着 source -> target 方向追踪上游依据。

    例如：
    OpenTask --depends_on--> UserGoal
    Decision --implements--> UserGoal
    Constraint --refines--> UserGoal
    """

    allowed_relations = {
        "depends_on",
        "implements",
        "serves",
        "refines",
        "supports",
        "derived_from",
        "produces",
    }

    visited = set()
    stack = [start_id]

    while stack:
        current = stack.pop()

        if current in visited:
            continue

        visited.add(current)

        for edge in outgoing_edges(graph, current, allowed_relations):
            if edge.target in graph.nodes and edge.target not in visited:
                stack.append(edge.target)

    return visited


def expand_by_goal_neighborhood(graph: TaskGraph, seed_ids: Set[str]) -> Set[str]:
    """
    第4讲生成的真实图里，很多节点是直接挂到 UserGoal 上的。

    例如：
    Decision --implements--> UserGoal
    Constraint --depends_on--> UserGoal
    Fact --serves--> UserGoal
    OpenTask --depends_on--> UserGoal

    如果只从 current_focus 往上游追踪，可能只能得到：
    current_focus -> UserGoal -> 顶层 UserGoal

    这样会漏掉同一个 UserGoal 下的关键事实、约束、决策。
    所以这里补一层：围绕相关 UserGoal 读取邻居节点。
    """

    allowed_relations = {
        "depends_on",
        "implements",
        "serves",
        "refines",
        "supports",
        "derived_from",
        "produces",
    }

    result = set(seed_ids)

    goal_ids = {
        node_id
        for node_id in seed_ids
        if graph.nodes.get(node_id) and graph.nodes[node_id].type == "UserGoal"
    }

    for goal_id in goal_ids:
        for edge in incoming_edges(graph, goal_id, allowed_relations):
            if edge.source in graph.nodes:
                result.add(edge.source)

    # 如果某些已选节点产出了文件，也把文件带上
    for node_id in list(result):
        for edge in outgoing_edges(graph, node_id, {"produces"}):
            if edge.target in graph.nodes:
                result.add(edge.target)

    return result


def expand_incoming_neighbors(
    graph: TaskGraph,
    seed_ids: Set[str],
    max_rounds: int = 2,
) -> Set[str]:
    """
    从已选节点出发，反向吸收指向它们的相关节点。

    目的：
    1. 当前焦点沿 depends_on/implements 等关系追到上游后，
       还要把“补充说明、细化、修正、支撑”这些节点拉进来。

    2. 例如：
       n_0048 --refines--> n_0047
       n_0047 --derived_from--> n_0039
       n_0039 --depends_on--> n_0034

       如果 n_0039 或 n_0047 已经相关，那么 n_0048 也应该被纳入。

    3. max_rounds=2 是为了避免无限扩展整个图。
       第一轮拿直接相关节点；
       第二轮拿这些节点的 refinement/support/detail。
    """

    allowed_relations = {
        "depends_on",
        "implements",
        "serves",
        "refines",
        "supports",
        "derived_from",
        "produces",
    }

    result = set(seed_ids)
    frontier = set(seed_ids)

    for _ in range(max_rounds):
        next_frontier = set()

        for node_id in frontier:
            for edge in incoming_edges(graph, node_id, allowed_relations):
                if edge.source in graph.nodes and edge.source not in result:
                    result.add(edge.source)
                    next_frontier.add(edge.source)

        if not next_frontier:
            break

        frontier = next_frontier

    return result


def collect_relevant_node_ids(graph: TaskGraph, current_focus_id: str) -> Set[str]:
    # 1. 先从当前焦点沿 outgoing edge 追到上游依据
    upstream_ids = trace_upstream(graph, current_focus_id)

    # 2. 围绕 UserGoal 拉入直接相关的大背景
    goal_neighborhood_ids = expand_by_goal_neighborhood(graph, upstream_ids)

    # 3. 再围绕所有已选节点，拉入 refinement/support/detail 节点
    relevant_ids = expand_incoming_neighbors(
        graph,
        goal_neighborhood_ids,
        max_rounds=2,
    )

    return relevant_ids


# =========================
# superseded 历史收集
# =========================

def collect_superseded_history(graph: TaskGraph) -> List[Dict]:
    history = []
    already_added = set()

    # 1. 优先根据 invalidates 边收集原因
    for edge in graph.edges:
        if edge.relation != "invalidates":
            continue

        source = graph.nodes.get(edge.source)
        target = graph.nodes.get(edge.target)

        if not source or not target:
            continue

        history.append({
            "item": target.content,
            "reason": source.content,
        })

        already_added.add(target.node_id)

    # 2. 如果某些节点 status=superseded，但没有 invalidates 边，也要收集
    for node in graph.nodes.values():
        if node.status == "superseded" and node.node_id not in already_added:
            history.append({
                "item": node.content,
                "reason": "图中未记录明确 invalidates 原因，只知道该节点 status=superseded。",
            })

    return history


# =========================
# 构建 Context Pack
# =========================

def build_context_pack(
    graph: TaskGraph,
    current_focus_id: Optional[str] = None
) -> Dict:
    if current_focus_id is None:
        focus = latest_active_open_task(graph)

        if focus is None:
            raise ValueError(
                "没有找到 active OpenTask，请手动指定 current_focus_id"
            )

        current_focus_id = focus.node_id
    else:
        if current_focus_id not in graph.nodes:
            raise ValueError(f"current_focus_id 不存在：{current_focus_id}")

        focus = graph.nodes[current_focus_id]

    relevant_ids = collect_relevant_node_ids(graph, current_focus_id)

    pack = {
        "task_id": graph.task_id,
        "turn_counter": graph.turn_counter,
        "current_focus_id": current_focus_id,
        "current_focus": focus.content,
        "goals": [],
        "active_constraints": [],
        "current_decisions": [],
        "relevant_facts": [],
        "open_tasks": [],
        "file_artifacts": [],
        "superseded_history": [],
    }

    relevant_nodes = [
        graph.nodes[node_id]
        for node_id in relevant_ids
        if node_id in graph.nodes
    ]

    relevant_nodes = sorted(
        relevant_nodes,
        key=lambda n: (n.created_at_turn, n.node_id)
    )

    for node in relevant_nodes:
        if node.status != "active":
            continue

        if node.type == "UserGoal":
            pack["goals"].append(node.content)

        elif node.type == "Constraint":
            pack["active_constraints"].append(node.content)

        elif node.type == "Decision":
            pack["current_decisions"].append(node.content)

        elif node.type == "Fact":
            pack["relevant_facts"].append(node.content)

        elif node.type == "OpenTask":
            pack["open_tasks"].append(node.content)

        elif node.type == "FileArtifact":
            pack["file_artifacts"].append(node.content)

    pack["superseded_history"] = collect_superseded_history(graph)

    return pack


# =========================
# 转成 Prompt
# =========================

def context_pack_to_prompt(pack: Dict) -> str:
    lines = []

    lines.append("以下是当前任务的结构化上下文，请基于它继续执行任务。")
    lines.append("")
    lines.append(f"任务 ID：{pack['task_id']}")
    lines.append(f"当前轮次：{pack['turn_counter']}")
    lines.append(f"当前焦点节点：{pack['current_focus_id']}")
    lines.append(f"当前焦点：{pack['current_focus']}")
    lines.append("")

    def add_list_section(title: str, items: List[str]):
        lines.append(f"## {title}")
        if not items:
            lines.append("- 无")
        else:
            for item in items:
                lines.append(f"- {item}")
        lines.append("")

    add_list_section("任务目标", pack["goals"])
    add_list_section("有效约束", pack["active_constraints"])
    add_list_section("当前有效决策", pack["current_decisions"])
    add_list_section("相关事实", pack["relevant_facts"])
    add_list_section("待办事项", pack["open_tasks"])
    add_list_section("相关文件", pack["file_artifacts"])

    lines.append("## 已推翻或废弃内容")
    if not pack["superseded_history"]:
        lines.append("- 无")
    else:
        for item in pack["superseded_history"]:
            lines.append(f"- 已推翻：{item['item']}")
            lines.append(f"  - 原因：{item['reason']}")
    lines.append("")

    lines.append("请注意：")
    lines.append("- 不要继续采用已推翻或 superseded 的方案。")
    lines.append("- 必须遵守有效约束。")
    lines.append("- 优先围绕当前焦点继续推进。")

    return "\n".join(lines)

def write_context_outputs(
    pack: dict,
    output_dir: str = ".",
    pack_filename: str = "context_pack.json",
    prompt_filename: str = "context_prompt.md",
) -> dict:
    """
    写出 Context Pack 的两个产物：

    1. context_pack.json
       - 机器可读
       - 后续程序自动化使用

    2. context_prompt.md
       - 人类可读
       - 当前阶段可直接复制粘贴给 LLM
       - 后续也可以被程序读取后提交给 LLM
    """

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    pack_path = output_path / pack_filename
    prompt_path = output_path / prompt_filename

    pack_path.write_text(
        json.dumps(pack, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    prompt_text = context_pack_to_prompt(pack)

    prompt_path.write_text(
        prompt_text,
        encoding="utf-8",
    )

    return {
        "pack_path": str(pack_path),
        "prompt_path": str(prompt_path),
    }

# =========================
# 命令行入口
# =========================

if __name__ == "__main__":
    # 1. 读取 graph_state.json 路径
    # 默认读取项目根目录下的 graph_state.json
    if len(sys.argv) < 2:
        graph_path = PROJECT_ROOT / "graph_state.json"
    else:
        graph_path = Path(sys.argv[1])

    # 2. 读取可选的当前焦点节点 ID
    # 如果不传，则由 build_context_pack 自动选择最新的 active OpenTask
    if len(sys.argv) >= 3:
        focus_id = sys.argv[2]
    else:
        focus_id = None

    # 3. 从第4讲产出的 graph_state.json 恢复 TaskGraph
    graph = load_task_graph_from_json(graph_path)

    # 4. 基于 TaskGraph 构建当前轮次需要提交给 LLM 的上下文包
    pack = build_context_pack(
        graph,
        current_focus_id=focus_id,
    )

    # 5. 将上下文包转换成最终要提交给 LLM 的 Prompt 文本
    prompt_text = context_pack_to_prompt(pack)

    # 6. 写入正式的 LLM 输入文件
    # 当前手动阶段：人打开这个文件复制给 LLM
    # 后续自动化阶段：程序读取同一个文件提交给 LLM API
    output_path = PROJECT_ROOT / "prompts" / "context_prompt.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(prompt_text, encoding="utf-8")

    # 7. 控制台只做提示，不再承载主要内容
    print("====== Context Pack Builder Done ======")
    print(f"读取任务图文件：{graph_path}")
    print(f"提交给 LLM 的上下文已写入：{output_path}")
    print("")

    if focus_id is None:
        print("当前焦点节点：自动选择最新的 active OpenTask")
    else:
        print(f"当前焦点节点：{focus_id}")

    print("")
    print("下一步：")
    print(f"1. 手动阶段：打开 {output_path}，复制全文提交给 LLM")
    print(f"2. 自动化阶段：程序读取同一个 {output_path}，并提交给 LLM API")