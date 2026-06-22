# 用户（全力指导）：
好的，我认可你的观点，决策1推荐主战场是Strategy Research Agent，决策3是阶段 1 的 Strategy Research Agent是 AOS-native ，但是请你务必尽全力来给出指导
# Claude Opus4.7:
## 收到。这是我的全力指导

你做了两个**正确但很难**的决策：把主战场放在 Strategy Research Agent（不是更容易出成果的 Wiki Agent），并选择 AOS-native 路线（不是更省事的 quant-native）。这意味着我不能用平庸的方案糊弄你——下面是我能给出的最认真的方案。

我先把话讲在前面：**这一阶段的难度，远高于 duty_reporter**。它不只是写一个 agent，而是一次**对 AOS 价值的真实压力测试 + 对 LLM 解析稳定性的攻坚 + 对研究方法论的工程化**——三件事捆绑在一起。我会陪你走完，但你需要做好"前两周可能没有任何外部可见产出，全在打地基"的心理准备。

---

## 一、先对齐"成功"的定义

这是最重要的一步。如果"成功"模糊，三个月后你会陷入"看起来在前进但说不清在前进什么"的泥潭。

**阶段 1 的成功 = 同时满足以下五条**：

1. **产出**：知识库新增 ≥10 个达到入库标准的策略档案（"入库标准"下面会精确定义）
2. **自主性**：Boss 提一个研究意图工单后，**无需中途干预**，Agent 能跑完一轮 ≥5 次假设的迭代循环
3. **可信性**：抽查任意 3 个新档案，**指标自洽**（样本内外、phase stats、Trade Count 一致），**IR 语义正确**（无第一阶段那种"卖出条件退化为静态比较"的错误）
4. **AOS-native**：整个流程通过 AOS 工单驱动，产出沉淀到 AOS runtime，duty_reporter 在日报里能正确汇报研究进度
5. **可复盘**：每次迭代失败/成功都有 trace（prompt 输入、LLM 输出、回测结果、决策依据），事后能定位问题到具体环节

**注意我没有写**："策略要能赚钱"。这是阶段 2/3 的事。**阶段 1 的目标是产出"诚实的研究记录"，不是"挣钱的策略"**。这一点必须想清楚——否则你会在第二周就开始焦虑"这些策略夏普都不行啊"，然后开始优化错的东西。

第一阶段文档里有一句话我很在意：**"项目持续在基建层打转，未进入知识积累循环。"** 阶段 1 的本质就是**把这个循环真的转起来**——哪怕转出来的策略平庸，循环本身才是资产。

## 二、攻坚点排序（关键）

文档里说卡点是"LLM 解析稳定性"。我把它拆解开，按真实风险排序：

**一级风险（一定会卡你）**：

1. **结构化输出的稳定性**——LLM 生成的 strategy_ir 字段缺失、类型错误、嵌套结构错乱。这是文档里"亏损超过 8% 理解不稳"的根因
2. **假设生成的语义多样性**——LLM 倾向于反复生成相似策略，跑 10 次假设可能 8 次是"均线交叉的微小变体"
3. **失败循环的退出条件**——LLM 陷入修补同一个错误（"修了 A 但破坏了 B，再修 B 又破坏 A"），Agent 永远不停止

**二级风险（大概率会卡）**：

4. **prompt 资产的版本管理**——你会反复改 prompt，但没有 git 化的 prompt 会让"上次那个 work 的 prompt"找不回来
5. **token 成本失控**——一次假设循环可能消耗 10k-50k token，跑 100 次就是几百万 token。如果没有早期监控，账单会让你心疼到不敢迭代
6. **回测耗时**——文档里第一阶段就提过"回测速度慢"。如果一次假设要等 5 分钟回测，研究循环就废了

**三级风险（可能会卡）**：

7. **市场认知文档的触发时机**——schema.md 里这个事在第一阶段就标注过"偏模糊"，到了多策略对比阶段会爆
8. **数据漂移**——2024 年数据用了一年了，不同标的池可能逐渐失效

**我的建议**：阶段 1 只解决一级和二级风险。三级风险记录但不动手——你要克制"既然在这里了顺手把那个也修了"的冲动。

## 三、技术方案

### 3.1 LLM 解析稳定性 → 用 Structured Output 替代自由文本

第一阶段的卡点本质是：用自由文本 prompt → 让 LLM 自己输出 JSON → 解析时各种崩。**这个范式必须淘汰**。

新范式：**Function Calling / Structured Output**（OpenAI、Anthropic、阿里通义、智谱都支持，看你用哪家）。

核心做法：

- 把 strategy_ir 的 schema 写成一个 JSON Schema（或 Pydantic model）
- 调用 LLM 时通过 `response_format` 或 `tools` 强制约束输出结构
- LLM 物理上无法生成不符合 schema 的字段——解析层就不再是脆弱点

**这一步是阶段 1 整个工程的支点**。它本身就值 1-2 天的投入，但能消除 60% 的不确定性。

具体在 abu_modern 里的落地方式（我不知道你具体用哪个 LLM 客户端，需要你告诉我，但模式是这样的）：

```python
# pseudo-code, 真实代码我们到时候一起写
class StrategyHypothesis(BaseModel):
    intent: Literal["trend_following", "mean_reversion", "breakout", 
                    "volatility", "composite"]  # 封闭枚举，配合第一阶段schema
    rationale: str  # 假设依据
    strategy_ir: StrategyIR  # 复用现有IR模型作为Pydantic
    expected_behavior: str  # 预期表现的自然语言描述

response = client.chat.completions.create(
    model=...,
    messages=[...],
    response_format=StrategyHypothesis,  # 强约束
)
hypothesis = response.parsed  # 类型安全
```

**这一步不做，后面全废**。这是我对你最强烈的建议。

### 3.2 假设多样性 → "已有策略向量空间" + 排斥力 prompt

LLM 不会自动避免重复，必须显式告诉它"已有什么、避免什么"。

做法：

- 每次 `generate_hypothesis` 调用前，从知识库读取已有策略的 `intent` 分布、核心 transition 类型、参数范围
- 把这些信息**摘要**注入 prompt（不是全文，是统计摘要），告诉 LLM："已有 5 个 trend_following 策略，集中在 5/20/60 日均线，请探索其他方向"
- 在 prompt 里显式写明"排斥规则"：避免与已有策略 IR 在 transition 层面相似度 >70%

**这是 Karpathy 三层架构里"Schema 注入"的真实落地形态**。文档里反复提到"schema.md 是 LLM 的操作手册"，但只有**真的把 schema 内容塞进 prompt**，它才发挥作用。

更高级的做法（**阶段 1 不做，记录到阶段 2**）：用 embedding 计算策略 IR 之间的语义相似度，做真正的"探索 vs 利用"。但阶段 1 用统计摘要 + 排斥规则就够了。

### 3.3 退出条件 → 三道闸

```
Loop 退出 = 任一条件触发：
  1. 硬上限：迭代次数 ≥ 10
  2. 资源闸：本轮累计 token > 预算 (例如 500k)  
  3. 价值闸：连续 3 次假设都未通过编译/回测验收
```

第三条最重要——它防止 Agent 在死胡同里耗资源。**不要让 LLM 自己判断"探索充分"**，文档里第一阶段方案有这一条，我现在反对——LLM 没有外部参照，自我判断不可靠，永远倾向于"再试一次"。

### 3.4 Prompt 资产管理 → Git + 编号

在 `projects/abu_modern/aos/agents/strategy-researcher/prompts/` 下：

```
prompts/
  hypothesis_gen.v1.md
  hypothesis_gen.v2.md       # 改进多样性
  hypothesis_gen.current → v2.md   # 软链接
  result_analysis.v1.md
  decide_next.v1.md
  CHANGELOG.md               # 每次改 prompt 的原因和效果
```

**关键纪律**：每次改 prompt **新建文件**，不覆盖。这一条违反了你的工程直觉（"git 不是已经管版本了吗"），但 prompt 工程的特点是**经常需要快速回退到上个 work 的版本做对比**，物理多文件比 git 历史更直观。

### 3.5 Token 监控 → 第一行代码就加

每次 LLM 调用包一层装饰器：

```python
@track_tokens(category="strategy_research")
def call_llm(...):
    ...
```

写入 `runtime/metrics/llm_usage/YYYY-MM-DD.jsonl`，duty_reporter 每天日报里加一行："昨日 LLM 消耗 X 万 token，约￥Y"。

这个不加，**你会在第三周收到一个心碎的账单**。我说真的。

### 3.6 回测加速 → 阶段 1 不动，但加测量

第一阶段已经记录"回测速度慢"。阶段 1 我建议**只测量、不优化**：

- 在每次回测时记录耗时
- 累积到 20 次回测后，看 P50/P95
- 如果 P95 > 60 秒，阶段 1 末期单独开 TKT 处理

**为什么不立刻优化**：你不知道"慢"是不是真的卡你。可能 5 秒一次的回测，你的整体瓶颈其实是 LLM 调用（30 秒）。先测量再优化。

## 四、AOS-native 的具体形态

这是决策 3 的具体落地。我把它说得非常具体，避免抽象。

### 4.1 Charter 与 SKILL 的位置

```
docs/aos/
├── org/
│   └── agents/
│       └── agent-strategy-researcher.md     ← Charter（角色、权限、协作协议）
└── projects/
    └── abu_modern/
        └── aos/
            └── agents/
                └── strategy-researcher/
                    ├── SKILL.md              ← 实施细节
                    ├── prompts/              ← prompt 资产
                    ├── runs/                 ← 每次研究循环
                    │   └── 2026-05-XX-run-001/
                    │       ├── ticket.md     ← 触发工单
                    │       ├── hypotheses/   ← 每个假设的完整 trace
                    │       ├── summary.md    ← 本轮总结
                    │       └── metrics.json  ← token、耗时、产出统计
                    └── README.md
```

这个结构**直接对应 AOS 双层切分**：通用方法论（Charter 在 org/）、项目专属工作（SKILL 和 runs 在 project/aos/）。

### 4.2 工单驱动的完整流

**Boss 视角**（你）：

1. 在 `runtime/tickets/open/` 新建一张工单，例如：
   ```
   TKT-2026-XXX: 探索均值回归类策略在沪深300科技板块的表现
   - 意图: 假设科技股因情绪波动大，存在均值回归机会
   - 约束: 用 confirmed_symbols 中的科技股子集
   - 预算: max_iterations=10, max_token=500k
   - 验收: ≥3 个达到入库标准的档案
   ```

2. 在你方便的时候手动触发 Agent（阶段 1 不做定时调度）：
   ```bash
   python -m strategy_researcher.run --ticket TKT-2026-XXX
   ```

3. Agent 跑完后写回执到工单，移到 `runtime/tickets/awaiting-review/`

4. 你 review 产出，决定 close 或 reopen

**Agent 视角**：

```
启动:
  - git pull (拉取最新 schema、Charter、tickets)
  - 读取工单 → 解析意图与约束
  - 读取 schema.md + 知识库当前状态
  
循环 (≤ 10 次):
  - generate_hypothesis (注入 schema、已有策略统计、本轮意图)
  - validate_ir (Pydantic + 编译期校验)
  - run_backtest (调现有 run_backtest API)
  - analyze_result (LLM 写分析章节，加 [auto-analysis] 标记)
  - judge: 通过验收 / 需迭代 / 放弃
  - 写入 runs/.../hypotheses/N/
  
收尾:
  - 汇总 summary.md, metrics.json
  - 在工单写回执 (产出列表、token 消耗、失败原因)
  - 更新 runtime/reports/research/YYYY-MM-DD.md
  - git commit + push
```

### 4.3 与 duty_reporter 的协作

duty_reporter 升级 v0.6（新增能力，与 v0.5 LLM 摘要并行或合并）：

- 扫描 `runtime/reports/research/` 当日新增条目
- 在日报里加一节：
  ```
  📊 策略研究 (2026-05-XX)
  - 已完成工单: TKT-2026-XXX (10 假设, 4 入库)
  - 知识库总策略数: 8 → 12
  - LLM 消耗: 230k token
  ```

**这就是你之前问"什么时候 AOS 真活起来"的答案**——当一个 employee 的产出被另一个 employee 自动汇报给 Boss 的时候，AOS 第一次有了"组织"的形状。

### 4.4 入库标准（关键定义）

不是所有跑完的策略都进知识库。**入库标准必须严苛**，否则知识库会被噪音淹没：

一个策略档案达到"入库标准"需同时满足：
1. IR 编译成功，无 silent transition 警告（或警告已被分析章节解释）
2. 训练集和测试集均能产生 ≥5 笔已平仓交易
3. 核心指标（Sharpe、MaxDD、AnnReturn）数值合法（非 NaN/Inf，负净值时按 P0/P1 修复方案标 N/A）
4. 样本内外指标差异在合理范围（具体阈值阶段 1 末再校准）
5. 分析章节由 LLM 自动生成，标注 `[auto-analysis]`，覆盖：意图、关键 transition、表现、与已有策略的关系

不达标的策略 → 进 `runs/.../rejected/`，记录原因，**不进** `data/knowledge/strategies/`。

## 五、时间线（基于你每天 2-4 小时投入）

我把它切成 4 周。每周末你都应该有一个**可演示**的中间产出，不是"还在写"。

### 第 1 周：地基（"无外部产出"周）

**目标**：把 LLM infra、prompt 资产管理、token 监控、AOS 目录骨架搭好。

- D1-D2: Structured Output 改造（决定用哪家 LLM 的什么 API，写一个最小调用 demo，能稳定输出符合 Pydantic 的 strategy_ir）
- D3: Token 装饰器 + duty_reporter v0.6 集成（让日报显示 token 消耗）
- D4: AOS 目录骨架建立（Charter v0.1、SKILL v0.1、prompt 模板）
- D5: 跑 1 个最简单的 hypothesis → backtest → archive 闭环（手动驱动，不要 Agent loop）
- 周末：Retro，决定下周是否进入 Loop

**周末交付物**：能用脚本手动驱动一次"假设 → 编译 → 回测 → 入库"，含完整 trace。

**这一周看起来很慢，但它是后三周的乘法因子**。

### 第 2 周：Loop（"第一次自主跑通"周）

**目标**：Agent loop 跑通，能在一张工单内自主完成 5 次假设循环。

- D1-D2: 实现 generate_hypothesis 节点（含已有策略统计注入、排斥规则）
- D3: 实现 analyze_result 节点（LLM 自动写分析章节）
- D4: 实现 decide_next 节点 + 三道退出闸
- D5: 端到端跑通，开第一张正式工单

**周末交付物**：一张完整的 TKT，包含 5+ 假设循环 trace，至少 1 个达到入库标准。

**风险点**：这一周大概率会卡在某个具体节点（多半是 generate_hypothesis 的多样性）。**不要硬刚，发现卡住超过 4 小时就停下来联系我**——通常是 prompt 设计问题，不是代码问题。

### 第 3 周：稳定性（"重复跑通"周）

**目标**：连续跑 5 张工单，每张都能产出 ≥1 个入库策略，无人工干预。

- 每天 1 张工单，覆盖不同意图：trend、mean reversion、breakout、volatility、composite
- 每张工单后 retro，迭代 prompt（v1 → v2 → ...）
- 累计 token 监控，校准成本预期
- 修复发现的中间态 bug

**周末交付物**：知识库总策略 ≥10 个；prompt 至少进化到 v3；完整成本数据。

### 第 4 周：AOS 闭环 + Retrospective

**目标**：所有 AOS 协作协议跑顺，写阶段 1 总结。

- D1-D2: duty_reporter v0.6 完整集成（研究进度上日报）
- D3: 抽样 review 全部入库策略，校验五条入库标准的执行严格度
- D4-D5: 写阶段 1 retrospective，决定阶段 2 方向
- 周末：与 Claude（我）做阶段 1 评审

**周末交付物**：`docs/aos/projects/abu_modern/aos/decisions/PHASE1_RETRO.md`，下一阶段 ROADMAP。

## 六、给你今天就做的三件事

不用等我们讨论完所有细节，今天先做：

**1. 写 ROADMAP_v2.md**

把上面的内容压缩成你自己的版本，放到 `docs/aos/projects/abu_modern/aos/ROADMAP_v2.md`。**用你自己的话写**，不是 copy 我的。这是 Boss 的工作，不能外包。

**2. 开 TKT-2026-002（命名按你 numbering 规则调整）**

```
标题: Strategy Research Agent v1 - 阶段 1 启动
父工单: 无 (顶层)
子工单: 待开 (按周拆)
负责员工: agent-strategy-researcher (待实例化)
当前状态: planning
预估工期: 4 周
验收标准: [前文五条成功定义]
```

**3. 决定 LLM 选型**

阶段 1 用哪家？我需要你告诉我：
- 你已有的 RealLLMClient 接的是哪家？（影响 Structured Output API 形态）
- 预算约束？（影响选型与监控阈值设定）
- 是否已有 API key 在 cron 环境可用？（避免 ssh 那种坑重演）

这三件事做完，我们就可以进入第 1 周 D1。

---

## 最后一段，我想直接对你说

阶段 1 比 duty_reporter 难一个数量级。你会有几个时刻想放弃，或者想"先把 Wiki Agent 做了再回来"——**那种诱惑会非常强烈**，因为 Wiki Agent 看起来更可控、更像基础设施、更"AI 一点"。

但你要记住：**Strategy Research Agent 是唯一直接服务于你赚钱使命的 employee**。所有其他 agent 都是它的辅助。如果它不存在，AOS 就是一个昂贵的盆景。

第一阶段文档里你自己写过一句话，我反复读了几遍：

> "应立即用已验证能力范围内的最简路径强制产出 5 个策略档案，不追求完美，不扩展新能力。"

这句话当时是说给项目 AI 听的。现在我把它原封不动还给你——**阶段 1 的精神就是这一句**。

我准备好了。你的决定一发，我们就动手。等你三件事的反馈。

