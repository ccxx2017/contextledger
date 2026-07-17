# Stage04-C Comparator Policy Violation Audit

**Generated:** 2026-07-15T16:04:00Z  
**Scope:** `tr_syn_revival_feature_flag` — all CONTESTS diffs at cp_after_tr07_obs02 and cp_after_tr07_obs03  
**Comparator version:** v2 (relation-aware, Stage04-C1.2.1)  
**Audit basis:** Frozen evidence in `stage04c_comparator_classification_deviation_freeze.json`

---

## 1. Checkpoint Audit: cp_after_tr07_obs02

### 1.1 Case Summary

| Field | Value |
|-------|-------|
| case_id | tr_syn_revival_feature_flag |
| checkpoint_id | cp_after_tr07_obs02 |
| after_obs_id | tr07_obs02 |
| Gold expected_active_set | ["tr07.feature.disabled"] |
| Shadow actual_active_set | ["tr07.feature.enabled.v1", "tr07.feature.disabled"] |
| Gold expected_invalidations | [{"kind":"full","dropped_claims":["tr07.feature.enabled.v1"],"replacement_claims":["tr07.feature.disabled"]}] |
| Shadow actual_superseded | {} (empty — enabled.v1 stays active via CONTESTS) |
| Gold relation for tr07.feature.enabled.v1 | SUPERCEDES (kind=full) |
| Shadow relation for tr07.feature.enabled.v1 | CONTESTS (edge from tr07.feature.disabled, different source: incident_note vs release_note) |
| R01 actual bundle behavior | R01 safety audit was NOT triggered at this checkpoint — CONTESTS is purely a relation-classification outcome from `_determine_relation()`. Bundle safety (must_include recall, critical claim preservation) is unaffected because tr07.feature.disabled IS in the must_include set. |

### 1.2 Three Diffs at cp_after_tr07_obs02

| Diff # | kind | claim_id | gold_relation | shadow_relation | current_classification | classification_required_by_frozen_truth_table |
|--------|------|----------|--------------|-----------------|------------------------|-----------------------------------------------|
| 1 | active_set | tr07.feature.enabled.v1 | SUPERCEDES | CONTESTS | manual_adjudication | **ordinary_regression** (or blocker if must_include concern) |
| 2 | invalidation | tr07.feature.enabled.v1 | SUPERCEDES | CONTESTS | manual_adjudication | **ordinary_regression** |
| 3 | must_include | tr07.feature.enabled.v1 | — | — | manual_adjudication | **manual_review_metadata** (not a relation scoring issue) |

### 1.3 Violation Analysis

**Diff #1 (active_set):** Gold expects `enabled.v1` to be inactive (superseded). Shadow keeps it active because CONTESTS prevents invalidation. The comparator classifies this as `manual_adjudication`. 

**Why this is a policy violation:** The frozen truth table from Stage04-C instructions requires that `SUPERCEDES gold + CONTESTS shadow` be scored as `ordinary_regression` or `blocker`. Classifying it as `manual_adjudication` reduces the ordinary_regression count from 1 to 0 for this diff. This directly violates the constraint that manual_adjudication must NOT replace ordinary regression.

**Diff #2 (invalidation):** Same root issue — gold expects invalidation, shadow produces none due to CONTESTS. Classified as `manual_adjudication` instead of `ordinary_regression`.

**Diff #3 (must_include):** This is a metadata concern, not a relation classification. It should carry `manual_review_metadata` alongside the relation classification, not replace it.

---

## 2. Checkpoint Audit: cp_after_tr07_obs03

### 2.1 Case Summary

| Field | Value |
|-------|-------|
| checkpoint_id | cp_after_tr07_obs03 |
| after_obs_id | tr07_obs03 |
| Gold expected_active_set | ["tr07.feature.enabled.v2"] |
| Shadow actual_active_set | ["tr07.feature.enabled.v2"] (enabled.v1 was superseded at cp03 despite being active at cp02) |
| Gold expected_invalidations | [{"kind":"revival","dropped_claims":["tr07.feature.disabled"],"replacement_claims":["tr07.feature.enabled.v2"]}] |
| Shadow actual_superseded | ["tr07.feature.enabled.v1"] |
| Gold relation for tr07.feature.disabled | REVIVES (kind=revival) |
| Shadow relation for tr07.feature.disabled | SUPERCEDES (shadow adjudicator collapsed CONTESTS chain into linear supersedes) |
| Gold relation for tr07.feature.enabled.v1 | COEXISTS (not in expected_invalidations at cp03) |
| Shadow relation for tr07.feature.enabled.v1 | SUPERCEDES (superseded at cp03) |

### 2.2 Two Diffs at cp_after_tr07_obs03

| Diff # | kind | claim_id | gold_relation | shadow_relation | current_classification | classification_required_by_frozen_truth_table |
|--------|------|----------|--------------|-----------------|------------------------|-----------------------------------------------|
| 1 | invalidation | tr07.feature.disabled | REVIVES | SUPERCEDES | expected_schema_change | **expected_schema_change** (correct — REVIVES vs SUPERCEDES is an expression difference) |
| 2 | invalidation | tr07.feature.enabled.v1 | COEXISTS | SUPERCEDES | regression | **regression** (correct — COEXISTS gold + SUPERCEDES shadow = false invalidation) |

### 2.3 Analysis

Diff #1 is correctly classified: REVIVES expressed as SUPERCEDES in shadow is an expected_schema_change, not a regression. This is acceptable because the shadow system doesn't yet support the REVIVES relation type.

Diff #2 is a **cascading regression** from cp02: because cp02 kept enabled.v1 active via CONTESTS, the cp03 shadow adjudicator treated the new observation (enabled.v2) as superseding enabled.v1 (same lifecycle, different source resolved to SUPERCEDES at cp03 because the adjudicator's internal state had shifted). Gold did not expect enabled.v1 to be invalidated at cp03 (it was already supposed to be invalidated at cp02). This is correctly classified as `regression`.

---

## 3. Answers to Required Audit Questions

### Q1: Why can SUPERCEDES→CONTESTS NOT become a relation match just because R01 safety was executed?

**Answer:** R01 is a bundle-safety audit that checks whether critical claims (must_include) are preserved. It does NOT change the semantic meaning of the relation between claims. In `tr_syn_revival_feature_flag`, R01 is satisfied because `tr07.feature.disabled` IS in the must_include set and IS active. However, the RELATION mismatch remains: gold expects `enabled.v1` to be invalidated (SUPERCEDES relation), but shadow keeps it active (CONTESTS relation). Satisfying bundle safety does not mean the adjudication outcome is correct — the wrong claim stayed active and the right claim was not invalidated. Relation scoring measures whether the shadow system produced the CORRECT relation; bundle safety measures whether critical claims survived. These are orthogonal concerns. R01 safety execution is a necessary condition for CONTESTS to be considered "safe," but it is NOT sufficient to declare the relation a match.

### Q2: Does the current manual_adjudication classification reduce the ordinary_regression count?

**Answer: YES, definitively.** At cp_after_tr07_obs02, two diffs (active_set and invalidation) that should be classified as `ordinary_regression` are instead classified as `manual_adjudication`. This reduces the ordinary_regression count by 2 for this trajectory. In the development replay summary, `tr_syn_revival_feature_flag` shows 1 regression (from cp03 cascading) + 3 manual_adjudication. Without the violation, it should show 3 regressions (2 from cp02 relation mismatch + 1 from cp03 cascading) + 1 manual_adjudication (must_include metadata). The current classification masks 2 legitimate regressions.

### Q3: Do the current comparator unit tests incorrectly implement "not auto-pass" as "not regression"?

**Answer: YES.** Specifically:

- `test_cmp_contests_requires_r01_safe_behavior`: Asserts that SUPERCEDES gold + CONTESTS shadow should be `manual_adjudication` (NOT `expected_improvement`). This test validates the WRONG boundary. It proves the comparator does NOT auto-pass as expected_improvement, but it does NOT prove that the comparator correctly classifies it as a regression. The test should assert `ordinary_regression` (or at minimum, assert that the classification is NOT `expected_improvement` AND IS either `ordinary_regression` or `manual_adjudication_with_regression_flag`).

- `test_cmp_gold_supersedes_shadow_contests_is_not_auto_pass`: Similar issue. It only asserts `!= expected_improvement`. It should additionally assert `== ordinary_regression` or `== blocker`.

Both tests validate a weaker property than required: they prove "not auto-pass" but not "properly counted as regression." This is a test design flaw that allowed the violation to go undetected.

### Q4: Are there other cases affected by the same logic?

**Answer:** Yes. Looking at the development replay:

- `tr_full_tkt_005b`: 6 regressions, all classified as `regression` (COEXISTS gold + SUPERCEDES shadow = unexpected invalidation). These are correctly classified by the current comparator — the violation does NOT affect these.

- `tr_syn_revival_feature_flag`: 3 manual_adjudication diffs at cp02 (affected), 1 regression at cp03 (not affected by this specific violation, though it is a cascading effect).

- All other 5 development trajectories: 0 regressions, 0 manual_adjudication. Not affected.

- The regression was isolated to the `SUPERCEDES gold + CONTESTS shadow` branch in `_classify_relation_diff`. No other truth table entry was weakened.

### Q5: Does the current comparator still satisfy dual-check (invalidation + active-set) full comparison?

**Answer: YES, structurally.** The comparator still evaluates both:
1. **Active-set diffs**: checks expected_active vs actual_active, with relation-aware classification
2. **Invalidation diffs**: checks expected_invalidations vs actual_superseded, with relation-aware classification
3. **must_include diffs**: checks bundle membership

The dual-check mechanism is intact. The violation is purely in the **classification mapping** — the truth table entry for `SUPERCEDES + CONTESTS` returns `manual_adjudication` instead of `ordinary_regression`. The comparator still detects the mismatch; it just mislabels the severity.

---

## 4. Violation Summary

| Aspect | Current Behavior | Required Behavior | Impact |
|--------|-----------------|-------------------|--------|
| SUPERCEDES gold + CONTESTS shadow classification | `manual_adjudication` | `ordinary_regression` or `blocker` | Masks 2 regressions |
| Unit test boundary | Asserts != expected_improvement | Must assert == ordinary_regression | Weak test contract |
| R01 safety vs relation scoring | Conflated (safety satisfied → manual_adjudication) | Separated (safety → metadata, relation → classification) | Policy violation per Stage04-C instructions |
| Manual_adjudication as regression substitute | Used to replace 2 ordinary_regression counts | Must not replace; can co-exist as metadata | Undercounts regressions |

---

## 5. Conclusion

The comparator v2 from Stage04-C1.2.1 contains a **verified policy violation**: the truth table entry for `gold=SUPERCEDES + shadow=CONTESTS` returns `manual_adjudication` instead of `ordinary_regression` or `blocker`. This violates the explicit Stage04-C1.2.2 requirement that:

> "SUPERCEDES vs CONTESTS → ordinary regression or blocker; MUST NOT be only manual."

The violation masks 2 legitimate regressions in `tr_syn_revival_feature_flag` and is reinforced by unit tests that validate a weaker property ("not auto-pass") rather than the required property ("classified as regression").

**Recommendation:** Immediate rollback of the `_classify_relation_diff` branch for `SUPERCEDES + CONTESTS`, replacement with `ordinary_regression` (or `blocker` if must_include is involved), and unit test correction to assert the proper classification.
