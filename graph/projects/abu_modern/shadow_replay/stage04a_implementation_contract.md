# Stage04-A Implementation Contract

## Scope

This contract authorizes **only** the shadow lifecycle adjudication side
implementation on branch `phase1-lifecycle-stage02`. It explicitly does **not**
authorize any modification to the formal main-chain components:

- `graph/scripts/reconcile_patch.py`
- `graph/scripts/apply_patch.py`
- `graph/scripts/build_context_bundle.py`
- `graph/scripts/entity_resolver.py`
- `graph/projects/abu_modern/graph_state.json`
- Any assembler default injection

## Inputs

| Input | Path | Access Mode |
| --- | --- | --- |
| Lifecycle fixtures | `graph/projects/abu_modern/fixtures/lifecycle/fixtures/lc_*.json` | read-only |
| Fixture schema | `graph/projects/abu_modern/fixtures/lifecycle/fixture_schema.json` | read-only |
| Benchmark v1 freeze manifest | `graph/projects/abu_modern/benchmark/v1_freeze/benchmark_v1_freeze_manifest.json` | read-only |
| Benchmark trajectories | `graph/projects/abu_modern/benchmark/phase05_v3/trajectories/*.json` | read-only |
| Benchmark gold | `graph/projects/abu_modern/benchmark/phase05_v3/gold/*.gold.json` | read-only |
| Current main graph state | `graph/projects/abu_modern/graph_state.json` | read-only |
| Contracts | `contracts/03_graph_schema.md`, `contracts/05_phase1_lifecycle_schema.md` | read-only |

## Outputs

All shadow outputs are written under a single run directory:

```text
graph/projects/abu_modern/shadow_replay/runs/<run_id>/
```

`<run_id>` format: `stage04a_<utc_iso_timestamp>_<fixture_id_or_benchmark>`.

Per-run outputs:

- `config.json` — run ID, input hashes, runtime fingerprint
- `shadow_graph_state.json` — shadow graph state snapshot
- `shadow_context_bundle.json` — assembled shadow context bundle
- `patches.jsonl` — one patch per processed event
- `diff_report.json` — checkpoint-by-checkpoint comparison against expected
- `gate_decision.json` — PASS / ARBITRATE / BLOCK
- `log.jsonl` — quarantine and adjudication decisions

## State Isolation

1. Shadow graph state is held in memory and persisted only under the run
   directory.
2. No shadow process accepts an `--in-place` flag or any flag that writes to
   `graph/projects/abu_modern/graph_state.json`.
3. All output paths are validated to be children of
   `graph/projects/abu_modern/shadow_replay/runs/`.
4. Shadow processes read the formal graph state only for reference (e.g. lint
   baseline comparison), never for mutation.

## Prohibition Against Writing the Formal Main Graph

The implementation enforces the boundary by:

- A runtime assertion `_assert_shadow_path(path)` that raises if `path` is not
  under `SHADOW_RUN_DIR`.
- No call sites in the shadow scripts construct a path pointing at
  `graph/projects/abu_modern/graph_state.json`.
- A final `git status --short` check is performed after each Stage04-A run.

## Failure Handling

| Failure Mode | Behavior |
| --- | --- |
| Fixture JSON parse error | Runner skips fixture, marks BLOCK, logs reason. |
| Shadow adjudication exception | Runner quarantines event, continues, marks diff as `unexplained`/`blocker`. |
| Determinism mismatch on second replay | Gate decision is BLOCK. |
| Attempted write outside shadow run dir | Process raises `ShadowIsolationError` immediately. |
| Missing expected checkpoint | Runner reports missing checkpoint as `unexplained` blocker. |

## Runtime Fingerprint

Every run records a fingerprint of the code that produced it:

- SHA-256 of `shadow_lifecycle_adjudicator.py`
- SHA-256 of `shadow_compiler.py`
- SHA-256 of `shadow_bundle_builder.py`
- SHA-256 of `fixture_replay_runner.py`
- SHA-256 of `contracts/05_phase1_lifecycle_schema.md`
- SHA-256 of `contracts/03_graph_schema.md`
- SHA-256 of the fixture file (when running fixtures)
- SHA-256 of the benchmark freeze manifest (when running benchmark)

## Patch / Graph / Bundle Hash

- **Patch hash**: SHA-256 of `patches.jsonl`.
- **Graph state hash**: SHA-256 of the serialized `shadow_graph_state.json`.
- **Bundle hash**: SHA-256 of the serialized `shadow_context_bundle.json`.
- These hashes are recorded in `config.json` and in the Stage04-A report for
  deterministic replay verification.

## Determinism Check

Each fixture is replayed twice in the same process with the same inputs. The
second run's patch, graph, and bundle hashes must equal the first run's hashes.
This is a **necessary but not sufficient** condition for main-chain candidacy.

## Exit Criteria for Stage04-A

Stage04-A is complete when:

1. All 8 lifecycle fixtures have been replayed and their semantic checkpoints
   compared.
2. Benchmark v1 split audit has been generated and blind-holdout isolation is
   confirmed.
3. Shadow diff spec has been updated with the five-class classification rules.
4. A Stage04-A report is submitted with per-fixture, per-split, per-checkpoint
   results.
5. No main-chain files have been modified.

Main-chain replacement remains **not approved** after Stage04-A.
