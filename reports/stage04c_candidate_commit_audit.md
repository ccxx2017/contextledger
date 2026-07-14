# Stage04-C Candidate Commit Audit

**Generated:** 2026-07-14T14:25:00Z
**Branch:** phase1-lifecycle-stage02

**Base commit:** d7d681e
**Evidence freeze commit:** e4dfcbf - Stage04-B2 evidence freeze: 12 reports + regression-ready evidence index
**Candidate source commit:** 2d24e01 - Stage04-C regression candidate source: shadow scripts + contracts

## Included Files (evidence freeze)

- reports/revival_feature_flag_adjudication_record.md
- reports/stage04b2_canonical_comparator_baseline.json
- reports/stage04b2_canonical_comparator_baseline_v2.json
- reports/stage04b2_canonical_comparator_comparison.md
- reports/stage04b2_fixture_determinism_check.json
- reports/stage04b2_fixture_inventory_and_replay.json
- reports/stage04b2_gate_decision_report.md
- reports/stage04b2_invalidation_metric_audit.md
- reports/stage04b2_isolation_and_commit_audit.md
- reports/stage04b2_manual_adjudication_disposition.md
- reports/stage04b2_regression_ready_evidence_index.json
- reports/stage04b2_resolution_record_audit.json

Purpose: Freeze all Stage04-B2 evidence as immutable audit trail before Stage04-C candidate source changes

## Included Files (candidate source)

- graph/projects/abu_modern/shadow_replay/scripts/benchmark_shadow_runner.py
- graph/projects/abu_modern/shadow_replay/scripts/fixture_replay_runner.py
- graph/projects/abu_modern/shadow_replay/scripts/shadow_lifecycle_adjudicator.py
- graph/projects/abu_modern/shadow_replay/scripts/shadow_resolution_adapter.py
- graph/projects/abu_modern/shadow_replay/contracts/shadow_resolution_adapter_contract.md
- graph/projects/abu_modern/shadow_replay/contracts/shadow_resolution_record_schema_v1.json

Purpose: All source code and contracts required for Stage04-C regression shadow replay

## Excluded Files

- run_scoped_outputs: graph/projects/abu_modern/shadow_replay/runs/stage04a_* and stage04b/* - safely regenerable, preserved in working tree
- design_docs: raw/projects/contextLedger/..., pack/compact - not required for regression
- stage04a_summary: stage04a_latest_summary.json - run output, safely regenerable
- stage04c_reports: reports/stage04c_* - generated during this step, not mixed into source commit
- decision_tables: contracts/shadow_adjudication_decision_table_v*.json - already tracked in base commit

## git diff --check Verification

- git diff --check: PASS (after whitespace fix in contract line 5)
- git diff --cached --check: PASS
- git diff --cached --name-status: 6 files (3 modified, 3 new)

## Dependency Manifest Verification

See reports/stage04c_candidate_dependency_manifest.json for full dependency inventory.
All 6 source/contract files required for regression are included in this commit.
12 evidence/report files are in the separate evidence freeze commit (e4dfcbf).
