# Stage04-C Regression Evaluation Report

**Generated:** 2026-07-14T09:05:00Z
**Split:** regression
**Candidate:** 2d24e01
**Evidence policy:** canonical_lf_v1 (fa57dfd)

## Summary

| Metric | Value |
|--------|-------|
| Cases | 6 |
| Gate decision | BLOCK |
| Blockers | 0 |
| Unexplained | 0 |
| Total regressions | 17 |
| R01-covered regressions | 14 (tr_revival_round5x) |
| Ordinary regressions | 3 (tr_syn_partial_checklist_clause: 2, tr_syn_out_of_order_price_band_present: 1) |
| Expected schema changes | 17 |
| Expected improvements | 4 |
| Unexpected supersedes | 6 |
| Min must_include_recall | 1.0 |
| Min active_set F1 | 0.3333 |
| R01 safety failures | 0 |

## tr_full_tkt_006

| Checkpoint | Diffs |
|------------|-------|
| cp_after_obs01 | {"blocker": 0, "regression": 0, "expected_schema_change": 0, "expected_improvement": 0, "unexplained": 0, "manual_adjudication": 0, "unexpected_supersedes": 0, "total": 0} |
| cp_after_obs02 | {"blocker": 0, "regression": 0, "expected_schema_change": 0, "expected_improvement": 1, "unexplained": 0, "manual_adjudication": 0, "unexpected_supersedes": 0, "total": 1} |
| cp_after_obs03 | {"blocker": 0, "regression": 0, "expected_schema_change": 0, "expected_improvement": 1, "unexplained": 0, "manual_adjudication": 0, "unexpected_supersedes": 1, "total": 2} |
| cp_after_obs04 | {"blocker": 0, "regression": 0, "expected_schema_change": 0, "expected_improvement": 1, "unexplained": 0, "manual_adjudication": 0, "unexpected_supersedes": 2, "total": 3} |
| cp_after_obs05 | {"blocker": 0, "regression": 0, "expected_schema_change": 0, "expected_improvement": 1, "unexplained": 0, "manual_adjudication": 0, "unexpected_supersedes": 3, "total": 4} |

Aggregate: blocker=0, regression=0, unexplained=0
must_include_recall min=1.0, active_set F1 min=1.0

## tr_syn_partial_checklist_clause

| Checkpoint | Diffs |
|------------|-------|
| cp_after_tr04_obs01 | {"blocker": 0, "regression": 0, "expected_schema_change": 1, "expected_improvement": 0, "unexplained": 0, "manual_adjudication": 0, "unexpected_supersedes": 0, "total": 1} |
| cp_after_tr04_obs02 | {"blocker": 0, "regression": 2, "expected_schema_change": 2, "expected_improvement": 0, "unexplained": 0, "manual_adjudication": 0, "unexpected_supersedes": 0, "total": 4} |

Aggregate: blocker=0, regression=2, unexplained=0
must_include_recall min=1.0, active_set F1 min=0.8571

## tr_syn_conditional_window_exception

| Checkpoint | Diffs |
|------------|-------|
| cp_after_tr06_obs01 | {"blocker": 0, "regression": 0, "expected_schema_change": 0, "expected_improvement": 0, "unexplained": 0, "manual_adjudication": 0, "unexpected_supersedes": 0, "total": 0} |
| cp_after_tr06_obs02 | {"blocker": 0, "regression": 0, "expected_schema_change": 0, "expected_improvement": 0, "unexplained": 0, "manual_adjudication": 0, "unexpected_supersedes": 0, "total": 0} |

Aggregate: blocker=0, regression=0, unexplained=0
must_include_recall min=1.0, active_set F1 min=1.0

## tr_revival_round5x

| Checkpoint | Diffs |
|------------|-------|
| cp_after_obs01 | {"blocker": 0, "regression": 0, "expected_schema_change": 0, "expected_improvement": 0, "unexplained": 0, "manual_adjudication": 0, "unexpected_supersedes": 0, "total": 0} |
| cp_after_obs02 | {"blocker": 0, "regression": 2, "expected_schema_change": 1, "expected_improvement": 0, "unexplained": 0, "manual_adjudication": 0, "unexpected_supersedes": 0, "total": 3} |
| cp_after_obs03 | {"blocker": 0, "regression": 3, "expected_schema_change": 2, "expected_improvement": 0, "unexplained": 0, "manual_adjudication": 0, "unexpected_supersedes": 0, "total": 5} |
| cp_after_obs04 | {"blocker": 0, "regression": 4, "expected_schema_change": 3, "expected_improvement": 0, "unexplained": 0, "manual_adjudication": 0, "unexpected_supersedes": 0, "total": 7} |
| cp_after_obs05 | {"blocker": 0, "regression": 5, "expected_schema_change": 4, "expected_improvement": 0, "unexplained": 0, "manual_adjudication": 0, "unexpected_supersedes": 0, "total": 9} |

Aggregate: blocker=0, regression=14, unexplained=0
must_include_recall min=1.0, active_set F1 min=0.3333

## tr_alias_quant_tools

| Checkpoint | Diffs |
|------------|-------|
| cp_after_obs01 | {"blocker": 0, "regression": 0, "expected_schema_change": 0, "expected_improvement": 0, "unexplained": 0, "manual_adjudication": 0, "unexpected_supersedes": 0, "total": 0} |
| cp_after_obs02 | {"blocker": 0, "regression": 0, "expected_schema_change": 1, "expected_improvement": 0, "unexplained": 0, "manual_adjudication": 0, "unexpected_supersedes": 0, "total": 1} |
| cp_after_obs03 | {"blocker": 0, "regression": 0, "expected_schema_change": 2, "expected_improvement": 0, "unexplained": 0, "manual_adjudication": 0, "unexpected_supersedes": 0, "total": 2} |

Aggregate: blocker=0, regression=0, unexplained=0
must_include_recall min=1.0, active_set F1 min=1.0

## tr_syn_out_of_order_price_band_present

| Checkpoint | Diffs |
|------------|-------|
| cp_after_tr22_obs01 | {"blocker": 0, "regression": 0, "expected_schema_change": 0, "expected_improvement": 0, "unexplained": 0, "manual_adjudication": 0, "unexpected_supersedes": 0, "total": 0} |
| cp_after_tr22_obs02 | {"blocker": 0, "regression": 1, "expected_schema_change": 1, "expected_improvement": 0, "unexplained": 0, "manual_adjudication": 0, "unexpected_supersedes": 0, "total": 2} |

Aggregate: blocker=0, regression=1, unexplained=0
must_include_recall min=1.0, active_set F1 min=0.6667

## Conclusion

### blocked

3 ordinary regressions remain after R01 exclusion. 
Adversarial split NOT authorized.
Sealed blind holdout NOT authorized.