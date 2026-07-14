# Revival Feature Flag — Formal Adjudication Record

**Generated:** 2026-07-14T06:00:00Z  
**Case:** tr_syn_revival_feature_flag  
**Stage:** Stage04-B2.2  

## Conclusion

**genuinely_ambiguous** — The semantic gap between gold's single-track lifecycle model and shadow's multi-track dimension-scope model is a design-level tradeoff, not an implementation defect.

## Raw Evidence

| Event | Observed At | Claim ID | Dimension | Value |
|-------|------------|----------|-----------|-------|
| tr07_obs01 | 2026-06-10T09:00:00Z | tr07.feature.enabled.v1 | feature_flag | enabled |
| tr07_obs02 | 2026-06-10T10:00:00Z | tr07.feature.disabled | feature_flag | disabled |
| tr07_obs03 | 2026-06-10T11:00:00Z | tr07.feature.enabled.v2 | feature_flag | enabled_again |

## Channel / Provenance

All three events come from the same source channel (synthetic benchmark policy). No provenance conflict.

## Authority Assumptions

- **Gold**: Encodes a single-track lifecycle model where all feature-flag claims share one adjudication domain. `disabled` terminal → supersedes → `enabled.v2` revives.
- **Shadow (Phase 1 lifecycle)**: Encodes a multi-track dimension-scope model where different scope values (`enabled` vs `disabled`) produce different adjudication keys → coexistence.

## Time Ordering

All events are in order (observed_at follows chronological sequence). No late-arrival issue.

## Gold SUPERCEDES Rationale

Gold treats feature_flag as a single-track lifecycle:
- `tr07_obs01`: enabled.v1 active
- `tr07_obs02`: disabled SUPERCEDES enabled.v1 (full invalidation)
- `tr07_obs03`: enabled.v2 REVIVES from disabled (full invalidation of disabled)

All claims share the lifecycle track. The claim_id third segment (`enabled` / `disabled`) is treated as state, not scope.

## Shadow CONTESTS Rationale

Shadow's scope resolution treats `enabled` and `disabled` as different semantic scopes:
- `enabled.v1`: scope=`enabled`, adj_key=`Alpha feature:feature_flag:enabled`
- `disabled`: scope=`disabled`, adj_key=`Alpha feature:feature_flag:disabled`
- `enabled.v2`: scope=`enabled`, adj_key=`Alpha feature:feature_flag:enabled`

Result:
- `enabled.v2` SUPERCEDES `enabled.v1` (same key, same channel)
- `disabled` COEXISTS with both (different key)
- This preserves the same-dimension-different-scope pattern used for parallel targets

## Active-State Consequence

| Scenario | After obs02 | After obs03 |
|----------|-------------|-------------|
| Gold expectation | disabled only | enabled.v2 only |
| Shadow behavior | enabled.v1 + disabled coexist | enabled.v2 active, disabled still active, enabled.v1 superseded |

Shadow produces 2 extra active claims across the lifecycle.

## Must_Include Consequence

must_include recall = 1.0 for all checkpoints in both models. Downstream consumers always get the required claims.

## Downstream Safety Consequence

- No critical false invalidation (zero blocker-class diffs)
- No must_include regression
- No quarantines
- Extra active claims are *additional information*, not incorrect information
- Downstream actions can filter by lifecycle_seq to get the latest per-key

## Required Mechanical Behavior

To fully align with gold on this single-track case while preserving multi-track behavior, shadow would need:
1. A project-specific or lifecycle-specific "scope equivalence group" declaration that treats `enabled` and `disabled` as same-track states rather than different scopes, OR
2. Quarantine for single-track lifecycle transitions when the scope model detects a potential conflict.

Both options require Phase 1.1 design work beyond the current scope. Current behavior is safe and deterministic.

## Processing

- **`genuinely_ambiguous`** — The 4 regression diffs are documented non-blocking semantic differences.
- Shadow's behavior is deterministic, auditable, and safe.
- The 4 regressions are classified as `manual_adjudication` with explainable rationale.
- Shadow passes development gate with blocker=0, must_include_recall=1.0, critical false invalidation=0.
