# Stage04-C Development Regression Reconciliation

**Generated:** 2026-07-14T10:41:00Z

## Revision: Scope fix refined (S006_exact_value_match removed)

After initial scope fix, two development cases became BLOCKED:
1. **tr_syn_revival_feature_flag** — 2 regressions (CONTESTS vs SUPERCEDE)
2. **tr_syn_non_invalidation_parallel_targets** — 1 blocker, 1 regression

### Root Cause Analysis

Both cases share the same root cause mechanism: **the initial scope fix included
`S006_exact_value_match`** which treated any claim_id third segment matching
`claim.value` as a state value. This was too aggressive.

#### Case 1: tr_syn_non_invalidation_parallel_targets — NOW FIXED

**Pre-fix (S006 active):**
- `tr12.target.staging.allowed` → seg=`staging`, value=`staging` → seg==value → scope=`_default_`
- `tr12.target.canary.allowed` → seg=`canary`, value=`canary` → seg==value → scope=`_default_`
- Same adj_key → second supersedes first → gold expects COEXISTS → BLOCK

**Fix:** Removed `S006_exact_value_match`. Only the versioned mapping is authoritative.
- `staging` ∉ STATE_VALUE_TOKENS → scope=`staging`  
- `canary` ∉ STATE_VALUE_TOKENS → scope=`canary`
- Different adj_keys → COEXISTS → PASS ✅

**Current status:** `tr_syn_non_invalidation_parallel_targets` = PASS

#### Case 2: tr_syn_revival_feature_flag — PRE-EXISTING COMPARATOR REGRESSION

**Pre-fix behavior (d7d681e PASS run 053749):**
- `enabled`/`disabled` both treated as scope values → different adj_keys
- Different adj_keys → each claim independent (no interaction)
- Old `compare_step` had COEXISTS handling → PASS

**Post-fix behavior:**
- `enabled`/`disabled` ∈ STATE_VALUE_TOKENS → scope=`_default_`  
- Same adj_key: `Alpha feature:feature_flag:_default_`
- Different sources (release_note vs incident_note) → CONTESTS (adjudicator rule)
- Current `compare_step` (simplified in 2d24e01) has no COEXISTS handling → regression

**This is NOT a scope fix regression.** The scope fix correctly normalizes these 
state values. The regression arises from two factors both pre-existing:

1. **Adjudicator CONTESTS rule** — Different source → CONTESTS (existed since Stage04-A)
2. **compare_step simplification** — Old comparator (d7d681e) had COEXISTS-aware 
   invalidation logic; current version (2d24e01+) does not.

The PASS run 053749 graph_state shows the SAME adjudicator behavior (CONTESTS between
tr07.feature.enabled.v1 and tr07.feature.disabled). The difference is exclusively in
how the comparator classified the result.

### Resolution

| Case | Previous | Current | Cause | Status |
|------|----------|---------|-------|--------|
| tr_syn_non_invalidation_parallel_targets | PASS | PASS | Fixed by removing S006 | ✅ Resolved |
| tr_syn_revival_feature_flag | PASS | 2 regressions | compare_step simplification (2d24e01) | ⚠️ Pre-existing |

The `tr_syn_revival_feature_flag` regression was masked before by:
1. Scope extraction defect (wrong scope → different adj_key → no interaction)
2. Comparator COEXISTS handling (removed in 2d24e01)

The scope fix corrects the normalization. The regression is a comparator gap 
inherited from the 2d24e01 simplification, not caused by the scope normalization change.
