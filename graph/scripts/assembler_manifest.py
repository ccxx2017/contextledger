#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assembler 行动就绪度声明（contracts/04_assembly.md §7，工作包 C2）。

核心区分（评审 §二.3）：主图未被错误写入 ≠ 主图足够完整、可以支撑当前行动。
本模块把"这份状态是否适合行动"变成机器可判定的封闭词表。

readiness 三态：
    ready      无未裁定事件、预算无溢出、无绕过发布
    degraded   存在非阻断风险（未登记 lint warning / pending_merge 超期），可用但须知情
    blocked    存在不得据此行动的情形（must_include 溢出 / 未裁定隔离条目 / 绕过发布）

被 build_context_bundle.py 在装配收尾调用；也可独立运行：
    python graph/scripts/assembler_manifest.py --project-id abu_modern --turn-id turn_085
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# reason_codes 封闭词表（contracts/04_assembly.md §7.2）
REASON_MUST_INCLUDE_OVER_BUDGET = "MUST_INCLUDE_OVER_BUDGET"
REASON_QUARANTINE_NONEMPTY = "QUARANTINE_NONEMPTY"
REASON_LINT_WARNING_PRESENT = "LINT_WARNING_PRESENT"
REASON_STATE_REVISION_STALE = "STATE_REVISION_STALE"
REASON_PREMISE_VIOLATED = "PREMISE_VIOLATED"
REASON_PENDING_MERGE_OVERDUE = "PENDING_MERGE_OVERDUE"
REASON_PUBLISHED_WITH_BYPASS = "PUBLISHED_WITH_BYPASS"

KNOWN_REASON_CODES = {
    REASON_MUST_INCLUDE_OVER_BUDGET,
    REASON_QUARANTINE_NONEMPTY,
    REASON_LINT_WARNING_PRESENT,
    REASON_STATE_REVISION_STALE,
    REASON_PREMISE_VIOLATED,
    REASON_PENDING_MERGE_OVERDUE,
    REASON_PUBLISHED_WITH_BYPASS,
}

_READINESS_ORDER = {"ready": 0, "degraded": 1, "blocked": 2}


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def state_revision(graph_state_path: Path) -> str:
    """行动前核验的唯一版本凭据：f"{committed_turn:04d}:{sha256[:12]}"。"""
    data = load_json(graph_state_path)
    h = hashlib.sha256()
    with open(graph_state_path, "rb") as f:
        h.update(f.read().replace(b"\r\n", b"\n").replace(b"\r", b"\n"))
    turn = int(data.get("turn_counter", 0))
    return f"{turn:04d}:{h.hexdigest()[:12]}"


def _quarantine_register_state(project_dir: Path, current_turn: int) -> tuple[list[dict[str, Any]], int]:
    """返回 (unreviewed 条目, 超期 unreviewed 数)。"""
    register_path = project_dir / "quarantine" / "quarantine_register.json"
    if not register_path.exists():
        return [], 0
    try:
        register = load_json(register_path)
    except Exception:
        return [{"register_key": "UNPARSEABLE_REGISTER"}], 1
    unreviewed = []
    overdue = 0
    for item in register.get("items", []):
        if not isinstance(item, dict) or item.get("disposition") != "unreviewed":
            continue
        unreviewed.append({
            "register_key": item.get("register_key"),
            "source_turn": item.get("source_turn"),
            "reason": item.get("reason"),
        })
        if current_turn - (item.get("source_turn") or 0) >= 5:
            overdue += 1
    return unreviewed, overdue


def _pending_merge_overdue(project_dir: Path, current_turn: int) -> int:
    register_path = project_dir / "pending_merge" / "pending_merge_register.json"
    if not register_path.exists():
        return 0
    try:
        register = load_json(register_path)
    except Exception:
        return 0
    overdue = 0
    for item in register.get("items", []):
        if not isinstance(item, dict):
            continue
        if str(item.get("remediation_status") or "").lower() == "tracked":
            due = item.get("escalate_on_or_after_turn")
            try:
                if current_turn >= int(due):
                    overdue += 1
            except (TypeError, ValueError):
                continue
    return overdue


def _untracked_lint_warnings(project_dir: Path) -> int:
    """当前 lint 报告中未登记进基线的 warning 数。"""
    lint_path = PROJECT_ROOT / "reports" / "current_graph_lint_report.json"
    baseline_path = project_dir / "reports" / "lint_baseline.json"
    if not lint_path.exists():
        return 0
    try:
        lint = load_json(lint_path)
    except Exception:
        return 0
    baseline_warnings = set()
    if baseline_path.exists():
        try:
            for w in load_json(baseline_path).get("warnings", []):
                baseline_warnings.add(json.dumps(w, sort_keys=True, ensure_ascii=False))
        except Exception:
            pass
    untracked = 0
    for w in lint.get("warnings", []):
        if json.dumps(w, sort_keys=True, ensure_ascii=False) not in baseline_warnings:
            untracked += 1
    return untracked


def _bypass_published(project_dir: Path, turn_id: str) -> bool:
    health_path = project_dir / "reports" / f"{turn_id}_auto" / "turn_health_report.json"
    if not health_path.exists():
        return False
    try:
        return bool(load_json(health_path).get("published_with_bypass"))
    except Exception:
        return False


def build_manifest(
    *,
    project_id: str,
    turn_id: str,
    graph_state_path: Path,
    rejected: bool = False,
) -> dict[str, Any]:
    project_dir = PROJECT_ROOT / "graph" / "projects" / project_id
    revision = state_revision(graph_state_path)
    try:
        current_turn = int(load_json(graph_state_path).get("turn_counter", 0))
    except Exception:
        current_turn = 0

    reason_codes: set[str] = set()
    unresolved_event_ids: list[dict[str, Any]] = []
    integrity_risks: list[str] = []

    # 1. must_include 溢出（装配层拒绝 → 硬阻塞）
    if rejected:
        reason_codes.add(REASON_MUST_INCLUDE_OVER_BUDGET)
        integrity_risks.append("装配被拒绝：active must_include 超预算，不存在可消费的完整当前态。")

    # 2. quarantine 登记簿（评审 §二.3：隔离成功 ≠ 状态可安全消费）
    unreviewed, overdue = _quarantine_register_state(project_dir, current_turn)
    if unreviewed:
        reason_codes.add(REASON_QUARANTINE_NONEMPTY)
        unresolved_event_ids.extend(unreviewed)
        if overdue:
            integrity_risks.append(
                f"存在 {overdue} 条超期未裁定的隔离写入（age>=5），涉及旧值是否仍有效的裁定。"
            )

    # 3. lint warning（未登记 → 降级）
    untracked_warnings = _untracked_lint_warnings(project_dir)
    if untracked_warnings:
        reason_codes.add(REASON_LINT_WARNING_PRESENT)
        integrity_risks.append(f"当前图存在 {untracked_warnings} 条未登记 lint warning。")

    # 4. pending_merge 超期
    overdue_merges = _pending_merge_overdue(project_dir, current_turn)
    if overdue_merges:
        reason_codes.add(REASON_PENDING_MERGE_OVERDUE)
        integrity_risks.append(f"pending_merge 存在 {overdue_merges} 条超期未消化条目。")

    # 5. 绕过闸门发布 → 硬阻塞
    if _bypass_published(project_dir, turn_id):
        reason_codes.add(REASON_PUBLISHED_WITH_BYPASS)
        integrity_risks.append("本轮产物经 --unsafe-rebuild-mode 绕过闸门发布。")

    if not reason_codes:
        readiness = "ready"
    elif reason_codes & {REASON_MUST_INCLUDE_OVER_BUDGET, REASON_QUARANTINE_NONEMPTY, REASON_PUBLISHED_WITH_BYPASS}:
        readiness = "blocked"
    else:
        readiness = "degraded"

    return {
        "kind": "assembler_manifest.v1",
        "project_id": project_id,
        "turn_id": turn_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "state_revision": revision,
        "readiness": readiness,
        "reason_codes": sorted(reason_codes),
        "unresolved_event_ids": unresolved_event_ids,
        "integrity_risks": integrity_risks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--turn-id", required=True)
    parser.add_argument("--graph", help="graph_state 路径，缺省按 project_id 推断")
    parser.add_argument("--out", help="输出路径，缺省 reports/assembler_manifest.<turn_id>.json")
    args = parser.parse_args()

    graph_path = Path(args.graph) if args.graph else PROJECT_ROOT / "graph" / "projects" / args.project_id / "graph_state.json"
    manifest = build_manifest(project_id=args.project_id, turn_id=args.turn_id, graph_state_path=graph_path)
    out = Path(args.out) if args.out else PROJECT_ROOT / "graph" / "projects" / args.project_id / "reports" / f"assembler_manifest.{args.turn_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote assembler manifest: {out} (readiness={manifest['readiness']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
