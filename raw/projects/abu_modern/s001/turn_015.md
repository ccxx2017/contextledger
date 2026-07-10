# 用户：
我现在已经把上述Ticket A的部分完成了。@Claude-Opus-4.7 我如何开始Ticket B呢？我能否使用“前面有趋势，经过一轮调整，结构紧凑，然后有放量拉升的那个点进去”，这是一个真实的用户需求
# Claude Opus4.7:
*Thinking...*

>  The user is starting Ticket B with a specific technical analysis pattern from real trading requirements — they're describing a consolidation breakout setup where price trends, consolidates in a tight range, then breaks out on volume. This is a classic chart pattern similar to cup-and-handle or flag formations that traders use as entry signals.
> 
> I'm mapping this into a state machine with distinct phases: trend detection, consolidation identification, breakout confirmation, and entry execution. This structure fits naturally into the investigation framework they're building, and I should help them draft the ticket with proper fields and concrete next steps to get started.

## Ticket B 启动：完全可以用这个需求

你这个描述是**非常好的投研工单素材**，理由：

1. **有机制**——趋势 + 缩量调整 + 放量突破，是 Minervini / O'Neil 体系里经典的 VCP（Volatility Contraction Pattern）/ 平台突破形态，不是拍脑袋
2. **可证伪**——能用 phases + transitions 精确表达，回测能给出明确的成败数字
3. **单一 intent**——`breakout` / `trend_continuation` 类，范围收敛
4. **假设空间丰富**——"前面"多长？"紧凑"多紧？"放量"多大？每个参数都是一轮独立实验的种子

这恰好是 strategy-researcher 的甜蜜点。

---

## 但工单不能直接用这句话——要做一次翻译

原话"那个点进去"是口语化的，需要翻译成**可被智能体消费、但不过度指定解**的工单。核心原则：

- **目标描述**用自然语言保留用户原意（让研究员理解"形态长啥样"）
- **约束**明确给死（universe、时间窗、禁用手法、成功标准）
- **不预先指定参数**（否则研究员退化为"参数网格跑腿员"，浪费其判断力）

---

## Ticket B 草稿（你复制微调即可）

文件路径：`${AOS_ROOT}/runtime/tickets/open/TKT-2026-00X-vcp-breakout-entry.md`

```markdown
---
ticket_id: TKT-2026-00X
title: VCP 形态突破点入场策略研究
intent_type: investigation
assigned_to: agent-strategy-researcher
status: open
priority: normal
created_by: Boss
created_at: 2026-05-08
tags: [breakout, trend_continuation, volume, consolidation, vcp]
---

## 研究目标

验证并落地如下形态的交易策略：

> 标的此前处于明确上升趋势 → 经历一轮时间和幅度有限的回调 →
> 回调末期价格结构趋于紧凑（波动收敛、换手萎缩）→
> 在某一日出现明显放量拉升并突破前期整理区间高点 →
> 以突破日或次日开盘作为买入点。

回答以下问题：
1. 该形态在 A 股市场是否存在可观测、可量化的统计优势？
2. "趋势""调整""紧凑""放量""突破"五要素中，哪一条对收益贡献最大？
   哪一条可以放宽甚至去掉而不伤害 sharpe？
3. 该策略的失效模式是什么（指数级熊市？题材股泡沫破裂？小市值流动性枯竭？）
4. 相对 KB 中现有 `breakout` / `trend_following` 档案的最佳 sharpe，能否提升？

## 约束

- **Universe**：沪深 A 股，剔除 ST / *ST / 上市不足 250 交易日的新股；
  日均成交额中位数 > 5000 万（过滤流动性太差的标的）
- **时间窗**：2018-01-01 ~ 2024-12-31，train/test 按 70/30 时间切分
  （不要随机切分，形态策略对时序敏感）
- **持仓约束**：多头 only；单笔仓位 ≤ 10%；同时持仓 ≤ 10 只
- **成本假设**：双边 0.0012（含佣金+印花税+滑点），按你们 backtest 默认即可
- **禁用**：未来函数、日内高频、杠杆、衍生品
- **主指标**：sharpe_ratio（样本外）；辅助关注 calmar、最大回撤、胜率、盈亏比

## 研究员的裁量空间（明确授权）

以下你自己决定，不需要问我：
- "前期趋势"的定义（多少日？MA 斜率？涨幅阈值？）
- "调整"的刻画（时间窗口？最大回撤百分比？）
- "紧凑"如何量化（ATR 收敛？布林带宽？真实波幅比？）
- "放量"的倍数（vs MA5 / MA20？几倍？）
- "突破"参照哪条线（整理区间 high？前高？某条 MA？）
- 出场规则（固定止盈？追踪止损？时间止损？MA 破位？）

建议第 1 轮用**最简定义**先跑出基线，后续轮次逐一放宽 / 收紧单个要素，
符合 `hypothesis_heuristics.md` 的"单一变量"原则。

## 成功标准

触发以下任一即视为工单完成：
- 找到一个样本外 sharpe > 1.2、最大回撤 < 25% 的参数组合，且机制解释清晰
- 或，证明该形态在 A 股**不成立**（样本外 sharpe ≤ 0.5 且跨多轮假设无法改善），
  附失效原因分析——**负向结论同样有价值，不要凑数**

## 交付要求

按 `prompts/report_template.md` 标准交付，报告命名：
`TKT-2026-00X-vcp-breakout-entry.md`

## Worklog

（留空，由 agent 追加）
```

---

## 启动步骤（按顺序走）

1. **决定 ticket_id**。看一下 `${TICKETS_DIR}/` 现有编号，取下一个顺位（比如 008 / 009）
2. **决定 intent_type 是否已定义**。如果你们 ticket schema 里还没有 `investigation` 这个值，先补一下（或临时用最接近的）
3. **落地工单文件**到 `${AOS_ROOT}/runtime/tickets/open/TKT-2026-00X-vcp-breakout-entry.md`
4. **commit + push**：
   ```
   git add aos/runtime/tickets/open/TKT-2026-00X-*.md
   git commit -m "ticket(research): TKT-2026-00X VCP 形态突破点入场研究"
   git push
   ```
5. **Ubuntu 侧拉取**：确认 openclaw 环境能看到这张新工单
6. **派单**：按你们现有的 openclaw 派单机制（飞书 @ / CLI 指令 / 看板操作），把这张工单派给 `agent-strategy-researcher`
7. **旁观**：不要中途插手，让它按 `research_workflow.md` 自己跑。它会：
   - Phase 0-2：同步 repo、校验工单、读 KB 找现有 breakout 档案
   - Phase 3：开始 round_1 ~ round_N 的假设循环
   - Phase 4-6：聚合、写报告、追加 worklog、提交
8. **它跑完你再看**：报告在 `${REPORT_DIR}/TKT-2026-00X-vcp-breakout-entry.md`；中间过程在 `${RESEARCH_RUNS}/TKT-2026-00X/`

---

## 关于研究员可能遇到的坑（给你心理准备）

这三件事很可能在 Trial 1 暴露，**都不是 Ticket A 的 bug，而是真实需求反馈**：

1. **KB 写入桥缺失**（前面提到过的假设）——研究员跑完一轮 builder 成功，但 `kb_query archives` 看不到新档案 → 需要单开一张后端 ticket 补桥
2. **Universe 预筛选能力不足**——"日均成交额中位数 > 5000 万"这种过滤如果 builder 不支持，研究员会降级处理（比如改用全市场），worklog 里会标记出来
3. **形态类策略的 IR 表达力**——VCP 需要"过去 N 日 ATR 的滑动比较"这种多阶段状态保持，如果 IR 的 phase/transition 表达力不够，研究员会在 round_1 就报告"假设无法完整翻译"。这是**比跑完 5 轮都失败更有价值的早期信号**。

这三种反馈中任意一种，都意味着 Trial 1 达成了"暴露真实缺口"的核心目的，**不要把它们当成失败**。

---

**一个小建议**：Ticket B 派出去后，你顺手开一个 Ticket B'（观察工单，不用派给任何 agent，就是你自己的 checklist）记录下这次 trial 里你观察到的所有异常——这会是后面 SKILL.md v0.3.0 最好的需求来源。

