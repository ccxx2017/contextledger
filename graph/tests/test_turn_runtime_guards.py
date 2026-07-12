#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from run_auto_turn import audit_committed_history  # noqa: E402
from sync_pending_merge_register import sync_register  # noqa: E402


class TurnRuntimeGuardsTest(unittest.TestCase):
    def test_history_audit_requires_every_committed_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project_dir = root / "graph" / "projects" / "demo"
            raw_dir = root / "raw" / "projects" / "demo" / "s001"
            (project_dir / "patches").mkdir(parents=True)
            (project_dir / "run").mkdir(parents=True)
            raw_dir.mkdir(parents=True)

            for turn in (1, 2):
                turn_id = f"turn_{turn:03d}"
                (raw_dir / f"{turn_id}.md").write_text("raw", encoding="utf-8")
            (project_dir / "patches" / "patch_001.json").write_text("{}", encoding="utf-8")
            (project_dir / "run" / "graph_state.turn_001.json").write_text("{}", encoding="utf-8")

            audit = audit_committed_history(
                project_dir=project_dir,
                raw_session_dir=raw_dir,
                committed_turn=2,
            )

            self.assertFalse(audit["ok"])
            self.assertEqual(audit["missing_patches"], ["turn_002"])
            self.assertEqual(audit["missing_snapshots"], ["turn_002"])
            self.assertEqual(audit["missing_raw"], [])

    def test_pending_merge_register_has_stable_escalation(self) -> None:
        pending = {
            "turn_id": "turn_007",
            "items": [
                {
                    "new_node_id": "n_0007",
                    "raw_entity_ref": "order-router",
                    "match_confidence": 0.61,
                    "candidate_aliases": [
                        {
                            "canonical_entity_ref": "order_router",
                            "evidence": ["token_overlap"],
                        }
                    ],
                }
            ],
        }
        register, report = sync_register(
            {"kind": "pending_merge_register.v1", "items": []},
            pending,
            current_turn=7,
            escalate_after_turns=5,
        )

        self.assertEqual(report["summary"]["added"], 1)
        entry = register["items"][0]
        self.assertEqual(entry["blocked_turn"], 7)
        self.assertEqual(entry["escalate_on_or_after_turn"], 12)
        self.assertEqual(entry["remediation_status"], "tracked")

        refreshed, refresh_report = sync_register(
            register,
            pending,
            current_turn=8,
            escalate_after_turns=5,
        )
        self.assertEqual(refresh_report["summary"]["refreshed"], 1)
        self.assertEqual(refreshed["items"][0]["blocked_turn"], 7)
        self.assertEqual(refreshed["items"][0]["last_seen_turn"], 8)


if __name__ == "__main__":
    unittest.main()
