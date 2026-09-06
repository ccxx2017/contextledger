#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""行动前版本/前提核验接口（contracts/04_assembly.md §7.4，工作包 C5）。

宿主在关键动作执行前核验装配依据是否仍然成立。只读，绝不改图。

退出码约定（这是宿主侧唯一依赖面，D3 边界契约）：
    0  前提成立，可行动
    2  前提不成立，stdout 输出 reason_codes JSON，宿主必须重新装配、重新决策

用法：
    python graph/scripts/verify_preaction.py \
        --project-id abu_modern \
        --state-revision 0084:b8ac9dafc4b9 \
        --must-include n_0001,n_0002 \
        --premine entity_ref=state ...
        --premise "quant-assistant=deployed"

核验项：
    1. 当前权威图 state_revision 与行动所依据的版本一致（否则 STATE_REVISION_STALE）
    2. must-include 列出的节点仍处于当前态（否则 PREMISE_VIOLATED）
    3. 每条 premise `entity_ref=state` 在当前态中仍成立（否则 PREMISE_VIOLATED）
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

REASON_STATE_REVISION_STALE = "STATE_REVISION_STALE"
REASON_PREMISE_VIOLATED = "PREMISE_VIOLATED"


def current_revision(graph_state_path: Path) -> str:
    data = json.loads(graph_state_path.read_text(encoding="utf-8"))
    h = hashlib.sha256()
    with open(graph_state_path, "rb") as f:
        h.update(f.read().replace(b"\r\n", b"\n").replace(b"\r", b"\n"))
    return f"{int(data.get('turn_counter', 0)):04d}:{h.hexdigest()[:12]}"


def verify(
    *,
    project_id: str,
    expected_revision: str,
    must_include: list[str],
    premises: list[str],
) -> tuple[bool, dict[str, Any]]:
    graph_state_path = PROJECT_ROOT / "graph" / "projects" / project_id / "graph_state.json"
    if not graph_state_path.exists():
        return False, {
            "result": "failed",
            "reason_codes": ["PREMISE_VIOLATED"],
            "detail": f"权威图不存在: {graph_state_path}",
        }

    graph = json.loads(graph_state_path.read_text(encoding="utf-8"))
    nodes = graph.get("nodes", {})
    if isinstance(nodes, list):
        nodes = {n["node_id"]: n for n in nodes if isinstance(n, dict)}
    active = {nid: n for nid, n in nodes.items() if n.get("status") == "active"}

    actual = current_revision(graph_state_path)
    reason_codes: list[str] = []
    detail: dict[str, Any] = {
        "expected_state_revision": expected_revision,
        "actual_state_revision": actual,
    }

    if expected_revision and actual != expected_revision:
        reason_codes.append(REASON_STATE_REVISION_STALE)

    violated_includes = []
    for nid in must_include:
        node = active.get(nid)
        if node is None:
            violated_includes.append({"node_id": nid, "reason": "not_active_or_missing"})
    if violated_includes:
        reason_codes.append(REASON_PREMISE_VIOLATED)
        detail["violated_must_include"] = violated_includes

    violated_premises = []
    for premise in premises:
        key, _, expected_state = premise.partition("=")
        key_norm = key.strip()
        expected_norm = expected_state.strip().lower()
        if not key_norm or not expected_norm:
            violated_premises.append({"premise": premise, "reason": "malformed"})
            continue
        match = any(
            str(n.get("entity_ref") or "") == key_norm
            and str(n.get("state") or "").strip().lower() == expected_norm
            for n in active.values()
        )
        if not match:
            violated_premises.append({"premise": premise, "reason": "no_active_node_matches"})
    if violated_premises:
        reason_codes.append(REASON_PREMISE_VIOLATED)
        detail["violated_premises"] = violated_premises

    if reason_codes:
        return False, {"result": "failed", "reason_codes": sorted(set(reason_codes)), "detail": detail}
    return True, {"result": "ok", "reason_codes": [], "state_revision": actual}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--state-revision", required=True, help="行动所依据的版本凭据（assembler_manifest.state_revision）")
    parser.add_argument("--must-include", default="", help="逗号分隔的节点 id，须仍处于当前态")
    parser.add_argument(
        "--premise",
        action="append",
        default=[],
        help="行动前提，格式 entity_ref=state，可重复",
    )
    args = parser.parse_args()

    must_include = [x.strip() for x in args.must_include.split(",") if x.strip()]
    ok, payload = verify(
        project_id=args.project_id,
        expected_revision=args.state_revision,
        must_include=must_include,
        premises=list(args.premise),
    )
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
