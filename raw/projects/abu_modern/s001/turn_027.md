# 用户：
@GPT-5.5 上面是我们工作的总结，请你指出接下来要怎么做？
# GPT5.5:
建议：**现在不要直接派 Ticket B。下一步先做 P1：清理根 bootstrap 里的身份和记忆污染，然后再派首个 strategy-researcher 研究工单。**

## 下一步顺序

```text
P0/P0.1 已完成
→ P1 清理 IDENTITY.md + AGENTS.md
→ 重跑身份/路由烟测
→ 派 Ticket B
→ 根据 Ticket B 真实结果决定是否进入多 agent 机制改造
```

## 1. 先做 P1：改两个根文件

优先改：

### A. `IDENTITY.md`

目标：去掉“小爪/个人助理”身份，改成：

> 当前 agent 是 OpenClaw 数字组织运行时成员。  
> 具体岗位身份由当前激活的 skill / 工单 / 用户指令共同决定。  
> 执行任务时以对应 `SKILL.md` 为最高行为准则。

### B. `AGENTS.md`

目标：关闭污染源：

- 不要启动时主动读取大量 `memory/*`
- 不要检查 email/calendar/weather/Twitter
- 不要把通用记忆维护规则凌驾于 skill 的读写边界之上
- 写文件只能写 `SKILL.md` 或工单允许的路径

`SOUL.md` 可以先不急，除非里面仍强烈强调“连续人格/主动读记忆”。

## 2. 做 P1 烟测

改完后重跑两类测试。

### 烟测 C：身份是否干净

飞书问：

```text
你是谁？当前这条消息是否需要激活某个 skill？如果需要，说明是哪一个；如果不需要，说明原因。
```

合格标准：

- 不再说自己是“小爪”
- 不主动读一堆 memory
- 能说清：具体岗位由 skill / 工单决定

### 烟测 D：Ticket B 前置检查

不要直接让它跑研究，先发：

```text
请只做前置检查，不调用任何 scripts。
请读取 TKT-2026-00X 的工单，并判断是否应该由 strategy_researcher 处理。
请列出你读取的 .md 文件路径。
```

合格标准：

- 读取根路由文件
- 读取 `skills/strategy_researcher/SKILL.md`
- 读取必要 prompts，例如 `research_workflow.md`
- 不读 `quant_assistant/TOOLS.md`
- 不调用 builder/backtest/order/deploy 脚本

## 3. 合格后再派 Ticket B

Ticket B 启动时不要口语化发一句需求，建议这样发：

```text
请执行 aos_repo 中的工单：
aos/tickets/TKT-2026-00X-xxx.md

你是 strategy_researcher。
请严格按照你的 SKILL.md 和 prompts/research_workflow.md 执行。
本次是 investigation 工单。
完成后写入 research-runs、报告和工单 worklog。
```

## 4. 暂时不要做源码级多 agent 改造

正式多 agent、bindings、skills allowlist 是机制级修复，但现在还没必要马上动。

触发条件是：

- Ticket B 中仍读错 skill；
- 仍混用 quant_assistant 工具；
- 仍主动读无关 memory；
- 仍不按 research_workflow 调用工具；
- trace 不可验收。

如果 Ticket B 跑通，再排期做机制层；如果 Ticket B 跑不通，优先根据失败点修 SKILL / bootstrap。  

**一句话：下一步是 P1 清理 `IDENTITY.md` 和 `AGENTS.md`，通过身份/路由烟测后，再派 Ticket B。**

