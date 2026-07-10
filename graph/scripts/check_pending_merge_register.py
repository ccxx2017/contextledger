#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from graph_lint import load_json


def write_json(path: str | Path, obj: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
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


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 pending_merge_register 是否存在超期未消化条目。")
    parser.add_argument("--register", required=True, help="pending_merge_register.json 路径")
    parser.add_argument("--current-turn", required=True, help="当前轮次，如 5 或 turn_005")
    parser.add_argument("--out", required=True, help="输出报告 JSON 路径")
    args = parser.parse_args()

    current_turn = parse_turn_number(args.current_turn)
    if current_turn is None:
        raise SystemExit(f"无法解析 --current-turn={args.current_turn!r}")

    register_path = Path(args.register)
    if not register_path.exists():
        register = {"kind": "pending_merge_register.v1", "items": []}
        write_json(register_path, register)
    else:
        register = load_json(register_path)
    items = register.get("items") or []
    if not isinstance(items, list):
        raise SystemExit(f"{register_path} 的 items 字段不是 list，无法检查。")

    overdue: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        status = str(item.get("remediation_status") or "").strip().lower()
        if status in {"resolved", "cancelled"}:
            continue
        due = item.get("escalate_on_or_after_turn")
        try:
            due_turn = int(due)
        except (TypeError, ValueError):
            continue
        if current_turn >= due_turn:
            snapshot = dict(item)
            snapshot["overdue_at_turn"] = current_turn
            overdue.append(snapshot)

    result = {
        "kind": "pending_merge_overdue_report.v1",
        "register_path": str(register_path),
        "current_turn": current_turn,
        "summary": {
            "tracked_items": len([x for x in items if isinstance(x, dict)]),
            "overdue_items": len(overdue),
        },
        "overdue_items": overdue,
    }
    write_json(args.out, result)
    print(f"Wrote pending merge overdue report: {args.out}")
    if overdue:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

