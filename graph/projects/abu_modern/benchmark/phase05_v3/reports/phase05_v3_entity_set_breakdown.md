# Phase 0.5 v3 Entity-Set Set-F1 (Resolved Harness)

本报告用于验证 `phase05_v3` 中的 resolved harness 是否真正测到了 resolver 的收益。

## 对账状态

- benchmark mentions 数量：`31`
- 覆盖到的 pending_merge 项数：`25`
- 已 resolved 项数：`16`
- 仍 tracked 项数：`9`
- mismatch 数量：`0`

## 口径

- `D2`：exact surface last-write-wins（以 `normalize_exact(mentions[0])` 为 entity key）。
- `CL(resolved)`：使用 `pending_merge_register` 中已 resolved 的真实 batch 决策做实体归并；对仍 `tracked` 的候选项不强行 merge。
- `expected`：gold 的 `entity_clusters` 先经过同一套 resolved key 映射，再计算 entity-set Set-F1。

## Per-Category 汇总

| category | steps | CL(resolved) entity-set Set-F1 | D2 entity-set Set-F1 | delta(CL-D2) |
|---|---:|---:|---:|---:|
| full | 17 | 0.882 | 0.759 | 0.124 |
| partial | 4 | 1.000 | 1.000 | 0.000 |
| conditional | 4 | 1.000 | 1.000 | 0.000 |
| revival | 8 | 1.000 | 0.738 | 0.262 |
| alias_trap | 10 | 0.690 | 0.690 | 0.000 |
| provenance_conflict | 4 | 0.500 | 0.500 | 0.000 |
| non_invalidation_decoy | 5 | 0.833 | 0.833 | 0.000 |
| out_of_order_late | 4 | 1.000 | 1.000 | 0.000 |

## Per-Trajectory 明细

### tr_alias_quant_tools

| after_obs_id | CL F1 | D2 F1 | expected_entities | CL_entities | D2_entities |
|---|---:|---:|---|---|---|
| obs01 | 1.000 | 1.000 | openclaw_skills/quant-assistant | openclaw_skills/quant-assistant | openclaw_skills/quant-assistant |
| obs02 | 0.667 | 0.667 | openclaw_skills/quant-assistant | openclaw_skills/quant-assistant, openclaw_skills/quant_assistant/tools.md | openclaw_skills/quant-assistant, openclaw_skills/quant_assistant/tools.md |
| obs03 | 0.500 | 0.500 | openclaw_skills/quant-assistant | openclaw_skills/quant-assistant, openclaw_skills/quant_assistant/tools.md, skills/quant_assistant/skill.md且调用正确脚本 | openclaw_skills/quant-assistant, openclaw_skills/quant_assistant/tools.md, skills/quant_assistant/skill.md且调用正确脚本 |

### tr_alias_tkt_split

| after_obs_id | CL F1 | D2 F1 | expected_entities | CL_entities | D2_entities |
|---|---:|---:|---|---|---|
| obs01 | 1.000 | 1.000 | tkt-2026-005b | tkt-2026-005b | tkt-2026-005b |
| obs02 | 0.667 | 0.667 | tkt-2026-005b | tkt-2026-005b, tkt-2026-005c | tkt-2026-005b, tkt-2026-005c |
| obs03 | 0.500 | 0.500 | tkt-2026-005b | tkt-2026-005b, tkt-2026-005c, tkt-2026-005d | tkt-2026-005b, tkt-2026-005c, tkt-2026-005d |
| obs04 | 0.400 | 0.400 | tkt-2026-005b | tkt-2026-005b, tkt-2026-005c, tkt-2026-005d, tkt-2026-005e | tkt-2026-005b, tkt-2026-005c, tkt-2026-005d, tkt-2026-005e |

### tr_alias_workspace_identity

| after_obs_id | CL F1 | D2 F1 | expected_entities | CL_entities | D2_entities |
|---|---:|---:|---|---|---|
| obs01 | 1.000 | 1.000 | openclaw_workspace/identity.md | openclaw_workspace/identity.md | openclaw_workspace/identity.md |
| obs02 | 0.667 | 0.667 | openclaw_workspace/identity.md | openclaw_workspace/identity.md, openclaw_workspace_structure | openclaw_workspace/identity.md, openclaw_workspace_structure |
| obs03 | 0.500 | 0.500 | openclaw_identity_mechanism | openclaw_identity_mechanism, openclaw_workspace/identity.md, openclaw_workspace_structure | openclaw_identity_mechanism, openclaw_workspace/identity.md, openclaw_workspace_structure |

### tr_decoy_strategy_scripts

| after_obs_id | CL F1 | D2 F1 | expected_entities | CL_entities | D2_entities |
|---|---:|---:|---|---|---|
| obs01 | 1.000 | 1.000 | openclaw_skills/strategy-researcher/scripts/call_backtest.py | openclaw_skills/strategy-researcher/scripts/call_backtest.py | openclaw_skills/strategy-researcher/scripts/call_backtest.py |
| obs02 | 0.667 | 0.667 | openclaw_skills/strategy-researcher/scripts/call_backtest.py | openclaw_skills/strategy-researcher/scripts/call_backtest.py, openclaw_skills/strategy-researcher/skill.md | openclaw_skills/strategy-researcher/scripts/call_backtest.py, openclaw_skills/strategy-researcher/skill.md |
| obs03 | 0.500 | 0.500 | openclaw_skills/strategy-researcher/scripts/call_backtest.py | openclaw_skills/strategy-researcher/scripts/call_backtest.py, openclaw_skills/strategy-researcher/skill.md, openclaw_skills/strategy-researcher/tools.md | openclaw_skills/strategy-researcher/scripts/call_backtest.py, openclaw_skills/strategy-researcher/skill.md, openclaw_skills/strategy-researcher/tools.md |

### tr_full_tkt_005b

| after_obs_id | CL F1 | D2 F1 | expected_entities | CL_entities | D2_entities |
|---|---:|---:|---|---|---|
| obs01 | 1.000 | 1.000 | tkt-2026-005b | tkt-2026-005b | tkt-2026-005b |
| obs02 | 1.000 | 1.000 | tkt-2026-005b | tkt-2026-005b | tkt-2026-005b |
| obs03 | 1.000 | 1.000 | tkt-2026-005b | tkt-2026-005b | tkt-2026-005b |
| obs04 | 1.000 | 1.000 | tkt-2026-005b | tkt-2026-005b | tkt-2026-005b |
| obs05 | 1.000 | 1.000 | tkt-2026-005b | tkt-2026-005b | tkt-2026-005b |

### tr_full_tkt_006

| after_obs_id | CL F1 | D2 F1 | expected_entities | CL_entities | D2_entities |
|---|---:|---:|---|---|---|
| obs01 | 1.000 | 1.000 | tkt-2026-006 | tkt-2026-006 | tkt-2026-006 |
| obs02 | 1.000 | 1.000 | tkt-2026-006 | tkt-2026-006 | tkt-2026-006 |
| obs03 | 1.000 | 1.000 | tkt-2026-006 | tkt-2026-006 | tkt-2026-006 |
| obs04 | 1.000 | 1.000 | tkt-2026-006 | tkt-2026-006 | tkt-2026-006 |
| obs05 | 1.000 | 1.000 | tkt-2026-006 | tkt-2026-006 | tkt-2026-006 |

### tr_prov_run54b

| after_obs_id | CL F1 | D2 F1 | expected_entities | CL_entities | D2_entities |
|---|---:|---:|---|---|---|
| obs01 | 0.000 | 0.000 | main_entity | run-54b-20250101-20251230-dfc9611d | run-54b-20250101-20251230-dfc9611d |
| obs02 | 0.000 | 0.000 | main_entity | run-54b-20250101-20251230-dfc9611d | run-54b-20250101-20251230-d37c696d, run-54b-20250101-20251230-dfc9611d |

### tr_revival_round5x

| after_obs_id | CL F1 | D2 F1 | expected_entities | CL_entities | D2_entities |
|---|---:|---:|---|---|---|
| obs01 | 1.000 | 1.000 | tkt-2026-005b_round5 | tkt-2026-005b_round5 | tkt-2026-005b_round5 |
| obs02 | 1.000 | 0.667 | tkt-2026-005b_round5 | tkt-2026-005b_round5 | tkt-2026-005b_round5, tkt-2026-005b_round5.3a_audit |
| obs03 | 1.000 | 0.500 | tkt-2026-005b_round5 | tkt-2026-005b_round5 | tkt-2026-005b_round5, tkt-2026-005b_round5.3a_audit, tkt-2026-005b_round5.3b_fix |
| obs04 | 1.000 | 0.400 | tkt-2026-005b_round5 | tkt-2026-005b_round5 | tkt-2026-005b_round5, tkt-2026-005b_round5.3a_audit, tkt-2026-005b_round5.3b_fix, tkt-2026-005b_round5.3c_verify |
| obs05 | 1.000 | 0.333 | tkt-2026-005b_round5 | tkt-2026-005b_round5 | tkt-2026-005b_round5, tkt-2026-005b_round5.3a_audit, tkt-2026-005b_round5.3b_fix, tkt-2026-005b_round5.3c_reverify, tkt-2026-005b_round5.3c_verify |

### tr_syn_conditional_region_exception

| after_obs_id | CL F1 | D2 F1 | expected_entities | CL_entities | D2_entities |
|---|---:|---:|---|---|---|
| tr05_obs01 | 1.000 | 1.000 | deployment rule | deployment rule | deployment rule |
| tr05_obs02 | 1.000 | 1.000 | deployment rule | deployment rule | deployment rule |

### tr_syn_conditional_window_exception

| after_obs_id | CL F1 | D2 F1 | expected_entities | CL_entities | D2_entities |
|---|---:|---:|---|---|---|
| tr06_obs01 | 1.000 | 1.000 | risk gate | risk gate | risk gate |
| tr06_obs02 | 1.000 | 1.000 | risk gate | risk gate | risk gate |

### tr_syn_non_invalidation_parallel_targets

| after_obs_id | CL F1 | D2 F1 | expected_entities | CL_entities | D2_entities |
|---|---:|---:|---|---|---|
| tr12_obs01 | 1.000 | 1.000 | deployment allow-list | deployment allow-list | deployment allow-list |
| tr12_obs02 | 1.000 | 1.000 | deployment allow-list | deployment allow-list | deployment allow-list |

### tr_syn_out_of_order_inventory_present

| after_obs_id | CL F1 | D2 F1 | expected_entities | CL_entities | D2_entities |
|---|---:|---:|---|---|---|
| tr14_obs01 | 1.000 | 1.000 | inventory snapshot | inventory snapshot | inventory snapshot |
| tr14_obs02 | 1.000 | 1.000 | inventory snapshot | inventory snapshot | inventory snapshot |

### tr_syn_out_of_order_price_band_present

| after_obs_id | CL F1 | D2 F1 | expected_entities | CL_entities | D2_entities |
|---|---:|---:|---|---|---|
| tr22_obs01 | 1.000 | 1.000 | price band | price band | price band |
| tr22_obs02 | 1.000 | 1.000 | price band | price band | price band |

### tr_syn_partial_checklist_clause

| after_obs_id | CL F1 | D2 F1 | expected_entities | CL_entities | D2_entities |
|---|---:|---:|---|---|---|
| tr04_obs01 | 1.000 | 1.000 | replay checklist | replay checklist | replay checklist |
| tr04_obs02 | 1.000 | 1.000 | replay checklist | replay checklist | replay checklist |

### tr_syn_partial_policy_clause

| after_obs_id | CL F1 | D2 F1 | expected_entities | CL_entities | D2_entities |
|---|---:|---:|---|---|---|
| tr03_obs01 | 1.000 | 1.000 | order gateway policy | order gateway policy | order gateway policy |
| tr03_obs02 | 1.000 | 1.000 | order gateway policy | order gateway policy | order gateway policy |

### tr_syn_provenance_conflict

| after_obs_id | CL F1 | D2 F1 | expected_entities | CL_entities | D2_entities |
|---|---:|---:|---|---|---|
| tr11_obs01 | 1.000 | 1.000 | broker adapter | broker adapter | broker adapter |
| tr11_obs02 | 1.000 | 1.000 | broker adapter | broker adapter | broker adapter |

### tr_syn_revival_feature_flag

| after_obs_id | CL F1 | D2 F1 | expected_entities | CL_entities | D2_entities |
|---|---:|---:|---|---|---|
| tr07_obs01 | 1.000 | 1.000 | alpha feature | alpha feature | alpha feature |
| tr07_obs02 | 1.000 | 1.000 | alpha feature | alpha feature | alpha feature |
| tr07_obs03 | 1.000 | 1.000 | alpha feature | alpha feature | alpha feature |

