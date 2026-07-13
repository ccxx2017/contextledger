#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate Stage04-A report from fixture replay summary and benchmark audit."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SHADOW_ROOT = SCRIPT_DIR.parent
REPO_ROOT = Path(__file__).resolve().parents[5]

SUMMARY_PATH = SHADOW_ROOT / "runs" / "stage04a_latest_summary.json"
AUDIT_PATH = REPO_ROOT / "graph" / "projects" / "abu_modern" / "benchmark" / "v1_freeze" / "split_audit_report.json"
REPORT_PATH = REPO_ROOT / "reports" / "stage04a_report.md"


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def shorten_hash(h: str) -> str:
    return h[:16] if isinstance(h, str) else "n/a"


def generate_report() -> str:
    summary = load_json(SUMMARY_PATH)
    audit = load_json(AUDIT_PATH)
    now = datetime.now(timezone.utc)

    lines: list[str] = []
    lines.append("# Stage04-A Report")
    lines.append("")
    lines.append(f"**Generated:** {now.strftime('%Y-%m-%dT%H:%M:%SZ')}")
    lines.append(f"**Branch:** `phase1-lifecycle-stage02`")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    pass_count = sum(1 for s in summary["summaries"] if s["gate_decision"] == "PASS")
    total_fixtures = len(summary["summaries"])
    all_deterministic = all(s["deterministic"] for s in summary["summaries"])
    lines.append(f"- Lifecycle fixtures replayed: {total_fixtures}")
    lines.append(f"- Fixtures passing: {pass_count}/{total_fixtures}")
    lines.append(f"- All replays deterministic: {all_deterministic}")
    lines.append(f"- Benchmark v1 split integrity OK: {audit.get('split_integrity_ok', False)}")
    lines.append(f"- Blind holdout isolated from development: {audit.get('conclusion', {}).get('blind_holdout_isolated_from_development', False)}")
    lines.append(f"- Main-chain replacement approved: **No**")
    lines.append("")
    lines.append("This report documents shadow lifecycle adjudication replay under isolation.")
    lines.append("No formal main-chain files were modified.")
    lines.append("")

    lines.append("## Implementation Contract")
    lines.append("")
    lines.append("See [graph/projects/abu_modern/shadow_replay/stage04a_implementation_contract.md](graph/projects/abu_modern/shadow_replay/stage04a_implementation_contract.md).")
    lines.append("")

    lines.append("## Per-Fixture Results")
    lines.append("")
    lines.append("| Fixture | Category | Gate | Deterministic | State Hash | Bundle Hash | Run Dir |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for s in summary["summaries"]:
        fixture_id = s["fixture_id"]
        # Load config to get hashes
        run_dir = REPO_ROOT / s["run_dir"]
        config = load_json(run_dir / "config.json")
        run1 = config["run1"]
        lines.append(
            f"| {fixture_id} | {run1['category']} | {s['gate_decision']} | {s['deterministic']} | "
            f"{shorten_hash(run1['final_graph_state_hash'])} | {shorten_hash(run1['final_bundle_hash'])} | `{s['run_dir']}` |"
        )
    lines.append("")

    lines.append("### Checkpoint Details")
    lines.append("")
    for s in summary["summaries"]:
        fixture_id = s["fixture_id"]
        run_dir = REPO_ROOT / s["run_dir"]
        diff_report = load_json(run_dir / "diff_report.json")
        config = load_json(run_dir / "config.json")
        lines.append(f"#### {fixture_id}")
        lines.append("")
        lines.append(f"- Input hash (fixture): `{config['fixture_sha256'][:16]}`")
        lines.append(f"- Runtime fingerprint: shadow adjudicator `{config['runtime_fingerprint']['shadow_scripts']['shadow_lifecycle_adjudicator.py'][:16]}...`")
        lines.append(f"- Patch hash: `{diff_report['patch_hash'][:16]}`")
        lines.append(f"- Final state hash: `{diff_report['final_graph_state_hash'][:16]}`")
        lines.append(f"- Final bundle hash: `{diff_report['final_bundle_hash'][:16]}`")
        lines.append(f"- Quarantine: {diff_report['quarantine']}")
        lines.append("")
        for cp in diff_report["checkpoints"]:
            lines.append(f"**Checkpoint `{cp['checkpoint_id']}`** (after `{cp['after_event_id']}`)")
            lines.append(f"- State hash: `{cp['graph_state_hash'][:16]}`")
            lines.append(f"- Bundle hash: `{cp['bundle_hash'][:16]}`")
            lines.append(f"- Diffs: total={cp['diff_counts']['total']}, blockers={cp['diff_counts']['blocker']}, "
                         f"regressions={cp['diff_counts']['regression']}, unexplained={cp['diff_counts']['unexplained']}")
            if cp["diffs"]:
                for d in cp["diffs"]:
                    lines.append(f"  - [{d['classification']}] {d['kind']}: {d['rationale']} (blocking={d['blocking']})")
            else:
                lines.append("  - No diffs.")
            lines.append("")

    lines.append("## Benchmark v1 Split Audit")
    lines.append("")
    lines.append(f"- Freeze manifest hash: `{audit['freeze_manifest_sha256'][:16]}`")
    lines.append(f"- Total cases: {audit['total_cases']}")
    lines.append(f"- Duplicated cases: {audit['duplicated_cases']}")
    lines.append("")
    lines.append("### Mechanism Distribution per Split")
    lines.append("")
    lines.append("| Split | Distribution |")
    lines.append("| --- | --- |")
    for split_name, dist in audit["mechanism_distribution"].items():
        dist_str = ", ".join(f"{k}={v}" for k, v in sorted(dist.items()))
        lines.append(f"| {split_name} | {dist_str} |")
    lines.append("")
    lines.append("### Blind Holdout Leakage Check")
    lines.append("")
    for item in audit["template_alias_leakage"]["per_case"]:
        score = item["leakage_score"]
        lines.append(f"- `{item['case_id']}`: overlap_ratio={score['overlap_ratio']}, overlap_count={score['overlap_count']}")
    lines.append("")

    lines.append("## Main-Chain Replacement Status")
    lines.append("")
    lines.append("**Not approved.** Stage04-A only proves that the shadow kernel can replay fixtures")
    lines.append("deterministically under isolation. The following remain required before any")
    lines.append("main-chain candidate switch:")
    lines.append("")
    lines.append("1. Full benchmark v1 regression and blind-holdout evaluation against the shadow chain.")
    lines.append("2. Demonstrated semantic benefit over the current main chain on holdout cases.")
    lines.append("3. `must_include_recall` >= D1 baseline.")
    lines.append("4. Zero critical false invalidation or all such cases quarantined.")
    lines.append("5. No `blocker` or `unexplained` diffs unresolved.")
    lines.append("6. Confirmation that shadow outputs did not contaminate `graph/projects/abu_modern/graph_state.json`.")
    lines.append("")

    lines.append("## Unresolved Risks")
    lines.append("")
    lines.append("- Shadow adjudicator is a heuristic proof-of-concept; it has not been validated against the full benchmark.")
    lines.append("- Alias resolution currently uses a simplified substring matcher, not the production resolver.")
    lines.append("- Benchmark v1 blind holdout has not yet been executed through the shadow chain.")
    lines.append("")

    lines.append("## Next Step")
    lines.append("")
    lines.append("Proceed to Stage04-B: run the full benchmark v1 splits through the shadow chain,")
    lines.append("produce per-split diff reports, and evaluate against the pre-registered safety red lines.")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    report = generate_report()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
