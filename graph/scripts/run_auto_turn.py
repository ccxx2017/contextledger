#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
run_auto_turn.py

单轮全自动驱动脚本（Phase 1 全自动连续执行）。
不再人工审 patch，机械层全权兜底；每轮输出一份 turn_health_report.json。

用法：
    python graph/scripts/run_auto_turn.py abu_modern turn_006

流程：
    build_graph_slice -> build_extractor_prompt -> invoke_extractor
    -> detect_close_candidates -> entity_resolver -> reconcile_patch
    -> [失败则自动重试 extractor，最多 3 次] -> apply_patch -> graph_lint
    -> diff_lint_reports -> build_context_bundle -> pending_merge 登记/检查
    -> turn_health_report.json

如果 reconcile 最终仍失败，本轮 patch 被隔离到 quarantine/，不污染主图。
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GRAPH_DIR = PROJECT_ROOT / "graph"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

DEFAULT_SYSTEM_PROMPT = GRAPH_DIR / "prompts" / "extractor_system.md"
ALIAS_CONTRACT = CONTRACTS_DIR / "05_entity_naming.md"
MAX_RECONCILE_RETRIES = 3


def run(
    cmd: list[str],
    *,
    check: bool = True,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    """执行子命令，失败时抛出 CalledProcessError。"""
    result = subprocess.run(
        [sys.executable, *cmd],
        cwd=PROJECT_ROOT,
        capture_output=capture,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, cmd, output=result.stdout, stderr=result.stderr
        )
    return result


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def parse_turn_number(turn_id: str) -> int:
    text = turn_id.strip().lower()
    if text.startswith("turn_"):
        text = text.split("_", 1)[1]
    return int(text)


def read_graph_turn_counter(graph_state_path: Path) -> int:
    graph_state = load_json(graph_state_path)
    if not isinstance(graph_state, dict):
        raise ValueError(f"主图不是 JSON object: {graph_state_path}")
    try:
        return int(graph_state["turn_counter"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"主图缺少合法 turn_counter: {graph_state_path}") from exc


def audit_committed_history(
    *,
    project_dir: Path,
    raw_session_dir: Path,
    committed_turn: int,
) -> dict[str, Any]:
    """检查已宣称提交的每一轮是否都有 raw、patch 与图快照。"""
    missing_raw: list[str] = []
    missing_patches: list[str] = []
    missing_snapshots: list[str] = []
    for turn in range(1, committed_turn + 1):
        turn_id = f"turn_{turn:03d}"
        if not (raw_session_dir / f"{turn_id}.md").exists():
            missing_raw.append(turn_id)
        if not (project_dir / "patches" / f"patch_{turn:03d}.json").exists():
            missing_patches.append(turn_id)
        if not (project_dir / "run" / f"graph_state.{turn_id}.json").exists():
            missing_snapshots.append(turn_id)
    return {
        "committed_turn": committed_turn,
        "missing_raw": missing_raw,
        "missing_patches": missing_patches,
        "missing_snapshots": missing_snapshots,
        "ok": not (missing_raw or missing_patches or missing_snapshots),
    }


def write_start_block_report(
    *,
    project_dir: Path,
    project_id: str,
    turn_id: str,
    stage: str,
    reason: str,
    continuity: dict[str, Any],
) -> None:
    work_dir = project_dir / "reports" / f"{turn_id}_auto"
    work_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        work_dir / "turn_health_report.json",
        {
            "turn_id": turn_id,
            "project_id": project_id,
            "stages": {stage: {"status": "BLOCKED", "continuity": continuity}},
            "summary": {"status": "BLOCKED", "stage": stage, "reason": reason},
            "committed": {"committed": False, "reason": reason},
            "lights": {
                "critical_status": "RED",
                "lint_baseline": "RED",
                "queue_health": "RED",
                "assembly_integrity": "RED",
            },
        },
    )


def ensure_dirs(project_dir: Path, turn_id: str) -> Path:
    work_dir = project_dir / "reports" / f"{turn_id}_auto"
    work_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "patches").mkdir(parents=True, exist_ok=True)
    (project_dir / "pending_merge").mkdir(parents=True, exist_ok=True)
    (project_dir / "quarantine").mkdir(parents=True, exist_ok=True)
    (project_dir / "run").mkdir(parents=True, exist_ok=True)
    (project_dir / "graph_slices").mkdir(parents=True, exist_ok=True)
    return work_dir


def quarantine_turn(
    project_dir: Path,
    turn_id: str,
    work_dir: Path,
    stage: str,
    reason: str,
    last_patch: Path | None,
) -> dict[str, Any]:
    quarantine_dir = project_dir / "quarantine"
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    quarantine_patch = quarantine_dir / f"{turn_id}_failed_patch.json"
    quarantine_meta = quarantine_dir / f"{turn_id}_failed.json"

    if last_patch and last_patch.exists():
        shutil.copy2(last_patch, quarantine_patch)

    meta = {
        "turn_id": turn_id,
        "stage": stage,
        "reason": reason,
        "quarantine_patch": str(quarantine_patch),
    }
    write_json(quarantine_meta, meta)

    return {
        "status": "QUARANTINE",
        "stage": stage,
        "reason": reason,
        "quarantine_patch": str(quarantine_patch),
        "quarantine_meta": str(quarantine_meta),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="全自动执行单轮 turn")
    parser.add_argument("project_id", help="项目 id，如 abu_modern")
    parser.add_argument("turn_id", help="轮次，如 turn_006")
    parser.add_argument("--raw-dir", default="raw/projects", help="raw 目录前缀")
    parser.add_argument("--session", default="s001", help="会话目录名")
    parser.add_argument("--dry-run", action="store_true", help="不提交主图，只生成 scratch 产物")
    parser.add_argument("--max-retry", type=int, default=MAX_RECONCILE_RETRIES, help="reconcile 失败后 extractor 重试次数")
    parser.add_argument("--max-nodes", type=int, default=12, help="bundle 预算")
    parser.add_argument("--budget-profile", default="phase1_prep_baseline", help="bundle budget profile")
    parser.add_argument("--warnings-non-blocking", action="store_true", help="lint warning 不阻塞提交")
    parser.add_argument("--pending-merge-non-blocking", action="store_true", help="pending_merge 超期不阻塞提交")
    parser.add_argument("--lint-errors-non-blocking", action="store_true", help="lint error 不阻塞提交（重建历史链时临时使用）")
    parser.add_argument("--reconcile-errors-non-blocking", action="store_true", help="reconcile error 不阻塞提交（重建历史链时临时使用）")
    args = parser.parse_args()

    project_id = args.project_id
    turn_id = args.turn_id
    turn_num = parse_turn_number(turn_id)
    prev_turn_num = turn_num - 1

    project_dir = GRAPH_DIR / "projects" / project_id
    graph_state_path = project_dir / "graph_state.json"
    prev_graph_state_path = project_dir / "run" / f"graph_state.turn_{prev_turn_num:03d}.json"

    if not graph_state_path.exists():
        print(f"FATAL: 主图不存在: {graph_state_path}", file=sys.stderr)
        return 1

    # 优先用 run/ 下的上一轮快照作为 before-graph，否则用当前 graph_state
    if prev_graph_state_path.exists():
        before_graph_path = prev_graph_state_path
    else:
        before_graph_path = graph_state_path

    raw_session_dir = PROJECT_ROOT / args.raw_dir / project_id / args.session
    raw_turn_path = raw_session_dir / f"{turn_id}.md"
    if not raw_turn_path.exists():
        print(f"FATAL: raw 文件不存在: {raw_turn_path}", file=sys.stderr)
        return 1

    committed_turn = read_graph_turn_counter(graph_state_path)
    continuity = audit_committed_history(
        project_dir=project_dir,
        raw_session_dir=raw_session_dir,
        committed_turn=committed_turn,
    )
    expected_turn = committed_turn + 1
    if turn_num != expected_turn:
        reason = (
            f"轮次不连续：主图已提交到 turn_{committed_turn:03d}，"
            f"本次只能执行 turn_{expected_turn:03d}，不能直接执行 {turn_id}。"
        )
        write_start_block_report(
            project_dir=project_dir,
            project_id=project_id,
            turn_id=turn_id,
            stage="turn_sequence_guard",
            reason=reason,
            continuity=continuity,
        )
        print(f"BLOCKED: {reason}", file=sys.stderr)
        return 2
    if not continuity["ok"]:
        reason = "已提交轮次缺少 raw、patch 或图快照；修复或裁定历史链后才能开始下一轮。"
        write_start_block_report(
            project_dir=project_dir,
            project_id=project_id,
            turn_id=turn_id,
            stage="committed_history_audit",
            reason=reason,
            continuity=continuity,
        )
        print(f"BLOCKED: {reason}", file=sys.stderr)
        return 2

    work_dir = ensure_dirs(project_dir, turn_id)

    # 产物路径
    slice_path = work_dir / f"slice_{turn_num:03d}.json"
    prompt_path = work_dir / f"extractor_prompt.{turn_id}.json"
    raw_patch_path = work_dir / f"patch_{turn_num:03d}.raw.json"
    raw_response_path = work_dir / f"extractor_raw_response.{turn_id}.txt"
    close_candidates_path = work_dir / f"close_candidates.{turn_id}.json"
    resolved_patch_path = work_dir / f"patch_{turn_num:03d}.resolved.json"
    entity_resolution_report_path = work_dir / f"entity_resolution.{turn_id}.json"
    pending_merge_turn_path = work_dir / f"pending_merge.{turn_id}.json"
    published_pending_merge_path = project_dir / "pending_merge" / f"pending_merge.{turn_id}.json"
    reconcile_report_path = work_dir / f"reconcile_report.{turn_id}.json"
    after_graph_path = work_dir / f"graph_state.after_{turn_id}.json"
    lint_report_path = work_dir / f"lint_report.{turn_id}.json"
    lint_delta_path = work_dir / f"lint_delta.{turn_id}.json"
    pending_merge_overdue_path = work_dir / f"pending_merge_overdue.{turn_id}.json"
    bundle_path = work_dir / f"context_bundle.{turn_id}.json"
    assembly_report_path = work_dir / f"assembly_report.{turn_id}.json"
    published_bundle_path = project_dir / "reports" / f"context_bundle.{turn_id}.json"
    published_assembly_report_path = project_dir / "reports" / f"assembly_report.{turn_id}.json"
    pending_merge_sync_report_path = work_dir / f"pending_merge_register_sync.{turn_id}.json"
    health_report_path = work_dir / "turn_health_report.json"

    health: dict[str, Any] = {
        "turn_id": turn_id,
        "project_id": project_id,
        "work_dir": str(work_dir),
        "stages": {},
    }
    current_stage = "init"

    try:
        # 1. build_graph_slice
        current_stage = "build_graph_slice"
        print(f"[{turn_id}] 1/9 build_graph_slice ...")
        run([
            "graph/scripts/build_graph_slice.py",
            "--graph", str(graph_state_path),
            "--turn", str(raw_turn_path),
            "--turn-id", str(turn_num),
            "--out", str(slice_path),
        ])
        health["stages"]["build_graph_slice"] = {"status": "OK", "out": str(slice_path)}

        # 2. invoke_extractor（同时生成 prompt snapshot）
        current_stage = "invoke_extractor"
        print(f"[{turn_id}] 2/9 invoke_extractor ...")
        run([
            "graph/scripts/invoke_extractor.py",
            "--system", str(DEFAULT_SYSTEM_PROMPT),
            "--slice", str(slice_path),
            "--turn", str(raw_turn_path),
            "--project-id", project_id,
            "--turn-id", turn_id,
            "--out", str(raw_patch_path),
            "--raw-response-out", str(raw_response_path),
            "--prompt-out", str(prompt_path),
        ])
        health["stages"]["invoke_extractor"] = {"status": "OK", "out": str(raw_patch_path)}

        # 3. detect_close_candidates
        current_stage = "detect_close_candidates"
        print(f"[{turn_id}] 3/9 detect_close_candidates ...")
        run([
            "graph/scripts/detect_close_candidates.py",
            "--graph", str(graph_state_path),
            "--patch", str(raw_patch_path),
            "--out", str(close_candidates_path),
        ])
        health["stages"]["detect_close_candidates"] = {"status": "OK", "out": str(close_candidates_path)}

        # 4. entity_resolver
        current_stage = "entity_resolver"
        print(f"[{turn_id}] 4/9 entity_resolver ...")
        run([
            "graph/scripts/entity_resolver.py",
            "--project-id", project_id,
            "--turn-id", turn_id,
            "--graph", str(graph_state_path),
            "--patch", str(raw_patch_path),
            "--out-patch", str(resolved_patch_path),
            "--report-out", str(entity_resolution_report_path),
            "--pending-merge-out", str(pending_merge_turn_path),
            "--alias-contract", str(ALIAS_CONTRACT),
        ])
        health["stages"]["entity_resolver"] = {"status": "OK", "out": str(resolved_patch_path)}

        # 4.5 sanitize entity_ref
        print(f"[{turn_id}] 4.5/9 sanitize entity_ref ...")
        run([
            "graph/scripts/sanitize_patch_entity_refs.py",
            "--patch", str(resolved_patch_path),
            "--graph", str(graph_state_path),
            "--out", str(resolved_patch_path),
        ])

        # 5. reconcile_patch（带重试）
        current_stage = "reconcile_patch"
        print(f"[{turn_id}] 5/9 reconcile_patch ...")
        reconcile_ok = False
        reconcile_report: dict[str, Any] | None = None
        current_patch = resolved_patch_path
        attempt = 0
        while True:
            try:
                run([
                    "graph/scripts/reconcile_patch.py",
                    str(graph_state_path),
                    str(current_patch),
                    "--out", str(reconcile_report_path),
                ])
                reconcile_report = load_json(reconcile_report_path)
                if reconcile_report.get("ok"):
                    reconcile_ok = True
                    break
                raise subprocess.CalledProcessError(1, ["reconcile_patch"])
            except subprocess.CalledProcessError:
                attempt += 1
                if attempt > args.max_retry:
                    break
                print(f"[{turn_id}] reconcile fail, retry extractor ({attempt}/{args.max_retry}) ...")
                # 重新调用 extractor，输出带 retry 标记的 patch
                retry_patch = work_dir / f"patch_{turn_num:03d}.retry_{attempt}.json"
                retry_response = work_dir / f"extractor_raw_response.{turn_id}.retry_{attempt}.txt"
                run([
                    "graph/scripts/invoke_extractor.py",
                    "--system", str(DEFAULT_SYSTEM_PROMPT),
                    "--slice", str(slice_path),
                    "--turn", str(raw_turn_path),
                    "--project-id", project_id,
                    "--turn-id", turn_id,
                    "--out", str(retry_patch),
                    "--raw-response-out", str(retry_response),
                ])
                # resolver 也需要重跑
                retry_resolved = work_dir / f"patch_{turn_num:03d}.resolved.retry_{attempt}.json"
                run([
                    "graph/scripts/entity_resolver.py",
                    "--project-id", project_id,
                    "--turn-id", turn_id,
                    "--graph", str(graph_state_path),
                    "--patch", str(retry_patch),
                    "--out-patch", str(retry_resolved),
                    "--report-out", str(work_dir / f"entity_resolution.{turn_id}.retry_{attempt}.json"),
                    "--pending-merge-out", str(pending_merge_turn_path),
                    "--alias-contract", str(ALIAS_CONTRACT),
                ])
                # 重试得到的 resolved patch 也需要做 entity_ref 清洗
                run([
                    "graph/scripts/sanitize_patch_entity_refs.py",
                    "--patch", str(retry_resolved),
                    "--graph", str(graph_state_path),
                    "--out", str(retry_resolved),
                ])
                current_patch = retry_resolved

        if not reconcile_ok or not reconcile_report:
            if reconcile_report and args.reconcile_errors_non_blocking:
                print(f"[{turn_id}] reconcile has errors but --reconcile-errors-non-blocking is set; continuing")
                health["stages"]["reconcile_patch"] = {
                    "status": "OK",
                    "out": str(reconcile_report_path),
                    "retries": attempt,
                    "errors": reconcile_report.get("summary", {}).get("errors", 0),
                    "warnings": reconcile_report.get("summary", {}).get("warnings", 0),
                }
            else:
                reason = f"reconcile 失败且重试 {args.max_retry} 次后仍无法通过"
                health["stages"]["reconcile_patch"] = {"status": "FAIL", "reason": reason}
                health["summary"] = quarantine_turn(
                    project_dir, turn_id, work_dir, "reconcile_patch", reason, current_patch
                )
                health["lights"] = {"critical_status": "RED", "lint_baseline": "RED", "queue_health": "RED", "assembly_integrity": "RED"}
                write_json(health_report_path, health)
                print(f"[{turn_id}] QUARANTINE: {reason}")
                return 0

        health["stages"]["reconcile_patch"] = {
            "status": "OK",
            "out": str(reconcile_report_path),
            "retries": attempt,
            "errors": reconcile_report.get("summary", {}).get("errors", 0),
            "warnings": reconcile_report.get("summary", {}).get("warnings", 0),
        }

            # 6. apply_patch
        current_stage = "apply_patch"
        print(f"[{turn_id}] 6/9 apply_patch ...")
        run([
            "graph/scripts/apply_patch.py",
            "--graph", str(graph_state_path),
            "--patch", str(current_patch),
            "--out", str(after_graph_path),
            "--expected-turn", turn_id,
        ])
        health["stages"]["apply_patch"] = {"status": "OK", "out": str(after_graph_path)}

        # 7. graph_lint
        current_stage = "graph_lint"
        print(f"[{turn_id}] 7/9 graph_lint ...")
        # graph_lint 在有 error 时返回非零，这是正常设计，不应当成脚本异常
        run(
            [
                "graph/scripts/graph_lint.py",
                str(after_graph_path),
                "--out", str(lint_report_path),
                "--expected-turn", turn_id,
                "--newer-than", str(current_patch),
            ],
            check=False,
        )
        lint_report = load_json(lint_report_path)
        health["stages"]["graph_lint"] = {
            "status": "OK",
            "errors": lint_report.get("summary", {}).get("errors", 0),
            "warnings": lint_report.get("summary", {}).get("warnings", 0),
        }

        # 8. diff_lint_reports
        # diff_lint_reports 在存在 introduced issues 时返回非零，这是正常输出，不应当成脚本异常
        current_stage = "diff_lint_reports"
        print(f"[{turn_id}] 8/9 diff_lint_reports ...")
        run([
            "graph/scripts/diff_lint_reports.py",
            "--before-graph", str(before_graph_path),
            "--after-graph", str(after_graph_path),
            "--expected-turn", turn_id,
            "--after-newer-than", str(current_patch),
            "--baseline", str(project_dir / "reports" / "lint_baseline.json"),
            "--out", str(lint_delta_path),
        ], check=False)
        lint_delta = load_json(lint_delta_path)
        introduced_errors = lint_delta.get("summary", {}).get("introduced_errors", 0)
        introduced_warnings = lint_delta.get("summary", {}).get("introduced_warnings", 0)
        overdue_baseline = lint_delta.get("summary", {}).get("overdue_baseline_issues", 0)
        health["stages"]["diff_lint_reports"] = {
            "status": "OK",
            "introduced_errors": introduced_errors,
            "introduced_warnings": introduced_warnings,
            "overdue_baseline_issues": overdue_baseline,
        }

        # 9. build_context_bundle
        current_stage = "build_context_bundle"
        print(f"[{turn_id}] 9/9 build_context_bundle ...")
        l1_must_count = 0
        try:
            run([
                "graph/scripts/build_context_bundle.py",
                "--graph", str(after_graph_path),
                "--project-id", project_id,
                "--turn-id", turn_id,
                "--out", str(bundle_path),
                "--report-out", str(assembly_report_path),
                "--max-nodes", str(args.max_nodes),
                "--budget-profile", args.budget_profile,
                "--newer-than", str(current_patch),
            ])
            bundle = load_json(bundle_path)
            l1_must_count = len(bundle.get("l1_baseline", {}).get("must_include", []))
            selected_ids = bundle.get("assembly", {}).get("selected_node_ids", [])
            health["stages"]["build_context_bundle"] = {
                "status": "OK",
                "bundle": str(bundle_path),
                "assembly_report": str(assembly_report_path),
                "l1_must_include_count": l1_must_count,
                "selected_count": len(selected_ids),
            }
        except subprocess.CalledProcessError:
            # bundle 可能因 must 超预算被拒绝，这是装配层真实行为
            reason = "assembly rejected or precondition failed"
            if assembly_report_path.exists():
                assembly_report = load_json(assembly_report_path)
                reason = assembly_report.get("result", reason)
            health["stages"]["build_context_bundle"] = {
                "status": "REJECTED",
                "assembly_report": str(assembly_report_path),
                "reason": reason,
            }

        # 10. check_pending_merge_register
        current_stage = "check_pending_merge_register"
        print(f"[{turn_id}] checking pending_merge_register ...")
        result = run([
            "graph/scripts/check_pending_merge_register.py",
            "--register", str(project_dir / "pending_merge" / "pending_merge_register.json"),
            "--current-turn", str(turn_num),
            "--out", str(pending_merge_overdue_path),
        ], check=False)
        overdue_report = load_json(pending_merge_overdue_path)
        overdue_items = overdue_report.get("summary", {}).get("overdue_items", 0)
        if result.returncode != 0 and overdue_items and not args.pending_merge_non_blocking:
            raise subprocess.CalledProcessError(
                result.returncode,
                ["graph/scripts/check_pending_merge_register.py"],
                output=result.stdout,
                stderr=result.stderr,
            )
        health["stages"]["check_pending_merge_register"] = {
            "status": "OK",
            "overdue_items": overdue_items,
        }

        # 红绿灯判定
        health.setdefault("summary", {"status": "OK"})
        # critical_status 只关心流程是否中断 / reconcile 是否成功；lint 问题交给 lint_baseline
        critical_green = (
            health["stages"]["reconcile_patch"]["status"] == "OK"
            and health["summary"].get("status") != "QUARANTINE"
        )
        baseline_green = (
            (
                args.lint_errors_non_blocking
                or health["stages"]["diff_lint_reports"]["introduced_errors"] == 0
            )
            and (
                args.warnings_non_blocking
                or health["stages"]["diff_lint_reports"]["introduced_warnings"] == 0
            )
        )
        queue_green = overdue_items == 0 or args.pending_merge_non_blocking
        assembly_green = (
            health["stages"]["build_context_bundle"]["status"] == "OK"
            and l1_must_count > 0
        )

        health["lights"] = {
            "critical_status": "GREEN" if critical_green else "RED",
            "lint_baseline": "GREEN" if baseline_green else "RED",
            "queue_health": "GREEN" if queue_green else "RED",
            "assembly_integrity": "GREEN" if assembly_green else "RED",
        }

        # 只有所有机械闸门通过，才允许把 scratch 产物发布为项目权威产物。
        all_green = all(v == "GREEN" for v in health["lights"].values())
        if all_green and not args.dry_run:
            current_stage = "sync_pending_merge_register"
            print(f"[{turn_id}] syncing pending_merge register ...")
            run([
                "graph/scripts/sync_pending_merge_register.py",
                "--pending-merge", str(pending_merge_turn_path),
                "--register", str(project_dir / "pending_merge" / "pending_merge_register.json"),
                "--current-turn", str(turn_num),
                "--report-out", str(pending_merge_sync_report_path),
            ])
            health["stages"]["sync_pending_merge_register"] = {
                "status": "OK",
                "report": str(pending_merge_sync_report_path),
            }

            print(f"[{turn_id}] all green, committing to main graph ...")
            shutil.copy2(after_graph_path, graph_state_path)
            shutil.copy2(after_graph_path, project_dir / "run" / f"graph_state.turn_{turn_num:03d}.json")
            shutil.copy2(current_patch, project_dir / "patches" / f"patch_{turn_num:03d}.json")
            shutil.copy2(pending_merge_turn_path, published_pending_merge_path)
            shutil.copy2(bundle_path, published_bundle_path)
            shutil.copy2(assembly_report_path, published_assembly_report_path)
            health["committed"] = {
                "graph_state": str(graph_state_path),
                "run_snapshot": str(project_dir / "run" / f"graph_state.turn_{turn_num:03d}.json"),
                "patch": str(project_dir / "patches" / f"patch_{turn_num:03d}.json"),
                "pending_merge": str(published_pending_merge_path),
                "bundle": str(published_bundle_path),
                "assembly_report": str(published_assembly_report_path),
            }
        elif args.dry_run:
            health["committed"] = {"dry_run": True}
        else:
            failed_lights = [name for name, value in health["lights"].items() if value != "GREEN"]
            reason = f"提交闸门未通过: {', '.join(failed_lights)}"
            health["summary"] = {
                "status": "BLOCKED",
                "stage": "precommit_gates",
                "reason": reason,
            }
            health["committed"] = {"committed": False, "reason": reason}

        write_json(health_report_path, health)
        print(f"[{turn_id}] DONE. health: {health['lights']}")
        return 0

    except subprocess.CalledProcessError as exc:
        # 未预见的脚本崩溃（如网络、文件缺失）
        stage = current_stage
        reason = f"{stage} 阶段脚本异常退出 (code={exc.returncode})"
        health["summary"] = quarantine_turn(project_dir, turn_id, work_dir, stage, reason, None)
        health["lights"] = {"critical_status": "RED", "lint_baseline": "RED", "queue_health": "RED", "assembly_integrity": "RED"}
        if exc.stderr:
            health["summary"]["stderr"] = exc.stderr[:2000]
        write_json(health_report_path, health)
        print(f"[{turn_id}] QUARANTINE: {reason}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
