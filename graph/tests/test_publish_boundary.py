#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发布边界测试（工作包 C4，评审 §工作包C：apply→lint 顺序此前无测试保护）。

用桩 Extractor（CL_EXTRACTOR_SCRIPT 环境变量接缝，工作包 C1c 引入）端到端驱动
run_auto_turn，断言两条铁律：

  A. lint 未全绿时：候选态不得发布——权威 graph_state.json 逐字节不变、
     patches/ 无新条目、scratch 候选产物存在、health 判 BLOCKED；
  B. 显式 --unsafe-rebuild-mode 绕过时：允许发布，但 turn_health_report 必须
     记录 published_with_bypass=true，且发布的 assembler_manifest 判 blocked。
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ID = "_pub_boundary_test"
SESSION = "s001"
TURN_ID = "turn_002"

STUB_PATCH_KINDS = {
    # 与 active n_0001 同 entity 同 state + invalidates 边但不 supersede
    # → reconcile 放行，lint 报 INVALIDATES_TARGET_NOT_SUPERSEDED
    # turn_id 必须是数字（真实 Extractor 产物约定，apply_patch 据此推进计数器）
    "lint_fail": {
        "task_id": "stub",
        "turn_id": 2,
        "new_nodes": [
            {
                "node_id": "n_9001",
                "entity_ref": "alpha",
                "content": "dup state claim from stub",
                "node_type": "Fact",
                "state": "open",
                "priority": "must_include",
            }
        ],
        "new_edges": [
            {"source": "n_9001", "target": "n_0001", "relation": "invalidates"}
        ],
        "superseded_nodes": [],
    },
    # 干净新节点：全绿可发布（供绕过场景的装配完整性绿灯）
    "clean": {
        "task_id": "stub",
        "turn_id": 2,
        "new_nodes": [
            {
                "node_id": "n_9002",
                "entity_ref": "beta",
                "content": "clean claim from stub",
                "node_type": "Fact",
                "state": "open",
                "priority": "must_include",
            }
        ],
        "new_edges": [],
        "superseded_nodes": [],
    },
}

STUB_SOURCE = '''
import argparse, json, sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--out")
parser.add_argument("--raw-response-out")
parser.add_argument("--prompt-out")
parser.add_argument("--meta-out")
parser.add_argument("--system")
parser.add_argument("--slice")
parser.add_argument("--turn")
parser.add_argument("--project-id")
parser.add_argument("--turn-id")
args, _ = parser.parse_known_args()

kind = __import__("os").environ.get("CL_STUB_PATCH", "clean")
patch = json.loads(Path(__import__("os").environ["CL_STUB_PATCH_FILE"]).read_text(encoding="utf-8"))

Path(args.out).parent.mkdir(parents=True, exist_ok=True)
Path(args.out).write_text(json.dumps(patch, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
Path(args.raw_response_out).parent.mkdir(parents=True, exist_ok=True)
Path(args.raw_response_out).write_text("```json\\n" + json.dumps(patch) + "\\n```\\n", encoding="utf-8")
Path(args.prompt_out).parent.mkdir(parents=True, exist_ok=True)
Path(args.prompt_out).write_text(json.dumps({"base_url": "stub", "model": "stub", "messages": []}) + "\\n", encoding="utf-8")
Path(args.meta_out).parent.mkdir(parents=True, exist_ok=True)
Path(args.meta_out).write_text(json.dumps({"base_url": "stub", "model": "stub-stub", "env_file": "stub", "api_key_present": True}) + "\\n", encoding="utf-8")
print("stub extractor wrote patch")
'''


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PublishBoundaryTest(unittest.TestCase):
    project_dir: Path
    env: dict
    _temp: tempfile.TemporaryDirectory

    @classmethod
    def setUpClass(cls) -> None:
        cls._temp = tempfile.TemporaryDirectory()
        temp_root = Path(cls._temp.name)
        cls.project_dir = REPO_ROOT / "graph" / "projects" / PROJECT_ID
        if cls.project_dir.exists():
            shutil.rmtree(cls.project_dir)
        (cls.project_dir / "run").mkdir(parents=True)
        (cls.project_dir / "patches").mkdir(parents=True)
        (cls.project_dir / "pending_merge").mkdir(parents=True)
        (cls.project_dir / "quarantine").mkdir(parents=True)
        (cls.project_dir / "reports").mkdir(parents=True)
        raw_dir = REPO_ROOT / "raw" / "projects" / PROJECT_ID / SESSION
        if raw_dir.exists():
            shutil.rmtree(raw_dir)
        raw_dir.mkdir(parents=True)
        (raw_dir / f"{TURN_ID}.md").write_text(
            "# turn_002\n\nstub raw turn for publish boundary test\n", encoding="utf-8"
        )
        # 提交历史审计（1..N 三件套存在性）：turn_001 的 raw / patch / 快照
        (raw_dir / "turn_001.md").write_text(
            "# turn_001\n\nseed history\n", encoding="utf-8"
        )
        (cls.project_dir / "patches" / "patch_001.json").write_text("{}", encoding="utf-8")

        seed_graph = {
            "turn_counter": 1,
            "nodes": {
                "n_0001": {
                    "node_id": "n_0001",
                    "entity_ref": "alpha",
                    "content": "existing active claim",
                    "node_type": "Fact",
                    "state": "open",
                    "status": "active",
                    "created_turn": 1,
                }
            },
            "edges": [],
        }
        (cls.project_dir / "graph_state.json").write_text(
            json.dumps(seed_graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        # 快照必须是合法图（diff_lint_reports 会读其 turn_counter 做时序校验）
        (cls.project_dir / "run" / "graph_state.turn_001.json").write_text(
            json.dumps(seed_graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (cls.project_dir / "reports" / "lint_baseline.json").write_text(
            json.dumps({"kind": "lint_baseline.phase1_prep.v1", "errors": [], "warnings": []}) + "\n",
            encoding="utf-8",
        )

        cls.patch_files: dict[str, Path] = {}
        for kind, patch in STUB_PATCH_KINDS.items():
            pf = temp_root / f"patch_{kind}.json"
            pf.write_text(json.dumps(patch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            cls.patch_files[kind] = pf

        cls.stub_script = temp_root / "stub_extractor.py"
        cls.stub_script.write_text(STUB_SOURCE, encoding="utf-8")

        cls.env = dict(os.environ)
        cls.env["CL_EXTRACTOR_SCRIPT"] = str(cls.stub_script)
        cls.env["CL_STUB_PATCH_FILE"] = str(cls.patch_files["lint_fail"])
        cls.env["CL_STUB_PATCH"] = "lint_fail"

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.project_dir.exists():
            shutil.rmtree(cls.project_dir)
        raw_dir = REPO_ROOT / "raw" / "projects" / PROJECT_ID
        if raw_dir.exists():
            shutil.rmtree(raw_dir)
        cls._temp.cleanup()

    def run_turn(self, *extra_args: str) -> dict:
        result = subprocess.run(
            [
                sys.executable, "graph/scripts/run_auto_turn.py",
                PROJECT_ID, TURN_ID,
                "--session", SESSION,
                *extra_args,
            ],
            cwd=REPO_ROOT,
            env=self.env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        health_path = self.project_dir / "reports" / f"{TURN_ID}_auto" / "turn_health_report.json"
        self.assertTrue(health_path.exists(), f"health report missing; stderr={result.stderr[-2000:]}")
        health = json.loads(health_path.read_text(encoding="utf-8"))
        health["_returncode"] = result.returncode
        health["_stderr_tail"] = result.stderr[-2000:]
        return health

    def test_1_lint_failure_blocks_publication(self) -> None:
        graph_state = self.project_dir / "graph_state.json"
        before_sha = sha256_file(graph_state)

        health = self.run_turn()

        # 候选态不得发布：权威图逐字节不变
        self.assertEqual(
            sha256_file(graph_state), before_sha,
            "lint 未全绿时权威 graph_state.json 不得被改写",
        )
        # patches/ 无新条目
        self.assertFalse(
            (self.project_dir / "patches" / "patch_002.json").exists(),
            "lint 未全绿时不得发布 patch",
        )
        # run/ 无新快照与产物
        self.assertFalse((self.project_dir / "run" / "graph_state.turn_002.json").exists())
        # scratch 候选产物存在（apply 确实发生过，只是未发布）
        scratch = self.project_dir / "reports" / f"{TURN_ID}_auto" / "graph_state.after_{0}.json".format(TURN_ID)
        self.assertTrue(scratch.exists(), "候选态应保留在 scratch 供排障")
        # health 判 BLOCKED，且失败在提交闸门
        self.assertEqual(health["summary"]["status"], "BLOCKED")
        self.assertEqual(health["summary"].get("stage"), "precommit_gates")
        self.assertNotIn("published_with_bypass", health)

    def test_2_bypass_mode_publishes_with_marked_blocked_manifest(self) -> None:
        health = self.run_turn(
            "--unsafe-rebuild-mode",
            "--lint-errors-non-blocking",
        )

        # 绕过发布必须留痕
        self.assertTrue(health.get("published_with_bypass"), "绕过闸门发布必须记录 published_with_bypass")
        self.assertIn("--lint-errors-non-blocking", health["summary"].get("bypass_flags", []))
        # 权威产物确实发布了
        self.assertTrue((self.project_dir / "patches" / "patch_002.json").exists())
        self.assertTrue((self.project_dir / "run" / "graph_state.turn_002.json").exists())
        # 发布的 assembler_manifest 判 blocked 且带封闭词表 code
        manifest_path = self.project_dir / "run" / f"assembler_manifest.{TURN_ID}.json"
        self.assertTrue(manifest_path.exists(), "发布时必须随附 assembler_manifest")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["readiness"], "blocked")
        self.assertIn("PUBLISHED_WITH_BYPASS", manifest["reason_codes"])

    def test_3_bypass_flags_require_master_switch(self) -> None:
        result = subprocess.run(
            [
                sys.executable, "graph/scripts/run_auto_turn.py",
                PROJECT_ID, TURN_ID,
                "--session", SESSION,
                "--lint-errors-non-blocking",
            ],
            cwd=REPO_ROOT,
            env=self.env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--unsafe-rebuild-mode", result.stderr)


if __name__ == "__main__":
    unittest.main()
