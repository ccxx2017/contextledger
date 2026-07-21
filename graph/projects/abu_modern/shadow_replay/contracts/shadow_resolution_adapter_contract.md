# Shadow Resolution Adapter Contract v1.1

## Purpose

Transforms a raw benchmark observation (with claim_bundle) into structured resolution records
and adjudicator-ready events. The adapter runs purely in shadow; it does not write to the formal main chain.

## Normalization Priorities (version 1.0)

### claim_dimension

| Priority | Rule ID | Source Field | Condition | Behavior |
|----------|---------|-------------|-----------|----------|
| 1 | R003_explicit | claim.dimension | Present and non-null | Use directly |
| 2 | R003_explicit_predicate | claim.type or claim.predicate | Not yet available in phase05_v3 | Reserved for future use |
| 3 | R003_legacy_v1 | claim_id.second_segment | Only when step 1-2 unavailable; claim_id.split('.')[1] | Use with fallback_used=true, legacy_mapping=v1. Auditable trail only. |
| 4 | R003_abstain | — | No dimension determined | Set dimension to None, abstain_reason documented |

### scope

| Priority | Rule ID | Source Field | Condition | Behavior |
|----------|---------|-------------|-----------|----------|
| 1 | R006_explicit | claim.scope or obs.claim_scope | Present and non-null | Use directly |
| 2 | R006_legacy_v1 | claim_id.third_segment | Only when step 1 unavailable AND third segment is semantic (multi-char alphabetic, not numeric/version-like) | Use with fallback_used=true, legacy_mapping=v1. Numeric segments (digits/all, digits+suffix, version strings like "v1", timestamps) fall through to step 3. |
| 3 | R006_default | _default_ | All remaining cases | Use "_default_". Semantically safe for single-track lifecycle progression. |
| 4 | R006_abstain | — | Ambiguous scope (future use) | abstain/quarantine |

### adjudication_key

Format: `{canonical_entity}:{claim_dimension}:{scope|_default_}`

- Same key + same source channel = SUPERCEDES candidate
- Same key + different source channel = CONTESTS
- Different keys = COEXISTS (or no relation)

## Forbidden Operations

- The adapter must NOT write to the formal main chain
- The adapter must NOT modify benchmark gold, split definitions, or sealed blind holdout
- The adapter must NOT produce deterministic results from non-deterministic inputs (abstain/quarantine must be explicit)

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1 | 2026-07-13 | Initial version with claim_id heuristic defaults |
| v1.1 | 2026-07-14 | Removed unconditional claim_id third-segment scope heuristic; added semantic vs numeric segmentation; formal priority table with rule IDs; added legacy_mapping_version tracking |
