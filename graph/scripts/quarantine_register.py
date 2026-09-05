#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""quarantine 登记簿：隔离不是终点，每一条被隔离的写入都必须有去向。

镜像 sync_pending_merge_register.py / check_pending_merge_register.py 的模式。

子命令：
    sync   扫描 quarantine/turn_*_failed.json，逐条登记进 quarantine_register.json。
           disposition 的机械判定规则：
             - 主链已存在同轮号的 patch（patches/patch_NNN.json）→ requeued
             - 否则 → unreviewed（等待人工裁定，check 会阻塞）
           人工可把 disposition 改为 accepted_loss / superseded；resolved 语义由
           requeued/superseded 覆盖，登记器不会覆盖已定案的条目。
    check  存在 unreviewed 且超过 escalate_after_turns 的条目时退出码 1。

用法：
    python graph/scripts/quarantine_register.py sync --project-id abu_modern
    python graph/scripts/quarantine_register.py check --project-id abu_modern \
        --current-turn 84 --out reports/quarantine_register_check.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

VALID_DISPOSITIONS = ("unreviewed", "accepted_loss", "requeued", "superseded")


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def parse_turn_number(value: Any) -> int | None:
    text = str(value or "").strip().lower()
    if text.startswith("turn_"):
        text = text.split("_", 1)[1]
    try:
        return int("".join(c for c in text if c.isdigit()) or "")
    except ValueError:
        return None


def project_paths(project_id: str) -> tuple[Path, Path, Path]:
    project_dir = PROJECT_ROOT / "graph" / "projects" / project_id
    return project_dir, project_dir / "quarantine", project_dir / "patches"


def sync_register(project_id: str) -> dict[str, Any]:
    project_dir, quarantine_dir, patches_dir = project_paths(project_id)
    register_path = quarantine_dir / "quarantine_register.json"
    register = (
        load_json(register_path)
        if register_path.exists()
        else {"kind": "quarantine_register.v1", "items": []}
    )
    existing = {item.get("register_key"): item for item in register.get("items", []) if isinstance(item, dict)}
    result_items = [item for item in register.get("items", []) if isinstance(item, dict)]

    added = refreshed = 0
    quarantine_files = sorted(quarantine_dir.glob("turn_*_failed.json")) if quarantine_dir.exists() else []
    for meta_path in quarantine_files:
        key = meta_path.stem  # 如 turn_014_failed
        try:
            meta = load_json(meta_path)
        except Exception:
            meta = {"error": "meta 不可解析"}

        turn_num = parse_turn_number(meta.get("turn_id") or key)
        old = existing.get(key)
        if old and old.get("disposition") in {"accepted_loss", "superseded", "requeued"}:
            # 已定案条目只刷新 last_seen，不覆盖人工/机械裁定
            old["last_seen_turn"] = turn_num
            refreshed += 1
            continue

        # 机械证据：主链同轮号 patch 是否存在（存在即说明该轮后来重跑成功入链）
        requeued = (
            turn_num is not None
            and (patches_dir / f"patch_{turn_num:03d}.json").exists()
        )
        disposition = "requeued" if requeued else "unreviewed"
        requires_evidence = (
            f"该隔离条目已有同轮号 patch 入主链（patches/patch_{turn_num:03d}.json），机械归为 requeued。"
            if requeued
            else f"回看 {meta_path.name} 与 {turn_id_str(turn_num)} raw 原文，裁定该写入是重试、放弃（accepted_loss）还是被后续轮次取代（superseded）。"
        )
        entry = {
            "register_key": key,
            "source_turn": turn_num,
            "source_file": meta_path.relative_to(PROJECT_ROOT).as_posix(),
            "stage": meta.get("stage"),
            "reason": meta.get("reason"),
            "disposition": disposition,
            "requires_evidence": requires_evidence,
            "escalate_after_turns": 5,
        }
        if old:
            result_items[result_items.index(old)] = entry
            refreshed += 1
        else:
            result_items.append(entry)
            added += 1

    updated = {
        "kind": "quarantine_register.v1",
        "project_id": project_id,
        "disposition_vocabulary": list(VALID_DISPOSITIONS),
        "items": result_items,
    }
    report = {
        "kind": "quarantine_register_sync_report.v1",
        "project_id": project_id,
        "summary": {
            "quarantine_files": len(quarantine_files),
            "added": added,
            "refreshed": refreshed,
            "tracked_items": len(result_items),
            "unreviewed_items": sum(1 for i in result_items if i.get("disposition") == "unreviewed"),
        },
    }
    write_json(register_path, updated)
    return report


def turn_id_str(turn_num: int | None) -> str:
    return f"turn_{turn_num:03d}" if turn_num is not None else "turn_???"


def check_register(project_id: str, current_turn: int, escalate_after_turns: int) -> dict[str, Any]:
    _, quarantine_dir, _ = project_paths(project_id)
    register_path = quarantine_dir / "quarantine_register.json"
    register = (
        load_json(register_path)
        if register_path.exists()
        else {"kind": "quarantine_register.v1", "items": []}
    )
    items = [i for i in register.get("items", []) if isinstance(i, dict)]

    blocking: list[dict[str, Any]] = []
    for item in items:
        if item.get("disposition") != "unreviewed":
            continue
        age = current_turn - (item.get("source_turn") or 0)
        item["age_turns"] = age
        if age >= escalate_after_turns:
            blocking.append(item)

    report = {
        "kind": "quarantine_register_check_report.v1",
        "project_id": project_id,
        "current_turn": current_turn,
        "summary": {
            "tracked_items": len(items),
            "unreviewed_items": sum(1 for i in items if i.get("disposition") == "unreviewed"),
            "blocking_items": len(blocking),
        },
        "blocking_items": blocking,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="quarantine 登记簿 sync/check")
    sub = parser.add_subparsers(dest="command", required=True)

    p_sync = sub.add_parser("sync", help="扫描 quarantine/ 并登记")
    p_sync.add_argument("--project-id", default="abu_modern")
    p_sync.add_argument("--report-out", help="可选同步报告路径")

    p_check = sub.add_parser("check", help="检查是否存在超期未裁定的隔离条目")
    p_check.add_argument("--project-id", default="abu_modern")
    p_check.add_argument("--current-turn", required=True, help="当前轮次，如 84 或 turn_084")
    p_check.add_argument("--escalate-after-turns", type=int, default=5)
    p_check.add_argument("--out", help="输出报告 JSON 路径")

    args = parser.parse_args()

    if args.command == "sync":
        report = sync_register(args.project_id)
        if args.report_out:
            write_json(Path(args.report_out), report)
        s = report["summary"]
        print(
            f"quarantine register synced: tracked={s['tracked_items']} "
            f"added={s['added']} refreshed={s['refreshed']} unreviewed={s['unreviewed_items']}"
        )
        return 0

    current_turn = parse_turn_number(args.current_turn)
    if current_turn is None:
        raise SystemExit(f"无法解析 --current-turn={args.current_turn!r}")
    report = check_register(args.project_id, current_turn, args.escalate_after_turns)
    if args.out:
        write_json(Path(args.out), report)
    s = report["summary"]
    print(
        f"quarantine register check: tracked={s['tracked_items']} "
        f"unreviewed={s['unreviewed_items']} blocking={s['blocking_items']}"
    )
    return 1 if s["blocking_items"] else 0


if __name__ == "__main__":
    sys.exit(main())
