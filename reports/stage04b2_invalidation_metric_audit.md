# Stage04-B2 Invalidation Metric Audit

**Generated:** 2026-07-14T06:00:00Z  
**Branch:** phase1-lifecycle-stage02  
**Comparator:** current shadow, full bidirectional invalidation check

## Purpose

Verify that:
1. Shadow does not hide false invalidations by narrowing check scope
2. `critical false invalidation = 0` comes from full comparison
3. `tr_syn_partial_policy_clause` PASS is not due to ignoring shadow extra relations

## Evaluation Method

Per checkpoint, the comparator now reports all five invalidation categories:

| Category | Meaning | Impacts Gate? |
|----------|---------|---------------|
| `expected_improvement` | True positive: shadow correctly superseded a claim | No |
| `regression` (invalidation) | False negative: expected invalidation missed by shadow | Yes (regression) |
| `unexpected_supersedes` | Shadow superseded a claim not in gold expected_invalidations | No (non-critical) |
| `expected_schema_change` | Expected semantic difference from new schema | No |
| `blocker` (invalidation) | Critical false invalidation | Yes (blocker) |

## Results by Case

### tr_full_tkt_005b
| Checkpoint | expected_improvement | unexpected_supersedes |
|-----------|---------------------|----------------------|
| cp_after_obs01 | 0 | 0 |
| cp_after_obs02 | 1 (obs01 -> obs02) | 0 |
| cp_after_obs03 | 1 (obs02 -> obs03) | 1 (obs01 residual) |
| cp_after_obs04 | 1 (obs03 -> obs04) | 2 (obs01, obs02 residual) |
| cp_after_obs05 | 1 (obs04 -> obs05) | 3 (obs01-03 residual) |

**Analysis:** All unexpected_supersedes are *residual* superseded claims from prior steps that were invalidated in earlier checkpoints. Gold only lists the *current step's* expected invalidations. There are zero undetected false invalidations.

### tr_syn_partial_policy_clause
| Checkpoint | expected_improvement | unexpected_supersedes |
|-----------|---------------------|----------------------|
| cp_after_tr03_obs01 | 0 | 0 |
| cp_after_tr03_obs02 | 1 (retries.2 -> retries.4) | 0 |

**Analysis:** The partial policy update correctly only supersedes retries.2. No false invalidation. timeout.30s and audit.required remain active.

### tr_syn_revival_feature_flag
| Checkpoint | regression | unexpected_supersedes |
|-----------|-----------|----------------------|
| cp_after_tr07_obs01 | 0 | 0 |
| cp_after_tr07_obs02 | 2 (enabled.v1 active/invalidation) | 0 |
| cp_after_tr07_obs03 | 2 (disabled active/invalidation) | 1 (enabled.v1 residual) |

**Analysis:** The 4 regressions are genuine semantic differences between gold's single-track lifecycle model and shadow's multi-track scope model. Zero false invalidations. This is a `manual_adjudication` case.

### Other Cases
- `tr_syn_conditional_region_exception`: no invalidation diffs
- `tr_alias_workspace_identity`: no invalidation diffs
- `tr_syn_non_invalidation_parallel_targets`: no invalidation diffs
- `tr_syn_out_of_order_inventory_present`: no invalidation diffs

## Conclusion

| Metric | Value | Source |
|--------|-------|--------|
| critical false invalidation | **0** | Full bidirectional comparison confirms zero blocker-class invalidation diffs |
| false negative (regression) invalidation | 4 | All from revival_feature_flag (manual_adjudication) |
| unexpected_supersedes (non-critical) | 7 | All residual supersedes from prior steps, not undetected false invalidations |
| hidden false invalidation risk | **None** | The full bidirectional check includes actual_superseded - expected_invalid for every checkpoint |

The `tr_syn_partial_policy_clause` PASS is genuine: the partial update correctly supersedes only the retries dimension, leaving timeout and audit unchanged. No hidden extra invalidation relations.

Shadow is not hiding false invalidations. The `critical false invalidation = 0` claim is validated by the full bidirectional comparison.
