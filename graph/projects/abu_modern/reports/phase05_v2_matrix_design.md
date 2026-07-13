# Phase 0.5 v2 Coverage Matrix Design

**Date:** 2026-07-13
**Project:** abu_modern
**Current turn_counter:** 84
**Goal:** Define the slot allocation and source mapping for the Phase 0.5 v2 benchmark replay.

## Design Rationale

v1 (commit `c7072b64`) had 23 synthetic trajectories across 8 categories. v2 must:
1. Reuse the proven v1 format so `score_phase05.py` runs unchanged.
2. Inject real cases from the 84-turn abu_modern chain where they exist (supersession, alias, provenance-like conflicts).
3. Keep synthetic construction only for categories that have no natural real cases (partial, conditional, out_of_order_late) or need augmentation (revival, non_invalidation_decoy).
4. Maintain category balance so no single category dominates the score.

Target size: **20 trajectories**. This keeps scoring fast while giving enough per-category mass to compute meaningful invalidation P/R breakdowns.

## Slot Allocation

| Category | Slots | Real abu_modern cases | Synthetic slots | Rationale |
|----------|-------|----------------------|-----------------|-----------|
| `full` | 3 | 2 | 1 | Many real supersession chains in TKT/Round families; keep 1 synthetic for baseline parity with v1. |
| `partial` | 3 | 0 | 3 | No schema support for sub-clause invalidation; must be synthetic. |
| `conditional` | 3 | 0 | 3 | No schema support for carve-outs; must be synthetic. |
| `revival` | 2 | 1 | 1 | Round 5.x audit→fix→verify→reverify chain is a real revival-like pattern. |
| `alias_trap` | 4 | 3 | 1 | Rich real cases in pending_merge + TKT splits. |
| `provenance_conflict` | 2 | 1 | 1 | `run-54b-*` hash variants provide a real provenance-like conflict. |
| `non_invalidation_decoy` | 2 | 1 | 1 | `openclaw_skills/strategy-researcher/scripts/` vs `SKILL.md` is a real parallel-target case. |
| `out_of_order_late` | 3 | 0 | 3 | No `observed_at` field in current schema; must be synthetic. |
| **Total** | **22** | **9** | **13** | Real:synthetic ratio ≈ 40:60. |

## Real Slot Candidate Mapping

### full (2 real slots)

| Slot | trajectory_id | Source entity / family | Why it fits |
|------|---------------|------------------------|-------------|
| full_01 | `tr_full_tkt_005b` | `TKT-2026-005B` family (n_0093, n_0101, n_0102, ...) | Ticket created, evolves through multiple states, eventually resolved. |
| full_02 | `tr_full_tkt_006` | `TKT-2026-006` family | Second independent ticket family with full lifecycle. |

### revival (1 real slot)

| Slot | trajectory_id | Source entity / family | Why it fits |
|------|---------------|------------------------|-------------|
| rev_01 | `tr_revival_round5x` | `TKT-2026-005B_round5` → `...round5.1_audit` → `...round5.2_reconciliation` → `...round5.3B_fix` → `...round5.3C_reverify` | Repeated audit/fix/verify cycles on the same underlying issue resemble revival/rollback. |

### alias_trap (3 real slots)

| Slot | trajectory_id | Source entity / family | Why it fits |
|------|---------------|------------------------|-------------|
| alias_01 | `tr_alias_quant_tools` | `openclaw_skills/quant_assistant/TOOLS.md` vs `openclaw_skills/quant-assistant` | Real pending_merge item with high confidence alias decision. |
| alias_02 | `tr_alias_tkt_split` | `TKT-2026-005B/C/D/E/F/G/H/I` family | Same base ticket fragments into lettered variants; false-split vs false-merge tradeoff. |
| alias_03 | `tr_alias_workspace_identity` | `openclaw_workspace/IDENTITY.md` vs `openclaw_workspace_structure` vs `openclaw_identity_mechanism` | Real pending_merge item with multiple medium-confidence candidates. |

### provenance_conflict (1 real slot)

| Slot | trajectory_id | Source entity / family | Why it fits |
|------|---------------|------------------------|-------------|
| prov_01 | `tr_prov_run54b` | `run-54b-20250101-20251230-d37c696d` vs `run-54b-20250101-20251230-dfc9611d` vs `run-e92b485b-...` | Multiple backtest runs with overlapping date ranges but different hashes; source-level conflict. |

### non_invalidation_decoy (1 real slot)

| Slot | trajectory_id | Source entity / family | Why it fits |
|------|---------------|------------------------|-------------|
| decoy_01 | `tr_decoy_strategy_scripts` | `openclaw_skills/strategy-researcher/scripts/call_backtest.py` vs `openclaw_skills/strategy-researcher/SKILL.md` vs `openclaw_skills/strategy-researcher/TOOLS.md` | Parallel targets under same skill namespace; easy to over-invalidate. |

## Synthetic Slot Requirements

| Category | Count | Construction notes |
|----------|-------|-------------------|
| `full` | 1 | Mirror v1 `tr01_full_leverage_flip` structure with different domain terms. |
| `partial` | 3 | Policy with clauses; later observation invalidates only one clause. |
| `conditional` | 3 | Global rule + region/window exception; both must remain active. |
| `revival` | 1 | Feature flag disabled then re-enabled; must track rollback and revival. |
| `alias_trap` | 1 | Same as v1 `tr16_alias_false_merge_trap` but with new entity names. |
| `provenance_conflict` | 1 | High-confidence probe vs low-confidence user note, same entity. |
| `non_invalidation_decoy` | 1 | Parallel modes/targets that look like invalidation but are not. |
| `out_of_order_late` | 3 | `observed_at` in-field and missing-field variants; late observation overrides early. |

## Coverage Matrix (v2)

| trajectory_id | full | partial | conditional | revival | alias_trap | provenance_conflict | non_invalidation_decoy | out_of_order_late | source |
|---------------|------|---------|-------------|---------|------------|---------------------|------------------------|-------------------|--------|
| tr_full_tkt_005b | Y | | | | | | | | real |
| tr_full_tkt_006 | Y | | | | | | | | real |
| tr_full_mirror_01 | Y | | | | | | | | synthetic |
| tr_partial_policy_01 | | Y | | | | | | | synthetic |
| tr_partial_checklist_01 | | Y | | | | | | | synthetic |
| tr_partial_clause_01 | | Y | | | | | | | synthetic |
| tr_conditional_region_01 | | | Y | | | | | | synthetic |
| tr_conditional_window_01 | | | Y | | | | | | synthetic |
| tr_conditional_carveout_01 | | | Y | | | | | | synthetic |
| tr_revival_round5x | | | | Y | | | | | real |
| tr_revival_feature_flag_01 | | | | Y | | | | | synthetic |
| tr_alias_quant_tools | | | | | Y | | | | real |
| tr_alias_tkt_split | | | | | Y | | | | real |
| tr_alias_workspace_identity | | | | | Y | | | | real |
| tr_alias_false_merge_01 | | | | | Y | | | | synthetic |
| tr_prov_run54b | | | | | | Y | | | real |
| tr_prov_probe_user_01 | | | | | | Y | | | synthetic |
| tr_decoy_strategy_scripts | | | | | | | Y | | real |
| tr_decoy_parallel_modes_01 | | | | | | | Y | | synthetic |
| tr_ooo_present_01 | | | | | | | | Y | synthetic |
| tr_ooo_missing_01 | | | | | | | | Y | synthetic |
| tr_ooo_latency_01 | | | | | | | | Y | synthetic |

## Execution Order

1. **Step A:** Extract the 9 real trajectories listed above into `benchmark/phase05_v2/trajectories/` and `benchmark/phase05_v2/gold/`.
2. **Step B:** Construct the 13 synthetic trajectories to fill remaining slots.
3. **Step C:** Run `score_phase05.py` on v2 and compare against v1 baseline.

## Open Questions / Risks

- Real abu_modern nodes do not carry `observed_at` / `valid_from` / `valid_to` fields. For real trajectories, timestamps will be derived from `created_turn` and synthetic offsets.
- Real trajectories may not perfectly fit a single category; ambiguous cases will be tagged with the primary category and noted in the trajectory `title`/`notes`.
- The `schema_neutral` flag on gold files should remain `true` so the benchmark does not leak current schema assumptions.
