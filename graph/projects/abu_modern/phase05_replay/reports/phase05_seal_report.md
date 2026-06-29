# Phase 0.5 Seal Report

## 封板结论

- Phase 0.5 封板完成：基准已经把能力缺口、样本覆盖与完成线写法固定下来。
- invalidation 是当前唯一明确分离的指标族：precision 差值=`0.316`，recall 差值=`0.500`。
- valid-time-present 仍为能力缺失：phase0 == flat_rag，差值=`0.000`，observed_at 在场=`0/4`。
- 必要性结论保持诚实：当前只构成弱证成立，真正的分离仍要等 Phase 1 把 partial / conditional / valid-time 做出来。
- FP 归位核对：classified=`13` / overall=`13` / unclassified=`0`。

## Invalidation By Tag

### phase0_current

- full: P=`1.000` / R=`1.000` (TP/FP/FN=`4/0/0`; pred/gold=`4/4`)
- partial: P=`0.000` / R=`0.000` (TP/FP/FN=`0/2/2`; pred/gold=`2/2`)
- conditional: P=`0.000` / R=`0.000` (TP/FP/FN=`0/2/2`; pred/gold=`2/2`)
- revival: P=`0.500` / R=`0.500` (TP/FP/FN=`2/2/2`; pred/gold=`4/4`)
- alias_trap: P=`1.000` / R=`NA` (TP/FP/FN=`0/0/0`; pred/gold=`0/0`)
- provenance_conflict: P=`0.000` / R=`NA` (TP/FP/FN=`0/3/0`; pred/gold=`3/0`)
- non_invalidation_decoy: P=`0.000` / R=`NA` (TP/FP/FN=`0/2/0`; pred/gold=`2/0`)
- out_of_order_late: P=`0.500` / R=`1.000` (TP/FP/FN=`2/2/0`; pred/gold=`4/2`)

### flat_rag

- full: P=`0.000` / R=`0.000` (TP/FP/FN=`0/0/4`; pred/gold=`0/4`)
- partial: P=`0.000` / R=`0.000` (TP/FP/FN=`0/0/2`; pred/gold=`0/2`)
- conditional: P=`0.000` / R=`0.000` (TP/FP/FN=`0/0/2`; pred/gold=`0/2`)
- revival: P=`0.000` / R=`0.000` (TP/FP/FN=`0/0/4`; pred/gold=`0/4`)
- alias_trap: P=`1.000` / R=`NA` (TP/FP/FN=`0/0/0`; pred/gold=`0/0`)
- provenance_conflict: P=`1.000` / R=`NA` (TP/FP/FN=`0/0/0`; pred/gold=`0/0`)
- non_invalidation_decoy: P=`1.000` / R=`NA` (TP/FP/FN=`0/0/0`; pred/gold=`0/0`)
- out_of_order_late: P=`0.000` / R=`0.000` (TP/FP/FN=`0/0/2`; pred/gold=`0/2`)

## Decoy 结论

- non_invalidation_decoy: false_positive_count=`2` / overall_false_positive_count=`13` (share=`0.154`)
- 写实结论：phase0 在 non_invalidation_decoy 上同样出现过度失效，但 precision 损失并不只集中在 decoy；partial / conditional / revival / provenance 也共同贡献了大量假阳性。这说明 §3.3 的问题不只是 decoy 咬钩，而是当前失效裁定整体偏激进，Phase 1 仍须默认保守。

## 完成线

- 详见 `phase05_completion_lines.md`；封板后不再用一个全局阈值覆盖所有形态。
