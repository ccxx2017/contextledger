# Phase 0.5 v2 Category Breakdown

## 说明

- 本文只执行收尾项 1：对 `phase0_current` 做 per-category 拆分。
- 数据来源：`phase05_score_report.json`
- 指标口径：
  - `P/R` = 该 category 的 invalidation precision / recall
  - `Set-F1` = 该 category 下全部 step 的 `active_set_f1` 平均值
  - `must_include recall` = 该 category 下全部 step 的 `must_include_recall` 平均值
- 注意：`tr_prov_run54b` 同时属于 `full + provenance_conflict`，`tr_revival_round5x` 同时属于 `full + revival`，因此 category 之间不是互斥分桶。

## 总表

| category | trajectories | steps | TP/FP/FN | invalidation P | invalidation R | Set-F1 | must_include recall |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 4 | 17 | 8 / 0 / 5 | 1.000 | 0.615 | 0.857 | 1.000 |
| partial | 2 | 4 | 0 / 2 / 2 | 0.000 | 0.000 | 0.750 | 0.625 |
| conditional | 2 | 4 | 0 / 2 / 2 | 0.000 | 0.000 | 0.833 | 0.750 |
| revival | 2 | 8 | 1 / 1 / 5 | 0.500 | 0.167 | 0.738 | 1.000 |
| alias_trap | 3 | 10 | 0 / 0 / 0 | 1.000 | NA | 1.000 | 1.000 |
| provenance_conflict | 2 | 4 | 0 / 1 / 1 | 0.000 | 0.000 | 0.667 | 0.750 |
| non_invalidation_decoy | 2 | 5 | 0 / 1 / 0 | 0.000 | NA | 0.933 | 0.900 |
| out_of_order_late | 2 | 4 | 0 / 2 / 0 | 0.000 | NA | 0.500 | 0.500 |

## Full Invalidation 判读

### 结论

- 若严格按 `full` category 总体口径判定，`full invalidation` **不健康**，当前不应继续推进 schema 扩展。
- 直接原因不是 precision，而是 recall 仅 `0.615`，仍有 `5` 个 gold invalidation 没被命中。

### 但问题位置更具体

- `pure full` 子集（`tr_full_tkt_005b`, `tr_full_tkt_006`）表现是完好的：
  - TP/FP/FN = `8 / 0 / 0`
  - P/R = `1.000 / 1.000`
  - Set-F1 = `1.000`
  - must_include recall = `1.000`
- `mixed full` 子集（`tr_prov_run54b`, `tr_revival_round5x`）表现明显失真：
  - TP/FP/FN = `0 / 0 / 5`
  - P/R = `0.000 / 0.000`
  - Set-F1 = `0.652`
  - must_include recall = `1.000`

### 解释

- 这说明基础的“纯 full replace”链路并没有塌。
- 当前 `full` category 被拉低，主要是因为带有 `provenance_conflict` 与 `revival` 语义的多标签真实轨迹也被计入了 `full`。
- 换句话说，问题更像是：
  - invalidation 裁决无法穿过 provenance 冲突
  - invalidation 裁决无法正确处理 revival / reverify 链
- 而不是最基础的 full replace 在简单轨迹上已经失效。

## Category 逐项观察

### full

- 轨迹：`tr_full_tkt_005b`, `tr_full_tkt_006`, `tr_prov_run54b`, `tr_revival_round5x`
- 观察：precision 很高，但 recall 不够；漏失全部集中在两条多标签真实轨迹。

### partial

- 轨迹：`tr_syn_partial_checklist_clause`, `tr_syn_partial_policy_clause`
- 观察：P/R 都为 `0`，符合“当前 schema 无法表达 partial”的预期。

### conditional

- 轨迹：`tr_syn_conditional_region_exception`, `tr_syn_conditional_window_exception`
- 观察：P/R 都为 `0`，符合“当前 schema 无法表达 carve-out”的预期。

### revival

- 轨迹：`tr_revival_round5x`, `tr_syn_revival_feature_flag`
- 观察：只命中了 `1` 个 revival 事件，且还伴随 `1` 个假阳性；这是当前最明显的真实链短板之一。

### alias_trap

- 轨迹：`tr_alias_quant_tools`, `tr_alias_tkt_split`, `tr_alias_workspace_identity`
- 观察：本 category 在 invalidation 维度没有 gold 事件，`P=1.000 / R=NA` 只表示 `pred=0 / gold=0`；这里更该看实体解析，不该把这项当成 invalidation 能力优秀的证据。

### provenance_conflict

- 轨迹：`tr_prov_run54b`, `tr_syn_provenance_conflict`
- 观察：`P/R = 0 / 0`，说明当前既不会做正确裁决，也会在不该失效时咬出错误事件。

### non_invalidation_decoy

- 轨迹：`tr_decoy_strategy_scripts`, `tr_syn_non_invalidation_parallel_targets`
- 观察：出现 `1` 个假阳性，说明当前 invalidation 裁决仍偏激进。

### out_of_order_late

- 轨迹：`tr_syn_out_of_order_inventory_present`, `tr_syn_out_of_order_price_band_present`
- 观察：`Set-F1` 与 `must_include recall` 都只有 `0.5`，同时 invalidation precision 为 `0`；`observed_at` 在场的迟到样本仍然完全没有被正确处理。

## 执行结论

- 按 `d:\CCXXLESSON\contextledger\pack\projects\contextLedger\context_ledger_secendary_ajustment.md#L3614-L3617` 的决策规则，当前应判定为：
  - `full invalidation 表现不健康`
  - 先做根因分析
  - 暂缓 schema 收敛 / schema 扩展
- 但根因分析的焦点应收窄到：
  - `tr_prov_run54b`
  - `tr_revival_round5x`
  - 以及它们代表的 `provenance_conflict` / `revival` 交叉裁决问题
- 不建议把纯 full replace 链路与这些多标签难例混为一谈。
