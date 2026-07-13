# Phase 0.5 v2 Flat RAG Baseline Definition

## 目的

- 本文只做一件事：在运行 `Q1 / Flat RAG baseline` 之前，先把 baseline 的形态与评分口径钉死。
- 本文是“跑分定义”，不是跑分结果。
- 在本文确认前，不执行 `phase05_v2_vs_flat_rag` 正式对比。

## 为什么必须先定义

- `Phase 0.5` 的核心指标不是普通检索命中率，而是：
  - `active-set Set-F1`
  - `must_include recall`
  - `invalidation P/R`
- Flat RAG 天然没有“当前态 / superseded / revival”概念。
- 如果不先定义 Flat RAG 怎样产出 active set、怎样解释 invalidation 指标，跑出来的分数没有判读意义。

## 当前实现现状

- 当前 `graph/scripts/score_phase05.py` 已有一个名为 `flat_rag` 的基线。
- 它的实际行为是：
  - 按 observation 首个 mention 的 `normalize_exact()` 结果做 entity key
  - 对每个 exact entity 只保留最后一次 observation
  - 不产出任何 invalidation 事件
- 因此，当前实现本质上对应：
  - `D2: exact-surface last-write-wins`
- 它**不是**“全量历史 dump”，也**不是**通用检索式 Top-K。

## 本次建议的 Flat RAG 定义

- 建议不要只跑一个 Flat RAG，而是固定跑两个：
  - `D1: full_history_dump`
  - `D2: exact_surface_last_write_wins`
- 原因：
  - `D1` 回答“全量保留的 recall 上限是什么”
  - `D2` 回答“朴素去重后的 precision / compactness 上限是什么”
- 不采用 `D3: Top-K retrieval`
  - 当前 benchmark 没有 query 变量
  - Top-K 在这个任务里没有稳定、可复现、可对比的定义

## 两个 baseline 的正式定义

### D1: full_history_dump

- 输入：截至当前 step 为止出现过的全部 observations
- active set 产出方式：
  - `predicted_active_set = 所有历史 observation 的 claim_id 并集`
- must_include 产出方式：
  - `predicted_must_include = 所有历史 observation 中 importance=critical 的 claim_id 并集`
- invalidation：
  - 永远为空集
- valid-time：
  - 不做单独推断
  - 若评分器要求输出 winner，则按“同 exact entity 的最后一次出现”做只读回填，但这不改变其无失效语义

### D2: exact_surface_last_write_wins

- 输入：截至当前 step 为止出现过的全部 observations
- entity key：
  - `normalize_exact(observation.mentions[0])`
- active set 产出方式：
  - 对每个 exact entity，仅保留最后一次 observation 的 claim_id 并集
- must_include 产出方式：
  - 对每个 exact entity，仅保留最后一次 observation 中 importance=critical 的 claim_id 并集
- invalidation：
  - 永远为空集
- valid-time：
  - 若评分器要求输出 winner，则复用“同 exact entity 的最后一次 observation”为 winner

## 指标定义与解释口径

### 1. active-set Set-F1

- `D1` 与 `D2` 都正常参与计算。
- 解释方式：
  - `D1` 更像 recall 上限参考
  - `D2` 更像朴素去重参考

### 2. must_include recall

- `D1` 与 `D2` 都正常参与计算。
- 这是 `Q1` 的关键指标。
- 判读规则建议固定为：
  - `ContextLedger.must_include_recall` 不应低于 `D1.full_history_dump`
  - 如果低于 `D1`，必须单独标红，因为这表示系统在“主动收敛”时静默丢失了关键约束
- 换句话说：
  - `D1` 不是强基线，但它是一个不能轻易输掉的 recall 下界检查

### 3. invalidation P/R

- Flat RAG 不产生 invalidation 事件，因此它**没有语义上的 invalidation 能力**。
- 这本身就是 `Q1` 的核心差异化判据：
  - `ContextLedger` 已经有显式 invalidation recall（当前 `0.474`）
  - `Flat RAG` 无论是 `D1` 还是 `D2`，都只是靠“全量保留”或“最后覆盖”回避失效问题，本质上没有 supersession 裁决能力
- 为了兼容现有评分器，定义分成两层：

- 语义展示层：
  - `D1.invalidiation P/R = N/A`
  - `D2.invalidiation P/R = N/A`
  - 在对外报告里明确写成“baseline 不产出 invalidation，不参与能力优劣比较”

- 评分兼容层：
  - 仍允许评分器接收 `predicted_invalidations = []`
  - 若某 category 存在 gold invalidation，则数值上会落成：
    - `precision = 0.0`
    - `recall = 0.0`
  - 若某 category 没有 gold invalidation，则：
    - `precision = 1.0`
    - `recall = N/A`
- 这些数值只用于让脚本完整产出 JSON，不作为 `Q1` 的核心判据。

### 4. valid-time adjudication

- Flat RAG 不具备真实 valid-time reasoning。
- 当前 benchmark 如需继续保留此项，对 Flat RAG 的解释口径应为：
  - `observed_at 在场`：只做 exact entity 的最后出现回填，不宣称具备时序裁决能力
  - 该项只作为“无能力基线写实”，不作为决定是否继续做 ContextLedger 的核心判据

## Q1 的正式判读框架

- `Q1` 不问“ContextLedger 是否在所有数字上都高于 Flat RAG”
- `Q1` 真正问的是：
  - 它是否在“保留关键约束”上至少不比 naive dump 更差
  - 它是否在“从历史中收敛出当前态”上比朴素 last-write-wins 更有信息价值

### 推荐主判据

1. `must_include recall`：
   - `ContextLedger >= D1`
   - 若不满足，直接记为高风险警示
2. `active-set Set-F1`：
   - `ContextLedger >= D2`
   - 若不满足，说明收敛出来的“当前态”并不比朴素去重更可信
3. `invalidation P/R`：
   - 只作为“ContextLedger 特有能力是否已开始形成分离”的辅助判据
   - 不拿 Flat RAG 的 `0/0` 或 `N/A` 去做简单数值胜负

## 本次建议的输出物

- 在本文获确认后，下一步应生成：
  - `phase05_v2_vs_flat_rag.md`
- 其中必须并排展示三条线：
  - `phase0_current`
  - `flat_rag_d1_full_history_dump`
  - `flat_rag_d2_exact_surface_lww`

## 建议执行顺序

1. 确认本文定义
2. 给评分脚本补两个显式 baseline 名称：
   - `flat_rag_d1`
   - `flat_rag_d2`
3. 运行 `phase05_v2` 三线对比
4. 产出 `phase05_v2_vs_flat_rag.md`
5. 再回到 `Q1` 做最终判读

## 本文结论

- 建议正式采纳：
  - `D1 + D2 双 baseline`
  - `invalidation 对 Flat RAG 按语义层记作 N/A，按评分兼容层保留空预测`
  - `must_include recall` 作为 `Q1` 的首要判据
- 在此定义获确认前，不应直接拿当前脚本里的单一 `flat_rag` 结果回答 `Q1`。
