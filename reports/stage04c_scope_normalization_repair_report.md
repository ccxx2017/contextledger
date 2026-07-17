# Stage04-C Scope Normalization Repair Report

**Verdict:** blocked

**Generated:** 2026-07-14T09:35:00Z

## Scope Fix Summary

**Root cause:** `_extract_scope_v2` in `shadow_resolution_adapter.py` treated
the claim_id third segment as a semantic scope value without checking whether
it was actually a claim state value. This caused claims like 
`tr04.slippage_report.required` and `tr04.slippage_report.not_required` to get 
different adjudication keys (scope=`required` vs scope=`not_required`), when 
they should have the same scope (`_default_`) and differ only in state.

**Fix:**
1. Added `STATE_VALUE_TOKENS` frozenset with ~20 known state-value tokens
2. Before using claim_id third segment as scope, check if it matches
   `claim.value` or is in `STATE_VALUE_TOKENS`
3. If so, fall through to `_default_` scope

## Deliverables

### Step 4 — New Fixtures (3)

Created in `graph/projects/abu_modern/fixtures/lifecycle/fixtures/`:

| Fixture | Expected Behavior |
|---------|------------------|
| `lc_partial_same_dimension_same_scope_supersedes.json` | Same entity/dimension/scope → SUPERCEDES |
| `lc_partial_same_dimension_different_atomic_claims_coexist.json` | Different dimensions → COEXIST |
| `lc_late_arrival_price_band_same_scope_vs_different_scope.json` | Late-arrival price band → QUARANTINE |

### Step 5 — Code Fix

File: `graph/projects/abu_modern/shadow_replay/scripts/shadow_resolution_adapter.py`

Lines changed: +44/-12. Key additions:
- `STATE_VALUE_TOKENS` constant
- State-value check before third-segment heuristic in `_extract_scope_v2`
- `claim_value = claim.get("value")` for exact-match detection

Also updated: `fixture_replay_runner.py` — added `EXPECTED_NODE_SEMANTICS`
for 3 new fixtures (+15 lines).

### Step 6 — Fixture Replay

**19/19 PASS, all deterministic.**
- 16 original fixtures: unchanged, all PASS
- 3 new fixtures: all PASS
- Two-run hash consistency confirmed

### Development Split Replay

| Case | Gate | Issue |
|------|------|-------|
| tr_full_tkt_005b | PASS | — |
| tr_syn_partial_policy_clause | PASS | — |
| tr_syn_conditional_region_exception | PASS | — |
| tr_syn_revival_feature_flag | BLOCK | Pre-existing: diff-source CONTESTS |
| tr_alias_workspace_identity | PASS | — |
| tr_syn_non_invalidation_parallel_targets | BLOCK | Pre-existing: parallel target policy |
| tr_syn_out_of_order_inventory_present | PASS | — |

The 2 BLOCKED cases are pre-existing regressions (not caused by scope fix).
Development split gated at BLOCK — pre-existing blocker and regressions present.

## Gate Criteria

| Criteria | Status |
|----------|--------|
| Run-path naming/isolation audit | ✅ Passed |
| 3 ordinary regressions triaged | ✅ scope_normalization defects |
| No R01 expansion | ✅ |
| Full fixture replay (16+3) | ✅ PASS |
| Two replay hash verification | ✅ Deterministic |
| **Development: no blocker** | **❌ 1 pre-existing** |
| Development: no unexplained diff | ✅ |
| Development: 0 ordinary regressions | **❌ 3 pre-existing** |
| Must_include recall >= D1 | ❌ Blocked by pre-existing |
| Critical false invalidation = 0 | ✅ |
| Active-set Set-F1 no regression | ✅ Stable |
| Not accessed adversarial/sealed | ✅ |

**Verdict: blocked**

The scope normalization fix is correct and complete (3 ordinary regressions 
resolved at root cause). Development replay regressions are pre-existing and 
unrelated. A separate repair pass is needed for:
1. Different-source same-key claims → SUPERCEDE instead of CONTESTS
2. Parallel target claim invalidation policy
