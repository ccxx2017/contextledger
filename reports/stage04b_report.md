# Stage04-B Report: Frozen Benchmark Shadow Evaluation

**Generated:** 2026-07-13T14:41:58.403136+00:00
**Branch:** `phase1-lifecycle-stage02`
**Candidate commit:** `943b3f7908c830a8ab683938c0196ee85c8d7d64-dirty`

## Executive Summary

- Lifecycle fixtures: **8/8 PASS**, deterministic replays confirmed.
- Benchmark v1 split audit: **integrity OK**, blind holdout isolated from development.
- Development split: **BLOCK** (diagnostic, 1 blocker, 24 regressions).
- Regression split: **BLOCK** (2 blockers, 33 regressions).
- Adversarial split: **BLOCK** (0 blockers, 3 regressions).
- Blind holdout: **not run** (sealed until regression passes gate).
- Main-chain candidate switch: **NOT APPROVED**.

## Evaluation Manifest

- [graph/projects/abu_modern/shadow_replay/stage04b_evaluation_manifest.json](graph/projects/abu_modern/shadow_replay/stage04b_evaluation_manifest.json)
- Freeze manifest hash: `8ec639a99546c9bb...`
- Metrics version: `phase05_v3_shadow_v2`

## Fixture Replay Results

| Fixture | Gate | Deterministic | Run Dir |
| --- | --- | --- | --- |
| lc_alias_abstain | PASS | True | `graph\projects\abu_modern\shadow_replay\runs\stage04a_20260713T143950_lc_alias_abstain` |
| lc_late_arrival | PASS | True | `graph\projects\abu_modern\shadow_replay\runs\stage04a_20260713T143950_lc_late_arrival` |
| lc_legacy_migration | PASS | True | `graph\projects\abu_modern\shadow_replay\runs\stage04a_20260713T143950_lc_legacy_migration` |
| lc_provenance_conflict | PASS | True | `graph\projects\abu_modern\shadow_replay\runs\stage04a_20260713T143950_lc_provenance_conflict` |
| lc_replay_determinism | PASS | True | `graph\projects\abu_modern\shadow_replay\runs\stage04a_20260713T143950_lc_replay_determinism` |
| lc_revival | PASS | True | `graph\projects\abu_modern\shadow_replay\runs\stage04a_20260713T143950_lc_revival` |
| lc_sequence_collision | PASS | True | `graph\projects\abu_modern\shadow_replay\runs\stage04a_20260713T143950_lc_sequence_collision` |
| lc_two_lifecycles_no_kill | PASS | True | `graph\projects\abu_modern\shadow_replay\runs\stage04a_20260713T143950_lc_two_lifecycles_no_kill` |

## Benchmark Split Results

| Split | Gate | Cases | Min must_include_recall | Min active_set_f1 | Blockers | Regressions |
| --- | --- | --- | --- | --- | --- | --- |
| development | BLOCK | 7 | 0.5 | 0.3333 | 1 | 24 |
| regression | BLOCK | 6 | 0.5 | 0.3333 | 2 | 33 |
| adversarial | BLOCK | 2 | 1.0 | 0.6667 | 0 | 3 |

### Blind Holdout

The sealed blind-holdout run was **not executed** because the regression split failed the pre-registered gate rules. Running it now would violate the Stage04-B protocol that blind holdout may only be used after regression passes.

## Isolation Verification

- `graph/scripts/reconcile_patch.py`: present
- `graph/scripts/apply_patch.py`: present
- `graph/scripts/build_context_bundle.py`: present
- `graph/projects/abu_modern/graph_state.json`: present
- Main-chain git diff: `none`
- All shadow outputs are under `graph/projects/abu_modern/shadow_replay/runs/`.

## Main-Chain Candidate Switch Status

**Not approved.** Stage04-B shows the shadow lifecycle adjudicator is deterministic and passes the curated fixtures, but it does not yet meet the safety red lines on the frozen benchmark:

1. Regression split has unresolved blockers and regressions.
2. Blind holdout was not run because the regression gate was not met.
3. `must_include_recall` on development/regression is below the D1 baseline of 1.0.
4. Active-set F1 on development/regression is below the Phase0 baseline.

The candidate switch application package is generated but marked as `blocked`.

## Unresolved Risks

- The shadow observation-to-event adapter collapses each observation to a single claim and uses `mentions[0]` as both `entity_ref` and `lifecycle_ref`, causing false invalidations on non-invalidation and multi-claim trajectories.
- Alias resolution remains a substring heuristic; it does not yet integrate the production resolver.
- Partial-invalidation semantics are reduced to dropped claim IDs; path-level invalidation is not represented.

## Next Steps

1. Improve the observation-to-event adapter (or add a resolver-driven pre-processor) so that `adjudication_key` distinguishes claims that should coexist from claims that should supersede.
2. Re-run development split until blockers and regressions are resolved.
3. Freeze the final candidate and re-run regression; only then execute the sealed blind-holdout run.
4. Re-evaluate adversarial safety after the adapter improvements.
