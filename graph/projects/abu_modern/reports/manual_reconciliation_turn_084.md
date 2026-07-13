# Manual Batch Reconciliation Report: turn_084 pending_merge backlog

**Date:** 2026-07-13T10:58:02.376790
**Operation:** One-time batch resolution of historical pending_merge items from turns 020-084.
**Reason:** Reduce pending_merge queue pressure before continuing to turn_085 (when raw input becomes available).

## Backups

- `graph\projects\abu_modern\pending_merge\pending_merge_register.json.batch_reconcile.bak`
- `graph\projects\abu_modern\run\graph_state.turn_084.json.batch_reconcile.bak`

## Summary

| Category | Count |
|----------|-------|
| Total items before | 59 |
| MERGE (high confidence) | 5 |
| LIKELY_MERGE (medium-high confidence) | 5 |
| KEEP_DISTINCT (low confidence) | 14 |
| Remaining REVIEW (still tracked) | 35 |
| Total items after | 59 |

| Metric | Before | After |
|--------|--------|-------|
| Overdue items at turn_084 | 54 | 33 |
| Resolved items | 0 | 24 |
| Graph nodes marked superseded by batch | 0 | 10 |

## Graph State Changes

- 10 source nodes were marked `state="superseded"` with `superseded_by` pointing to the canonical node.
- Canonical nodes received `merged_sources` arrays listing the superseded source node IDs.
- No node content was deleted; only state/relationship metadata was updated.

## Register Changes

### Merged items (10)

- `turn_031:n_0090:aos/runtime/tickets/open/TKT-2026-005B-vcp-breakout-entry.md` -> merged_into:n_0072 (confidence 0.9381)
- `turn_051:n_0128:backend/app/api/endpoints/backtests/start.py` -> merged_into:n_0048 (confidence 0.7561)
- `turn_055:n_0139:TKT-2026-005B_round5_result` -> merged_into:n_0138 (confidence 0.8511)
- `turn_055:n_0140:TKT-2026-005B_round5.1_audit` -> merged_into:n_0138 (confidence 0.8333)
- `turn_060:n_0155:TKT-2026-005B_round5.3C_reverify` -> merged_into:n_0151 (confidence 0.9677)
- `turn_068:n_0175:round_5.4a_feishu_audit_result` -> merged_into:n_0173 (confidence 0.8679)
- `turn_070:n_0179:run-54b-20250101-20251230-d37c696d` -> merged_into:n_0176 (confidence 0.9118)
- `turn_078:n_0192:round_6a_cache_remediation` -> merged_into:n_0187 (confidence 0.7600)
- `turn_082:n_0199:round_6a_full_diagnosis` -> merged_into:n_0196 (confidence 0.7755)
- `turn_083:n_0201:backend_defect_repair_implementation` -> merged_into:n_0198 (confidence 0.7368)

### Kept distinct items (14)

- `turn_020:n_0074:openclaw_root_tools_md` -> kept_distinct (confidence 0.5946)
- `turn_027:n_0085:identity_smoke_c` -> kept_distinct (confidence 0.5116)
- `turn_030:n_0087:src/agents/system-prompt.ts` -> kept_distinct (confidence 0.5098)
- `turn_030:n_0088:~/.openclaw/openclaw.json` -> kept_distinct (confidence 0.5000)
- `turn_032:n_0091:ticket_b_pre_execution_check_auto` -> kept_distinct (confidence 0.5490)
- `turn_045:n_0112:tkt_2026_005b_recovery_patch` -> kept_distinct (confidence 0.5366)
- `turn_052:n_0131:TKT-2026-005I-kb-minimum-sanity-check.md` -> kept_distinct (confidence 0.4906)
- `turn_064:n_0163:round_5.3e_consistency_check` -> kept_distinct (confidence 0.4783)
- `turn_067:n_0173:round_5.4a_feishu_audit` -> kept_distinct (confidence 0.5769)
- `turn_067:n_0174:round_5.4b_full_run` -> kept_distinct (confidence 0.4583)
- `turn_072:n_0181:round_5.5_baseline_freeze` -> kept_distinct (confidence 0.4727)
- `turn_072:n_0183:baseline_metadata_round_5.4b_fix1` -> kept_distinct (confidence 0.4918)
- `turn_077:n_0190:round_6a_stop_loss_7pct` -> kept_distinct (confidence 0.4906)
- `turn_081:n_0196:round_6a_backend_diagnosis` -> kept_distinct (confidence 0.5306)

## Remaining tracked items (35)

These items remain `remediation_status: tracked` and require future manual review or resolver escalation.
They are documented in `pending_merge_review_list.md`.

## Verification

- `pytest graph/tests/test_turn_runtime_guards.py` passed (2/2).
- `check_pending_merge_register.py --current-turn 84` reports 33 overdue items (down from 54).

## Notes

This reconciliation intentionally modifies the current state snapshot (`graph_state.turn_084.json`) without creating a new turn, because no raw input exists for turn_085 yet. The change is additive and documented; the patch chain from turn_001-084 remains reproducible, but turn_084 snapshot now reflects the reconciled state.
