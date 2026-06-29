# Phase 0.5 Gap Register

本文件登记当前基线在 `Phase 0.5` 失效回放基准上的失败点。
原则：只登记，不修复；失败是基准有效性的证据，不是要被抹平的噪音。

## 基线总览

- validation_ok: `true`
- phase0_current: invalidation P/R=`0.316/0.500`，active-set Set-F1=`0.850`，must_include recall=`0.827`，valid-time=`0.500`
- phase0_current.valid_time_breakdown: observed_at 在场=`0/4`，缺失回退=`4/4`
- flat_rag: invalidation P/R=`0.000/0.000`，active-set Set-F1=`0.850`，must_include recall=`0.827`，valid-time=`0.500`
- flat_rag.valid_time_breakdown: observed_at 在场=`0/4`，缺失回退=`4/4`
- invalidation 分离: precision 差值=`0.316`，recall 差值=`0.500`；这是当前两基线唯一明确发生分离的指标族
- valid-time-present: phase0 == flat_rag，差值=`0.000` -> 该能力缺失，列为 Phase 1 硬目标，不记作 Phase 0.5 失败
- FP 归位核对: classified=`13` / overall=`13` / unclassified=`0`

## 形态缺口

### invalidation_by_tag
- full: P/R=`1.000/1.000`，TP/FP/FN=`4/0/0`
- partial: P/R=`0.000/0.000`，TP/FP/FN=`0/2/2`
- conditional: P/R=`0.000/0.000`，TP/FP/FN=`0/2/2`
- revival: P/R=`0.500/0.500`，TP/FP/FN=`2/2/2`
- alias_trap: P/R=`1.000/NA`，TP/FP/FN=`0/0/0`
- provenance_conflict: P/R=`0.000/NA`，TP/FP/FN=`0/3/0`
- non_invalidation_decoy: P/R=`0.000/NA`，TP/FP/FN=`0/2/0`
- out_of_order_late: P/R=`0.500/1.000`，TP/FP/FN=`2/2/0`

### partial
- 失败轨迹：phase0_current=['tr03_partial_policy_clause', 'tr04_partial_checklist_clause']，flat_rag=['tr03_partial_policy_clause', 'tr04_partial_checklist_clause']
- 结论：现有基线把同实体重复观测视为整节点替换，无法保留旧观测中未被触碰的子句。
- 映射：对应白皮书 §3.1 所说的二值单调 current set 无法表达 partial invalidation。

### conditional
- 失败轨迹：phase0_current=['tr05_conditional_region_exception', 'tr06_conditional_window_exception']，flat_rag=['tr05_conditional_region_exception', 'tr06_conditional_window_exception']
- 结论：现有基线既不会显式刻画 carve-out，也不会把“全局规则 + 条件例外”作为并存当前态。
- 映射：对应 §3.1 的 conditional invalidation 未支持。

### revival
- 失败轨迹：phase0_current=['tr07_revival_feature_flag', 'tr08_revival_research_stream']，flat_rag=['tr07_revival_feature_flag', 'tr08_revival_research_stream']
- 结论：现有基线最多能把后到观测当成新的 full replace，无法把 rollback / re-enable 标成 revival 形态。
- 映射：对应 §3.1 的 revival / rollback 未支持。

### alias_trap
- 失败轨迹：phase0_current=['tr09_alias_same_service', 'tr10_alias_same_person', 'tr19_alias_abbreviation_split_trap', 'tr21_alias_mixed_cost_profile']，flat_rag=['tr09_alias_same_service', 'tr10_alias_same_person', 'tr19_alias_abbreviation_split_trap', 'tr21_alias_mixed_cost_profile']
- conservative_exact_surface: false_split=`1.000` (4/4)，false_merge=`0.000` (0/4)
- aggressive_token_overlap: false_split=`0.500` (2/4)，false_merge=`0.750` (3/4)
- weighted_cost.equal_cost: conservative=`4`，aggressive=`5`，preferred=`conservative_exact_surface`
- weighted_cost.split_is_2x: conservative=`8`，aggressive=`7`，preferred=`aggressive_token_overlap`
- weighted_cost.merge_is_5x: conservative=`4`，aggressive=`17`，preferred=`conservative_exact_surface`
- 结论：保守合并降低误杀但放大 false-split；激进合并减少 split 却在 `Phoenix / Phoenix desk` 一类轨迹上引入 false-merge。
- 映射：对应白皮书 §3.3 的“合并保守是否优于激进”必须由基准裁定，不能先验封板。

### provenance_conflict
- 失败轨迹：phase0_current=['tr11_provenance_conflict', 'tr17_provenance_conflict_probe_wins', 'tr18_provenance_conflict_policy_wins']，flat_rag=['tr11_provenance_conflict', 'tr17_provenance_conflict_probe_wins', 'tr18_provenance_conflict_policy_wins']
- 结论：当前两条基线都没有 source/provenance 权重，遇到高可信探针与低可信口述冲突时只会按到达顺序或窗口保留。
- 映射：该缺口不属于当前二值 schema 的单一字段补丁，需要显式裁决策略。

### non_invalidation_decoy
- 失败轨迹：phase0_current=['tr12_non_invalidation_parallel_targets', 'tr13_non_invalidation_parallel_modes', 'tr21_alias_mixed_cost_profile']，flat_rag=['tr12_non_invalidation_parallel_targets', 'tr13_non_invalidation_parallel_modes', 'tr21_alias_mixed_cost_profile']
- 统计：false_positive_count=`2` / overall_false_positive_count=`13` (share=`0.154`)
- 结论：phase0 在 non_invalidation_decoy 上同样出现过度失效，但 precision 损失并不只集中在 decoy；partial / conditional / revival / provenance 也共同贡献了大量假阳性。这说明 §3.3 的问题不只是 decoy 咬钩，而是当前失效裁定整体偏激进，Phase 1 仍须默认保守。
- 映射：这暴露了 node-atomic replace 对 set-like facts 的过拟合。

### out_of_order_late
- 失败轨迹：phase0_current=['tr14_out_of_order_with_observed_at', 'tr22_out_of_order_price_band_present']，flat_rag=['tr14_out_of_order_with_observed_at', 'tr15_missing_observed_at_fallback', 'tr22_out_of_order_price_band_present', 'tr23_missing_observed_at_latency_fallback']
- 分项现状：observed_at 在场=`0/4`，缺失回退=`4/4`
- 结论：这不是“0.500 抛硬币”，而是 observed_at 在场改判能力根本不存在；缺失时退回到达序这条回退路径则可工作。
- 写实结论：valid-time-present 上 phase0 与 flat_rag 打平，差值为 0，这表示能力缺失，而不是 Phase 0.5 里某个可微调的小失误。
- 映射：对应白皮书 §1.5 中 `observed_at` 缺失前，valid≈tx 假设在乱序/迟到下崩掉。

## 红线结论

- 当前报告不是“现有 schema 全过了”，而是明确记录哪些形态按预期失败。
- 若后续某次运行让 `partial / conditional / revival / out_of_order_late` 全部无差别通过，应先怀疑基准被 fix-to-pass 污染。 
