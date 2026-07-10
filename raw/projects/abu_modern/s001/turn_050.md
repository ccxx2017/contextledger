# 用户：
好的，附件(修正数字员工的实施进行中.md)是我们的整体工作的介绍，接下来我们该怎么做？
# GPT5.5:
*Thinking...*

> **Proposing validation steps**
> 
> I could suggest starting with a limited scale validation by using the same Round4 IR for 20 symbols over a 3-year period. This approach would focus on testing the backend and the tool without drawing any research conclusions just yet. If this initial test is successful, then research loops could potentially benefit by using the 20/3 setup to derive better signals. It seems like a structured way to begin!

结论：**下一步不要直接进入完整研究**。  
应该走：

> **先固化工具契约 → 再让 strategy_researcher 做一次受限放大验证 → 再进入真正的单变量研究迭代。**

## 1. 先开一个小补丁工单：固化 Round 4 暴露的问题

建议新建：

`TKT-2026-005F-strategy-researcher-tool-contract-sync.md`

目标不是研究，而是把这次 smoke 中临时发现/修改的东西固化：

- `call_builder.py --endpoint` 不能只停留在 Ubuntu skill 目录的本地修改里，要同步到正式技能资产源。
- `TOOLS.md` 明确写：
  - investigation 必须用 `/strategy-builder/compile-ir`
  - 禁止 `/strategy-builder/invoke`
  - `execution-config` 回测必须传完整 `strategy_ir`，不是只传 `strategy_id`
- `research_workflow.md` 补充新流程：
  - compile-ir → archive_created → call_backtest execution-config → kb_query 读取 KB 口径
- `metrics.py` 要兼容新路径，不能再把 compile-ir + execution-config 的结果误判为 `no_backtest`。
- 明确 400/404 的客户端格式探索错误不等于 Boss guardrail；但 5xx/timeout/connection failure 仍然一票暂停。

这个工单应由**项目AI/工具维护者**做，不由 strategy_researcher 做研究时顺手改。

## 2. 然后恢复 005B，但先做“受限放大验证”

Round 4 已经证明链路能跑通，但样本太小。下一步建议不是立刻改策略，而是先验证工具能否在授权上限内稳定运行：

> 使用 Round 4 同一 IR，不改假设，只把规模放大到 `symbols≤20 / years≤3 / timeout=90s`。

这一步只回答一个问题：

> 工具链在受限上限内是否稳定？

如果通过，才进入真正研究迭代。

如果失败，立即 `paused_for_boss_review`，不要继续试。

## 3. 放大验证通过后，再做真正 Round 5 研究

Round 5 建议只改一个变量，符合 `hypothesis_heuristics.md` 的单变量原则。

我建议优先测试：

> **在 Round 4 放量突破基线之上，加入“前期趋势过滤”。**

例如：

- Round 4 基线：突破 20 日高点 + volume > volume_ma20
- Round 5：在此基础上增加前期趋势条件，例如 `MA20 > MA60` 或 `60日涨幅 > X%`

原因：VCP 形态的核心不是单纯突破，而是**上升趋势中的整理后突破**。Round 4 亏损严重，很可能是没有过滤“无趋势乱突破”。

## 4. 暂时不要做的事

现在不要做：

- 不要跑 231 标的大回测
- 不要把 Round 4 当研究结论
- 不要启动完整 A 股 2018-2024 全样本研究
- 不要急着做多 agent 源码级改造
- 不要跳到部署、实盘、下单相关流程

后端异步化仍然重要，但它是**完整研究放量前的必要条件**，不是当前受限研究的阻塞项。

## 推荐顺序

1. **005F：固化工具契约**
2. **005B：受限放大验证，同 IR，≤20 标的，≤3 年**
3. **005B：Round 5，单变量加入趋势过滤**
4. 若连续 2-3 轮受限研究稳定，再考虑：
   - 扩大样本
   - 后端异步化
   - strategy_researcher v0.3 工作流升级
   - 多 agent 机制改造

一句话：**现在已经从“抢修工具链”进入“受控研究恢复”阶段，但还没到完整研究阶段。**
