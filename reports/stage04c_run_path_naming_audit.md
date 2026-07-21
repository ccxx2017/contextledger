# Stage04-C Run Path Naming Audit

**Generated:** 2026-07-14T09:35:00Z

## Issue

Stage04-C regression run output was written to:

`
runs/stage04b/regression/stage04b_20260714T090005_regression/
`

Instead of the expected Stage04-C run-scoped path:

`
runs/stage04c_regression_<run_id>/
`

## Root Cause

The runner script enchmark_shadow_runner.py has a hardcoded output_run_prefix = "stage04b" at module level. This prefix was never updated for Stage04-C. When invoked with --split regression, the runner constructs:

`
runs/stage04b/regression/<run_id>/
`

The manifest was generated with the correct prefix (stage04c), but the runner overrides it.

## Impact Assessment

| Risk | Assessment |
|------|------------|
| Read/overwrite Stage04-B output | NONE - Stage04-B runs archived to runs_archive/ |
| Confusion with Stage04-B data | LOW - run_id timestamp is unique |
| Cross-contamination | NONE - clean worktree, no existing stage04b/regression/ |

## Manifest vs Actual Run ID

| Field | Value |
|-------|-------|
| manifest.run_id | stage04c_regression_20260714T090005 |
| actual run directory | stage04b_20260714T090005_regression |
| Consistent? | NO |

## Input/Output Independence

| Check | Result |
|-------|--------|
| Clean worktree | YES |
| Stage04-B outputs present | NO (archived) |
| Formal paths modified | NO |
| runs_archive read/written | NO |
| All inputs from freeze manifest | YES |

## Conclusion

Naming inconsistency is a cosmetic defect in the runner's output path construction.
No outputs were overwritten, no historical data was read or confused.

**Assessment: Run output is valid despite naming issue.**

**Recommendation:** Fix the hardcoded output_run_prefix in enchmark_shadow_runner.py.
