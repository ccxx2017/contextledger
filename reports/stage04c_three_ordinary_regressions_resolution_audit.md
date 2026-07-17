# Stage04-C Three Ordinary Regressions Resolution Audit

**Generated:** 2026-07-14T10:40:00Z

## Pre-fix Status (Stage04-C1 regression run)

Three ordinary regressions were identified at Stage04-C1:
1. **tr_syn_partial_checklist_clause** × 2 (two false-negative invalidations)
2. **tr_syn_out_of_order_price_band_present** × 1 (active-set and invalidation errors)

All three were root-caused to **scope_normalization defect**: claim_id third
segment values like `required`/`not_required` and `wide`/`narrow` were 
incorrectly treated as semantic scope values, producing different adjudication_keys
for claims that should share the same entity:dimension:scope key.

## Post-fix Verification

### Fix Applied

**File:** `shadow_resolution_adapter.py::_extract_scope_v2()`

1. Added versioned scope normalization mapping:  
   `contracts/shadow_scope_normalization_mapping_v1.json` (20 tokens, 5 rule categories)
2. Before using claim_id third segment as scope, check the versioned mapping.
3. If token matches a known state value, fall through to `_default_` scope.
4. Only the versioned mapping (not heuristic `seg == claim.value`) is authoritative.

### Verification: tr_syn_partial_checklist_clause

**Pre-fix:**  
- `tr04.slippage_report.required` → scope=`required` → adj_key=`Replay checklist:slippage_report:required`  
- `tr04.slippage_report.not_required` → scope=`not_required` → adj_key=`Replay checklist:slippage_report:not_required`
- Different keys → COEXISTS → false-negative invalidation

**Post-fix:**  
- `required` ∈ STATE_VALUE_TOKENS → scope=`_default_`
- `not_required` ∈ STATE_VALUE_TOKENS → scope=`_default_`
- Same adj_key: `Replay checklist:slippage_report:_default_`
- Same source → SUPERCEDES → correct invalidation ✅

**Fixture verification:** New fixture `lc_partial_same_dimension_same_scope_supersedes`
PASS with SUPERCEDES relation.

### Verification: tr_syn_out_of_order_price_band_present

**Pre-fix:**  
- `tr22.price_band.wide` → scope=`wide` → adj_key=`Price band:price_band:wide`  
- `tr22.price_band.narrow` → scope=`narrow` → adj_key=`Price band:price_band:narrow`
- Different keys → COEXISTS → late-arrival not detected

**Post-fix:**  
- `wide` ∈ STATE_VALUE_TOKENS → scope=`_default_`
- `narrow` ∈ STATE_VALUE_TOKENS → scope=`_default_`
- Same adj_key: `Price band:price_band:_default_`
- Late-arrival detected: effective_at(T10:01) < previous observed_at(T10:05)
- Quarantine applied ✅

**Fixture verification:** New fixture `lc_late_arrival_price_band_same_scope_vs_different_scope`
PASS with quarantine.

### Conclusion

All three ordinary regressions are **resolved** by the scope normalization fix.
Each was caused by the same root defect: claim_id third segment misinterpreted as scope.

## Evidence

| Case | Pre-fix adj_key | Post-fix adj_key | Verified by |
|------|-----------------|------------------|-------------|
| tr_syn_partial_checklist_clause (required) | `Replay checklist:slippage_report:required` | `Replay checklist:slippage_report:_default_` | New fixture PASS |
| tr_syn_partial_checklist_clause (not_required) | `Replay checklist:slippage_report:not_required` | `Replay checklist:slippage_report:_default_` | New fixture PASS |
| tr_syn_out_of_order_price_band_present (wide) | `Price band:price_band:wide` | `Price band:price_band:_default_` | New fixture PASS |
| tr_syn_out_of_order_price_band_present (narrow) | `Price band:price_band:narrow` | `Price band:price_band:_default_` | New fixture PASS |
