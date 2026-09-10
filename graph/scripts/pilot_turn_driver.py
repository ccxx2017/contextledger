#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pilot 逐轮 CL 驱动（P1/P2 开发轨迹的 CL-V0 臂引擎）。

每轮宿主会话结束后运行一次：
    raw 组装（用户消息 + 工具摘要）→ slice → Extractor(v2) → sanitize
    → reconcile → apply → lint → current_states 导出 → manifest 重生成
    → 宿主控制文件刷新（expected_state_revision 指向最新装配）

用法：
    python graph/scripts/pilot_turn_driver.py \
        --cl-project pilot_p1 --turn-num 1 \
        --user-text "任务启动：..." \
        --trace "D:/.../traces/p1/cl_v0/turn_001.jsonl" \
        --control-file "D:/.../pilot/p1/task-project/.opencode/cl_v0.json" \
        --env-file graph/projects/pilot_p1/pilot_p1.env
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = PROJECT_ROOT / "graph" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import apply_patch as apply_mod  # noqa: E402
import reconcile_patch as reconcile_mod  # noqa: E402

V2_PROMPT = PROJECT_ROOT / "graph" / "prompts" / "extractor_system_lifecycle_v2.md"


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [sys.executable, *cmd], cwd=PROJECT_ROOT, capture_output=True,
        text=True, encoding="utf-8", errors="replace",
    )
    if check and result.returncode != 0:
        stdout_tail = (result.stdout or "")[-800:]
        stderr_tail = (result.stderr or "")[-800:]
        raise RuntimeError(f"步骤失败(rc={result.returncode}): {' '.join(cmd)}\nstdout_tail={stdout_tail}\nstderr_tail={stderr_tail}")
    return result


def load_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def write_json(p: Path, obj: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def revision_of(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n"))
    data = json.loads(p.read_text(encoding="utf-8"))
    return f"{int(data.get('turn_counter', 0)):04d}:{h.hexdigest()[:12]}"


def tool_summary_from_trace(trace_path: Path | None) -> list[str]:
    if not trace_path or not trace_path.exists():
        return []
    lines = []
    for raw_line in trace_path.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if e.get("type") == "tool_execute_before":
            tool = (e.get("payload") or {}).get("tool")
            args = json.dumps((e.get("payload") or {}).get("args"), ensure_ascii=False)[:200]
            lines.append(f"- 工具调用 {tool}: {args}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cl-project", required=True)
    parser.add_argument("--turn-num", type=int, required=True)
    parser.add_argument("--user-text", required=True)
    parser.add_argument("--trace", help="本轮宿主 trace JSONL（用于工具摘要进 raw）")
    parser.add_argument("--control-file", help="宿主侧 cl_v0.json 控制文件路径（每轮刷新）")
    parser.add_argument("--env-file", default="env")
    parser.add_argument("--skip-cl-call", action="store_true", help="baseline 臂离线模式占位（本轮只建 raw 不调 LLM）")
    parser.add_argument("--reuse-existing-patch", action="store_true", help="复用已抽取的 patch（状态归一化重处理用）")
    parser.add_argument("--agents-md", help="AGENTS.md 供给通道路径（每轮刷新 CL 当前态）")
    args = parser.parse_args()

    project_dir = PROJECT_ROOT / "graph" / "projects" / args.cl_project
    turn_id = f"turn_{args.turn_num:03d}"
    work_dir = project_dir / "reports" / f"{turn_id}_pilot"
    work_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "patches").mkdir(exist_ok=True)
    (project_dir / "run").mkdir(exist_ok=True)
    raw_session = PROJECT_ROOT / "raw" / "projects" / args.cl_project / "s001"
    raw_session.mkdir(parents=True, exist_ok=True)

    # 1. 组装 raw（本轮时间 + 用户消息 + 工具摘要）
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    raw_lines = [f"# {turn_id}", "", f"【本轮时间】{now}", "", "【用户】", args.user_text, ""]
    tool_lines = tool_summary_from_trace(Path(args.trace) if args.trace else None)
    if tool_lines:
        raw_lines += ["【本轮工具活动摘要】"] + tool_lines + [""]
    raw_path = raw_session / f"{turn_id}.md"
    raw_path.write_text("\n".join(raw_lines), encoding="utf-8")

    state_path = project_dir / "graph_state.json"
    base_graph = state_path if state_path.exists() else project_dir / "graph_state.seed.json"

    if args.skip_cl_call:
        print(f"[{turn_id}] raw 已组装（skip-cl-call），未调 Extractor。")
        return 0

    # 2-5. 抽取链路（--reuse-existing-patch 时直接复用上一轮已物化的 after 图）
    slice_path = work_dir / f"slice_{args.turn_num:03d}.json"
    patch_path = project_dir / "patches" / f"patch_{args.turn_num:03d}.json"
    after_path = work_dir / f"graph_state.after_{turn_id}.json"

    if args.reuse_existing_patch:
        if not after_path.exists():
            print(f"[{turn_id}] reuse 失败：{after_path} 不存在（首轮未跑过）")
            return 1
    else:
        run(["graph/scripts/build_graph_slice.py",
             "--graph", str(base_graph), "--turn", str(raw_path),
             "--turn-id", str(args.turn_num), "--out", str(slice_path)])

        # P4 重试回路（镜像 run_auto_turn）：reconcile 失败 → 重新采样，最多 3 次
        MAX_RETRY = 3
        report = None
        patch_path = None
        for attempt in range(1, MAX_RETRY + 1):
            retry_tag = "" if attempt == 1 else f".retry_{attempt - 1}"
            patch_path = project_dir / "patches" / f"patch_{args.turn_num:03d}{retry_tag}.json"
            run(["graph/scripts/invoke_extractor.py",
                 "--project-id", args.cl_project, "--turn-id", turn_id,
                 "--slice", str(slice_path), "--turn", str(raw_path),
                 "--system", str(V2_PROMPT),
                 "--env-file", args.env_file,
                 "--out", str(patch_path),
                 "--raw-response-out", str(work_dir / f"extractor_raw.{turn_id}{retry_tag}.txt"),
                 "--prompt-out", str(work_dir / f"prompt.{turn_id}{retry_tag}.json"),
                 "--meta-out", str(work_dir / f"extractor_meta.{turn_id}{retry_tag}.json")])
            run(["graph/scripts/sanitize_patch_entity_refs.py",
                 "--patch", str(patch_path), "--graph", str(base_graph), "--out", str(patch_path)])
            run(["graph/scripts/reconcile_patch.py", str(base_graph), str(patch_path),
                 "--out", str(work_dir / f"reconcile_{turn_id}.json")], check=False)
            report = load_json(work_dir / f"reconcile_{turn_id}.json")
            if report.get("ok"):
                break
            print(f"[{turn_id}] reconcile FAIL（第 {attempt}/{MAX_RETRY} 次采样）：{len(report.get('errors') or [])} errors")
        else:
            # 重试耗尽：隔离语义（不推进主图），登记 + AGENTS.md 带警告刷新 + manifest 重生成
            quarantine_dir = project_dir / "quarantine"
            quarantine_dir.mkdir(exist_ok=True)
            write_json(quarantine_dir / f"{turn_id}_failed.json", {
                "turn_id": turn_id, "stage": "reconcile_patch",
                "reason": f"reconcile 失败且重试 {MAX_RETRY} 次后仍无法通过",
                "errors": ((report or {}).get("errors") or [])[:10],
            })
            run(["graph/scripts/quarantine_register.py", "sync", "--project-id", args.cl_project])
            # 隔离时主图未推进：以 base_graph 重建上一轮的当前态
            current_states = {}
            try:
                base_data = load_json(base_graph)
                for node in base_data.get("nodes", {}).values():
                    if (node.get("status") or "active") == "active" and node.get("entity_ref"):
                        state = node.get("state")
                        if state and str(state).strip().lower() not in {"unknown", "null"}:
                            key = f"{node['entity_ref']}@{node['state_slot']}" if node.get("state_slot") else str(node["entity_ref"])
                            current_states[key] = str(state)
            except Exception:
                pass
            if args.agents_md:
                agent_lines = ["# CL-PILOT-STATE", ""]
                for key, st in current_states.items():
                    agent_lines.append(f"{key} = {st}")
                agent_lines += [
                    "",
                    f"【CL 警告】{turn_id} 未通过机械裁定（隔离中）：上述当前态可能缺失本轮变更，请勿据其断言本轮事件。",
                    f"【CL 就绪度】blocked（QUARANTINE_NONEMPTY）",
                    f"【CL 版本】{revision_of(state_path) if state_path.exists() else 'unknown'}",
                ]
                Path(args.agents_md).write_text("\n".join(agent_lines) + "\n", encoding="utf-8")
            run(["graph/scripts/assembler_manifest.py",
                 "--project-id", args.cl_project, "--turn-id", turn_id,
                 "--out", str(project_dir / "run" / f"assembler_manifest.{turn_id}.json")])
            print(f"[{turn_id}] QUARANTINE：本轮未裁定，主图未推进；AGENTS.md 已带警告刷新，manifest=blocked")
            return 1

        run(["graph/scripts/apply_patch.py",
             "--graph", str(base_graph), "--patch", str(patch_path),
             "--expected-turn", turn_id, "--out", str(after_path)])
        run(["graph/scripts/graph_lint.py", str(after_path), "--out", str(work_dir / f"lint_{turn_id}.json")],
            check=False)

    # 6. 提交 + 状态归一化 + 导出 current_states + manifest
    graph_data = load_json(after_path)
    # 兼容规则（contracts/03 §当前态：缺 status 视为 active）：v1 契约下 extractor
    # 不输出 status，新节点在此机械归一为 active（superseded_marks 已由 apply 写入）。
    for node in graph_data.get("nodes", {}).values():
        if not node.get("status"):
            node["status"] = "active"
    state_path.write_text(json.dumps(graph_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (project_dir / "run" / f"graph_state.{turn_id}.json").write_text(
        json.dumps(graph_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    current_states: dict[str, str] = {}
    for node in graph_data.get("nodes", {}).values():
        if node.get("status") == "active" and node.get("entity_ref"):
            state = node.get("state")
            if not state or str(state).strip().lower() in {"unknown", "null"}:
                continue  # 无状态声明的节点（如 Fact）不构成状态断言
            entity = str(node["entity_ref"])
            slot = node.get("state_slot")
            key = f"{entity}@{slot}" if slot else entity
            current_states[key] = str(state)
    states_path = project_dir / "run" / "current_states.json"
    write_json(states_path, {
        "kind": "current_states.v1",
        "as_of_turn": turn_id,
        "states": current_states,
    })

    # 7. manifest（用主模块构建，落 run/）
    import assembler_manifest
    manifest = assembler_manifest.build_manifest(
        project_id=args.cl_project, turn_id=turn_id, graph_state_path=state_path)
    manifest_path = project_dir / "run" / f"assembler_manifest.{turn_id}.json"
    write_json(manifest_path, manifest)

    # 7.5 AGENTS.md 供给通道刷新（1.18.29 实证：experimental hook 变异被丢弃，
    # 文件通道是唯一有效注入面；首载与中途刷新均已验证）
    if args.agents_md:
        agent_lines = ["# CL-PILOT-STATE", ""]
        for key, st in current_states.items():
            agent_lines.append(f"{key} = {st}")
        agent_lines += [
            "",
            f"【CL 就绪度】{manifest['readiness']}"
            + (f"（{', '.join(manifest['reason_codes'])}）" if manifest["reason_codes"] else ""),
            f"【CL 版本】{manifest['state_revision']}",
            "【CL 使用规则】以上为经裁定机制维护的当前态；与其冲突的早期记忆应以此为准。",
        ]
        Path(args.agents_md).write_text("\n".join(agent_lines) + "\n", encoding="utf-8")

    # 8. 刷新宿主控制文件（每轮重新装配）
    if args.control_file:
        control_path = Path(args.control_file)
        control = {}
        if control_path.exists():
            control = load_json(control_path)
        control.update({
            "cl_home": str(PROJECT_ROOT).replace("\\", "/"),
            "cl_project": args.cl_project,
            "expected_state_revision": revision_of(state_path),
            "manifest_path": str(manifest_path).replace("\\", "/"),
            "current_states_path": str(states_path).replace("\\", "/"),
        })
        write_json(control_path, control)

    print(f"[{turn_id}] CL 轮完成：nodes={len(graph_data.get('nodes', {}))} "
          f"states={current_states} revision={control.get('expected_state_revision') if args.control_file else revision_of(state_path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
