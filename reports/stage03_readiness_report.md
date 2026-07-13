# Stage03 Readiness Report

**Branch:** `phase1-lifecycle-stage02`  
**Report date:** 2026-07-13  
**Scope:** Confirm that the lifecycle RFC decision table has been converted into
executable acceptance rules before any main-chain implementation begins.

## Stage02 Closure

Stage02 was closed with an atomic commit containing:

- `contracts/05_phase1_lifecycle_schema.md`
- `reports/current_state_manifest.json` (regenerable via `graph/scripts/generate_state_manifest.py`)
- `reports/current_graph_lint_report.json`
- `graph/scripts/generate_state_manifest.py`

The working tree is clean and `git diff --check` passes.

## RFC Decision Table — Executable Acceptance Rules

| Decision | Rule | How It Is Enforced |
| --- | --- | --- |
| `lifecycle_ref` allocation | LLM proposes clues; Resolver matches or abstains; mechanical layer generates stable ID. | Fixture `lc_two_lifecycles_no_kill` and `lc_alias_abstain`. |
| `lifecycle_seq` allocation | Only the mechanical layer assigns `lifecycle_seq`; LLM output is not trusted as final. | Fixture `lc_sequence_collision`. |
| `observed_at` | Set by ledger step reception; monotonic and immutable. | Fixture `lc_late_arrival`. |
| `effective_at` | May be missing, late, or uncertain; ordering is by `observed_at`. | Fixture `lc_late_arrival`. |
| Late arrival | Late events affect future compilation only; no rewrite of old patches. | Fixture `lc_late_arrival` checkpoint asserts old patch stays superseded. |
| `CONTESTS` | Conflicting provenance enters `CONTESTS`; never auto-collapses to `SUPERCEDES`. | Fixture `lc_provenance_conflict` + shadow replay auto-block rule #8. |
| Partial invalidation | Phase 1 requires atomic node-level invalidation; field-level patch DSL is out of scope. | RFC `Non-goals for Phase 1`. |
| Conditional invalidation | Conditions require explicit schema; missing condition defaults to conservative preserve. | Fixture `lc_provenance_conflict`. |
| Revival | Expressed as a new event with `REVIVES` relation; old patch is never edited. | Fixture `lc_revival`. |
| Resolver abstain | Low-confidence resolution quarantines the event or creates a provisional node. | Fixture `lc_alias_abstain`. |
| Legacy migration | Legacy nodes without `lifecycle_ref` use a versioned `adjudication_key` fallback. | Fixture `lc_legacy_migration`. |
| Determinism | Same input + same code = same graph state + same bundle. | Fixture `lc_replay_determinism`. |
| Quarantine | Any shadow failure must quarantine or terminate; no best-effort silent result. | Shadow replay auto-block rule #7. |

## Stage03 Deliverables Status

1. **Benchmark v1 freeze manifest** — Done.
   - Path: `graph/projects/abu_modern/benchmark/v1_freeze/benchmark_v1_freeze_manifest.json`
   - Splits: development=7, regression=6, blind_holdout=2, adversarial=2
   - Validator: `python graph/scripts/validate_benchmark_v1_freeze.py`

2. **Lifecycle fixtures** — Done.
   - Schema: `graph/projects/abu_modern/fixtures/lifecycle/fixture_schema.json`
   - Fixtures: 8 covering all required categories
   - Validator: `python graph/scripts/validate_lifecycle_fixtures.py`

3. **Shadow replay executable spec** — Done.
   - Spec: `graph/projects/abu_modern/shadow_replay/shadow_replay_spec.md`
   - Diff schema: `graph/projects/abu_modern/shadow_replay/diff_report_schema.json`
   - Example: `graph/projects/abu_modern/shadow_replay/example_diff_report.json`

## Main-Chain Implementation Boundary

The following remain **out of scope** until shadow replay passes:

- Modifying `reconcile_patch.py`, `apply_patch.py`, or assembler default injection.
- Rewriting existing patches for migration.
- Using manual patches to fix fixtures.
- Allowing shadow output to leak into `graph/projects/abu_modern/graph_state.json`.

## Sign-Off

Stage03 side-track artifacts are complete. The next step is to build the shadow
adjudication chain and run the fixtures through it, not to modify the main chain.
