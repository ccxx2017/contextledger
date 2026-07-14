# Stage04-B Metric Reconciliation: 1 vs 5 Blockers

**Generated:** 2026-07-14T04:00:00Z
**Branch:** `phase1-lifecycle-stage02`

## Compared Runs

| Attribute | Pre-Fix (Baseline) | Post-Fix (Current) |
| --- | --- | --- |
| Run ID | `stage04b_20260713T144000_development` | `stage04b_20260714T030414_development` |
| Based on commit | afe0dc3 | afe0dc3 + uncommitted shadow fixes |
| Metrics version | phase05_v3_shadow | phase05_v3_shadow_v2 |
| Diff spec | shadow_replay_spec.md (same hash) | shadow_replay_spec.md (same hash) |
| `observation_to_event` | Single-event per obs | Multi-event per claim |
| `_determine_relation` source | Raw provenance | Channel prefix |
| `_observation_base` filter | Not present | Present (sibling COEXISTS) |

## Per-Case Blocker Reconciliation

| Case | Pre-Fix Blockers | Post-Fix Blockers | Change | Explanation |
| --- | --- | --- | --- | --- |
| `tr_full_tkt_005b` | 0 | 0 | 0 | Pre-fix: CONTESTS (different turn sources) kept all nodes active, no false invalidation. Post-fix: channel-based source correctly SUPERCEDES. |
| `tr_syn_partial_policy_clause` | 1 | 3 | +2 | Pre-fix: single-claim adapter collapsed 3 claims into 1. Post-fix: multi-claim, but all share entity_ref -> sibling SUPERCEDES. **New regression from multi-claim.** |
| `tr_syn_conditional_region_exception` | 0 | 2 | +2 | Pre-fix: different obs had different mentions -> different entity_ref -> coexistence. Post-fix: same mentions[0] -> SUPERCEDES. **New regression.** |
| `tr_syn_revival_feature_flag` | 0 | 0 | 0 | Pre-fix: 5 regressions (different turn sources). Post-fix: 2 regressions (different channels). |
| `tr_alias_workspace_identity` | 0 | 0 | 0 | Unchanged. |
| `tr_syn_non_invalidation_parallel_targets` | 0 | 2 | +2 | Pre-fix: different mentions -> coexistence. Post-fix: same mentions[0] -> SUPERCEDES. **New regression.** |
| `tr_syn_out_of_order_inventory_present` | 0 | 2 | +2 | Pre-fix: different mentions (hash suffix) -> coexistence. Post-fix: same mentions[0] -> SUPERCEDES. **New regression.** |

## Root Cause: Multi-Claim Adapter Collateral Damage

The multi-claim adapter fix for `tr_full_tkt_005b` has the side effect that ALL claims now derive `entity_ref` from `mentions[0]`. The core problem is that `mentions[0]` is an inadequate key for all five relationship types required by the gold trajectories:

1. **Same entity, same dimension, same channel**: progression -> SUPERCEDES
2. **Same entity, different dimension, same scope**: partial clause -> COEXISTS
3. **Same entity, different scope, same dimension**: conditional exception -> COEXISTS
4. **Same entity, same dimension, different channel**: provenance conflict -> CONTESTS
5. **Same entity, different time, same channel**: late arrival -> coexist without replacing

A resolver that provides dimension-scope-aware adjudication keys is required. Building this in the shadow is the next step.

## Canonical Pre-Fix Baseline (Locked)

The canonical pre-fix baseline for development split is re-stated with post-fix comparator sensitivity for fairness:

| Metric | Pre-Fix (old comparator) | Post-Fix (current comparator) |
| --- | --- | --- |
| total blockers | 1 | 9 |
| total regressions | 24 | 11 |
| min must_include recall | 0.5 | 0.0 |
| min active_set_set_f1 | 0.3333 | 0.0 |

**Caveat:** The pre-fix numbers look better primarily because the pre-fix comparator was less sensitive (it did not detect COEXISTS violations as blockers). The post-fix comparator is more honest — it flags cases that were always semantically wrong but previously undetected. A truly fair before-after comparison requires re-running the pre-fix input through the post-fix comparator.

