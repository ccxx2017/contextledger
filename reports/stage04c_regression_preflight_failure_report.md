# Stage04-C Regression Preflight Failure Report

**Generated:** 2026-07-14T16:00:00Z
**Branch:** phase1-lifecycle-stage02
**Candidate commit:** 2d24e01
**Clean worktree:** D:\\CCXXLESSON\\contextledger\clean_worktree_stage04c
**Gate: blocked**

## Failure Detail

Two evidence index hashes do not match in candidate commit 2d24e01:

| Evidence File | Expected Hash | Actual Hash | Root Cause |
|---------------|--------------|-------------|------------|
| stage04b2_invalidation_metric_audit.md | 39073663dde77910 | d5f691f602ad502e | CRLF normalization in git: original working-tree file was CRLF-mixed (3831 bytes, 1 CRLF), but commit 2d24e01 stores LF-only (3830 bytes, 0 CRLF). Autocrlf checkout produces different CRLF distribution than the original. |
| stage04b2_isolation_and_commit_audit.md | 3d7305efd0e6bdbc | 537be475464631a6 | Same root cause: git line-ending conversion during commit/checkout cycle. |

Both mismatches are **mechanical CRLF/LF only** ¡ª zero semantic diff.

## Resolution Path

The evidence index was generated from working-tree files (CRLF-mixed), but commit e4dfcbf
stored them as LF-only (Windows autocrlf conversion during git add). This is a known
platform artifact that cannot be fixed without:

a) Recreating the evidence freeze commit with .gitattributes (requires modifying a committed SHA), or
b) Accepting the hash mismatch as a mechanical line-ending artifact (requires policy exception).

Per review AI instruction: both options require approval. Code/evidence modification is forbidden.

## Protected Path Verification

| Path | Status |
|------|--------|
| reconcile_patch.py | Unchanged vs d7d681e, unchanged vs 2d24e01 |
| apply_patch.py | Unchanged vs d7d681e, unchanged vs 2d24e01 |
| build_context_bundle.py | Unchanged vs d7d681e, unchanged vs 2d24e01 |
| graph/assembler/ | Unchanged vs d7d681e, unchanged vs 2d24e01 |
| graph/graph_state.json | Unchanged vs d7d681e, unchanged vs 2d24e01 |
| benchmark/v1_freeze/ | Unchanged vs d7d681e, unchanged vs 2d24e01 |

## Gate Decision

### blocked

Evidence hash mismatch (2 of 7) prevents clean preflight. No regression executed.
No candidate code, evidence, fixture, gold, or benchmark was modified.
