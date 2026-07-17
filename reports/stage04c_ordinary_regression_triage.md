# Stage04-C Ordinary Regression Triage

**Generated:** 2026-07-14T09:40:00Z

## Regression 1: tr_syn_partial_checklist_clause (cp_after_tr04_obs02, claim tr04.slippage_report.required)

### Raw Observations

| Observation | Claims |
|-------------|--------|
| tr04_obs01 (T09:00) | tr04.backtest.required=[required], tr04.paper_trade.required=[required], tr04.slippage_report.required=[required] |
| tr04_obs02 (T09:20) | tr04.slippage_report.not_required=[not_required] |

### Claim Decomposition

| Claim ID | Entity | Dimension | Scope (current) | State |
|----------|--------|-----------|----------------|-------|
| tr04.backtest.required | Replay checklist | backtest | required | required |
| tr04.paper_trade.required | Replay checklist | paper_trade | required | required |
| tr04.slippage_report.required | Replay checklist | slippage_report | required | required |
| tr04.slippage_report.not_required | Replay checklist | slippage_report | not_required | not_required |

### Adjudication Keys (current)

| Claim | Key |
|-------|-----|
| tr04.slippage_report.required | Replay checklist:slippage_report:required |
| tr04.slippage_report.not_required | Replay checklist:slippage_report:not_required |

### Problem

Scope extraction treats equired and 
ot_required as semantic scope values, producing different adjudication keys. Gold expects slippage_report.required to be SUPERCEDED by slippage_report.not_required (same dimension, same scope, different state ¡ª lifecycle update).

### Root Cause Layer

**scope_normalization**

equired and 
ot_required are states of the same dimension (slippage_report), not different scopes. The current scope extraction rule uses the claim_id's third segment (after second dot) as scope, but in this case equired/
ot_required is the claim VALUE, not a scope identifier.

**Proposed repair:** When claim_id has format <entity>.<dimension>.<value> and the "scope" segment appears to be a boolean/state value (equired/
ot_required/enabled/disabled), normalize scope to a constant default and treat the value as claim state rather than scope.

---

## Regression 2: tr_syn_partial_checklist_clause (cp_after_tr04_obs02, claim tr04.slippage_report.required - false negative invalidation)

This is the mirror of Regression 1. Gold expects slippage_report.required in the superseded set (via partial invalidation). Shadow has it active (not superseded) because different adjudication keys prevent the SUPERCEDES relation.

### Root Cause Layer

**scope_normalization** (same root cause as Regression 1)

### Additional Detail

| Check | Value |
|-------|-------|
| Gold invalidation set | [tr04.slippage_report.required] |
| Shadow superseded set | [] |
| Shadow active set | [tr04.slippage_report.required, tr04.slippage_report.not_required] |
| False-negative invalidation | tr04.slippage_report.required expected superseded but active |

---

## Regression 3: tr_syn_out_of_order_price_band_present (cp_after_tr22_obs02, claim tr22.price_band.narrow)

### Raw Observations

| Observation | Claims | observed_at | effective_at |
|-------------|--------|-------------|--------------|
| tr22_obs01 | tr22.price_band.wide=[wide] | 2026-06-22T10:05:00Z | 2026-06-22T10:05:00Z |
| tr22_obs02 | tr22.price_band.narrow=[narrow] | 2026-06-22T10:01:00Z | 2026-06-22T10:01:00Z |

### Key Observation

tr22_obs02 has observed_at < tr22_obs01.observed_at but arrives after tr22_obs01. This is a late-arrival event.

### Gold Expectation

Gold expects 	r22.price_band.wide to remain active after tr22_obs02. 	r22.price_band.narrow should NOT replace 	r22.price_band.wide because it's a late arrival with earlier effective_at.

### Shadow Behavior

Shadow treats wide and 
arrow as different scope values, producing different adjudication keys:
- 	r22.price_band.wide: key=Price band:price_band:wide
- 	r22.price_band.narrow: key=Price band:price_band:narrow

Different keys -> COEXISTS. Both active. False regression: 
arrow should not appear in active set.

### Root Cause Layer

**time_ordering / scope_normalization**

Two issues:
1. wide and 
arrow are different state values for the same price_band dimension, not different scopes. Scope should be normalized to a constant.
2. Even if scope is fixed, the late-arrival rule (R010) must prevent 
arrow from SUPERCEDING wide because 
arrow.effective_at < wide.effective_at and 
arrow arrived after wide.

### Proposed Repair

1. Normalize state-like scope values (wide/
arrow) to a constant default for claims on the same entity+dimension.
2. Apply late-arrival time-ordering rule: if B.observed_at > A.observed_at but B.effective_at < A.effective_at, B should not SUPERCEDE A (coexist with warning or quarantine).

---

## Summary

| Regression | Case | Root Cause Layer | Verdict |
|------------|------|-----------------|---------|
| 1 | tr_syn_partial_checklist_clause | scope_normalization | defect |
| 2 | tr_syn_partial_checklist_clause | scope_normalization | defect |
| 3 | tr_syn_out_of_order_price_band_present | time_ordering / scope_normalization | defect |

All 3 are **scope_normalization defects**: state values (equired/
ot_required, wide/
arrow) being mistakenly treated as scope discriminators instead of claim state values.

**Not genuinely_ambiguous.** These are deterministic implementation defects in the scope extraction logic.
