# Shadow Replay Executable Specification

## Purpose

Shadow replay runs the existing main-chain adjudication pipeline and a candidate
lifecycle-aware pipeline against the same inputs, compares outputs, and classifies
every difference before any candidate is allowed to replace the main chain.

## Scope

This spec applies to `graph/projects/abu_modern` on branch
`phase1-lifecycle-stage02`. It does **not** authorize changes to the current
`reconcile_patch.py`, `apply_patch.py`, or assembler injection. It only defines
the comparison contract and blocking rules.

## Pipeline Overview

```text
event_stream
    |---> main_chain_compiler  ---> main_graph_state
    |                                 main_context_bundle
    |---> shadow_chain_compiler ---> shadow_graph_state
                                      shadow_context_bundle
                                         |
                                         v
                              diff_engine (this spec)
                                         |
                                         v
                              diff_report.json
                                         |
                                         v
                              gate_decision: PASS / ARBITRATE / BLOCK
```

## Invariants

1. **No main graph mutation.** Shadow outputs live only under
   `graph/projects/abu_modern/shadow_replay/runs/<run_id>/`.
2. **Determinism.** Two runs with the same `event_stream`, same contract hashes,
   same resolver/cleaner/extractor hashes, and same fixture must produce the same
   patch sequence, graph state, context bundle, and metrics.
3. **LLM uncertainty isolation.** If the shadow chain uses an LLM, the diff engine
   must separate:
   - backend determinism (fixed LLM output) and
   - frontend semantic variance (real LLM output).
4. **Event immutability.** Original events and historical patches are never
   rewritten for the purpose of shadow replay.

## Diff Report Schema

See `diff_report_schema.json`. Each diff entry contains:

- `checkpoint_id`
- `old_state_hash`
- `shadow_state_hash`
- `node_level_status_diffs`
- `relation_diffs`
- `must_include_diffs`
- `quarantine_diffs`
- `assembler_token_diffs`
- `classification`: one of `expected_improvement`, `expected_schema_change`,
  `regression`, `unexplained`
- `rationale`
- `blocking`: boolean

## Diff Classification

| Class | Definition | Default Action |
| --- | --- | --- |
| `expected_improvement` | Shadow fixes a known false merge, false split, or invalidation error documented in a fixture or benchmark gap register. | Allow after fixture passes. |
| `expected_schema_change` | Difference is a direct consequence of adding `lifecycle_ref`, `lifecycle_seq`, `observed_at`/`effective_at`, or new relations such as `REVIVES`/`CONTESTS`. | Allow if enumerated in RFC change list. |
| `regression` | `must_include_recall` drops, active set F1 drops, critical constraints silent-fail, or a fixture expectation is violated. | Block. |
| `unexplained` | Difference cannot be attributed to an expected improvement or schema change. | Block until classified. |

## Gate Rules

### Auto-block Conditions

Any of the following triggers `BLOCK`:

1. `must_include_recall` below the D1 baseline (1.0 for Phase 0.5).
2. `must_include_recall` below the current main-chain score (1.0).
3. Any lifecycle fixture fails against the shadow chain.
4. Any `regression`-classified diff without a matching `expected_improvement`.
5. Any `unexplained` diff.
6. New silent invalidation of a critical constraint.
7. Quarantine count increases without a documented reason.
8. `CONTESTS` auto-collapses to `SUPERCEDES`.
9. Determinism check fails for fixed-LLM-output replay.

### Human Arbitration Required

The gate emits `ARBITRATE` when:

- A diff is `expected_schema_change` but touches a legacy node whose
  `adjudication_key` fallback behavior is not yet covered by fixtures.
- A benchmark regression split case changes status and the cause is not a
  documented benchmark design assumption.

### Pass Conditions

The gate emits `PASS` only when:

1. All lifecycle fixtures pass.
2. No `regression` or `unexplained` diffs remain.
3. `must_include_recall` >= current main-chain score.
4. `active_set_set_f1` is not below current main-chain score by more than 0.01.
5. Blind holdout cases show no negative flip unless the negative flip is an
   expected improvement (e.g., correctly splitting a false merge).

## Replacement Candidate Threshold

A shadow chain becomes a **replacement candidate** only after three consecutive
independent replay runs produce `PASS` with identical diff classification counts.

## Output Locations

```text
graph/projects/abu_modern/shadow_replay/
  runs/<run_id>/
    config.json
    main_graph_state.json
    shadow_graph_state.json
    main_context_bundle.json
    shadow_context_bundle.json
    diff_report.json
    gate_decision.json
  summaries/
    latest.json
```

## Example

See `example_diff_report.json`.
