# Stage04-B Blocker Triage Report

**Generated:** 2026-07-14T03:00:00Z
**Branch:** `phase1-lifecycle-stage02`
**Candidate commit:** `afe0dc3` (with shadow adjudicator fixes)
**Metrics version:** phase05_v3_shadow_v2

## Freeze Evidence

- Pre-fix run (afe0dc3): development BLOCK (1 blocker, 24 regressions), regression BLOCK (2 blockers, 33 regressions)
- Failure freeze recorded at: `reports/stage04b_failure_freeze.json`
- Pre-fix fixture failures: `lc_legacy_migration`, `lc_revival`, `lc_two_lifecycles_no_kill`
- Post-fix re-fixture: 11/11 PASS (8 original + 3 new)
- Current shadow script hashes:
  - `shadow_lifecycle_adjudicator.py`: `d75ca1bb02abe0ac`
  - `benchmark_shadow_runner.py`: `18e8612785a7d782`
  - `shadow_compiler.py`: `2db7d947b8d5ec08`
  - `shadow_bundle_builder.py`: `96e3d0fc5e1f24b5`
  - `fixture_replay_runner.py`: `fd298dcd659cc8e5`
- Decision table: `graph/projects/abu_modern/shadow_replay/contracts/shadow_adjudication_decision_table_v1.json`
- New fixtures: `lc_same_source_progression`, `lc_diff_source_conflict`, `lc_multi_claim_partial`

## Blocker and Regression Root-Cause Distribution (Development Split)

| Root Cause Layer | Count | Impact on must_include | Impact on active_set_f1 | Impact on false invalidation |
| --- | --- | --- | --- | --- |
| `entity_resolution` | 7 | must_include recall drops to 0.5 on partial/clause and conditional cases | active_set_f1 drops to 0.5 on multi-claim coexists cases | supersedes coexisting claims (3 blockers) |
| `lifecycle_resolution` | 2 | none directly | active_set_f1 dropped to 0.6667 | none |
| `adjudication_relation` | 1 | none | none | one CONTESTS classified as insufficient (tr_syn_revival_feature_flag) |
| `observed_effective_time_ordering` | 1 | must_include recall drops to 0.0 on out-of-order inventory case | active_set_f1 drops to 0.3333 | supersedes late-arriving claim |
| `gold_or_baseline_defect` | 0 | — | — | — |
| `unresolved` | 0 | — | — | — |

## Per-Blocker Analysis

### Blocker B1-1: tr_syn_partial_policy_clause — missing must_include `tr03.retries.2`

```
case_id:              tr_syn_partial_policy_clause
checkpoint_id:        cp_after_tr03_obs01
raw observation:      obs01 has 3 claims (timeout=30s, retries=2, audit=required)
                        source channel=policy_doc, mentions=["Order gateway policy"]
old-chain output:     Not available (shadow-only run)
shadow adapter output: 3 events, each with entity_ref="Order gateway policy",
                        lifecycle_ref="Order gateway policy", source="policy_doc"
resolved entity_ref:  "Order gateway policy" (from mentions[0])
resolved lifecycle_ref: "Order gateway policy" (same as entity_ref)
adjudication_key:     "Order gateway policy" (lifecycle_ref fallback)
relation classification: Claim2 supersedes Claim1, Claim3 supersedes Claim2
                        (same entity/lc/adj_key → each new claim supersedes previous)
expected gold state:    active={tr03.timeout.30s, tr03.retries.2, tr03.audit.required}
actual shadow state:    active={tr03.audit.required} only (last claim survives)
must_include impact:    tr03.retries.2 missing → must_include recall=0.5
quarantine decision:    none
root-cause layer:      entity_resolution
proposed minimal fix:  Claims from the same observation must COEXIST, not SUPERCEDE.
                        Fix applied: _observation_base filtering in adjudicator prevents
                        sibling claims from superseding each other. Additional fix needed:
                        claims from different observations of the same entity that reference
                        different dimensions (timeout vs retries vs audit) should COEXIST.
                        Requires claim-dimension-aware entity resolution.
```

### Blocker B1-2: tr_syn_partial_policy_clause — missing must_include `tr03.timeout.30s` (cp_after_tr03_obs02)

```
case_id:              tr_syn_partial_policy_clause
checkpoint_id:        cp_after_tr03_obs02
raw observation:      obs02 has 1 claim (retries=4)
shadow adapter output: 1 event, entity_ref="Order gateway policy", source="policy_doc"
adjudication_key:     "Order gateway policy"
relation classification: SUPERCEDES (same channel, same entity)
expected gold state:    active={tr03.timeout.30s, tr03.retries.4, tr03.audit.required}
actual shadow state:    active={tr03.retries.4} only (supersedes tr03.audit.required)
must_include impact:    tr03.timeout.30s missing → must_include recall=0.5
root-cause layer:      entity_resolution
proposed minimal fix:  Claims within an entity that are about different dimensions
                        should not supersede each other. The fix requires a resolver-level
                        understanding of claim dimensions to determine which claims
                        replace which. Out of scope for current shadow adjudicator.
```

### Blocker B2: tr_syn_conditional_region_exception — missing `tr05.trading.blocked.global`

```
case_id:              tr_syn_conditional_region_exception
checkpoint_id:        cp_after_tr05_obs02
raw observation:      obs01 claim='blocked_global', obs02 claim='tokyo_simulation_allowed'
                        Both from channel=risk_memo, mentions=["Deployment rule"]
shadow:               both events share entity_ref="Deployment rule" → SUPERCEDES
expected gold:        active={blocked.global, allowed.tokyo.sim} (conditional exception)
actual shadow:        active={allowed.tokyo.sim} only
root-cause layer:      entity_resolution
proposed fix:         Conditional exceptions need COEXISTS, not SUPERCEDES.
                        Requires the adapter to emit events with different lifecycle_refs
                        for different scopes or a resolver to mark conditionality.
```

### Blocker B3: tr_syn_non_invalidation_parallel_targets — missing `tr12.target.staging.allowed`

```
case_id:              tr_syn_non_invalidation_parallel_targets
checkpoint_id:        cp_after_tr12_obs02
raw observation:      obs01 claim='staging', obs02 claim='canary'
                        Both from channel=release_sheet, mentions=["Deployment allow-list"]
shadow:               same entity_ref → SUPERCEDES
expected gold:        active={staging, canary} (parallel targets)
actual shadow:        active={canary} only
root-cause layer:      entity_resolution
proposed fix:         Parallel targets need COEXISTS. Same as B2.
```

### Blocker B4: tr_syn_out_of_order_inventory_present — missing `tr14.inventory.10`

```
case_id:              tr_syn_out_of_order_inventory_present
checkpoint_id:        cp_after_tr14_obs02
raw observation:      obs01 claim=10 (warehouse_feed#1005, effective=2026-01-02)
                        obs02 claim=0 (warehouse_feed#1000_late, effective=2026-01-01)
                        Same channel=warehouse_feed, mentions=["Inventory snapshot"]
shadow:               same entity_ref → SUPERCEDES (obs02 replaces obs01)
expected gold:        active={10} only (late arrival does not replace)
actual shadow:        active={0} (wrong claim active)
root-cause layer:      observed_effective_time_ordering
proposed fix:         The adjudicator must check effective_at ordering.
                        If obs02's effective_at < obs01's, it should not SUPERCEDE.
                        This requires time-awareness in the adjudicator.
```

### Blocker B5: tr_syn_revival_feature_flag — `tr07.feature.enabled.v1` unexpected active

```
case_id:              tr_syn_revival_feature_flag
checkpoint_id:        cp_after_tr07_obs02
raw observation:      obs01 (release_note channel): enabled
                        obs02 (incident_note channel): disabled
                        Different source channels → CONTESTS in shadow
expected gold:        active={disabled}, invalid={enabled.v1}
actual shadow:        active={enabled.v1, disabled} (CONTESTS, both active)
root-cause layer:      adjudication_relation
assessment:           CONSERVATIVE. The shadow CONTESTS behavior follows the RFC:
                        provenance conflicts should not be collapsed to SUPERCEDES.
                        The gold assumes incident_note authority > release_note authority.
                        This is a design choice, not a bug. Classified as expected_schema_change.
```

## Representative Regression Analysis (Top 10)

| # | Case | Checkpoint | Diff Kind | Claim | Root-Cause Layer | Explanation |
| --- | --- | --- | --- | --- | --- | --- |
| R1 | tr_syn_partial_policy_clause | cp_after_tr03_obs01 | active_set | tr03.audit.required | entity_resolution | Same entity/adj_key causes 3 sibling claims to collapse to 1 active node. |
| R2 | tr_syn_partial_policy_clause | cp_after_tr03_obs02 | active_set | tr03.audit.required | entity_resolution | Multi-claim collapse from obs01 persists. tr03.audit.required never created as independent node. |
| R3 | tr_syn_partial_policy_clause | cp_after_tr03_obs02 | invalidation | tr03.retries.2 | entity_resolution | tr03.retries.2 was never created independently (collapsed in obs01 resolution), so can't be found in superseded set. |
| R4 | tr_syn_revival_feature_flag | cp_after_tr07_obs02 | active_set | tr07.feature.enabled.v1 | adjudication_relation | CONTESTS from different channels keeps both active. Gold expects only the most recent. |
| R5 | tr_syn_revival_feature_flag | cp_after_tr07_obs02 | invalidation | tr07.feature.enabled.v1 | adjudication_relation | CONTESTS means no supersession. expected_invalidation not found. |
| R6 | tr_syn_out_of_order_inventory_present | cp_after_tr14_obs02 | active_set | tr14.inventory.10 | observed_effective_time_ordering | Late-arriving claim replaces earlier instead of coexisting. |
| R7 | tr_syn_out_of_order_inventory_present | cp_after_tr14_obs02 | active_set | tr14.inventory.0 | observed_effective_time_ordering | Late claim active when it should be ignored. |
| R8 | tr_syn_conditional_region_exception | cp_after_tr05_obs02 | active_set | tr05.trading.blocked.global | entity_resolution | Conditional exception treated as full replacement, not COEXISTS. |
| R9 | tr_syn_non_invalidation_parallel_targets | cp_after_tr12_obs02 | active_set | tr12.target.staging.allowed | entity_resolution | Parallel targets treated as replacement, not COEXISTS. |
| R10 | tr_syn_out_of_order_inventory_present | cp_after_tr14_obs02 | must_include | tr14.inventory.10 | observed_effective_time_ordering | Dropped from bundle because wrong node is active. |

## Distribution Summary

| Root Cause Layer | Development | Regression | Adversarial |
| --- | --- | --- | --- | --- |
| `entity_resolution` | 7 (all COEXISTS-style scenarios) | 7 | 0 |
| `adjudication_relation` | 2 (CONTESTS vs SUPERCEDES) | 2 | 0 |
| `observed_effective_time_ordering` | 2 (late arrival) | 2 | 0 |
| `input_adapter` | 0 | 0 | 0 |
| `shadow_compiler` | 0 | 0 | 0 |
| `bundle_assembly` | 0 | 0 | 0 |
| `gold_or_baseline_defect` | 0 | 0 | 0 |
| `unresolved` | 0 | 0 | 0 |

## Impact on Key Metrics

| Metric | Baseline | Development (current) | Impact |
| --- | --- | --- | --- |
| must_include recall | 1.0 (D1) | 0.0 (tr14) / 0.5 (tr03, tr05, tr12) | 3 blocker-dropped must_include |
| active-set Set-F1 | 0.8979 (Phase0) | 0.0 (tr14) / 0.5 (tr03) / 0.6667 (tr05,tr12,tr07) | COEXISTS vs SUPERCEDES mismatch |
| false invalidation | 0 | 3 (coexisting claims wrongly superseded) | 3 blockers |
| quarantine rate | 0 | 0 | quarantine not triggered |

## Gate Decision

**`blocked`** — Development split has 5 unresolved blockers. No regression or blind-holdout allowed.

The remaining 5 blockers are diverse and require deeper entity resolution and time-ordering logic.
These cannot be fixed within the current shadow adjudicator's simple adapter architecture.

## Recommended Next Steps

1. Accept that the current shadow adjudicator covers **linear progression and provenance conflict** correctly (tr_full_tkt_005b, tr_same_source_progression, tr_diff_source_conflict, fixtures), but does not handle **multi-claim entity resolution** or **out-of-order time semantics**.
2. For the real main-chain implementation, the resolver must provide dimension-aware adjudication keys so that timeout vs retries vs audit coexist.
3. The conditional/parallel non-invalidation cases require the adjudicator to reference claim dimensions for COEXISTS vs SUPERCEDES decisions.
4. Out-of-order inventory requires observed_at/effective_at comparison in the adjudicator or compiler.
5. The CONTESTS-vs-SUPERCEDES choice for different channels (tr_syn_revival_feature_flag) should be a conscious design decision, not a bug.
