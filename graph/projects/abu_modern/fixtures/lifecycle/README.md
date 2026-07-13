# Lifecycle Fixtures

This directory contains mechanism-level fixtures for the Phase 1 lifecycle schema.
They are specifications of expected behavior, not yet executable against the main
reconcile/apply/assembler chain. They will drive the shadow replay suite before any
main-chain replacement is accepted.

## Files

- `fixture_schema.json` — JSON schema for every fixture.
- `fixtures/lc_*.json` — Eight minimal fixtures covering the lifecycle decision table.

## Fixture Inventory

| Fixture ID | Category | Purpose |
| --- | --- | --- |
| `lc_two_lifecycles_no_kill` | lifecycle_identity | Same entity, two lifecycles must coexist. |
| `lc_revival` | revival | Superseded node can be revived without rewriting history. |
| `lc_provenance_conflict` | provenance_conflict | Conflicting sources produce `CONTESTS`, not full invalidation. |
| `lc_late_arrival` | late_arrival | `observed_at` drives ordering; late `effective_at` does not rewrite past patches. |
| `lc_legacy_migration` | legacy_migration | Legacy nodes without `lifecycle_ref` keep an `adjudication_key` fallback. |
| `lc_alias_abstain` | alias_abstain | Ambiguous alias resolution triggers resolver abstain / quarantine. |
| `lc_sequence_collision` | sequence_collision | Colliding `lifecycle_seq` is handled conservatively. |
| `lc_replay_determinism` | replay_determinism | Same input + same code produces identical graph state and bundle. |

## Validation

Run from the repository root:

```bash
python graph/scripts/validate_lifecycle_fixtures.py
```

## Relation to Shadow Replay

Each fixture will be replayed through both the old and shadow adjudication chains.
A fixture failure in the shadow chain is a blocking defect. Fixture success is a
necessary, but not sufficient, condition for replacing the main chain.
