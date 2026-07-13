# Stage04-A Report

**Generated:** 2026-07-13T13:44:51Z
**Branch:** `phase1-lifecycle-stage02`

## Executive Summary

- Lifecycle fixtures replayed: 8
- Fixtures passing: 5/8
- All replays deterministic: True
- Benchmark v1 split integrity OK: True
- Blind holdout isolated from development: True
- Main-chain replacement approved: **No**

This report documents shadow lifecycle adjudication replay under isolation.
No formal main-chain files were modified.

## Implementation Contract

See [graph/projects/abu_modern/shadow_replay/stage04a_implementation_contract.md](graph/projects/abu_modern/shadow_replay/stage04a_implementation_contract.md).

## Per-Fixture Results

| Fixture | Category | Gate | Deterministic | State Hash | Bundle Hash | Run Dir |
| --- | --- | --- | --- | --- | --- | --- |
| lc_alias_abstain | alias_abstain | PASS | True | ff4a4d26cc0cd1e7 | 4a63cd291d36b2ea | `graph\projects\abu_modern\shadow_replay\runs\stage04a_20260713T134132_lc_alias_abstain` |
| lc_late_arrival | late_arrival | PASS | True | 330efb0a5eb6c585 | 32a1f2fd910c5a4f | `graph\projects\abu_modern\shadow_replay\runs\stage04a_20260713T134132_lc_late_arrival` |
| lc_legacy_migration | legacy_migration | BLOCK | True | 4212e1b49a01334b | 2f4ada1277ef1384 | `graph\projects\abu_modern\shadow_replay\runs\stage04a_20260713T134132_lc_legacy_migration` |
| lc_provenance_conflict | provenance_conflict | PASS | True | 3ad0636f912f807a | 671c2a2361449a16 | `graph\projects\abu_modern\shadow_replay\runs\stage04a_20260713T134132_lc_provenance_conflict` |
| lc_replay_determinism | replay_determinism | PASS | True | 33baa0ee1cf28fd3 | 4ec14bc62f56803a | `graph\projects\abu_modern\shadow_replay\runs\stage04a_20260713T134132_lc_replay_determinism` |
| lc_revival | revival | BLOCK | True | 8fb1176bb6fdb3fc | d09c982e5a138944 | `graph\projects\abu_modern\shadow_replay\runs\stage04a_20260713T134132_lc_revival` |
| lc_sequence_collision | sequence_collision | PASS | True | 7136b581112815c9 | 4acf8c20229cd3e0 | `graph\projects\abu_modern\shadow_replay\runs\stage04a_20260713T134132_lc_sequence_collision` |
| lc_two_lifecycles_no_kill | lifecycle_identity | BLOCK | True | e78283f6667760bc | f8dff3f986819898 | `graph\projects\abu_modern\shadow_replay\runs\stage04a_20260713T134132_lc_two_lifecycles_no_kill` |

### Checkpoint Details

#### lc_alias_abstain

- Input hash (fixture): `6ef51ef36214e87b`
- Runtime fingerprint: shadow adjudicator `8ca124ec4b24e609...`
- Patch hash: `8bcd3f8e38f0520f`
- Final state hash: `ff4a4d26cc0cd1e7`
- Final bundle hash: `4a63cd291d36b2ea`
- Quarantine: [{'event_id': 'evt_051', 'reason': 'resolver_abstain_alias_mismatch'}]

**Checkpoint `cp_after_051`** (after `evt_051`)
- State hash: `ff4a4d26cc0cd1e7`
- Bundle hash: `4a63cd291d36b2ea`
- Diffs: total=0, blockers=0, regressions=0, unexplained=0
  - No diffs.

#### lc_late_arrival

- Input hash (fixture): `972621a2d9e2c868`
- Runtime fingerprint: shadow adjudicator `8ca124ec4b24e609...`
- Patch hash: `4052178d8822bd2e`
- Final state hash: `330efb0a5eb6c585`
- Final bundle hash: `32a1f2fd910c5a4f`
- Quarantine: []

**Checkpoint `cp_after_031`** (after `evt_031`)
- State hash: `330efb0a5eb6c585`
- Bundle hash: `32a1f2fd910c5a4f`
- Diffs: total=0, blockers=0, regressions=0, unexplained=0
  - No diffs.

#### lc_legacy_migration

- Input hash (fixture): `075ba8d67eaf28f7`
- Runtime fingerprint: shadow adjudicator `8ca124ec4b24e609...`
- Patch hash: `c7aebf473602168c`
- Final state hash: `4212e1b49a01334b`
- Final bundle hash: `2f4ada1277ef1384`
- Quarantine: []

**Checkpoint `cp_after_041`** (after `evt_041`)
- State hash: `4212e1b49a01334b`
- Bundle hash: `2f4ada1277ef1384`
- Diffs: total=1, blockers=1, regressions=1, unexplained=0
  - [regression] relation: Expected relation COEXISTS from n_legacy_fact to n_updated_fact (blocking=True)

#### lc_provenance_conflict

- Input hash (fixture): `86b31998d3e62ca8`
- Runtime fingerprint: shadow adjudicator `8ca124ec4b24e609...`
- Patch hash: `e798f744dbdd6246`
- Final state hash: `3ad0636f912f807a`
- Final bundle hash: `671c2a2361449a16`
- Quarantine: []

**Checkpoint `cp_after_021`** (after `evt_021`)
- State hash: `3ad0636f912f807a`
- Bundle hash: `671c2a2361449a16`
- Diffs: total=0, blockers=0, regressions=0, unexplained=0
  - No diffs.

#### lc_replay_determinism

- Input hash (fixture): `6dfe08d205595ead`
- Runtime fingerprint: shadow adjudicator `8ca124ec4b24e609...`
- Patch hash: `80cd9eac26adc81c`
- Final state hash: `33baa0ee1cf28fd3`
- Final bundle hash: `4ec14bc62f56803a`
- Quarantine: []

**Checkpoint `cp_run_2_identical`** (after `evt_071`)
- State hash: `33baa0ee1cf28fd3`
- Bundle hash: `4ec14bc62f56803a`
- Diffs: total=0, blockers=0, regressions=0, unexplained=0
  - No diffs.

#### lc_revival

- Input hash (fixture): `afa54857bc64c716`
- Runtime fingerprint: shadow adjudicator `8ca124ec4b24e609...`
- Patch hash: `b0071c22ba719693`
- Final state hash: `8fb1176bb6fdb3fc`
- Final bundle hash: `d09c982e5a138944`
- Quarantine: []

**Checkpoint `cp_after_011`** (after `evt_011`)
- State hash: `df4006047e5ea573`
- Bundle hash: `65bf6a41f8ee15b6`
- Diffs: total=2, blockers=1, regressions=1, unexplained=0
  - [expected_schema_change] active_set: Unexpected active node n_8f3589814bdc (blocking=False)
  - [regression] superseded_set: Expected superseded node 'n_exp_v1_cancelled' not found (blocking=True)

**Checkpoint `cp_after_012`** (after `evt_012`)
- State hash: `8fb1176bb6fdb3fc`
- Bundle hash: `d09c982e5a138944`
- Diffs: total=1, blockers=1, regressions=1, unexplained=0
  - [regression] relation: Expected relation derived_from from n_exp_v2_revived to n_exp_v1_active (blocking=True)

#### lc_sequence_collision

- Input hash (fixture): `3b46dfe81136fa34`
- Runtime fingerprint: shadow adjudicator `8ca124ec4b24e609...`
- Patch hash: `f7b524afda80ff76`
- Final state hash: `7136b581112815c9`
- Final bundle hash: `4acf8c20229cd3e0`
- Quarantine: [{'event_id': 'evt_062', 'reason': 'lifecycle_seq_collision'}]

**Checkpoint `cp_after_062`** (after `evt_062`)
- State hash: `7136b581112815c9`
- Bundle hash: `4acf8c20229cd3e0`
- Diffs: total=0, blockers=0, regressions=0, unexplained=0
  - No diffs.

#### lc_two_lifecycles_no_kill

- Input hash (fixture): `72a1b99c9ef4fdcd`
- Runtime fingerprint: shadow adjudicator `8ca124ec4b24e609...`
- Patch hash: `066eb3d930a87884`
- Final state hash: `e78283f6667760bc`
- Final bundle hash: `f8dff3f986819898`
- Quarantine: []

**Checkpoint `cp_after_002`** (after `evt_002`)
- State hash: `e78283f6667760bc`
- Bundle hash: `f8dff3f986819898`
- Diffs: total=1, blockers=1, regressions=1, unexplained=0
  - [regression] relation: Expected relation COEXISTS from n_deploy to n_ticket_open (blocking=True)

## Benchmark v1 Split Audit

- Freeze manifest hash: `8ec639a99546c9bb`
- Total cases: 17
- Duplicated cases: {}

### Mechanism Distribution per Split

| Split | Distribution |
| --- | --- |
| development | alias_trap=1, conditional=1, full=1, out_of_order_late=1, partial=1, revival=1, unknown=1 |
| regression | alias_trap=1, conditional=1, full=1, out_of_order_late=1, partial=1, revival=1 |
| blind_holdout | alias_trap=1, non_invalidation_decoy=1 |
| adversarial | provenance_conflict=2 |

### Blind Holdout Leakage Check

- `tr_decoy_strategy_scripts`: overlap_ratio=0.4412, overlap_count=30
- `tr_alias_tkt_split`: overlap_ratio=0.4675, overlap_count=36

## Main-Chain Replacement Status

**Not approved.** Stage04-A only proves that the shadow kernel can replay fixtures
deterministically under isolation. The following remain required before any
main-chain candidate switch:

1. Full benchmark v1 regression and blind-holdout evaluation against the shadow chain.
2. Demonstrated semantic benefit over the current main chain on holdout cases.
3. `must_include_recall` >= D1 baseline.
4. Zero critical false invalidation or all such cases quarantined.
5. No `blocker` or `unexplained` diffs unresolved.
6. Confirmation that shadow outputs did not contaminate `graph/projects/abu_modern/graph_state.json`.

## Unresolved Risks

- Shadow adjudicator is a heuristic proof-of-concept; it has not been validated against the full benchmark.
- Alias resolution currently uses a simplified substring matcher, not the production resolver.
- Benchmark v1 blind holdout has not yet been executed through the shadow chain.

## Next Step

Proceed to Stage04-B: run the full benchmark v1 splits through the shadow chain,
produce per-split diff reports, and evaluate against the pre-registered safety red lines.
