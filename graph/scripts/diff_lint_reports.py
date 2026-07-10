#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from graph_lint import lint_graph, load_json


def write_json(path: str | Path, obj: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def issue_signature(issue: dict[str, Any]) -> str:
    stable_keys = [
        "code",
        "message",
        "node_id",
        "old_node_id",
        "new_node_id",
        "edge_id",
        "entity_ref",
        "source",
        "target",
        "state",
        "relation",
    ]
    payload = {key: issue.get(key) for key in stable_keys if key in issue}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def issues_to_map(issues: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {issue_signature(item): item for item in issues}


def code_histogram(issues: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for issue in issues:
        code = str(issue.get("code") or "UNKNOWN").strip() or "UNKNOWN"
        counter[code] += 1
    return dict(sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])))


def load_baseline(baseline_path: str | None) -> dict[str, Any]:
    if not baseline_path:
        return {"errors": [], "warnings": []}
    path = Path(baseline_path)
    if not path.exists():
        return {"errors": [], "warnings": []}
    return load_json(baseline_path)


def parse_turn_counter(graph: dict[str, Any]) -> int | None:
    value = graph.get("turn_counter")
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


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


def require_existing_file(path_str: str, *, role: str, hint: str) -> Path:
    path = Path(path_str)
    if not path.exists():
        raise SystemExit(f"{role} 不存在: {path}。{hint}")
    return path


def require_newer_than(target_path: Path, reference_path: str | Path, *, role: str) -> None:
    reference = Path(reference_path)
    if not reference.exists():
        raise SystemExit(f"{role} 参考文件不存在: {reference}")

    if target_path.stat().st_mtime_ns <= reference.stat().st_mtime_ns:
        raise SystemExit(
            f"{target_path} 的修改时间不晚于 {reference}。"
            f"为避免 {role} 误读同名旧快照，已拒绝执行；请先重新生成本轮 after_graph。"
        )


def validate_turn_pair(
    before_graph: dict[str, Any],
    after_graph: dict[str, Any],
    expected_turn: Any,
    *,
    before_path: Path,
    after_path: Path,
) -> int:
    expected = parse_turn_number(expected_turn)
    if expected is None:
        raise SystemExit(f"无法解析 --expected-turn={expected_turn!r}")

    before_turn = parse_turn_counter(before_graph)
    after_turn = parse_turn_counter(after_graph)
    if before_turn is None:
        raise SystemExit(f"{before_path} 缺少可解析的 turn_counter，无法校验输入是否为前态。")
    if after_turn is None:
        raise SystemExit(f"{after_path} 缺少可解析的 turn_counter，无法校验输入是否为本轮快照。")

    if after_turn != expected:
        raise SystemExit(
            f"{after_path} 的 turn_counter={after_turn}，与预期 turn_{expected:03d} 不一致。"
            "为避免误读旧快照，已拒绝执行 diff。"
        )

    expected_before = expected - 1
    if before_turn > expected_before:
        raise SystemExit(
            f"{before_path} 的 turn_counter={before_turn}，已超过预期前态 turn_{expected_before:03d}。"
            "请确认 before_graph 指向的是上一轮权威图，而不是已推进后的图。"
        )
    if before_turn < expected_before:
        print(
            f"WARN: {before_path} 的 turn_counter={before_turn}，与预期前态 turn_{expected_before:03d} 不一致；"
            f"将按 quarantine 跳过模式 diff（中间轮次被隔离）。"
        )
    return expected


def collect_overdue_baseline_issues(
    baseline_matched_errors: list[dict[str, Any]],
    baseline_matched_warnings: list[dict[str, Any]],
    current_turn: int | None,
) -> list[dict[str, Any]]:
    if current_turn is None:
        return []

    overdue: list[dict[str, Any]] = []
    for issue in [*baseline_matched_errors, *baseline_matched_warnings]:
        status = str(issue.get("remediation_status") or "").strip().lower()
        if status != "tracked":
            continue

        escalate_on_or_after_turn = issue.get("escalate_on_or_after_turn")
        try:
            due_turn = int(escalate_on_or_after_turn)
        except (TypeError, ValueError):
            continue

        if current_turn < due_turn:
            continue

        item = dict(issue)
        item["overdue_at_turn"] = current_turn
        overdue.append(item)

    return overdue


def classify_delta(
    before_report: dict[str, Any],
    after_report: dict[str, Any],
    baseline_report: dict[str, Any] | None = None,
    current_turn: int | None = None,
) -> dict[str, Any]:
    baseline_report = baseline_report or {"errors": [], "warnings": []}
    before_errors = {issue_signature(item): item for item in before_report.get("errors", [])}
    after_errors = {issue_signature(item): item for item in after_report.get("errors", [])}
    before_warnings = {issue_signature(item): item for item in before_report.get("warnings", [])}
    after_warnings = {issue_signature(item): item for item in after_report.get("warnings", [])}
    baseline_errors = issues_to_map(baseline_report.get("errors", []))
    baseline_warnings = issues_to_map(baseline_report.get("warnings", []))

    known_error_signatures = set(before_errors) | set(baseline_errors)
    known_warning_signatures = set(before_warnings) | set(baseline_warnings)

    introduced_errors = [after_errors[key] for key in after_errors.keys() - known_error_signatures]
    preexisting_errors = [after_errors[key] for key in after_errors.keys() & known_error_signatures]
    introduced_warnings = [after_warnings[key] for key in after_warnings.keys() - known_warning_signatures]
    preexisting_warnings = [after_warnings[key] for key in after_warnings.keys() & known_warning_signatures]
    baseline_matched_errors = [after_errors[key] for key in after_errors.keys() & set(baseline_errors)]
    baseline_matched_warnings = [after_warnings[key] for key in after_warnings.keys() & set(baseline_warnings)]
    overdue_baseline_issues = collect_overdue_baseline_issues(
        baseline_matched_errors,
        baseline_matched_warnings,
        current_turn,
    )

    return {
        "summary": {
            "before_errors": len(before_errors),
            "after_errors": len(after_errors),
            "before_warnings": len(before_warnings),
            "after_warnings": len(after_warnings),
            "baseline_errors": len(baseline_errors),
            "baseline_warnings": len(baseline_warnings),
            "introduced_errors": len(introduced_errors),
            "preexisting_errors": len(preexisting_errors),
            "introduced_warnings": len(introduced_warnings),
            "preexisting_warnings": len(preexisting_warnings),
            "baseline_matched_errors": len(baseline_matched_errors),
            "baseline_matched_warnings": len(baseline_matched_warnings),
            "overdue_baseline_issues": len(overdue_baseline_issues),
        },
        "introduced_errors": introduced_errors,
        "preexisting_errors": preexisting_errors,
        "introduced_warnings": introduced_warnings,
        "preexisting_warnings": preexisting_warnings,
        "baseline_matched_errors": baseline_matched_errors,
        "baseline_matched_warnings": baseline_matched_warnings,
        "overdue_baseline_issues": overdue_baseline_issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="机械区分 lint 的 [L1] 本轮引入 / [L2] 存量问题")
    parser.add_argument("--before-graph", required=True, help="应用前 graph_state.json")
    parser.add_argument("--after-graph", required=True, help="应用后 graph_state.json")
    parser.add_argument("--baseline", help="持久 L2 基线路径，例如 graph/projects/<project_id>/reports/lint_baseline.json")
    parser.add_argument("--expected-turn", required=True, help="预期正在比较的轮次，如 4 或 turn_004")
    parser.add_argument("--after-newer-than", help="要求 after_graph 的修改时间晚于该参考文件，例如本轮 patch")
    parser.add_argument("--out", required=True, help="输出路径")
    args = parser.parse_args()

    before_path = require_existing_file(
        args.before_graph,
        role="before_graph",
        hint="请传入应用前的权威 graph_state.json。",
    )
    after_path = require_existing_file(
        args.after_graph,
        role="after_graph",
        hint="请先运行 apply_patch.py 生成本轮 graph_state 快照，再执行 diff_lint_reports.py。",
    )

    before_graph = load_json(before_path)
    after_graph = load_json(after_path)
    baseline_report = load_baseline(args.baseline)
    if args.after_newer_than:
        require_newer_than(after_path, args.after_newer_than, role="diff_lint_reports.py")
    current_turn = validate_turn_pair(
        before_graph,
        after_graph,
        args.expected_turn,
        before_path=before_path,
        after_path=after_path,
    )

    before_report = lint_graph(before_graph)
    after_report = lint_graph(after_graph)
    delta = classify_delta(before_report, after_report, baseline_report, current_turn=current_turn)
    issue_code_histogram = {
        "before": {
            "errors": code_histogram(before_report.get("errors", [])),
            "warnings": code_histogram(before_report.get("warnings", [])),
        },
        "after": {
            "errors": code_histogram(after_report.get("errors", [])),
            "warnings": code_histogram(after_report.get("warnings", [])),
        },
        "introduced": {
            "errors": code_histogram(delta.get("introduced_errors", [])),
            "warnings": code_histogram(delta.get("introduced_warnings", [])),
        },
        "baseline": {
            "errors": code_histogram(baseline_report.get("errors", [])),
            "warnings": code_histogram(baseline_report.get("warnings", [])),
        },
    }
    result = {
        "kind": "lint_delta.phase1_prep.v1",
        "before_graph": str(before_path),
        "after_graph": str(after_path),
        "baseline_path": args.baseline,
        "current_turn": current_turn,
        "baseline_report": baseline_report,
        "before_report": before_report,
        "after_report": after_report,
        "issue_code_histogram": issue_code_histogram,
        **delta,
    }

    write_json(args.out, result)
    print(f"Wrote lint delta: {args.out}")
    if result["summary"]["introduced_errors"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
