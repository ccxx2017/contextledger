#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""影子命名空间 CL 状态构建器（工作包 D2/D4 的 CL 侧配套）。

读取场景定义中的 cl_event_stream（预注册真值事件流），用主链裁定器
（lifecycle_adjudicator，纯机械、无 LLM 调用）重放，把最终图写入
影子命名空间项目（graph/projects/<shadow_project>/graph_state.json）。

单写者边界：本脚本拒绝写主项目名；影子项目与主项目物理隔离。

用法：
    python graph/scripts/build_shadow_state.py \
        --scenario <contextledger-host>/scenarios/reassignment_recovery.json \
        --shadow-project abu_modern_host_shadow
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "graph" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from lifecycle_adjudicator import adjudicate_event, decision_to_patch  # noqa: E402
import apply_patch as apply_mod  # noqa: E402

FORBIDDEN_PROJECTS = {"abu_modern"}


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--shadow-project", default="abu_modern_host_shadow")
    args = parser.parse_args()

    if args.shadow_project in FORBIDDEN_PROJECTS or not args.shadow_project.endswith("_host_shadow"):
        print(
            f"REFUSED: 影子项目名必须是 *_host_shadow 且不得为主项目（得到 {args.shadow_project!r}）",
            file=sys.stderr,
        )
        return 2

    scenario = load_json(Path(args.scenario))
    events = scenario.get("cl_event_stream") or []
    if not events:
        print("场景缺少 cl_event_stream（预注册真值事件流）", file=sys.stderr)
        return 2

    graph: dict[str, Any] = {"turn_counter": 0, "nodes": {}, "edges": []}
    actions: dict[str, str] = {}
    timeline: list[dict[str, Any]] = []
    counter = 0
    for event in events:
        counter += 1
        decision = adjudicate_event(event, graph)
        actions[str(event.get("event_id"))] = decision.action
        patch = decision_to_patch(decision, event, node_id=f"sh_{counter:04d}")
        graph = apply_mod.apply_patch(graph, patch)
        # 状态时间线：每个事件后的当前态快照（供影子对比按 turn 时点取态）
        current_states = {}
        for node in graph["nodes"].values():
            if node.get("status") == "active" and node.get("entity_ref"):
                current_states[str(node["entity_ref"])] = node.get("state")
        timeline.append({
            "as_of": event.get("observed_at"),
            "after_event_id": event.get("event_id"),
            "action": decision.action,
            "current_states": current_states,
        })

    project_dir = PROJECT_ROOT / "graph" / "projects" / args.shadow_project
    (project_dir / "run").mkdir(parents=True, exist_ok=True)
    (project_dir / "raw" / "s001").mkdir(parents=True, exist_ok=True)
    graph["shadow_provenance"] = {
        "scenario": str(Path(args.scenario)),
        "built_at": datetime.now(timezone.utc).isoformat(),
        "event_actions": actions,
        "note": "机械构建（主链裁定器，无 LLM）；仅供影子对比，不参与主链",
    }
    out = project_dir / "graph_state.json"
    out.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    timeline_out = project_dir / "state_timeline.json"
    timeline_out.write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    active = [n["entity_ref"] for n in graph["nodes"].values() if n.get("status") == "active"]
    print(f"shadow state built: {len(graph['nodes'])} nodes, active entities: {sorted(set(active))}, timeline points: {len(timeline)}")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
