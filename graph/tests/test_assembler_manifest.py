#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assembler readiness manifest 测试（工作包 C3，contracts/04_assembly.md §7）。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import assembler_manifest  # noqa: E402
from verify_preaction import verify  # noqa: E402


def make_graph_state(turn_counter: int, *, body: str = "x") -> dict:
    return {
        "turn_counter": turn_counter,
        "nodes": {
            "n_0001": {
                "node_id": "n_0001",
                "entity_ref": "alpha",
                "content": body,
                "state": "open",
                "status": "active",
            }
        },
        "edges": [],
    }


class AssemblerManifestTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)
        # 将模块的仓库根指到临时目录，实现完全隔离
        self._original_root = assembler_manifest.PROJECT_ROOT
        assembler_manifest.PROJECT_ROOT = self.root
        self.project_dir = self.root / "graph" / "projects" / "demo"
        (self.project_dir / "quarantine").mkdir(parents=True)
        (self.project_dir / "pending_merge").mkdir(parents=True)
        (self.project_dir / "reports").mkdir(parents=True)
        (self.root / "reports").mkdir(parents=True)
        self.graph_path = self.project_dir / "graph_state.json"
        self.graph_path.write_text(
            json.dumps(make_graph_state(2), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        assembler_manifest.PROJECT_ROOT = self._original_root
        self._temp.cleanup()

    def build(self, *, rejected: bool = False) -> dict:
        return assembler_manifest.build_manifest(
            project_id="demo",
            turn_id="turn_003",
            graph_state_path=self.graph_path,
            rejected=rejected,
        )

    def test_state_revision_is_turn_prefixed_content_hash(self) -> None:
        manifest = self.build()
        revision = manifest["state_revision"]
        self.assertTrue(revision.startswith("0002:"), revision)
        self.assertEqual(len(revision), 5 + 12)

    def test_state_revision_strictly_changes_across_turns(self) -> None:
        first = self.build()["state_revision"]
        self.graph_path.write_text(
            json.dumps(make_graph_state(3, body="y"), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        second = self.build()["state_revision"]
        self.assertNotEqual(first, second)
        self.assertTrue(second.startswith("0003:"))

    def test_clean_project_is_ready(self) -> None:
        manifest = self.build()
        self.assertEqual(manifest["readiness"], "ready")
        self.assertEqual(manifest["reason_codes"], [])
        self.assertEqual(manifest["unresolved_event_ids"], [])

    def test_over_budget_rejection_maps_to_blocked(self) -> None:
        manifest = self.build(rejected=True)
        self.assertEqual(manifest["readiness"], "blocked")
        self.assertIn("MUST_INCLUDE_OVER_BUDGET", manifest["reason_codes"])

    def test_unreviewed_quarantine_blocks_with_unresolved_ids(self) -> None:
        register = {
            "kind": "quarantine_register.v1",
            "items": [
                {
                    "register_key": "turn_001_failed",
                    "source_turn": 1,
                    "disposition": "unreviewed",
                    "reason": "reconcile 失败且重试后仍无法通过",
                }
            ],
        }
        (self.project_dir / "quarantine" / "quarantine_register.json").write_text(
            json.dumps(register, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        manifest = self.build()
        self.assertEqual(manifest["readiness"], "blocked")
        self.assertIn("QUARANTINE_NONEMPTY", manifest["reason_codes"])
        self.assertEqual(manifest["unresolved_event_ids"][0]["register_key"], "turn_001_failed")

    def test_reviewed_quarantine_does_not_block(self) -> None:
        register = {
            "kind": "quarantine_register.v1",
            "items": [
                {
                    "register_key": "turn_001_failed",
                    "source_turn": 1,
                    "disposition": "requeued",
                }
            ],
        }
        (self.project_dir / "quarantine" / "quarantine_register.json").write_text(
            json.dumps(register, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        manifest = self.build()
        self.assertEqual(manifest["readiness"], "ready")

    def test_overdue_pending_merge_degrades(self) -> None:
        register = {
            "kind": "pending_merge_register.v1",
            "items": [
                {
                    "register_key": "k1",
                    "remediation_status": "tracked",
                    "escalate_on_or_after_turn": 1,
                }
            ],
        }
        (self.project_dir / "pending_merge" / "pending_merge_register.json").write_text(
            json.dumps(register, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        manifest = self.build()
        self.assertEqual(manifest["readiness"], "degraded")
        self.assertIn("PENDING_MERGE_OVERDUE", manifest["reason_codes"])

    def test_reason_codes_stay_in_closed_vocabulary(self) -> None:
        # 同时注入多种风险，断言所有产出 code 都在封闭词表内
        (self.project_dir / "pending_merge" / "pending_merge_register.json").write_text(
            json.dumps(
                {
                    "kind": "pending_merge_register.v1",
                    "items": [{"remediation_status": "tracked", "escalate_on_or_after_turn": 1}],
                }
            ),
            encoding="utf-8",
        )
        (self.root / "reports" / "current_graph_lint_report.json").write_text(
            json.dumps({"warnings": [{"level": "warning", "code": "SOME_WARN"}]}),
            encoding="utf-8",
        )
        manifest = self.build()
        for code in manifest["reason_codes"]:
            self.assertIn(code, assembler_manifest.KNOWN_REASON_CODES)

    def test_bypass_published_blocks(self) -> None:
        health_dir = self.project_dir / "reports" / "turn_003_auto"
        health_dir.mkdir(parents=True)
        (health_dir / "turn_health_report.json").write_text(
            json.dumps({"published_with_bypass": True}), encoding="utf-8"
        )
        manifest = self.build()
        self.assertEqual(manifest["readiness"], "blocked")
        self.assertIn("PUBLISHED_WITH_BYPASS", manifest["reason_codes"])


class VerifyPreactionTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)
        self.project_dir = self.root / "graph" / "projects" / "demo"
        self.project_dir.mkdir(parents=True)
        self.graph_path = self.project_dir / "graph_state.json"
        self.graph_path.write_text(
            json.dumps(make_graph_state(5), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        self._original_root = sys.modules["verify_preaction"].PROJECT_ROOT
        import verify_preaction

        verify_preaction.PROJECT_ROOT = self.root

    def tearDown(self) -> None:
        import verify_preaction

        verify_preaction.PROJECT_ROOT = self._original_root
        self._temp.cleanup()

    def current_revision(self) -> str:
        import hashlib

        h = hashlib.sha256()
        h.update(self.graph_path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n"))
        return f"0005:{h.hexdigest()[:12]}"

    def test_current_revision_and_active_include_pass(self) -> None:
        ok, payload = verify(
            project_id="demo",
            expected_revision=self.current_revision(),
            must_include=["n_0001"],
            premises=["alpha=open"],
        )
        self.assertTrue(ok, payload)
        self.assertEqual(payload["reason_codes"], [])

    def test_stale_revision_fails_with_stale_code(self) -> None:
        ok, payload = verify(
            project_id="demo",
            expected_revision="0001:aaaaaaaaaaaa",
            must_include=[],
            premises=[],
        )
        self.assertFalse(ok)
        self.assertIn("STATE_REVISION_STALE", payload["reason_codes"])

    def test_violated_premise_fails_with_premise_code(self) -> None:
        ok, payload = verify(
            project_id="demo",
            expected_revision=self.current_revision(),
            must_include=[],
            premises=["alpha=closed"],
        )
        self.assertFalse(ok)
        self.assertIn("PREMISE_VIOLATED", payload["reason_codes"])

    def test_superseded_must_include_fails(self) -> None:
        graph = make_graph_state(6)
        graph["nodes"]["n_0001"]["status"] = "superseded"
        self.graph_path.write_text(json.dumps(graph), encoding="utf-8")
        ok, payload = verify(
            project_id="demo",
            expected_revision=self.current_revision(),
            must_include=["n_0001"],
            premises=[],
        )
        self.assertFalse(ok)
        self.assertIn("PREMISE_VIOLATED", payload["reason_codes"])


if __name__ == "__main__":
    unittest.main()
