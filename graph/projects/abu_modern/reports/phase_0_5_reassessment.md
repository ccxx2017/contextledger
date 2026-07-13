# Phase 0.5 Reassessment Report

**Generated:** 2026-07-13
**Project:** abu_modern
**Current turn_counter:** 84

## Executive Summary

This report reassesses whether the previous Phase 0.5 benchmark should be re-executed, extended, or deferred, given that abu_modern has grown from a handful of turns to a fully rebuilt 84-turn chain with committed guards, sync scripts, and tests.

**Preliminary conclusion: Conclusion A — re-execute Phase 0.5.**
The old benchmark artifacts exist only in git history (commit `c7072b6495a2176561fdabae73af2afcb18bb55c`), not in the current working tree. Data scale has grown by an order of magnitude, the system now has real alias/supersession cases from 84 turns of dialogue, and the schema has not yet evolved to support the fine-grained invalidation semantics that Phase 0.5 was designed to probe. Re-execution is warranted; the old artifacts should be restored as a baseline for comparison.

## ① Old Phase 0.5 Artifact Status

| Check | Result |
|-------|--------|
| Old artifacts in current HEAD | **NO** |
| Old artifacts in git history | **YES** (commit `c7072b64`) |
| Score scripts still present | `graph/scripts/score_phase05.py`, `graph/scripts/seed_phase05_replay.py` |
| Trajectory/gold directories in HEAD | **NO** |
| Coverage matrix in HEAD | **NO** |
| Gap register in HEAD | **NO** |

Old artifacts extracted to `C:\tmp\old_*` for this assessment: 23 trajectories, coverage matrix, gap register, score report, and README.

## ② Data Scale Comparison

| Dimension | Old Phase 0.5 | Current abu_modern | Ratio |
|-----------|---------------|-------------------|-------|
| Turns | ~5 (Phase 0 manual turns) | 84 | ~17x |
| Nodes | N/A (synthetic trajectories) | 204 | — |
| Edges | N/A | 340 | — |
| Trajectories | 23 | 84-turn real chain | 84-turn real chain supersedes synthetic 23 |

The data-scale criterion (`≥5x`) is overwhelmingly satisfied.

## ③ Case Coverage Comparison

### Old Phase 0.5 coverage (23 trajectories)

| Category | Count in old benchmark |
|----------|------------------------|
| alias_trap | 6 |
| conditional | 2 |
| full | 4 |
| non_invalidation_decoy | 4 |
| out_of_order_late | 4 |
| partial | 2 |
| provenance_conflict | 3 |
| revival | 2 |

### Current abu_modern real cases

| Category | Evidence | Assessment |
|----------|----------|------------|
| full / complete invalidation | 63 resolved nodes, 10 superseded nodes | **Present** |
| partial invalidation | No `invalidation_type` or sub-clause tracking | **Absent as explicit schema** |
| conditional invalidation | No carve-out fields | **Absent as explicit schema** |
| revival / rollback | No `revival` state or valid-time fields | **Absent as explicit schema** |
| alias trap / false merge | 59 pending_merge items, 10 resolved merges, 14 kept distinct | **Present as real cases** |
| provenance conflict | No provenance/source-rank fields; all evidence is `surface_or_token_similarity` | **Absent as explicit schema** |
| non-invalidation decoy | No decoy-type field; cannot distinguish true invalidation from parallel targets/modes | **Absent as explicit schema** |
| out_of_order_late | No `observed_at` or `valid_time` fields | **Absent as explicit schema** |

**Assessment:** abu_modern now has *real* alias/supersession cases that did not exist in the old small dataset, but it still lacks schema fields for partial/conditional/revival/provenance/decoy/valid-time. The coverage matrix has qualitatively expanded in alias/supersession but remains empty in the other advanced categories.

## ④ Schema Evolution Status

| Field / Capability | Present? | Notes |
|--------------------|----------|-------|
| `state` (active/superseded/resolved) | Yes | Values: {None: 97, 'open': 20, 'in_progress': 2, 'resolved': 63, 'deployed': 8, 'blocked': 1, 'cancelled': 1, 'superseded': 10, 'implemented': 2} |
| `status` field | True | Values: {'superseded': 61, 'active': 3} |
| `invalidation_type` | False | — |
| `valid_from` / `valid_to` | False | — |
| `observed_at` | False | — |
| `priority` | Yes | All 204 nodes have priority |

**Interpretation:** The schema is still essentially the Phase 0 schema. This is actually good news for the benchmark — Phase 0.5 is designed to expose exactly these gaps. Re-executing it now will produce a honest gap map against a much larger, real dataset.

## ⑤ Guard / Sync / Test Status

| Component | Status | Evidence |
|-----------|--------|----------|
| `turn_sequence_guard` | Committed | `graph/scripts/run_auto_turn.py` |
| `committed_history_audit` | Committed | `graph/scripts/run_auto_turn.py` |
| `pending_merge_register_sync` | Committed | `graph/scripts/sync_pending_merge_register.py` |
| `check_pending_merge_register.py` | Committed and working | Reduced overdue count from 54→33 |
| `pytest graph/tests/test_turn_runtime_guards.py` | **2/2 passed** | Just verified |
| `run_auto_turn.py` reproducibility | Verified | Rebuilt turn_020–084 successfully |

The mechanical layer is now solid enough that a new benchmark run can be reproduced and regression-tested.

## ⑥ Pending Merge Real Cases

- Total pending_merge items: 59
- Resolved in batch reconciliation: 24 (10 merges, 14 kept distinct)
- Still tracked: 35
- Evidence type used by resolver: `{('surface_or_token_similarity',): 59}`

**Observation:** Every pending_merge decision was based solely on `surface_or_token_similarity`. This is a direct, real-world instantiation of the alias-strategy tradeoff that Phase 0.5 measured. The 24 resolved items are pre-labeled gold data for alias_trap / false_merge / split cases.

Examples of real alias/supersession cases:
- `turn_031:n_0090:aos/runtime/tickets/open/TKT-2026-005B-vcp-breakout-entry.md` merged into `merged_into:n_0072` (confidence 0.9381)
- `turn_051:n_0128:backend/app/api/endpoints/backtests/start.py` merged into `merged_into:n_0048` (confidence 0.7561)
- `turn_055:n_0139:TKT-2026-005B_round5_result` merged into `merged_into:n_0138` (confidence 0.8511)
- `turn_055:n_0140:TKT-2026-005B_round5.1_audit` merged into `merged_into:n_0138` (confidence 0.8333)
- `turn_060:n_0155:TKT-2026-005B_round5.3C_reverify` merged into `merged_into:n_0151` (confidence 0.9677)
- `turn_020:n_0074:openclaw_root_tools_md` kept distinct (confidence 0.5946)
- `turn_027:n_0085:identity_smoke_c` kept distinct (confidence 0.5116)
- `turn_030:n_0087:src/agents/system-prompt.ts` kept distinct (confidence 0.5098)

## ⑦ Old Metric Definitions

The old Phase 0.5 score script (`graph/scripts/score_phase05.py`) defines:

- `invalidation P/R` — hard metric for conservative invalidation
- `active-set Set-F1` — membership correctness
- `must_include recall` — critical constraint retention
- `valid-time present/absent` — temporal reasoning split
- `alias_strategy_tradeoff` — false_split vs false_merge cost analysis

Old results:
- phase0_current: invalidation P/R=`0.316/0.500`, active-set Set-F1=`0.850`, must_include recall=`0.827`, valid-time=`0.500`
- flat_rag: invalidation P/R=`0.000/0.000`, active-set Set-F1=`0.850`, must_include recall=`0.827`, valid-time=`0.500`

These metrics are still meaningful and should be reused. The key difference is that the new run will use 84 real turns instead of 23 synthetic trajectories.

## ⑧ In-Flight Work Check

| Item | Status |
|------|--------|
| Modified files in workspace | `pack/projects/contextLedger/context_ledger_secendary_ajustment.md` only |
| Active branches | `main` only |
| Background processes | None detected |
| Uncommitted code changes | None |
| OpenCode integration | Not started |

No higher-priority in-flight work would be disrupted by re-running Phase 0.5.

## Decision Framework Applied

### Conclusion A criteria
- Old artifacts not in current HEAD? **YES** (only in history)
- Data scale growth ≥5x and new real case categories? **YES** (~17x turns, real alias/supersession cases)
- Schema/guard changes making old conclusions inapplicable? **PARTIAL** — schema unchanged, but guards now enforce reproducibility, so old ad-hoc benchmark cannot be dropped back in without re-validation

### Conclusion B criteria
- Old artifacts still present and runnable? **NO** (not in HEAD)
- Framework and metrics still valid? **YES**
- Only need to add new cases? **NO** — the old synthetic trajectories no longer represent the current system state

### Conclusion C criteria
- Key categories still missing and need synthetic construction first? **PARTIAL** — partial/conditional/revival/provenance/decoy/valid-time are still schema gaps, but the immediate value is in leveraging the *real* alias/supersession cases that now exist.

## Final Conclusion: A — Re-execute Phase 0.5

**Recommendation:** Re-execute Phase 0.5 on the current abu_modern chain.

**Rationale:**
1. The old benchmark artifacts are not in the current working tree; they exist only as historical reference.
2. Data scale has grown from ~5 manual turns to 84 automated turns — far exceeding the 5x threshold.
3. Real alias and supersession cases now exist in abundance (59 pending_merge items, 10 superseded nodes, 24 resolved merge/keep-distinct decisions), which the old synthetic benchmark could not have captured.
4. The schema has not evolved to support invalidation_type / valid_time / observed_at / provenance, so Phase 0.5 still has genuine gaps to expose.
5. Guard, sync, and test infrastructure are now committed and passing, making the new benchmark reproducible.
6. The old 23-trajectory artifact set should be restored from commit `c7072b64` as a **baseline for comparison**, not as the canonical benchmark.

**Suggested next steps:**
1. Restore the old `phase05_replay/` directory from commit `c7072b6495a2176561fdabae73af2afcb18bb55c` into a `phase05_replay.v1/` reference directory.
2. Design `phase05_replay.v2/` that replays the 84-turn abu_modern chain (or a representative subset) and extracts real trajectories for full/partial/conditional/revival/alias/provenance/decoy/out_of_order categories.
3. Reuse `score_phase05.py` metrics; add a comparison column showing old (23 synthetic) vs new (84 real turns) scores.
4. Do **not** start writing new trajectories until this report is reviewed and the v2 design is approved.
