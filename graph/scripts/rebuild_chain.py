#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Rebuild the turn chain from current turn_counter + 1 up to a target turn."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    project_id = "abu_modern"
    end_turn = 84
    session = "s001"

    project_dir = Path("graph/projects") / project_id
    graph_state_path = project_dir / "graph_state.json"
    log_path = project_dir / "rebuild_chain.log"

    gs = load_json(graph_state_path)
    start_turn = gs["turn_counter"] + 1

    with open(log_path, "a", encoding="utf-8") as log:
        log.write(
            f"Rebuilding {project_id} turns {start_turn:03d}..{end_turn:03d} "
            f"(current turn_counter={gs['turn_counter']})\n"
        )

        for turn in range(start_turn, end_turn + 1):
            turn_id = f"turn_{turn:03d}"
            progress = f"[{turn - start_turn + 1}/{end_turn - start_turn + 1}]"
            print(f"\n{'='*60}")
            print(f"[{turn_id}] Starting rebuild {progress}")
            print(f"{'='*60}")

            # Verify sequence
            gs = load_json(graph_state_path)
            expected = gs["turn_counter"] + 1
            if turn != expected:
                msg = (
                    f"Sequence mismatch: turn_counter={gs['turn_counter']}, "
                    f"expected turn_{expected:03d}, requested {turn_id}"
                )
                print(f"FATAL: {msg}", file=sys.stderr)
                log.write(f"FATAL {turn_id}: {msg}\n")
                return 1

            # Run the turn, streaming logs
            cmd = [
                sys.executable,
                "graph/scripts/run_auto_turn.py",
                project_id,
                turn_id,
                "--session", session,
                "--max-nodes", "80",
                "--warnings-non-blocking",
                "--pending-merge-non-blocking",
                "--lint-errors-non-blocking",
                "--reconcile-errors-non-blocking",
            ]
            with open(
                project_dir / "rebuild_chain.stdout.log", "a", encoding="utf-8", errors="replace"
            ) as stdout_file, open(
                project_dir / "rebuild_chain.stderr.log", "a", encoding="utf-8", errors="replace"
            ) as stderr_file:
                log.write(f"RUN {turn_id}: {' '.join(cmd)}\n")
                result = subprocess.run(cmd, stdout=stdout_file, stderr=stderr_file)

            # Check health report
            health_path = (
                project_dir / "reports" / f"{turn_id}_auto" / "turn_health_report.json"
            )
            if not health_path.exists():
                msg = f"Health report not found: {health_path}"
                print(f"FATAL: {msg}", file=sys.stderr)
                log.write(f"FATAL {turn_id}: {msg}\n")
                return 1

            health = load_json(health_path)
            lights = health.get("lights", {})
            summary = health.get("summary", {})
            status = summary.get("overall_status") or summary.get("status", "UNKNOWN")
            log.write(
                f"DONE {turn_id}: status={status} lights={json.dumps(lights)}\n"
            )

            if status not in ("GREEN", "YELLOW", "OK"):
                msg = f"Turn {turn_id} failed with status={status}"
                print(f"FATAL: {msg}", file=sys.stderr)
                log.write(f"FATAL {turn_id}: {msg}\n")
                return 1

            # Refresh counter and throttle slightly
            gs = load_json(graph_state_path)
            print(f"[{turn_id}] Completed. turn_counter is now {gs['turn_counter']}")

    print("\nAll requested turns rebuilt successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
