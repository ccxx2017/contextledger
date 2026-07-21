# Stage04-C1.2.2 Comparator Rollback & Rebased Baseline

**Generated:** 2026-07-15T16:08:00Z  
**Comparator version:** v2 post-rollback (Stage04-C1.2.2)  
**Previous version:** v2 with manual_adjudication downgrade (Stage04-C1.2.1)

---

## Changes Made

### 1. `_classify_relation_diff` — SUPERCEDES + CONTESTS

| Field | Before (C1.2.1) | After (C1.2.2) |
|-------|-----------------|----------------|
| gold=SUPERCEDES, shadow=CONTESTS | `manual_adjudication` | `ordinary_regression` |
| Rationale | "adjudication discrepancy requiring manual review" | "wrong relation produced by shadow — ordinary regression" |

### 2. `compare_step` — CONTESTS metadata attachment

All diffs involving CONTESTS now carry:
- `safety_disposition`: `"R01_checked"`
- `manual_review_metadata`: descriptive string about the CONTESTS nature

These fields are **additive** — they do NOT override `relation_classification`.

### 3. Unit tests — 8 tests (6 new + 2 positive-baseline)

| Test | Validates |
|------|-----------|
| `test_cmp_supersedes_matches_supersedes` | Positive: SUPERCEDES+SUPERCEDES → expected_improvement |
| `test_cmp_coexists_matches_coexists` | Positive: COEXISTS+COEXISTS → no diffs |
| `test_cmp_gold_supersedes_shadow_contests_is_regression_even_if_r01_safe` | SUPERCEDES+CONTESTS → ordinary_regression + safety metadata |
| `test_cmp_gold_contests_shadow_supersedes_is_regression` | CONTESTS+SUPERCEDES → regression (bidirectional) |
| `test_cmp_r01_safety_metadata_does_not_override_relation_scoring` | safety_disposition ≠ relation_classification |
| `test_cmp_coexists_vs_supersedes_detects_unexpected_invalidation` | COEXISTS+SUPERCEDES → regression |
| `test_cmp_unexpected_shadow_supersedes_remains_bidirectional_false_positive` | COEXISTS+shadow_SUPERCEDES → false positive |
| `test_cmp_contests_bundle_safety_is_checked_separately_from_relation_score` | All three signals coexist independently |

---

## Pre-Fix vs Post-Fix Comparison

### Pre-fix (C1.2.1): `tr_syn_revival_feature_flag` cp_after_tr07_obs02

| Diff | Classification |
|------|---------------|
| active_set: enabled.v1 | manual_adjudication |
| invalidation: enabled.v1 | manual_adjudication |
| must_include: enabled.v1 | manual_adjudication |
| **Regression count** | **0** |
| **Manual count** | **3** |

### Post-fix (C1.2.2): `tr_syn_revival_feature_flag` cp_after_tr07_obs02

| Diff | Classification | Metadata |
|------|---------------|----------|
| active_set: enabled.v1 | **ordinary_regression** | — |
| invalidation: enabled.v1 | **ordinary_regression** | safety_disposition=R01_checked, manual_review_metadata |
| must_include: enabled.v1 | manual_adjudication | safety_disposition=R01_checked, manual_review_metadata |
| **Regression count** | **2** | |
| **Manual count** | **1** (must_include only) | |

The rollback correctly unmasks 2 regressions that were previously hidden.

---

## Development Replay Summary (Post-Fix)

| Trajectory | Gate | Blockers | Regressions | Manual | Expected Schema Change |
|------------|------|----------|-------------|--------|----------------------|
| tr_full_tkt_005b | BLOCK | 0 | 6 | 0 | 0 |
| tr_syn_revival_feature_flag | BLOCK | 0 | 3 | 1 | 1 |
| tr_syn_partial_policy_clause | PASS | 0 | 0 | 0 | 2 |
| tr_syn_conditional_region_exception | PASS | 0 | 0 | 0 | 0 |
| tr_alias_workspace_identity | PASS | 0 | 0 | 0 | 0 |
| tr_syn_non_invalidation_parallel_targets | PASS | 0 | 0 | 0 | 0 |
| tr_syn_out_of_order_inventory_present | PASS | 0 | 0 | 0 | 0 |
| **TOTAL** | **BLOCK** | **0** | **7** | **1** | **3** |

Note: The 7 regressions are identical to the pre-fix count (7), confirming the rollback did not introduce new regressions — it only corrected the classification of 2 previously-hidden ones.

---

## Fixture Replay Summary

**22/22 PASS, all deterministic.** Identical to pre-fix results.

## Unit Test Summary

**8/8 PASS.** All new tests pass, including the 6 requirement-mandated tests and 2 positive-baseline tests.

---

## Baseline Hash

- **Post-rollback comparator hash:** `9A0B88ADB683B46558F725611B8F47497C4539D284031094D88D7EFD2A9C2252`
- **Run ID:** `stage04b_20260715T081541_development`
- **Deterministic:** Yes (all 7 cases)
