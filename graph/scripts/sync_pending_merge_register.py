#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""将某轮 entity resolver 输出的 pending_merge 同步到可追踪登记表。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, obj: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def parse_turn_number(value: Any) -> int:
    text = str(value).strip().lower()
    if text.startswith("turn_"):
        text = text.split("_", 1)[1]
    return int(text)


def item_key(turn_id: str, item: dict[str, Any]) -> str:
    return ":".join(
        [
            turn_id,
            str(item.get("new_node_id") or ""),
            str(item.get("raw_entity_ref") or ""),
        ]
    )


def top_candidate(item: dict[str, Any]) -> dict[str, Any]:
    candidates = item.get("candidate_aliases") or []
    if not isinstance(candidates, list) or not candidates:
        return {}
    first = candidates[0]
    return first if isinstance(first, dict) else {}


def sync_register(
    register: dict[str, Any],
    pending_merge: dict[str, Any],
    *,
    current_turn: int,
    escalate_after_turns: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    turn_id = str(pending_merge.get("turn_id") or f"turn_{current_turn:03d}")
    source_items = pending_merge.get("items") or []
    if not isinstance(source_items, list):
        raise ValueError("pending_merge.items 必须是 list")

    existing_items = register.get("items") or []
    if not isinstance(existing_items, list):
        raise ValueError("pending_merge_register.items 必须是 list")

    existing_by_key = {
        str(item.get("register_key")): item
        for item in existing_items
        if isinstance(item, dict) and item.get("register_key")
    }
    result_items = [item for item in existing_items if isinstance(item, dict)]
    added = 0
    refreshed = 0

    for source in source_items:
        if not isinstance(source, dict):
            continue
        key = item_key(turn_id, source)
        old = existing_by_key.get(key)
        if old and str(old.get("remediation_status", "tracked")) in {"resolved", "cancelled"}:
            continue

        candidate = top_candidate(source)
        blocked_turn = int(old.get("blocked_turn", current_turn)) if old else current_turn
        entry = {
            "register_key": key,
            "source_turn": turn_id,
            "source_pending_merge": f"pending_merge.{turn_id}.json",
            "new_node_id": source.get("new_node_id"),
            "raw_entity_ref": source.get("raw_entity_ref"),
            "canonical_entity_ref": candidate.get("canonical_entity_ref"),
            "match_confidence": source.get("match_confidence"),
            "evidence": candidate.get("evidence") or [],
            "candidate_aliases": source.get("candidate_aliases") or [],
            "requires_evidence": (
                f"回看 {turn_id} 的 raw 原文，裁定该实体是 alias、supersede 还是 coexist。"
            ),
            "blocked_turn": blocked_turn,
            "escalate_after_turns": escalate_after_turns,
            "escalate_on_or_after_turn": blocked_turn + escalate_after_turns,
            "remediation_status": "tracked",
            "resolution": None,
            "last_seen_turn": current_turn,
        }
        if old:
            result_items[result_items.index(old)] = entry
            refreshed += 1
        else:
            result_items.append(entry)
            added += 1

    updated = {
        "kind": "pending_merge_register.v1",
        "items": result_items,
    }
    report = {
        "kind": "pending_merge_register_sync_report.v1",
        "turn_id": turn_id,
        "summary": {
            "source_items": len([item for item in source_items if isinstance(item, dict)]),
            "added": added,
            "refreshed": refreshed,
            "tracked_items": len(result_items),
        },
    }
    return updated, report


def main() -> int:
    parser = argparse.ArgumentParser(description="同步 pending_merge 到 pending_merge_register")
    parser.add_argument("--pending-merge", required=True, help="resolver 输出的 pending_merge.turn_xxx.json")
    parser.add_argument("--register", required=True, help="pending_merge_register.json 路径")
    parser.add_argument("--current-turn", required=True, help="当前轮次")
    parser.add_argument("--escalate-after-turns", type=int, default=5)
    parser.add_argument("--report-out", help="可选同步报告路径")
    args = parser.parse_args()

    if args.escalate_after_turns < 1:
        raise SystemExit("--escalate-after-turns 必须至少为 1")

    register_path = Path(args.register)
    register = (
        load_json(register_path)
        if register_path.exists()
        else {"kind": "pending_merge_register.v1", "items": []}
    )
    pending_merge = load_json(args.pending_merge)
    updated, report = sync_register(
        register,
        pending_merge,
        current_turn=parse_turn_number(args.current_turn),
        escalate_after_turns=args.escalate_after_turns,
    )
    write_json(register_path, updated)
    if args.report_out:
        write_json(args.report_out, report)
    print(f"Updated pending merge register: {register_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
