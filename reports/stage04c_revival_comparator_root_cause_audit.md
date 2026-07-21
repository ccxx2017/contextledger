# Stage04-C Revival Comparator Root Cause Audit (C1.2.2 Updated)

**Generated:** 2026-07-15T16:08:00Z  
**Case:** tr_syn_revival_feature_flag  
**Affected checkpoints:** cp_after_tr07_obs02, cp_after_tr07_obs03  
**Comparator version:** v2 post-rollback (Stage04-C1.2.2)  
**Previous version:** v2 with manual_adjudication downgrade (Stage04-C1.2.1) — ROLLED BACK

---

## Case Overview

Three observations from two different sources tracking a feature flag lifecycle:

| Obs | Source | Claim | State | Time |
|-----|--------|-------|-------|------|
| tr07_obs01 | release_note | tr07.feature.enabled.v1 | enabled | T08:00 |
| tr07_obs02 | incident_note | tr07.feature.disabled | disabled | T09:00 |
| tr07_obs03 | release_note | tr07.feature.enabled.v2 | enabled_again | T13:00 |

Gold expects this to be a linear timeline: enabled -> disabled -> re-enabled = SUPERCEDES chain.

---

## Root Cause Analysis (C1.2.2 Updated)

### Primary Root Cause: Shadow Adjudicator CONTESTS Over-Match

**Layer:** Shadow lifecycle adjudicator (`shadow_lifecycle_adjudicator.py`)  
**Method:** `_determine_relation()`  
**Rule:** `if new_source != prev_source: return "CONTESTS"`

This treats ALL different-source claims on the same adjudication_key as CONTESTS. But for lifecycle updates across different reporting channels (release_note -> incident_note), the intent is SUPERCEDES (time progression), not CONTESTS (provenance conflict).

### Comparator Fix Applied in C1.2.2

The comparator v2 rollback (Stage04-C1.2.2) correctly changed the classification:

| Checkpoint | Gold Relation | Shadow Relation | C1.2.1 Classification | C1.2.2 Classification |
|-----------|--------------|-----------------|----------------------|----------------------|
| cp_after_tr07_obs02 (active_set) | SUPERCEDES | CONTESTS | manual_adjudication (WRONG) | **ordinary_regression** (CORRECT) |
| cp_after_tr07_obs02 (invalidation) | SUPERCEDES | CONTESTS | manual_adjudication (WRONG) | **ordinary_regression** (CORRECT) |
| cp_after_tr07_obs02 (must_include) | - | - | manual_adjudication | manual_adjudication (metadata only) |
| cp_after_tr07_obs03 (invalidation) | REVIVES | SUPERCEDES | expected_schema_change | expected_schema_change |
| cp_after_tr07_obs03 (invalidation) | COEXISTS | SUPERCEDES | regression | regression |

The C1.2.2 rollback unmasks 2 regressions that were previously hidden as manual_adjudication. These are now correctly counted as ordinary_regression.

### R01 Safety Metadata (C1.2.2 Addition)

All CONTESTS-related diffs now carry:
- `safety_disposition`: "R01_checked"
- `manual_review_metadata`: descriptive string

These are **additive** to the relation classification and do NOT override it.

---

## Stage04-C1.2.2 Requirements Checklist

| Requirement | Status | Evidence |
|------------|--------|----------|
| 1. Freeze current comparator evidence | DONE | stage04c_comparator_classification_deviation_freeze.json |
| 2. Comparator Policy Violation Audit | DONE | stage04c_comparator_policy_violation_audit.md |
| 3. Roll back non-compliant relation classification | DONE | ordinary_regression for SUPERCEDES+CONTESTS |
| 4. Fix comparator-only tests (8 tests) | DONE | 8/8 PASS |
| 5. Triage 6 tr_full_tkt_005b regressions | DONE | stage04c_full_tkt_005b_regression_triage.md |
| 6. Re-run: unit tests, 22 fixtures, 2x determinism, dev replay | DONE | All passed |
| 7. Final conclusion | BLOCKED | See below |

### Blocking Criteria Assessment

| Criterion | Status | Detail |
|-----------|--------|--------|
| Unauthorized SUPERCEDES->CONTESTS->manual_adjudication downgrade removed | PASS | Changed to ordinary_regression |
| R01 safety separated from relation scoring | PASS | safety_disposition is additive metadata |
| Comparator-only tests prove relation mismatch scored | PASS | 8/8 PASS |
| Bidirectional invalidation, active-state, unexpected supersede/quarantine intact | PASS | 22/22 fixtures PASS |
| tr_syn_revival_feature_flag relation mismatch correctly scored | PASS | 2 regressions now counted |
| tr_full_tkt_005b 6 regressions triaged | PASS | All 6 -> shadow_compiler layer |
| 22 fixtures PASS + deterministic | PASS | All 22 PASS, all deterministic |
| Development: zero blockers | PASS | 0 blockers |
| Development: zero unexplained diff | PASS | 0 unexplained |
| Development: ordinary regressions = 0 | FAIL | **7 regressions remain** |
| must_include recall >= D1 (1.0) | PASS | 1.0 |
| Critical false invalidation = 0 | PASS | 0 |
| R01 not expanded | PASS | Unchanged |
| Did NOT run regression/adversarial/blind holdout | PASS | Compliant |

---

## Final Verdict

**Status: blocked**

The comparator rollback in Stage04-C1.2.2 is **correct and complete**. The 7 remaining regressions are:
1. **6 from tr_full_tkt_005b**: shadow_compiler fan-out defect (creates SUPERCEDES edges to ALL previous claims instead of just the immediate predecessor)
2. **1 from tr_syn_revival_feature_flag**: cascading effect from cp02 where CONTESTS kept enabled.v1 active, causing cp03 to produce an unexpected supersede

These are **shadow adjudicator/compiler defects**, not comparator defects. The comparator correctly identifies, classifies, and reports them.

**Next step (outside Stage04-C scope):** Fix the shadow adjudicator's CONTESTS over-match rule and the shadow compiler's fan-out edge-building logic. Then re-run development replay.
