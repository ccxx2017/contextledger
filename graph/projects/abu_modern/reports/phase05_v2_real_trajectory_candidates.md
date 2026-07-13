# Phase 0.5 v2 Real Trajectory Candidates

**Generated:** 2026-07-13
**Range analyzed:** turn_020 to turn_084 (65 turns)

## Summary

- Total unique entity_refs tracked: 104
- Multi-turn entities with state changes: 44
- Supersession links in final graph: 10
- TKT ticket families: 10
- Alias clusters from pending_merge: 90

## Top Candidate Trajectories

| # | entity_ref | guessed category | turn span | distinct turns | node count | states | superseded? | alias? |
|---|------------|------------------|-----------|----------------|------------|--------|-------------|--------|
| 1 | `duty_reporter` | full | 20-84 | 65 | 195 | open=130 | False | False |
| 2 | `openclaw_skills/strategy-researcher` | alias | 20-84 | 65 | 195 | open=65 | False | True |
| 3 | `strategy_research_agent` | full | 20-84 | 65 | 130 | open=65 | False | False |
| 4 | `TKT-2026-006` | alias | 20-84 | 65 | 130 | open=65 | False | True |
| 5 | `openclaw_root_tools_md` | alias | 20-84 | 65 | 126 | open=1, deployed=60 | False | True |
| 6 | `openclaw_skills/strategy-researcher/TOOLS.md` | alias | 20-84 | 65 | 115 | open=65, deployed=50 | False | True |
| 7 | `workspace_root_bootstrap_audit` | alias | 20-84 | 65 | 65 | open=4, in_progress=61 | False | True |
| 8 | `openclaw_skills/quant_assistant/TOOLS.md` | alias | 24-84 | 61 | 61 | open=1, deployed=60 | False | True |
| 9 | `aos/runtime/tickets/open/TKT-2026-005B-vcp-breakout-entry.md` | full_or_supersession | 31-84 | 54 | 54 | superseded=1 | True | True |
| 10 | `TKT-2026-005B` | alias | 32-84 | 53 | 463 | resolved=153, deployed=40 | False | True |
| 11 | `TKT-2026-005C` | alias | 33-84 | 52 | 104 | blocked=44, open=10, resolved=50 | False | True |
| 12 | `aos/services/backtest-api` | full | 34-84 | 51 | 53 | open=51 | False | False |
| 13 | `TKT-2026-005E` | alias | 39-84 | 46 | 87 | open=5, resolved=41 | False | True |
| 14 | `TKT-2026-005D` | alias | 39-84 | 46 | 46 | open=4, implemented=42 | False | True |
| 15 | `tkt_2026_005b_recovery_patch` | alias | 45-84 | 40 | 40 | open=1, resolved=39 | False | True |
| 16 | `TKT-2026-005F` | alias | 50-84 | 35 | 104 | open=1, resolved=34 | False | True |
| 17 | `TKT-2026-005H` | alias | 51-84 | 34 | 102 | resolved=68 | False | True |
| 18 | `TKT-2026-005G` | alias | 51-84 | 34 | 68 | resolved=34 | False | True |
| 19 | `backend/app/api/endpoints/backtests/start.py` | full_or_supersession | 51-84 | 34 | 34 | superseded=1 | True | True |
| 20 | `TKT-2026-005I` | alias | 52-84 | 33 | 161 | resolved=64, open=1 | False | True |
| 21 | `TKT-2026-005B_round5` | alias | 54-84 | 31 | 31 | open=1, resolved=30 | False | True |
| 22 | `TKT-2026-005B_round5_result` | full_or_supersession | 55-84 | 30 | 30 | superseded=1 | True | True |
| 23 | `TKT-2026-005B_round5.1_audit` | full_or_supersession | 55-84 | 30 | 30 | open=1, resolved=28, superseded=1 | True | True |
| 24 | `TKT-2026-005B_round5.2_reconciliation` | alias | 56-84 | 29 | 29 | open=1, resolved=28 | False | True |
| 25 | `TKT-2026-005B_round5.3A_audit` | alias | 58-84 | 27 | 53 | open=1, resolved=26 | False | True |
| 26 | `TKT-2026-005B_round5.3B_fix` | alias | 58-84 | 27 | 53 | open=1, resolved=26 | False | True |
| 27 | `TKT-2026-005B_round5.3C_reverify` | full_or_supersession | 60-84 | 25 | 25 | open=1, resolved=23, superseded=1 | True | True |
| 28 | `TKT-2026-005B_round5.3D_reconcile` | alias | 61-84 | 24 | 24 | open=2, resolved=22 | False | True |
| 29 | `round_5.3e_consistency_check` | alias | 64-84 | 21 | 21 | open=1, resolved=20 | False | True |
| 30 | `round_5.3f_artifact_source_reconciliation` | alias | 65-84 | 20 | 20 | open=1, resolved=19 | False | True |
| 31 | `round_5.4a_artifact_chain_fix` | alias | 66-84 | 19 | 19 | open=1, in_progress=1, resolved=17 | False | True |
| 32 | `round_5.4a_feishu_audit` | alias | 67-84 | 18 | 18 | open=1, resolved=17 | False | True |
| 33 | `round_5.4b_full_run` | alias | 67-84 | 18 | 18 | open=2, blocked=1, in_progress=1, resolved=14 | False | True |
| 34 | `round_5.4a_feishu_audit_result` | full_or_supersession | 68-84 | 17 | 17 | superseded=1 | True | True |
| 35 | `round_5.4b_fix1` | alias | 69-84 | 16 | 16 | open=1, implemented=1, resolved=14 | False | True |
| 36 | `run-54b-20250101-20251230-d37c696d` | full_or_supersession | 70-84 | 15 | 15 | superseded=1 | True | True |
| 37 | `round_5.5_baseline_freeze` | alias | 72-84 | 13 | 13 | open=1, resolved=12 | False | True |
| 38 | `confirm_train_split_0.7` | full | 74-84 | 11 | 11 | open=1, resolved=10 | False | False |
| 39 | `round_6a_stop_loss_7pct` | alias | 77-84 | 8 | 8 | blocked=3, open=5 | False | True |
| 40 | `round_6a_cache_remediation` | full_or_supersession | 78-84 | 7 | 7 | open=1, in_progress=1, resolved=4, superseded=1 | True | True |
| 41 | `round_6a_backend_diagnosis` | alias | 81-84 | 4 | 4 | open=1, resolved=3 | False | True |
| 42 | `backend_defect_repair` | alias | 82-84 | 3 | 3 | open=1, implemented=2 | False | True |
| 43 | `round_6a_full_diagnosis` | full_or_supersession | 82-84 | 3 | 3 | superseded=1 | True | True |
| 44 | `backend_defect_repair_implementation` | full_or_supersession | 83-84 | 2 | 2 | superseded=1 | True | True |

## Supersession Chains

| source node | source entity_ref | target node | target entity_ref | reason |
|-------------|-------------------|-------------|-------------------|--------|
| n_0090 | `aos/runtime/tickets/open/TKT-2026-005B-vcp-breakout-entry.md` | n_0072 | `aos/runtime/tickets/open/TKT-2026-005-vcp-breakout.md` | batch_reconcile:MERGE |
| n_0128 | `backend/app/api/endpoints/backtests/start.py` | n_0048 | `backend/app/api/endpoints/knowledge.py` | batch_reconcile:LIKELY_MERGE |
| n_0139 | `TKT-2026-005B_round5_result` | n_0138 | `TKT-2026-005B_round5` | batch_reconcile:MERGE |
| n_0140 | `TKT-2026-005B_round5.1_audit` | n_0138 | `TKT-2026-005B_round5` | batch_reconcile:LIKELY_MERGE |
| n_0155 | `TKT-2026-005B_round5.3C_reverify` | n_0151 | `TKT-2026-005B_round5.3C_verify` | batch_reconcile:MERGE |
| n_0175 | `round_5.4a_feishu_audit_result` | n_0173 | `round_5.4a_feishu_audit` | batch_reconcile:MERGE |
| n_0179 | `run-54b-20250101-20251230-d37c696d` | n_0176 | `run-54b-20250101-20251230-dfc9611d` | batch_reconcile:MERGE |
| n_0192 | `round_6a_cache_remediation` | n_0187 | `round_6a_cache_pollution` | batch_reconcile:LIKELY_MERGE |
| n_0199 | `round_6a_full_diagnosis` | n_0196 | `round_6a_backend_diagnosis` | batch_reconcile:LIKELY_MERGE |
| n_0201 | `backend_defect_repair_implementation` | n_0198 | `backend_defect_repair` | batch_reconcile:LIKELY_MERGE |

## TKT Ticket Families

### TKT-2026-005B
- `TKT-2026-005B`: turns 32-84, states={'resolved': 153, None: 270, 'deployed': 40}
- `TKT-2026-005B_round5`: turns 54-84, states={'open': 1, 'resolved': 30}
- `TKT-2026-005B_round5.1_audit`: turns 55-84, states={'open': 1, 'resolved': 28, 'superseded': 1}
- `TKT-2026-005B_round5.2_audit`: turns 57-84, states={None: 28}
- `TKT-2026-005B_round5.2_reconciliation`: turns 56-84, states={'open': 1, 'resolved': 28}
- `TKT-2026-005B_round5.3A_audit`: turns 58-84, states={'open': 1, 'resolved': 26, None: 26}
- `TKT-2026-005B_round5.3B_fix`: turns 58-84, states={'open': 1, 'resolved': 26, None: 26}
- `TKT-2026-005B_round5.3C_fix`: turns 60-84, states={None: 25}
- `TKT-2026-005B_round5.3C_reverify`: turns 60-84, states={'open': 1, 'resolved': 23, 'superseded': 1}
- `TKT-2026-005B_round5.3C_verify`: turns 58-84, states={'open': 27}
- `TKT-2026-005B_round5.3D_reconcile`: turns 61-84, states={'open': 2, 'resolved': 22}
- `TKT-2026-005B_round5.3D_report`: turns 63-84, states={None: 22}
- `TKT-2026-005B_round5.3_engine_audit`: turns 57-84, states={'open': 28}
- `TKT-2026-005B_round5_result`: turns 55-84, states={None: 29, 'superseded': 1}
- `aos/runtime/tickets/open/TKT-2026-005B-vcp-breakout-entry.md`: turns 31-84, states={None: 53, 'superseded': 1}

### TKT-2026-005
- `TKT-2026-005`: turns 20-84, states={'open': 65}
- `TKT-2026-005G`: turns 51-84, states={'resolved': 34, None: 34}
- `TKT-2026-005H`: turns 51-84, states={'resolved': 68, None: 34}
- `TKT-2026-005I`: turns 52-84, states={None: 96, 'resolved': 64, 'open': 1}
- `TKT-2026-005I-kb-minimum-sanity-check-validation.md`: turns 52-84, states={'deployed': 33}
- `TKT-2026-005I-kb-minimum-sanity-check.md`: turns 52-84, states={'deployed': 33}
- `aos/runtime/tickets/open/TKT-2026-005-vcp-breakout.md`: turns 20-84, states={None: 65}

### TKT-2026-002
- `TKT-2026-002`: turns 20-84, states={'resolved': 65}
- `aos/runtime/tickets/open/TKT-2026-002-charter-strategy-researcher.md`: turns 20-84, states={'open': 65}

### TKT-2026-004
- `TKT-2026-004`: turns 20-84, states={'resolved': 130}
- `aos/runtime/tickets/open/TKT-2026-004strategy_researcher_Agent_HTTP_适配脚本.md`: turns 20-84, states={'deployed': 65}

### TKT-2026-003
- `TKT-2026-003`: turns 20-84, states={'resolved': 65}

### TKT-2026-006
- `TKT-2026-006`: turns 20-84, states={'open': 65, None: 65}

### TKT-2026-005C
- `TKT-2026-005C`: turns 33-84, states={'blocked': 44, 'open': 10, 'resolved': 50}

### TKT-2026-005D
- `TKT-2026-005D`: turns 39-84, states={'open': 4, 'implemented': 42}

### TKT-2026-005E
- `TKT-2026-005E`: turns 39-84, states={'open': 5, 'resolved': 41, None: 41}

### TKT-2026-005F
- `TKT-2026-005F`: turns 50-84, states={'open': 1, None: 69, 'resolved': 34}

## Alias Clusters from pending_merge

- `TKT-2026-005B_round5_result` ↔ `TKT-2026-005`, `TKT-2026-005B`, `TKT-2026-005B_round5`, `TKT-2026-005B_round5.1_audit`, `TKT-2026-005B_round5.2_audit`, `TKT-2026-005B_round5.2_reconciliation`, `TKT-2026-005B_round5.3B_fix`, `TKT-2026-005B_round5.3C_verify`, `TKT-2026-005B_round5.3D_reconcile`, `TKT-2026-005B_round5.3_engine_audit`, `TKT-2026-005B_round5_result`, `TKT-2026-005C`, `TKT-2026-005E`, `TKT-2026-005G`, `TKT-2026-005I`, `TKT-2026-005I-kb-minimum-sanity-check-validation.md`, `round_5.4a_feishu_audit`
- `TKT-2026-005` ↔ `TKT-2026-005`, `TKT-2026-005B`, `TKT-2026-005B_round5`, `TKT-2026-005B_round5_result`, `TKT-2026-005C`, `TKT-2026-005D`, `TKT-2026-005E`, `TKT-2026-005F`, `TKT-2026-005G`, `TKT-2026-005H`, `TKT-2026-005I`, `TKT-2026-006`
- `TKT-2026-005B` ↔ `TKT-2026-005`, `TKT-2026-005B`, `TKT-2026-005B_round5`, `TKT-2026-005B_round5.2_audit`, `TKT-2026-005B_round5_result`, `TKT-2026-005C`, `TKT-2026-005E`, `TKT-2026-005F`, `TKT-2026-005H`, `TKT-2026-005I-kb-minimum-sanity-check.md`, `TKT-2026-006`, `tkt_2026_005b_recovery_patch`
- `TKT-2026-005B_round5.2_audit` ↔ `TKT-2026-005B`, `TKT-2026-005B_round5.2_audit`, `TKT-2026-005B_round5.3A_audit`, `TKT-2026-005B_round5.3B_fix`, `TKT-2026-005B_round5.3C_verify`, `TKT-2026-005B_round5.3_engine_audit`, `TKT-2026-005B_round5_result`, `TKT-2026-005C`, `TKT-2026-005F`, `TKT-2026-005I`, `round_5.4a_artifact_chain_fix`, `round_5.4a_feishu_audit_result`
- `TKT-2026-005B_round5.3B_fix` ↔ `TKT-2026-005B_round5.2_audit`, `TKT-2026-005B_round5.3A_audit`, `TKT-2026-005B_round5.3B_fix`, `TKT-2026-005B_round5.3C_fix`, `TKT-2026-005B_round5.3C_reverify`, `TKT-2026-005B_round5.3C_verify`, `TKT-2026-005B_round5.3D_reconcile`, `TKT-2026-005B_round5_result`, `round_5.4b_fix1_feishu_audit`, `round_5.4b_full_run`
- `round_5.4a_feishu_audit_result` ↔ `TKT-2026-005B_round5.2_audit`, `TKT-2026-005B_round5.3A_audit`, `round_5.4a_feishu_audit`, `round_5.4a_feishu_audit_result`, `round_5.4b_fix1`, `round_5.4b_fix1_feishu_audit`, `round_5.4b_full_run`, `round_5.5_baseline_freeze`, `round_6a_cache_pollution`, `round_6a_stop_loss_7pct`
- `openclaw_identity_mechanism` ↔ `agents/git_sync_protocol`, `identity_smoke_c`, `openclaw_identity_mechanism`, `openclaw_root_tools_md`, `openclaw_skills`, `openclaw_skills/quant-assistant`, `openclaw_workspace/AGENTS.md`, `openclaw_workspace_structure`, `~/.openclaw/openclaw.json`
- `openclaw_workspace_structure` ↔ `openclaw_agent_routing_default`, `openclaw_agent_runtime_mechanisms`, `openclaw_identity_mechanism`, `openclaw_root_tools_md`, `openclaw_skills/quant-assistant`, `openclaw_skills/quant_assistant/TOOLS.md`, `openclaw_workspace/AGENTS.md`, `openclaw_workspace/IDENTITY.md`, `openclaw_workspace_structure`
- `openclaw_skills/quant-assistant` ↔ `openclaw_identity_mechanism`, `openclaw_skills/quant-assistant`, `openclaw_skills/quant_assistant/TOOLS.md`, `openclaw_skills/strategy-researcher/SKILL.md`, `openclaw_skills/strategy-researcher/TOOLS.md`, `openclaw_skills/strategy_researcher/SKILL.md`, `openclaw_workspace_structure`, `skills/quant_assistant/SKILL.md且调用正确脚本`
- `openclaw_skills/strategy-researcher/SKILL.md` ↔ `openclaw_skills/quant-assistant`, `openclaw_skills/strategy-researcher`, `openclaw_skills/strategy-researcher/SKILL.md`, `openclaw_skills/strategy-researcher/TOOLS.md`, `openclaw_skills/strategy-researcher/prompts/research_workflow.md`, `openclaw_skills/strategy-researcher/scripts`, `openclaw_skills/strategy-researcher/scripts/call_backtest.py`, `openclaw_skills/strategy_researcher/SKILL.md`
- `TKT-2026-005B_round5` ↔ `TKT-2026-005`, `TKT-2026-005B`, `TKT-2026-005B_round5`, `TKT-2026-005B_round5.1_audit`, `TKT-2026-005B_round5_result`, `TKT-2026-005C`, `TKT-2026-005E`, `TKT-2026-005I`
- `TKT-2026-005B_round5.3A_audit` ↔ `TKT-2026-005B_round5.2_audit`, `TKT-2026-005B_round5.3B_fix`, `TKT-2026-005B_round5.3C_verify`, `TKT-2026-005B_round5.3D_reconcile`, `round_5.4a_artifact_chain_fix`, `round_5.4a_feishu_audit`, `round_5.4a_feishu_audit_result`
- `round_5.4b_full_run` ↔ `TKT-2026-005B_round5.3B_fix`, `TKT-2026-005B_round5.3C_fix`, `round_5.4a_artifact_chain_fix`, `round_5.4a_feishu_audit`, `round_5.4a_feishu_audit_result`, `round_5.4b_fix1`, `round_5.4b_full_run`
- `openclaw_skills` ↔ `openclaw_agent_routing_default`, `openclaw_identity_mechanism`, `openclaw_root_tools_md`, `openclaw_skills`, `openclaw_skills/strategy-researcher/TOOLS.md`, `workspace_root_bootstrap_audit`
- `openclaw_skills/strategy-researcher/scripts` ↔ `openclaw_skills/strategy-researcher`, `openclaw_skills/strategy-researcher/SKILL.md`, `openclaw_skills/strategy-researcher/TOOLS.md`, `openclaw_skills/strategy-researcher/scripts`, `openclaw_skills/strategy-researcher/scripts/call_backtest.py`, `openclaw_skills/strategy_researcher/SKILL.md`
- `openclaw_skills/strategy-researcher/scripts/call_backtest.py` ↔ `openclaw_skills/strategy-researcher`, `openclaw_skills/strategy-researcher/SKILL.md`, `openclaw_skills/strategy-researcher/scripts`, `openclaw_skills/strategy-researcher/scripts/call_backtest.py`, `openclaw_skills/strategy-researcher/scripts/call_builder.py`, `openclaw_skills/strategy_researcher/SKILL.md`
- `openclaw_skills/strategy_researcher` ↔ `aos/org/skills/strategy_researcher`, `docs/aos/org/agents/agent-strategy-researcher.md`, `openclaw_skills/strategy-researcher`, `openclaw_skills/strategy_researcher`, `openclaw_skills/strategy_researcher/SKILL.md`, `skills/strategy_researcher/SKILL.md`
- `TKT-2026-005B_round5.3C_verify` ↔ `TKT-2026-005B_round5.2_audit`, `TKT-2026-005B_round5.3A_audit`, `TKT-2026-005B_round5.3B_fix`, `TKT-2026-005B_round5.3C_reverify`, `TKT-2026-005B_round5.3C_verify`, `TKT-2026-005B_round5_result`
- `TKT-2026-005B_round5.3D_reconcile` ↔ `TKT-2026-005B_round5.3A_audit`, `TKT-2026-005B_round5.3B_fix`, `TKT-2026-005B_round5.3C_fix`, `TKT-2026-005B_round5.3D_reconcile`, `TKT-2026-005B_round5.3D_report`, `TKT-2026-005B_round5_result`
- `round_5.4a_artifact_chain_fix` ↔ `TKT-2026-005B_round5.2_audit`, `TKT-2026-005B_round5.3A_audit`, `round_5.3f_artifact_source_reconciliation`, `round_5.4a_artifact_chain_fix`, `round_5.4a_feishu_audit`, `round_5.4b_full_run`

## Recommendations for v2 Coverage Matrix

Based on this scan, the following real cases are strong candidates for v2 trajectories:

| Category | Candidate entity_refs / families | Source |
|----------|----------------------------------|--------|
| full / supersession | TKT-2026-005 family, Round 5.x audit/fix/verify chain | Real abu_modern chain |
| alias_false_merge | openclaw_skills quant_assistant variants, SOUL.md vs log.md | pending_merge register |
| alias_split | TKT-2026-005 / 005B / 005C / 005D / 005E / 005F | Real abu_modern chain |
| provenance_conflict | run-54b-... IDs with different hashes | Real abu_modern chain |
| non_invalidation_decoy | openclaw_skills/strategy-researcher scripts vs SKILL.md | pending_merge register |
| partial / conditional / revival / out_of_order | **No natural real cases found** — will need synthetic construction | Synthetic |

Next: select the top N candidates and convert them into trajectory/gold JSON files compatible with `score_phase05.py`.
