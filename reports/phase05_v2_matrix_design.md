# Phase 0.5 v2 覆盖矩阵设计

## 修正项

- 真实轨迹数量已校正为 `8`，不是先前口头汇报中的 `9`。
- 本次将矩阵收敛为 `19` 个槽位，保持在 18-20 的建议范围内。
- 之所以最终是 `17` 条轨迹覆盖 `19` 个槽位，是因为 `tr_revival_round5x` 与 `tr_prov_run54b` 都是多标签真实轨迹，会自然抬高槽位数。

## 槽位规划

| 类别 | 目标槽位 | 当前构成 | 说明 |
|---|---:|---|---|
| full | 4 | 4 real | 真实轨迹里已有两个多标签样本，因此自然形成 4 个 full 槽位。 |
| partial | 2 | 2 synthetic | 当前 schema 已知缺口，用 synthetic 诚实暴露。 |
| conditional | 2 | 2 synthetic | 当前 schema 已知缺口，用 synthetic 诚实暴露。 |
| revival | 2 | 1 real + 1 synthetic | 保留一个真实 revival，再补一个合成模板。 |
| alias_trap | 3 | 3 real | 真实数据已足够。 |
| provenance_conflict | 2 | 1 real + 1 synthetic | 补一条标准冲突裁决模板。 |
| non_invalidation_decoy | 2 | 1 real + 1 synthetic | 增加 precision 压力测试。 |
| out_of_order_late | 2 | 2 synthetic | 只保留 observed_at 在场的乱序样本，避免 fallback 样本稀释信号。 |
| 合计 | 19 | 10 real slots + 9 synthetic slots | 满足建议区间。 |

## 轨迹清单

| trajectory_id | 来源 | 类别 |
|---|---|---|
| tr_alias_quant_tools | real | alias_trap |
| tr_alias_tkt_split | real | alias_trap |
| tr_alias_workspace_identity | real | alias_trap |
| tr_decoy_strategy_scripts | real | non_invalidation_decoy |
| tr_full_tkt_005b | real | full |
| tr_full_tkt_006 | real | full |
| tr_prov_run54b | real | provenance_conflict, full |
| tr_revival_round5x | real | revival, full |
| tr_syn_conditional_region_exception | synthetic | conditional |
| tr_syn_conditional_window_exception | synthetic | conditional |
| tr_syn_non_invalidation_parallel_targets | synthetic | non_invalidation_decoy |
| tr_syn_out_of_order_inventory_present | synthetic | out_of_order_late |
| tr_syn_out_of_order_price_band_present | synthetic | out_of_order_late |
| tr_syn_partial_checklist_clause | synthetic | partial |
| tr_syn_partial_policy_clause | synthetic | partial |
| tr_syn_provenance_conflict | synthetic | provenance_conflict |
| tr_syn_revival_feature_flag | synthetic | revival |

## 计数核对

- 轨迹总数：`17`（real=`8`，synthetic=`9`）
- 槽位总数：`19`
- 各类槽位：`{"full": 4, "partial": 2, "conditional": 2, "revival": 2, "alias_trap": 3, "provenance_conflict": 2, "non_invalidation_decoy": 2, "out_of_order_late": 2}`

