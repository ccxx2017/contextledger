# Stage04-C Preflight Recheck Report

**Generated:** 2026-07-14T15:30:00Z
**Branch:** phase1-lifecycle-stage02
**Clean worktree path:** D:\CCXXLESSON\contextledger\clean_worktree_stage04c (detached HEAD)

## Candidate Commit

| Field | Value |
|-------|-------|
| Base commit | d7d681e |
| Evidence freeze commit | e4dfcbf (12 evidence reports) |
| Candidate source commit | 2d24e01 (6 source/contract files) |
| Current HEAD | a2e39f (preflight recheck + gitignore + gitattributes) |

## Clean Git Status Proof

git status --short = (empty)
**Result: PASS**

## Dependency Manifest Verification
Dependency manifest SHA256: 72847290466e4f4a
All 21 dependency files confirmed present in clean worktree.

## Fixture Execution Result
Smoke test: lc_alias_abstain.json in clean worktree = PASS, deterministic=True
(Full 16-fixture inventory already verified in Stage04-B2 evidence index)

## Protected Path Diff Proof
**Result: PASS** (no changes to reconcile_patch, apply_patch, assembler, graph_state, benchmark v1)

## R01 Rule Hash Verification
R01 rule SHA256: e4c854a7e8f5cbb3 (versioned in evidence freeze commit e4dfcbf)

## Evidence Index Hash Verification
| 16 fixtures all PASS | recorded=e128cc990e99f1ce actual=e128cc990e99f1ce | PASS
| All 16 fixtures deterministic (two repla | recorded=ed2ee08b363762b1 actual=ed2ee08b363762b1 | PASS
| Full bidirectional invalidation comparis | recorded=39073663dde77910 actual=39073663dde77910 | PASS
| Canonical comparator baseline (pre-fix v | recorded=c92719b270d9cad1 actual=c92719b270d9cad1 | PASS
| development blockers = 0 | recorded=4f1c203496a4a3dd actual=4f1c203496a4a3dd | PASS
| Resolution record audit: no unversioned  | recorded=8aa95fe2523e72ab actual=8aa95fe2523e72ab | PASS
| Shadow output isolated; no formal main c | recorded=3d7305efd0e6bdbc actual=3d7305efd0e6bdbc | PASS
**Overall:** PASS

## Split Execution Status
- regression split: NOT executed
- adversarial split: NOT executed
- sealed blind holdout: NOT executed

## Gate Decision

### preflight_passed_regression_authorized

All preflight conditions satisfied. Regression split execution is now authorized.
Regression/adversarial/blind_holdout NOT executed.

Remaining restrictions:
- Regression split may be executed **once**
- Adversarial split: NOT authorized
- Sealed blind holdout: NOT authorized
- No code, rule, fixture, gold, or benchmark modifications during regression run