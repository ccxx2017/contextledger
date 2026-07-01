#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
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


def load_baseline(baseline_path: str | None) -> dict[str, Any]:
    if not baseline_path:
        return {"errors": [], "warnings": []}
    return load_json(baseline_path)


def classify_delta(
    before_report: dict[str, Any],
    after_report: dict[str, Any],
    baseline_report: dict[str, Any] | None = None,
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
        },
        "introduced_errors": introduced_errors,
        "preexisting_errors": preexisting_errors,
        "introduced_warnings": introduced_warnings,
        "preexisting_warnings": preexisting_warnings,
        "baseline_matched_errors": baseline_matched_errors,
        "baseline_matched_warnings": baseline_matched_warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="机械区分 lint 的 [L1] 本轮引入 / [L2] 存量问题")
    parser.add_argument("--before-graph", required=True, help="应用前 graph_state.json")
    parser.add_argument("--after-graph", required=True, help="应用后 graph_state.json")
    parser.add_argument("--baseline", help="持久 L2 基线路径，例如 graph/projects/<project_id>/reports/lint_baseline.json")
    parser.add_argument("--out", required=True, help="输出路径")
    args = parser.parse_args()

    before_graph = load_json(args.before_graph)
    after_graph = load_json(args.after_graph)
    baseline_report = load_baseline(args.baseline)

    before_report = lint_graph(before_graph)
    after_report = lint_graph(after_graph)
    delta = classify_delta(before_report, after_report, baseline_report)
    result = {
        "kind": "lint_delta.phase1_prep.v1",
        "before_graph": str(Path(args.before_graph)),
        "after_graph": str(Path(args.after_graph)),
        "baseline_path": args.baseline,
        "baseline_report": baseline_report,
        "before_report": before_report,
        "after_report": after_report,
        **delta,
    }

    write_json(args.out, result)
    print(f"Wrote lint delta: {args.out}")
    if result["summary"]["introduced_errors"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
