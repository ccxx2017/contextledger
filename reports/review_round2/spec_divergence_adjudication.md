# 规格分歧裁定表（评审第二轮 §三.1）

裁定依据：**原始事件、用户意图、领域契约（RFC §8/§7.2）、各候选解释的行动后果**。
明确不以"oracle 也这么算"作为依据——oracle 与主链一致只证明实现相互一致。

背景：交叉核对 27 fixtures → 16 一致 / 7 规格分歧 / 4 文档化偏离 / 0 无注记缺口。
（改派 fixture 此前 5 条"分歧"是测量器语义注册表缺条目，属观测局限，已修复转入一致。）

| # | fixture | 分歧内容 | 裁定 | 依据与行动后果 | 处置 |
|---|---|---|---|---|---|
| 1 | `lc_multi_claim_partial` | 期望 `invalidates mc_0001→mc_0001`（**自环失效**） | **gold 错误**（fixture 编写笔误：自失效语义无意义） | 原始事件：partial 更新同一声明；用户意图：旧原子声明被新声明部分取代，失效边应为 新→旧；自环不产生任何合法行动解释 | gold 勘误登记（机制级 fixture，按纪律：先在 development 验证修正再改，附版本注记；不静默改冻结文件） |
| 2 | `lc_same_key_different_source` | 期望两个不同来源的互斥声明**共存**（ready+degraded 均 active）；实现按时间推进 SUPERSEDES | **实现错误**（登记为已知缺陷 #1，deferred） | RFC §8："provenance conflict 不得默认折叠成 full invalidation"。跨源时间推进自动 SUPERSEDES 恰好构成这种折叠——audit_probe 与 ops_team 的可信度不同，后到的 probe 值不该静默取代 ops 值。行动后果：下游据未裁定的 probe 值行动 | 登记已知缺陷 #1：**跨源 + 时间推进的组合仍会误取代**。影响真实案例：任何"审计/探测数据源 vs 业务数据源"并发报告的场景。计划中的 D4 场景事件全部同源 → 不阻塞 pilot；pilot 选案例时不得把此类案例当通过证据 |
| 3 | `lc_diff_source_conflict` | 期望 CONTESTS 后**争议值仍以原值可见**；实现把争议值隔离为 state=None（`_contested_state` 保留） | **规格含糊**（未定义争议值的表示） | 实现选择：未裁定的值不进入 state 维度（否则等于未裁定就接受该值，且触发主链"state 冲突须显式取代"不变量）。行动后果对比：规格版下游可见争议值（可能误用）；实现版下游看到"无已接受值"（保守方向） | 维持实现选择；规格补一句话即可消除含糊（待 RFC 修订时补） |
| 4 | `lc_different_source_true_conflict_contests` | 同 #3（值表示）+ CONTESTS 边方向 | **规格含糊**（同上 + 边方向未定义） | 同 #3；边方向：实现统一为 新→旧（与 invalidates 一致），规格未定义方向 | 同 #3 |
| 5 | `lc_provenance_conflict` | 同 #3 | **规格含糊** | 同 #3 | 同 #3 |
| 6 | `lc_legacy_migration` | 期望 legacy 节点与 lifecycle 节点间 COEXISTS 边（方向 旧→新）；实现边方向 新→旧 | **规格含糊**（COEXISTS 方向未定义；无向关系的方向登记属实现自由度） | 双方都保持 active，状态集合零差异；边仅作文档。行动后果无差别 | 规格修订时定义方向；不阻塞 |
| 7 | `lc_two_lifecycles_no_kill` | 同 #6（跨 lifecycle COEXISTS 方向） | **规格含糊**（同上） | 同 #6 | 同 #6 |

## 4 项文档化偏离的复核（评审 §五）

| fixture | 类 | 复核结论 |
|---|---|---|
| `lc_late_arrival_missing_effective` | deliberate | **规则已细化**（评审 §五要求）：缺 `effective_at` 本身不再导致硬隔离；但语义状态变更若**同时缺 lifecycle_seq 与 effective_at**，仅凭接收顺序（observed_at 推进）不得覆盖关键状态 → 弃权（`test_no_temporal_credential_does_not_overwrite_semantic_change`）。有任一可信凭据（seq=顺序权威 / effective_at=业务时点）则允许推进。该 fixture 的事件带 seq → 按顺序权威推进，属"非无条件覆盖"，符合评审"可以不硬隔离，但不能无条件按接收顺序覆盖" |
| `lc_conditional_different_scope` 等 3 项 | deferred（claim_scope） | 影响面分析见下节 |

## claim_scope deferred 的影响真实案例（评审 §五放行意见）

- **影响的案例形态**：同一 `state_slot` 下存在**多个作用域取值**且需按作用域分别裁定的场景
  （例如"东京区允许、全局禁止"并存；"staging 环境已部署、canary 未部署"并存）。
- **不影响**：整体对象单一状态维度上的取消/改派/恢复（state_slot 已显式化维度，
  这正是本轮把 state_slot 设为一等字段的收益）。
- **对评审首场景的判定**：方案取消（refactor-plan-a → approval_status）、任务改派
  （impl-owner → assignment）、恢复——全部是**整体对象级**状态，claim_scope 不参与裁定，
  **不阻塞 pilot**。
- **前置检查义务**：pilot 选案例时，若出现"只取消某一部分/某作用域"的需求，
  该案例必须标记为 `known_gap: claim_scope`，不得作为通过证据，也不得静默简化成整体取消。

## turn_090 lint 修复期限检查（评审 §五）

当前 `turn_counter=84` < 90，**期限未到**。5E/1W 存量违例仍登记在
`lint_baseline.json`（`escalate_on_or_after_turn: 90`）。到期处理按原契约：
diff_lint_reports 将其升级为 overdue → 阻断提交。不为进入实验而顺延。
