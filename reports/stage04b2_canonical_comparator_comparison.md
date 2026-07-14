# Stage04-B2 Canonical Comparator Comparison

**Generated:** 2026-07-14T06:00:00Z  
**Method:** Both A (pre-fix) and B (post-fix) run through the SAME current comparator

## Candidate Versions

| Attribute | Pre-Fix (A) | Post-Fix (B) |
|-----------|-------------|--------------|
| Candidate commit | afe0dc3 (old shadow scripts) | d7d681e + uncommitted shadow fixes |
| Runner commit | Same comparator (d7d681e-based with invalidation audit) | Same |
| Pre-fix run ID | stage04b_20260714T060323_development | — |
| Post-fix run ID | — | stage04b_20260714T060357_development |

## Aggregate Summary

Pre-fix shut down the system after the proposed change. | Metric | Pre-Fix | Post-Fix | Delta |
|--------|---------|----------|-------|
| Blockers | 1 | 0 | **-1** |
| Regressions | 24 | 4 | **-20** |
| Min must_include_recall | 0.5 | 1.0 | **+0.5** |
| Min active_set_set_f1 | 0.3333 | 0.6667 | **+0.3334** |

## Per-Case Breakdown

| Case | Pre-Fix Gate | Pre Blockers | Pre Regressions | Post-Fix Gate | Post Blockers | Post Regressions |
|------|-------------|-------------|-----------------|---------------|---------------|------------------|
| tr_full_tkt_005b | BLOCK | 0 | 14 | PASS | 0 | 0 |
| tr_syn_partial_policy_clause | BLOCK | 1 | 5 | PASS | 0 | 0 |
| tr_syn_conditional_region_exception | BLOCK | 0 | 1 | PASS | 0 | 0 |
| tr_syn_revival_feature_flag | BLOCK | 0 | 0 | BLOCK | 0 | 4 |
| tr_alias_workspace_identity | BLOCK | 0 | 3 | PASS | 0 | 0 |
| tr_syn_non_invalidation_parallel_targets | BLOCK | 0 | 1 | PASS | 0 | 0 |
| tr_syn_out_of_order_inventory_present | BLOCK | 0 | 0 | PASS | 0 | 0 |

## Key Improvements

- **tr_full_tkt_005b**: Multi-claim adapter replaces single-obs->single-claim collapse; lifecycle progression correctly handled via claim_id matching in compare_step
- **tr_syn_partial_policy_clause**: Scope heuristic correctly assigns `_default_` for numeric values (2, 4, 30s) so partial policy update works
- **tr_alias_workspace_identity**: CONTESTS correctly identifies different-provenance same-key claims
- **tr_syn_non_invalidation_parallel_targets**: Scope heuristic correctly assigns semantic scopes (staging, canary) for parallel targets

## Residual

- **tr_syn_revival_feature_flag**: 4 regressions are all `manual_adjudication` (single-track vs multi-track scope model difference). Formal adjudication record exists.

## Comparator Metadata

- **Comparator hash**: d7d681e-based with bidirectional invalidation audit
- **Metrics version**: phase05_v3_shadow_v2
- **Diff spec hash**: shadow_replay_spec.md (unchanged)
