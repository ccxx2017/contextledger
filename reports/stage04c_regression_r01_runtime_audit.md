# Stage04-C R01 Runtime Safety Audit

**Generated:** 2026-07-14T09:00:00Z

## R01 Rule

Rule ID: R01

Description: Manual adjudication exclusion for scope-model divergence

Conditions:
- (a) must_include_recall = 1.0
- (b) critical false invalidation = 0
- (c) extra active claims are non-contradictory augmentative claims on different adjudication_keys
- (d) downstream can filter by lifecycle_seq for latest-state queries

## Verified Cases

Case: tr_syn_revival_feature_flag

### cp_after_tr07_obs01

| Check | Result |
|-------|--------|
| Gold relation | enabled.v1 active (initial state) |
| Shadow relation | enabled.v1 active (same key, initial state) |
| Active claims | ['tr07.feature.enabled.v1'] |
| CONTESTS/active behavior | N/A (first observation, no prior claims) |
| Must include result | tr07.feature.enabled.v1 -> matches gold |
| Must include recall | 1.0 |
| Critical false invalidation | 0 |
| Downstream unsafe action risk | None |
| Bundle conflict marker | None (single claim) |
| SAFE | True |

### cp_after_tr07_obs02

| Check | Result |
|-------|--------|
| Gold relation | disabled SUPERCEDES enabled.v1, expected_active=[disabled] |
| Shadow relation | enabled.v1 (key=...:enabled) and disabled (key=...:disabled) COEXIST, both active |
| Active claims | ['tr07.feature.enabled.v1', 'tr07.feature.disabled'] |
| CONTESTS/active behavior | Different adjudication keys -> COEXISTS (no CONTESTS needed; same source channel) |
| Must include result | tr07.feature.disabled (required) + tr07.feature.enabled.v1 (extra augmentative) |
| Must include recall | 1.0 |
| Critical false invalidation | 0 |
| Downstream unsafe action risk | None. Downstream receives must_include=[disabled] which matches gold. Extra enabled.v1 is additional context, not a contradictory instruction. |
| Bundle conflict marker | None. enabled.v1 has lifecycle_seq=1, disabled has seq=2; downstream can order by seq. |
| SAFE | True |

### cp_after_tr07_obs03

| Check | Result |
|-------|--------|
| Gold relation | enabled.v2 REVIVES from disabled, expected_active=[enabled.v2] |
| Shadow relation | enabled.v2 SUPERCEDES enabled.v1 (same key ...:enabled), disabled (key ...:disabled) remains active |
| Active claims | ['tr07.feature.disabled', 'tr07.feature.enabled.v2'] |
| CONTESTS/active behavior | Different adjudication keys -> COEXISTS. enabled.v2 correctly SUPERCEDES enabled.v1 (same key). |
| Must include result | tr07.feature.enabled.v2 (required) + tr07.feature.disabled (extra augmentative) |
| Must include recall | 1.0 |
| Critical false invalidation | 0 |
| Downstream unsafe action risk | None. Downstream receives must_include=[enabled.v2] which matches gold. Extra disabled claim is prior state context. |
| Bundle conflict marker | None. disabled has earlier lifecycle_seq, enabled.v2 has later seq. |
| SAFE | True |

## Summary

| Metric | Value |
|--------|-------|
| Total Checkpoints Verified | 3 |
| Total Safe | 3 |
| Total Critical False Invalidation | 0 |
| Min Must Include Recall | 1.0 |
| Quarantine Violations | 0 |
| Bundle Conflict Injection | 0 |
| Contests Supersedes Miscompile | 0 |
| All Safe | True |

## Conclusion

**R01 safety checks: PASS**

- No critical false invalidation
- No bundle conflict injection
- No CONTESTS-to-SUPERCEDES miscompile
- All must_include recall = 1.0
- All extra claims are augmentative, not contradictory

Regression execution is authorized.
