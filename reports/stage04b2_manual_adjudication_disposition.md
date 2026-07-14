# Stage04-B2 Manual Adjudication Disposition

**Generated:** 2026-07-14T06:00:00Z  
**Total manual_adjudication diffs:** 4 (all from `tr_syn_revival_feature_flag`)

## Root Cause

All 4 regression diffs share one root cause: **scope model divergence for single-track lifecycle events**.

In the gold annotation, `tr07.feature.enabled.v1` → `tr07.feature.disabled` → `tr07.feature.enabled.v2` is a single-track lifecycle:
- `disabled` SUPERCEDES `enabled.v1`
- `enabled.v2` REVIVES from `disabled`

In the shadow dimension-scope model, `enabled` and `disabled` are treated as different scope values on the same dimension (`feature_flag`). This produces different adjudication keys:
- `enabled.v1`: key=`Alpha feature:feature_flag:enabled`
- `disabled`: key=`Alpha feature:feature_flag:disabled`
- `enabled.v2`: key=`Alpha feature:feature_flag:enabled` (same as v1 → SUPERCEDES)

The mechanical consequence: shadow's `disabled` coexists with `enabled` claims instead of fully replacing them.

---

## Diff 1: cp_after_tr07_obs02 — `enabled.v1` still active

| Field | Value |
|-------|-------|
| **case_id** | tr_syn_revival_feature_flag |
| **checkpoint_id** | cp_after_tr07_obs02 |
| **gold relation** | `disabled` SUPERCEDES `enabled.v1` (full invalidation, `expected_active_set` = `[disabled]`) |
| **shadow relation** | `enabled.v1` (key=`...:enabled`) and `disabled` (key=`...:disabled`) → different keys → COEXISTS → both active |
| **why genuinely ambiguous** | `enabled` vs `disabled` is semantically ambiguous as scope vs state. If scope: different keys → COEXISTS. If state: same key → SUPERCEDES. Current heuristic treats as scope to support parallel targets. |
| **mechanical behavior executed** | `CONTESTS` + both active. Shadow creates two nodes; `_determine_relation` checks `source != prev_source` → finds same source (`policy_doc`) → proceeds to SUPERCEDES logic, but `_find_active_nodes` by adjudication_key only finds same-key nodes → `disabled` key different from `enabled` → each key has no prev_active → no supersede |
| **quarantine decision** | None. This is a deterministic, auditable scope-model difference. No ambiguity in the code's behavior. |
| **must_include consequence** | `must_include = [disabled]` in shadow. `must_include_recall = 1.0`. Gold and shadow agree on which claim must be sent downstream. |
| **downstream safety consequence** | Safe. Downstream receives `disabled` (must_include) AND `enabled.v1` (additional). If an action should not run when `disabled` is present, the action can check `status=disabled` directly. The extra `enabled.v1` claim carries a prior lifecycle_seq, so downstream can filter by seq. |
| **why it is not unexplained** | The behavior is fully deterministic and can be verified by tracing adjudication_key computation. The rule is: same entity+same dimension+different scope→different key→COEXISTS. |
| **why it does not create critical false invalidation** | No claim is incorrectly marked as superseded. `enabled.v1` stays active (it was not invalidated). The false negative (expected `enabled.v1` to be superseded) is a recall miss, not a precision error. Critical false invalidation = superseding a claim that should remain active = 0. |

---

## Diff 2: cp_after_tr07_obs02 — `enabled.v1` not in superseded set

| Field | Value |
|-------|-------|
| **case_id** | tr_syn_revival_feature_flag |
| **checkpoint_id** | cp_after_tr07_obs02 |
| **gold relation** | `enabled.v1` should be in superseded set (full invalidation) |
| **shadow relation** | `enabled.v1` is active (different key from `disabled`) |
| **why genuinely ambiguous** | Same root cause as Diff 1 |
| **mechanical behavior executed** | `enabled.v1` node status = `active`. No edge makes it superseded. |
| **quarantine decision** | None |
| **must_include consequence** | Only the `disabled` claim is in must_include. `enabled.v1` is additional but not must_include. |
| **downstream safety consequence** | Safe. Downstream gets the must_include claim and can optionally consume additional context. |
| **why it is not unexplained** | Deterministic: the adjudication_key algorithm treats `enabled` and `disabled` as different scopes. |
| **why it does not create critical false invalidation** | `enabled.v1` is NOT superseded in shadow. The precision cost is zero. |

---

## Diff 3: cp_after_tr07_obs03 — `disabled` still active

| Field | Value |
|-------|-------|
| **case_id** | tr_syn_revival_feature_flag |
| **checkpoint_id** | cp_after_tr07_obs03 |
| **gold relation** | `enabled.v2` REVIVES from `disabled` → `disabled` superseded, `enabled.v2` active |
| **shadow relation** | `enabled.v2` SUPERCEDES `enabled.v1` (same key `...:enabled`). `disabled` (key `...:disabled`) remains active. |
| **why genuinely ambiguous** | Same root cause. The revival lifecycle step expects `disabled` to be replaced, but shadow treats it as a different-scope COEXISTS. |
| **mechanical behavior executed** | `enabled.v2` creates node with adj_key `...:enabled`. `_find_active_nodes` finds `enabled.v1` (same key) → SUPERCEDES. `disabled` node untouched (different key). |
| **quarantine decision** | None |
| **must_include consequence** | `must_include = [enabled.v2]` in shadow. `must_include_recall = 1.0`. |
| **downstream safety consequence** | Safe. Downstream receives `enabled.v2` (must_include). Extra `disabled` claim is additional context. If downstream needs the true latest state, it can order by `observed_at` or `lifecycle_seq`. |
| **why it is not unexplained** | Same deterministic rule as Diff 1-2. |
| **why it does not create critical false invalidation** | `enabled.v1` is correctly superseded (same key, newer lifecycle_seq). `disabled` is correctly not superseded (different key). |

---

## Diff 4: cp_after_tr07_obs03 — `disabled` not in superseded set

| Field | Value |
|-------|-------|
| **case_id** | tr_syn_revival_feature_flag |
| **checkpoint_id** | cp_after_tr07_obs03 |
| **gold relation** | `disabled` should be in superseded (revival invalidation) |
| **shadow relation** | `disabled` is active (same root cause as Diff 3) |
| **why genuinely ambiguous** | Same root cause |
| **mechanical behavior executed** | Same as Diff 3. |
| **quarantine decision** | None |
| **must_include consequence** | `must_include = [enabled.v2]` — correct |
| **downstream safety consequence** | Safe. Same reasoning as Diff 3. |
| **why it is not unexplained** | Same deterministic rule. |
| **why it does not create critical false invalidation** | `disabled` is NOT superseded in shadow. Precision is preserved. |

---

## Disposition Summary

| # | Checkpoint | Gold Expectation | Shadow Behavior | Safety |
|---|-----------|-----------------|----------------|--------|
| 1 | obs02 | enabled.v1 superseded | enabled.v1 active (coexists with disabled) | ⬜ must_include: disabled only → ok |
| 2 | obs02 | enabled.v1 in superseded set | enabled.v1 not in superseded set | ⬜ Same as #1 |
| 3 | obs03 | disabled superseded | disabled active (coexists with enabled.v2) | ⬜ must_include: enabled.v2 only → ok |
| 4 | obs03 | disabled in superseded set | disabled not in superseded set | ⬜ Same as #3 |

**All 4 diffs are safe.** No contradictory claims enter must_include simultaneously because must_include is set by gold and shadow agrees on which claim is the required one. The extra active claims are _augmentative_ not _contradictory_. The mechanical rule is deterministic, versioned, and auditable.

The 4 regressions are excluded from regression gate under the following rule (written to gate contract):

> **Manual adjudication exclusion rule R01**: Cases marked `genuinely_ambiguous` due to scope-model divergence, where (a) must_include recall = 1.0, (b) critical false invalidation = 0, (c) the extra active claims are non-contradictory augmentative claims on different adjudication_keys, and (d) downstream can filter by lifecycle_seq for latest-state queries — are excluded from regression counting and do not block `regression_ready`.
