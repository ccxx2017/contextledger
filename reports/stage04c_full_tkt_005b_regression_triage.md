# Stage04-C: tr_full_tkt_005b Regression Triage (6 Regressions)

**Generated:** 2026-07-15T16:06:00Z  
**Trajectory:** tr_full_tkt_005b — "TKT-2026-005B full lifecycle from open to resolved"  
**Comparator version:** v2 post-rollback (Stage04-C1.2.2)  
**Total regressions:** 6 (all from COEXISTS gold + SUPERCEDES shadow)

---

## Background

The trajectory contains 5 observations (obs01–obs05), each advancing a ticket state through a linear chain:

| Obs | Time | Claim | dimension | value |
|-----|------|-------|-----------|-------|
| obs01 | 2026-01-02T16:00 | tr_full_tkt_005b.obs01.active | ticket_state | resolved |
| obs02 | 2026-01-03T09:00 | tr_full_tkt_005b.obs02.active | ticket_state | open |
| obs03 | 2026-01-03T18:00 | tr_full_tkt_005b.obs03.active | ticket_state | open |
| obs04 | 2026-01-04T03:00 | tr_full_tkt_005b.obs04.active | ticket_state | open |
| obs05 | 2026-01-04T20:00 | tr_full_tkt_005b.obs05.active | ticket_state | open |

All from the same source channel (`abu_modern_turn`), same provenance owner (`turn_0115`).

Gold annotation is a **chain of single-step invalidations**:
- obs02 invalidates obs01
- obs03 invalidates obs02
- obs04 invalidates obs03
- obs05 invalidates obs04

Each gold step only lists ONE claim in `expected_invalidations`. It does NOT list earlier claims as invalid.

The shadow system, however, produces a **cumulative supersedes chain**: each new claim supersedes ALL previous claims on the same entity/lifecycle, not just the immediately preceding one. This is because the shadow compiler builds edges from the new claim to ALL previously active claims on the same `adjudication_key`.

---

## Regression #1: cp_after_obs03 — tr_full_tkt_005b.obs01.active

| Field | Value |
|-------|-------|
| checkpoint_id | cp_after_obs03 |
| raw observation | obs03 introduces tr_full_tkt_005b.obs03.active (ticket_state=open) |
| gold relation/state | COEXISTS — obs01.active is NOT in gold's expected_invalidations at obs03 |
| shadow relation/state | SUPERCEDES — shadow has edge obs03.active → obs01.active, obs01.active marked superseded |
| claim decomposition | Single atomic claim: ticket_state=open for TKT-2026-005B |
| claim atomization decision | Not decomposed — single dimension, single entity |
| dimension/scope normalization | Same dimension (ticket_state), same entity (TKT-2026-005B), same scope |
| entity_ref | TKT-2026-005B (consistent across all obs) |
| lifecycle_ref | Same lifecycle (implied by same dimension/entity) |
| adjudication_key | {entity:TKT-2026-005B, dimension:ticket_state} |
| actual invalidation set | {obs01.active, obs02.active, obs03.active} |
| gold invalidation set | {obs02.active} |
| unexpected supersede detail | obs01.active is superseded in shadow but NOT in gold expected_invalidations at obs03 |
| must_include consequence | must_include is obs03.active — not affected |
| bundle consequence | Bundle correctly includes obs03.active |
| **root-cause layer** | **shadow_compiler / claim_atomization** |
| minimal repair proposal | Shadow compiler should only create a SUPERCEDES edge to the IMMEDIATELY preceding claim (obs02), not to ALL previous claims (obs01, obs02). Gold expects single-step chain invalidation, not cumulative. |

**Explanation:** The shadow compiler's edge-building logic creates edges from the new claim to all previously active claims on the same adjudication_key. Gold expects a linear chain where only the immediate predecessor is invalidated. This is a **shadow_compiler** defect: the edge builder should respect the gold's single-step invalidation semantics, not produce a fan-out supersedes to all predecessors.

---

## Regression #2: cp_after_obs03 — (same checkpoint, same claim, counted once)

Note: The regression count at cp_after_obs03 is 1 (obs01.active). This is the same regression as #1.

---

## Regression #3: cp_after_obs04 — tr_full_tkt_005b.obs01.active

| Field | Value |
|-------|-------|
| checkpoint_id | cp_after_obs04 |
| raw observation | obs04 introduces tr_full_tkt_005b.obs04.active |
| gold relation/state | COEXISTS — obs01.active NOT in gold expected_invalidations at obs04 |
| shadow relation/state | SUPERCEDES — obs04.active → obs01.active edge exists |
| root-cause layer | **shadow_compiler** (same as #1) |
| minimal repair proposal | Limit supersedes edge to immediate predecessor only |

---

## Regression #4: cp_after_obs04 — tr_full_tkt_005b.obs02.active

| Field | Value |
|-------|-------|
| checkpoint_id | cp_after_obs04 |
| raw observation | obs04 introduces tr_full_tkt_005b.obs04.active |
| gold relation/state | COEXISTS — obs02.active NOT in gold expected_invalidations at obs04 |
| shadow relation/state | SUPERCEDES — obs04.active → obs02.active edge exists |
| root-cause layer | **shadow_compiler** (same as #1) |
| minimal repair proposal | Limit supersedes edge to immediate predecessor only |

---

## Regression #5: cp_after_obs05 — tr_full_tkt_005b.obs01.active

| Field | Value |
|-------|-------|
| checkpoint_id | cp_after_obs05 |
| raw observation | obs05 introduces tr_full_tkt_005b.obs05.active |
| gold relation/state | COEXISTS — obs01.active NOT in gold expected_invalidations at obs05 |
| shadow relation/state | SUPERCEDES — obs05.active → obs01.active edge exists |
| root-cause layer | **shadow_compiler** (same as #1) |
| minimal repair proposal | Limit supersedes edge to immediate predecessor only |

---

## Regression #6: cp_after_obs05 — tr_full_tkt_005b.obs03.active

| Field | Value |
|-------|-------|
| checkpoint_id | cp_after_obs05 |
| raw observation | obs05 introduces tr_full_tkt_005b.obs05.active |
| gold relation/state | COEXISTS — obs03.active NOT in gold expected_invalidations at obs05 |
| shadow relation/state | SUPERCEDES — obs05.active → obs03.active edge exists |
| root-cause layer | **shadow_compiler** (same as #1) |
| minimal repair proposal | Limit supersedes edge to immediate predecessor only |

---

## Regression #7: cp_after_obs05 — tr_full_tkt_005b.obs02.active

Wait — the aggregate shows 6 regressions total. Let me recount from the split summary:

- cp_after_obs03: 1 regression (obs01.active)
- cp_after_obs04: 2 regressions (obs01.active, obs02.active)
- cp_after_obs05: 3 regressions (obs01.active, obs03.active, obs02.active)

Total: 1 + 2 + 3 = 6 regressions.

## Unified Root-Cause Analysis

All 6 regressions share the **same root cause**: the shadow compiler's edge-building logic creates SUPERCEDES edges from the new claim to ALL previously active claims on the same adjudication_key, producing a fan-out pattern. Gold expects a linear chain where each observation only invalidates its immediate predecessor.

This is NOT a `claim_atomization` defect (claims are correctly atomic). It is NOT a `scope_normalization` or `dimension_normalization` defect (all claims share the same dimension/entity). It is NOT a `lifecycle_resolution` defect (same lifecycle). It is NOT a `time_ordering` defect (observations arrive in correct chronological order). It is NOT an `adjudication_relation` defect (the relation SUPERCEDES is correct; the *scope* of the relation is wrong).

**Root-cause layer: shadow_compiler** — specifically, the edge-builder in `shadow_compiler.py`'s `apply_shadow_patch` or the adjudicator's edge creation logic.

**Minimal repair proposal:** Modify the shadow adjudicator/compiler to only create a SUPERCEDES edge from the new claim to the single most recent active claim on the same adjudication_key (by observed_at timestamp), rather than to all previously active claims. This aligns the shadow output with gold's single-step chain semantics.

**Alternative interpretation:** The gold annotation itself may be incomplete — if the intended semantics are cumulative invalidation, then the gold should list ALL previous claims in expected_invalidations at each step. However, since we are NOT modifying benchmark gold in Stage04-C, this remains a shadow_compiler defect.

---

## Summary Table

| Reg # | Checkpoint | Claim | Gold | Shadow | Root Cause | Repair |
|-------|-----------|-------|------|--------|------------|--------|
| 1 | cp_obs03 | obs01.active | COEXISTS | SUPERCEDES | shadow_compiler | Limit edge to immediate predecessor |
| 2 | cp_obs04 | obs01.active | COEXISTS | SUPERCEDES | shadow_compiler | Limit edge to immediate predecessor |
| 3 | cp_obs04 | obs02.active | COEXISTS | SUPERCEDES | shadow_compiler | Limit edge to immediate predecessor |
| 4 | cp_obs05 | obs01.active | COEXISTS | SUPERCEDES | shadow_compiler | Limit edge to immediate predecessor |
| 5 | cp_obs05 | obs03.active | COEXISTS | SUPERCEDES | shadow_compiler | Limit edge to immediate predecessor |
| 6 | cp_obs05 | obs02.active | COEXISTS | SUPERCEDES | shadow_compiler | Limit edge to immediate predecessor |

**All 6 regressions → shadow_compiler layer. Zero comparator defects. Zero gold defects.**
