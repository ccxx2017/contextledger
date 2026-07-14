# Stage04-B2 Isolation and Commit Audit

**Generated:** 2026-07-14T06:00:00Z  
**Branch:** phase1-lifecycle-stage02  

## Git Status

```bash
$ git branch --show-current
> phase1-lifecycle-stage02

$ git rev-parse HEAD
> d7d681ef5b4d574dd9b08174e209d2f0dfc12082

$ git status --short
```

(118 lines of output — all changes confined to shadow_replay/* and reports/*)

## Modified Files (non-run, non-design-doc)

Only these 3 shadow script files have staged/unstaged modifications:

| File | Status | Description |
|------|--------|-------------|
| `benchmark_shadow_runner.py` | MM | Multi-event loop; bidirectional invalidation; obs-level checkpoint; adapter import |
| `fixture_replay_runner.py` | MM | Complete EXPECTED_NODE_SEMANTICS for all 16 fixtures; BOM fix |
| `shadow_lifecycle_adjudicator.py` | MM | Late-arrival detection; _compute_adjudication_key priority |
| `shadow_resolution_adapter.py` | ?? (new) | New module; observation_to_event with versioned priority |

All changes are confined to `graph/projects/abu_modern/shadow_replay/scripts/` — no formal path touched.

## Formal Path Isolation

The following formal paths have NOT been modified in any commit or uncommitted change:

| Path | Status | Verification |
|------|--------|-------------|
| `reconcile_patch.py` | ✅ Unchanged | git diff HEAD --name-only |
| `apply_patch.py` | ✅ Unchanged | git diff HEAD --name-only |
| `build_context_bundle.py` | ✅ Unchanged | git diff HEAD --name-only |
| `graph/assembler/` | ✅ Unchanged | git diff HEAD --name-only |
| `graph/graph_state.json` | ✅ Unchanged | git diff HEAD --name-only |
| `raw/` (formal patch ledger) | ✅ Unchanged | Only design doc changes |
| `benchmark/v1_freeze/` | ✅ Unchanged | git diff HEAD --name-only |
| `blind_holdout/` | ✅ Unchanged | Not present; not touched |

## Shadow Output Isolation

All shadow run output is written to:
- `graph/projects/abu_modern/shadow_replay/runs/stage04b/development/` (benchmark)
- `graph/projects/abu_modern/shadow_replay/runs/stage04a_*` (fixtures)

These are run-scoped directories. No output leaks into:
- Formal `graph_state.json`
- Formal `raw/patch ledger`
- Formal `context_bundle` paths
- Formal assembler state

## Run Output Evidence

| Latest Run | Path |
|-----------|------|
| Development (post-fix) | `.../stage04b/development/stage04b_20260714T060728_development/` |
| Pre-fix comparator | `.../stage04b/development/stage04b_20260714T060323_development/` |
| All 16 fixtures (latest) | `.../runs/stage04a_20260714T055147_*/` |

All outputs are pristine: shadow graph state, shadow bundles, patches, logs, diff reports. No cross-contamination with formal paths.
