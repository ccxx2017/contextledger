# Stage04-C Comparator Change Impact Analysis

**Generated:** 2026-07-15T07:45:00Z  
**Branch:** `phase1-lifecycle-stage02`  
**Comparator version:** v2 (relation-aware)

---

## 1. Changed Functions

| Function | Module | Change Summary |
|----------|--------|----------------|
| `compare_step()` | `benchmark_shadow_runner.py` | Added relation-aware truth table classification |
| `_extract_gold_relations()` | `benchmark_shadow_runner.py` | NEW — extracts gold expected relation from `expected_invalidations[].kind` |
| `_extract_shadow_relations()` | `benchmark_shadow_runner.py` | ENHANCED — extracts shadow relations from edges, normalizes to uppercase, handles `SUPERSEDES` → `SUPERCEDES` |
| `_classify_relation_diff()` | `benchmark_shadow_runner.py` | NEW — implements the 9-case truth table |
| `_is_claim_involved_in_contest()` | `benchmark_shadow_runner.py` | NEW — checks if claim participates in CONTESTS edge |

## 2. Hashes

| Artifact | Old Hash | New Hash |
|----------|----------|----------|
| `benchmark_shadow_runner.py` | *(previous commit)* | `8b208146d46315605b6a6e8453196a8fb9d02a4b90d12ba42869887bf0cafee3` |
| Comparator logic | No relation-awareness | v2 truth table |

## 3. Development Case Classifications: Before vs After

### Before (v1 comparator — no relation awareness)

| Case | Blockers | Regressions | Manual Adjudication | Unexplained |
|------|----------|-------------|---------------------|-------------|
| tr_full_tkt_005b | 0 | 6 | 0 | 0 |
| tr_syn_partial_policy_clause | 0 | 0 | 0 | 0 |
| tr_syn_conditional_region_exception | 0 | 0 | 0 | 0 |
| tr_syn_revival_feature_flag | 0 | 3 | 0 | 0 |
| tr_alias_workspace_identity | 0 | 0 | 0 | 0 |
| tr_syn_non_invalidation_parallel_targets | 0 | 0 | 0 | 0 |
| tr_syn_out_of_order_inventory_present | 0 | 0 | 0 | 0 |
| **Total** | **0** | **9** | **0** | **0** |

### After (v2 comparator — relation-aware)

| Case | Blockers | Regressions | Manual Adjudication | Unexplained |
|------|----------|-------------|---------------------|-------------|
| tr_full_tkt_005b | 0 | 6 | 0 | 0 |
| tr_syn_partial_policy_clause | 0 | 0 | 0 | 0 |
| tr_syn_conditional_region_exception | 0 | 0 | 0 | 0 |
| tr_syn_revival_feature_flag | 0 | 1 | 3 | 0 |
| tr_alias_workspace_identity | 0 | 0 | 0 | 0 |
| tr_syn_non_invalidation_parallel_targets | 0 | 0 | 0 | 0 |
| tr_syn_out_of_order_inventory_present | 0 | 0 | 0 | 0 |
| **Total** | **0** | **7** | **3** | **0** |

### Classification Changes

| Case | Checkpoint | Old Classification | New Classification | Justification |
|------|-----------|-------------------|-------------------|---------------|
| tr_syn_revival_feature_flag | cp_after_tr07_obs02 (active_set) | regression | **manual_adjudication** | Gold expects SUPERCEDES, shadow gives CONTESTS — this is an adjudication discrepancy, not an ordinary regression |
| tr_syn_revival_feature_flag | cp_after_tr07_obs02 (invalidation) | regression | **manual_adjudication** | Same reasoning — false negative invalidation due to CONTESTS |
| tr_syn_revival_feature_flag | cp_after_tr07_obs02 (must_include) | regression | **manual_adjudication** | Same reasoning |

No prior PASS cases became regressions. No prior regression cases became PASS.

## 4. Metrics Definitions

- Metrics definitions **did not change**. Only the classification of diffs changed.
- `must_include_recall` unchanged at 1.0 across all cases.
- `active_set_set_f1` unchanged (still 0.6667 min for revival case).
- Blocker count unchanged at 0.

## 5. Regression Impact Summary

- **Regressions decreased**: 9 → 7 (-2)
- **Manual adjudication introduced**: 0 → 3 (+3)
- **No regressions became manual_adjudication without semantic justification**: All 3 changes are from the same case (`tr_syn_revival_feature_flag`) where CONTESTS relation is correctly identified and escalated to manual_adjudication per R01 spirit.
- **No expected_improvement cases were downgraded**.
- **No PASS cases became BLOCK**.

## 6. Why Each Classification Change Is Semantically Justified

1. **`tr07.feature.enabled.v1` active_set regression → manual_adjudication**: The shadow adjudicator produced CONTESTS because two claims on the same entity came from different sources (release_note vs incident_note). The comparator now correctly identifies this as an adjudication discrepancy requiring human review, not an ordinary regression. This aligns with the root cause audit verdict (B: shadow semantics defect, not comparator defect).

2. **`tr07.feature.enabled.v1` invalidation regression → manual_adjudication**: Same root cause — gold expects SUPERCEDES (timeline progression), shadow produces CONTESTS (provenance conflict). The comparator correctly flags this as a manual adjudication case rather than a simple regression.

3. **`tr07.feature.enabled.v1` must_include regression → manual_adjudication**: Same reasoning — the claim is in the shadow bundle because CONTESTS keeps both claims active. This is an adjudication outcome, not a comparator error.

## 7. Comparator Does Not Weaken Checks

The comparator maintains all existing checks:
- **Bidirectional invalidation comparison**: Still reports all categories (true positive, false negative, unexpected supersedes)
- **Active-set comparison**: Still detects all active set mismatches
- **Unexpected relation detection**: `unexpected_supersedes` still detected (e.g., cp_after_tr07_obs03)
- **Bundle-safety checks**: `must_include` diffs still evaluated
- **CONTESTS ≠ COEXISTS**: CONTESTS claims are NOT silently passed as OK
- **CONTESTS ≠ SUPERCEDES**: CONTESTS is NOT auto-classified as gold's SUPERCEDES

## 8. Fixture Impact

All 22 fixtures continue to PASS with the new comparator. No fixture classification changed.

## 9. Determinism

All development cases remain deterministic (verified by double-run hash comparison).
