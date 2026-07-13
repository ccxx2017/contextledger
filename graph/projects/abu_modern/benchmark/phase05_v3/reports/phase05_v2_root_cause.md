# Phase 0.5 v2 Root Cause Analysis

## 范围

- 本文按 `context_ledger_secendary_ajustment.md#L3635-L3682` 的要求，只分析两条轨迹：
  - `tr_prov_run54b`
  - `tr_revival_round5x`
- 对每条轨迹回答 5 个问题：
  - gold 期望
  - 系统实际裁定
  - 偏差点
  - 根因类型（A/B/C）
  - 若为 C 类，对 Q3 的含义

## 总结先行

| trajectory | 根因类型 | 简结论 |
|---|---|---|
| `tr_prov_run54b` | `C` resolver 误分类 | 系统把两个 hash 变体当成两个并存实体；全自动主链直到人工 batch merge 前都没有形成 supersession。 |
| `tr_revival_round5x` | `A` schema gap | benchmark 的 gold 要求“同一 lifecycle 流上的单流裁决”，而当前 schema 实际建模成一组并列子任务 / 结果实体，无法表达 revival / workflow-lineage。 |

## 先回答一个关键问题：有没有 B 类裁决 bug

- 目前**没有证据**表明两条轨迹属于 `B` 类。
- 原因很直接：两条轨迹在 `phase0_current` 与 `flat_rag` 下的实际表现几乎一样，都是：
  - `predicted_invalidations = 0`
  - active set 累积增长
- 这说明错误并不是“已经进入同一实体流，但 reconcile / adjudication 判错了”。
- 偏差发生得更早：要么卡在实体归并，要么 gold 所要求的实体流本身就超出了当前 schema 能表达的范围。

## 轨迹一：tr_prov_run54b

### 1. gold 期望

- `obs01`：`run-54b-...-dfc9611d` 为当前 active
- `obs02`：`run-54b-...-d37c696d` 替代旧 run
- 正确裁定应为：
  - active set 只保留 `obs02`
  - invalidation: `obs02 -> obs01`
  - 两个 mention 属于同一实体流，只是不同版本 / 不同 hash 的 run

### 2. 系统实际裁定

- `phase0_current` 与 `flat_rag` 的结果相同：
  - `predicted_active_set = [obs01, obs02]`
  - `predicted_invalidations = []`
  - `must_include recall = 1.0`
- 也就是说：
  - 系统没有把新 run 判成旧 run 的后继
  - 而是把两个 run 当成并存事实

### 3. 偏差点

- 偏差发生在 **entity resolver / entity keying**，不是 reconcile。
- 直接证据：
  - benchmark 评分明细里，`obs02` 之后系统仍保留两个 active claim，说明两条观测没有进入同一实体流。
  - `pending_merge.turn_070.json` 明确出现了高置信度候选：
    - `raw_entity_ref = run-54b-...-d37c696d`
    - `canonical_entity_ref = run-54b-...-dfc9611d`
    - `match_confidence = 0.9118`
  - 这说明 resolver **知道它们很像**，但在自动链路当下并没有完成可用的同流裁定。

### 4. 根因类型

- 归类为 `C：entity resolver 误分类`

### 5. 为什么是 C，不是 A / B

- 不是 `B`：
  - 因为它根本没有进入“同一实体流上的 adjudication”阶段，自然谈不上 reconcile 判错。
- 优先归为 `C` 而不是 `A`：
  - 当前 schema 至少能表达“后到事实 supersede 先到事实”的 full replace，这在纯 full 子集里已经验证通过。
  - 这里失败的直接原因，是 hash 变体没有在自动链路中被当场收敛成同一流。
- 但它也暴露出一个**次级 schema 压力**：
  - 即使后续 batch merge 发生了，`pending_merge_register` 里也是把新 run 合并进旧 canonical：
    - `resolution_note = Batch MERGE: canonical=run-54b-...-dfc9611d`
  - 这会把“同一 lineage 的新版本”压成“旧实体的 alias”，从表示能力上看并不理想。
  - 这不是本条的主根因，但说明后续 schema 里最好要有 `version/provenance lineage` 的一等表示。

### 6. 对 Q3 的含义

- 这条轨迹**直接覆盖了 Q3 的一部分**。
- 它表明：
  - resolver 对 hash 变体并不是过于保守，而是**高置信地想合并**
  - 真问题在于“合并之后怎么表达”以及“何时自动生效”
- 换句话说，Q3 不再只是“该不该 merge”，而变成：
  - 对版本化实体，merge 是否会错误抹平 successor 语义
  - `alias merge` 和 `version succession` 不能继续混用

## 轨迹二：tr_revival_round5x

### 1. gold 期望

- gold 把以下 5 条 observation 当作**同一条 round_state 流**：
  - `TKT-2026-005B_round5`
  - `TKT-2026-005B_round5.3A_audit`
  - `TKT-2026-005B_round5.3B_fix`
  - `TKT-2026-005B_round5.3C_verify`
  - `TKT-2026-005B_round5.3C_reverify`
- 它要求每一步都只保留最新当前态：
  - `obs02` invalidates `obs01`
  - `obs03` invalidates `obs02`
  - `obs04` invalidates `obs03`
  - `obs05` invalidates `obs04`
- 本质上，gold 期待的是：
  - 一个跨 audit / fix / verify / reverify 的单流 lifecycle
  - 其中 later stage 会替代 earlier stage

### 2. 系统实际裁定

- `phase0_current` 与 `flat_rag` 同样表现一致：
  - `predicted_invalidations = []`
  - active set 从 1 个逐步涨到 5 个
  - `entity_resolution.false_split_rate = 1.0`
- 也就是说：
  - 系统把这些 observation 全部当成不同实体
  - 没有形成 gold 所要求的“单流替代链”

### 3. 偏差点

- 偏差不是单点 bug，而是 **schema 表达模型与 gold 目标不一致**。
- 直接证据有两层：
  - benchmark 评分层：
    - 所有 observation 都被独立保留，说明系统没有“同一 lifecycle 流”的表达
  - 主图数据层：
    - `graph_state.turn_084.json` 中，这些实体本来就被建模为一组不同的 entity_ref：
      - `TKT-2026-005B_round5.3A_audit`
      - `TKT-2026-005B_round5.3B_fix`
      - `TKT-2026-005B_round5.3C_verify`
      - `TKT-2026-005B_round5.3C_reverify`
      - `TKT-2026-005B_round5.3D_reconcile`
    - 它们是并列子任务 / 子结果，而不是同一实体的多次版本更新
- `pending_merge` 虽然多次对这些 entity_ref 给出候选，但候选 canonical 本身也在来回漂移：
  - 有时指向 `round5.2_audit`
  - 有时指向 `round5_result`
  - 有时指向 `round5.3C_verify`
- 这进一步说明：问题不是“明明 schema 足够却判错”，而是系统缺少一个稳定的一等概念去表示这条 lifecycle。

### 4. 根因类型

- 归类为 `A：schema gap`

### 5. 为什么是 A，不是 C / B

- 不是 `B`：
  - 一样没有进入稳定的同流 adjudication 阶段。
- 不把它主归因为 `C`：
  - resolver 的确也有碎片化问题，但更深层的问题是：
    - 当前 schema 把 `audit / fix / verify / reverify` 这些内容天然建成不同实体
    - benchmark gold 要求的却是“同一 round_state 流上的状态推进 / revival”
  - 也就是说，即使 resolver 更激进一些，当前 schema 仍缺少明确的 lifecycle / revival 表达位。
- 这条轨迹最接近原文中的预判：
  - `revival` 在当前二值 schema 下无法被一等表达
  - 现在看到的证据支持这个判断

### 6. 对 Q2 的含义

- 这条轨迹**直接补强了 Q2**：
  - `revival / workflow-lineage` 是真实缺口，不是抽象推测
  - gap 不只是“缺一个 revival label”
  - 更准确地说，缺的是：
    - 同一 lifecycle 流的稳定聚类
    - 子阶段与主阶段之间的 lineage 表达
    - revival / reverify 这类“回到同一审议流继续推进”的语义位

## 最终判定

| trajectory | gold 期望 | 系统实际 | 偏差点 | 根因类型 |
|---|---|---|---|---|
| `tr_prov_run54b` | 新 run 取代旧 run | 两个 run 并存，无 invalidation | entity resolver / pending_merge 未在自动链路中收敛同流 | `C` |
| `tr_revival_round5x` | 单一 round_state 流逐步替代 | audit/fix/verify/reverify 全部并存 | schema 只会建模成并列子实体，缺 lifecycle/revival 一等概念 | `A` |

## 对后续顺序的影响

- `Q2（缺陷补到哪算够）`：
  - 已被这次分析明显推进。
  - 至少有一个真实缺口已被确认：`revival / lifecycle lineage`
- `Q3（合并保守对不对）`：
  - 已被 `tr_prov_run54b` 部分触达。
  - 当前不是单纯“保守 or 激进”问题，而是 merge 后缺少 successor/provenance 表达。
- `Q1（Flat RAG 基线）`：
  - 仍然**必须补**
  - 因为本报告只回答“为什么失败”，并不回答“ContextLedger 相比 Flat RAG 到底值不值得继续做”

## 建议动作

1. 不进入大规模 schema 扩张。
2. 先把 `tr_prov_run54b` 记为 `C` 类根因样本，纳入 Q3 交叉验证材料。
3. 把 `tr_revival_round5x` 记为 `A` 类真实缺口，纳入 schema gap register。
4. 下一步仍应补 `Flat RAG baseline`，因为这是唯一无法被根因分析替代的问题。
