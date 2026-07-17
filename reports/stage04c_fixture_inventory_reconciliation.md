# Stage04-C Fixture Inventory Reconciliation

**Generated:** 2026-07-14T11:05:00Z

## Full Fixture Inventory (22 total)

| # | fixture_id | file | hash | category | round | result |
|---|-----------|------|------|----------|-------|--------|
| 1 | lc_alias_abstain | lc_alias_abstain.json | 6ef51ef36214e87b | alias_abstain | original_16 | PASS (deterministic) |
| 2 | lc_conditional_different_scope | lc_conditional_different_scope.json | 2cf692f66a743f63 | conditional | original_16 | PASS (deterministic) |
| 3 | lc_diff_source_conflict | lc_diff_source_conflict.json | 912c51cfe61099f5 | provenance_conflict | original_16 | PASS (deterministic) |
| 4 | lc_late_arrival | lc_late_arrival.json | 972621a2d9e2c868 | late_arrival | original_16 | PASS (deterministic) |
| 5 | lc_late_arrival_effective_time | lc_late_arrival_effective_time.json | 391361966b72a613 | late_arrival | original_16 | PASS (deterministic) |
| 6 | lc_late_arrival_missing_effective | lc_late_arrival_missing_effective.json | 944ddfe7adb4bb7b | late_arrival | original_16 | PASS (deterministic) |
| 7 | lc_late_arrival_price_band_same_scope_vs_different_scope | lc_late_arrival_price_band_same_scope_vs_different_scope.json | 2923a186c640ec08 | late_arrival | stage04c_scope_fix | PASS (deterministic) |
| 8 | lc_legacy_migration | lc_legacy_migration.json | 075ba8d67eaf28f7 | legacy_migration | original_16 | PASS (deterministic) |
| 9 | lc_multi_claim_different_predicates | lc_multi_claim_different_predicates.json | 9e1a7d7c4c99716d | multi_claim | original_16 | PASS (deterministic) |
| 10 | lc_multi_claim_partial | lc_multi_claim_partial.json | 6b8143e509006c1b | multi_claim | original_16 | PASS (deterministic) |
| 11 | lc_parallel_target_coexist | lc_parallel_target_coexist.json | b6c875b733334947 | parallel | original_16 | PASS (deterministic) |
| 12 | lc_parallel_targets_same_dimension_must_coexist | lc_parallel_targets_same_dimension_must_coexist.json | 4cb4d2cc0d8e7e39 | parallel | stage04c1_2_new | PASS (deterministic) |
| 13 | lc_partial_same_dimension_different_atomic_claims_coexist | lc_partial_same_dimension_different_atomic_claims_coexist.json | c18dabd950ca0b97 | partial_update | stage04c_scope_fix | PASS (deterministic) |
| 14 | lc_partial_same_dimension_same_scope_supersedes | lc_partial_same_dimension_same_scope_supersedes.json | cdb15d25857baadf | partial_update | stage04c_scope_fix | PASS (deterministic) |
| 15 | lc_provenance_conflict | lc_provenance_conflict.json | 86b31998d3e62ca8 | provenance_conflict | original_16 | PASS (deterministic) |
| 16 | lc_replay_determinism | lc_replay_determinism.json | 6dfe08d205595ead | replay_determinism | original_16 | PASS (deterministic) |
| 17 | lc_revival | lc_revival.json | afa54857bc64c716 | revival | original_16 | PASS (deterministic) |
| 18 | lc_same_key_different_source_r01 | lc_same_key_different_source_r01.json | d8753f92e4e68733 | provenance_conflict | stage04c1_2_new | PASS (deterministic) |
| 19 | lc_same_source_progression | lc_same_source_progression.json | de39e226a51d2d13 | input_adapter | original_16 | PASS (deterministic) |
| 20 | lc_sequence_collision | lc_sequence_collision.json | 3b46dfe81136fa34 | sequence_collision | original_16 | PASS (deterministic) |
| 21 | lc_state_value_vs_real_scope_ambiguity | lc_state_value_vs_real_scope_ambiguity.json | 7e8069c1060e1bf5 | scope_normalization | stage04c1_2_new | PASS (deterministic) |
| 22 | lc_two_lifecycles_no_kill | lc_two_lifecycles_no_kill.json | 72a1b99c9ef4fdcd | lifecycle_identity | original_16 | PASS (deterministic) |

## Round Summary

- Original 16: 16/16 PASS
- Stage04-C scope fix (+3): 3/3 PASS
- Stage04-C1.2 new (+3): 3/3 PASS
- **Total: 22/22 PASS, all deterministic**

## Coverage

| C1.1 Required Fixture | Status | Notes |
|---------------------|--------|-------|
| same_key_different_source_with_R01_behavior | ✅ lc_same_key_different_source_r01 | CONTESTS coexistence |
| parallel_targets_same_dimension_must_coexist | ✅ lc_parallel_targets_same_dimension_must_coexist | Different scope values COEXIST |
| state_value_token_vs_real_scope_ambiguity | ✅ lc_state_value_vs_real_scope_ambiguity | enabled→_default_ vs staging→keep |
