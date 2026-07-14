
# 用户：
附件(pack\projects\contextLedger\ContextLedger 项目背景包（新AI接手用）.md)是我的contextLedger项目的项目设计以及执行情况的简要叙述，作为你了解这个项目的背景信息，请你在阅读它后，尽你最大的智慧给出评价和下一步的执行指导

# GPT-5.6-Sol:
我读完后的总体判断是：

> **ContextLedger 已经不是一个“记忆系统构想”，而是一个已经找到核心价值、完成机械闭环验证、正在进入语义正确性攻坚阶段的工程项目。**
> 它值得继续做，但接下来必须收缩战线：暂时不要扩产品形态、MemoryPack 或宿主范围，而应集中解决 **实体解析、生命周期裁定、时序/来源冲突和真实下游收益验证**。

下面是我的具体评价与执行建议。

---

\ # 一、总体评价

\ ## 1. 项目的核心方向是成立的

ContextLedger 解决的并不是普通意义上的“让模型记住更多”，而是：

- 当前任务状态是什么；
- 哪些旧事实已经失效；
- 哪些决策仍然有效；
- 哪些约束必须进入下一次执行上下文；
- 如何在长程任务中避免“废案复活”和“旧状态污染”。

这与普通 RAG、向量记忆、滚动摘要有本质区别。

RAG 擅长回答：

> “过去出现过什么相关内容？”

ContextLedger 要回答的是：

> “截至当前，什么仍然成立？”

后者才是长程自动执行 Agent 真正缺失的能力。尤其是在后台 Agent、多工具并发、任务持续演化的场景中，“召回了旧信息”不仅是噪声，还可能直接触发错误动作。

因此，你将项目定位为：

> **长程 Agent 的领域状态层，而不是聊天记忆、插件或独立智能体**

这是正确的。

---

\ ## 2. 最有价值的资产不是 Graph，而是“可裁定的状态演化”

单独看 Graph、事件日志、append-only、状态编译，这些技术都不是不可复制的。

真正形成项目差异化的是以下组合：

1. 稳定实体或生命周期身份；
2. 新旧事件之间的冲突定位；
3. 失效、替代、恢复等状态转移；
4. 当前有效集合的确定性编译；
5. 最终上下文中的强制包含保证；
6. 全过程可回放、可审计、可隔离。

也就是说，ContextLedger 的护城河不是“存储上下文”，而是：

> **把自然语言任务过程编译为可追踪、可撤销、可重放的当前信念态。**

这是一个比“AI memory”更准确、也更有工程价值的定义。

---

\ ## 3. 项目已经完成了非常关键的自我纠偏

从文档看，项目过程中出现过两类危险操作：

- 运行中修改清洗器，破坏事件链确定性；
- 人工补 patch 写入主图，绕过隔离原则。

能够回滚到 checkpoint、冻结版本、恢复 quarantine-only，并重新批量执行，说明项目已经建立了正确的工程纪律。

这是比“某一轮指标更好”更重要的成果。因为对于 ContextLedger 这种状态基础设施：

> 一个低一点但可复现的分数，比一个高一点但不可审计的分数更有价值。

Phase 0 和 Phase 0.5 的封板方式是成熟的：有停止条件、有重放验证、有机制矩阵，而不是无止境补案例。

---

\ # 二、目前最关键的结构性问题

\ ## 1. 当前瓶颈已经不在机械核，而在“语义编译前端”

你现有结构可以抽象为：

```text
自然语言/事件
    ↓
Extractor
    ↓
Entity Resolver
    ↓
Adjudication / Reconcile
    ↓
Append-only Patch
    ↓
Graph State Compiler
    ↓
Assembler
```

其中后半段已经相对可控：

- Apply 可以确定性执行；
- Replay 可以验证；
- Lint 可以机械检查；
- Quarantine 可以阻断污染；
- Assembler 可以执行 must_include。

真正的不确定性集中在前三步：

- Extractor 是否提取对了状态声明；
- Resolver 是否把表面不同的称谓对齐到同一对象；
- Adjudicator 是否把“冲突”错误地理解为“失效”。

这意味着下一阶段不应该继续堆 Graph 类型或 Assembler 功能，而应把前端语义链路进一步拆开。

---

\ ## 2. entity_ref 同时承担了太多职责

目前 entity_ref 至少承担了：

- 实体身份；
- 冲突分桶；
- 失效匹配；
- 状态聚合；
- 检索锚点。

这是导致系统脆弱的根本原因。

现实中，“同一实体”不等于“同一状态流”。例如：

- 同一个任务可能有多个执行轮次；
- 同一个方案可能有多个版本；
- 同一个实验对象可能同时存在多个环境状态；
- 同一个文件可能对应不同分支或不同生成周期。

因此，引入：

```text
lifecycle_ref
lifecycle_stage
lifecycle_seq
adjudication_key = lifecycle_ref ?? entity_ref
```

方向是正确的。它相当于把：

- “这是什么对象”
- “这是该对象的哪一段生命史”
- “它应该与哪些声明发生裁定”

拆开了。

但我建议对该设计**有条件批准**，不能只把三个 optional 字段加到 schema 就开始跑。

---

\ ## 3. lifecycle_seq 不能由 LLM 自由生成

这是生命周期方案中最危险的潜在问题。

如果 Extractor 直接决定：

```text
lifecycle_ref = round5
lifecycle_seq = 3
```

那么你只是把原来的 entity_ref 不稳定性转移到了 lifecycle_ref 和 lifecycle_seq。

建议明确权责：

\ ### LLM 可以提出

- surface entity；
- 可能的 lifecycle alias；
- 状态变化类型；
- 事件之间可能的关系；
- 事件中出现的显式时间和阶段描述。

\ ### Resolver 可以决定

- canonical entity；
- lifecycle 候选匹配；
- 是否建立新生命周期；
- 是否需要 abstain/quarantine。

\ ### 机械层必须决定

- 最终 lifecycle_ref；
- sequence 编号；
- 合法状态转移；
- adjudication_key；
- 同桶事件排序；
- 当前 active 集合。

核心原则是：

> **LLM 提议语义，机械层分配身份和执行状态转移。**

否则 ContextLedger 的强保证最终仍建立在 LLM 命名一致性之上。

---

\ # 三、生命周期 schema 在实现前必须补齐的内容

我建议在 `05_phase1_lifecycle_schema.md` 中至少补齐以下九项。

\ ## 1. 身份不变量

必须明确：

- 一个 node 能否没有 lifecycle_ref；
- 一个 lifecycle_ref 是否只能属于一个 canonical entity；
- 一个 entity 是否允许同时存在多个 active lifecycle；
- lifecycle_ref 是否可跨项目复用；
- lifecycle_ref 一旦分配后是否不可变；
- alias 合并后 lifecycle_ref 如何迁移。

建议：

```text
entity_ref       = 对象身份
lifecycle_ref    = 对象的一条状态演化流
adjudication_key = 冲突裁定分桶键
```

三者不要互相隐式替代。

---

\ ## 2. sequence 的分配规则

需要明确：

- sequence 是事件到达顺序，还是业务发生顺序；
- late arrival 是否重排；
- 重排是否改变已有 patch；
- sequence 冲突如何处理；
- replay 后能否保证完全一致。

我的建议是不要只保留一个时间或序号，而要区分：

```text
observed_at / ledger_step
effective_at / event_time
```

其中：

- `observed_at`：系统什么时候收到，必须单调、不可修改；
- `effective_at`：业务事件实际何时生效，可以迟到、缺失或不确定。

这实际上是一个轻量级双时态模型。没有这一区分，`out_of_order_late` 问题会不断以新形式回来。

---

\ ## 3. 状态转移表

应该为不同节点类型定义允许的转移，例如：

```text
proposed → active
active → superseded
active → suspended
suspended → active
superseded → revived
active → partially_superseded
```

但不要一开始无限扩状态枚举。可以先使用：

- node 本身的事实状态；
- relationship 表达替代、暂停、恢复；
- compiler 派生最终 active 状态。

关键是明确哪些转移：

- 可以机械执行；
- 必须进入 quarantine；
- 只能保守地保持旧状态；
- 需要外部裁定。

---

\ ## 4. full / partial / conditional / revival 的正式语义

这四类不能只作为 benchmark 标签存在，必须对应可执行语义。

\ ### Full invalidation

新声明完全取代旧声明。

\ ### Partial invalidation

只替代旧声明中的一个字段、范围或子命题。不能把整个 node 简单置为 superseded，除非旧 node 已经原子化。

因此这里有一个重要设计选择：

> 要么要求状态声明原子化；要么引入 field/path 级失效。

Phase 1 建议优先采用“原子化声明”，不要过早建设通用 JSON path 失效系统。

\ ### Conditional invalidation

必须包含条件作用域，例如：

```text
condition:
  environment: staging
  branch: feature-x
```

条件不明确时，不应执行硬失效。

\ ### Revival

应建模为新事件恢复某一旧状态，而不是重新把旧 patch 改回 active。旧事件保持不变，当前状态由 compiler 根据 revival 关系重新派生。

---

\ ## 5. provenance conflict 与 invalidation 必须彻底分离

目前低 precision 中，provenance conflict 是最大的单项来源之一。这说明系统可能隐含采用了：

> 两个说法冲突，所以后来的说法让前面的失效。

但以下情形不应自动失效：

- 用户和工具结果冲突；
- 两个不同来源给出不同判断；
- 推测和实测冲突；
- 不同环境下的结果不同；
- 同一时间的并列证据冲突；
- 来源可信度不足。

建议将结果分成至少三种：

```text
SUPERCEDES       明确替代
COEXISTS         作用域不同或允许并存
CONTESTS         发生冲突，但不足以判定谁失效
```

`CONTESTS` 不应直接修改 active 状态。它应进入待裁定集合，或者由来源优先级规则处理。

---

\ ## 6. Resolver 必须支持 abstain

Resolver 不应该被迫每次都返回一个 canonical entity。

建议接口类似：

```json
{
  "surface_ref": "round5方案",
  "candidates": [
    {
      "entity_ref": "proposal.round5",
      "score": 0.78,
      "evidence": ["alias_match", "same_project"]
    }
  ],
  "resolution": "abstain",
  "reason": "ambiguous_lifecycle"
}
```

基本原则：

- 错误合并通常比暂时不合并更危险；
- false invalidation 通常比 missed invalidation 更危险；
- 低置信度结果必须可进入 quarantine；
- 不允许静默降级为新 entity_ref 后继续运行。

---

\ ## 7. 旧数据迁移规则

由于字段是新增的，必须明确：

```text
lifecycle_ref 缺失时，是否默认等于 entity_ref？
```

这可以作为兼容规则，但只能是明确的版本化规则，而不是代码中的隐式 fallback。

建议：

```text
schema_version < lifecycle_v1:
    adjudication_key = entity_ref

schema_version >= lifecycle_v1:
    adjudication_key = lifecycle_ref if present
    else entity_ref under explicit legacy mode
```

并为迁移前后分别保留 checkpoint。

---

\ ## 8. 新增 lint 规则

至少加入：

- lifecycle_ref 指向不存在的实体；
- 同一 lifecycle_ref 跨 canonical entity；
- lifecycle_seq 重复或非法倒退；
- revival 找不到可恢复目标；
- partial invalidation 缺少作用域；
- conditional invalidation 缺少 condition；
- provenance conflict 被直接写成 full invalidation；
- adjudication_key 发生非授权改变；
- legacy 与 lifecycle_v1 节点发生模糊混裁。

---

\ ## 9. replay fixture

每种机制必须有最小回放夹具：

- 同实体、不同生命周期；
- alias 指向同 lifecycle；
- alias 指向不同 lifecycle；
- late arrival；
- provenance conflict；
- partial；
- conditional；
- revival；
- false alias temptation；
- sequence collision；
- legacy migration。

这些 fixture 必须比真实批量跑更早完成。

---

\ # 四、建议重新划分 Extractor、Resolver 和 Adjudicator

现在最值得做的架构调整，是避免 Extractor 同时承担“理解”和“裁决”。

建议职责如下。

\ ## Extractor：只提取声明

输出：

- 事件中明确出现的对象；
- 状态声明；
- 显式否定；
- 显式替代关系；
- 时间、环境、分支、来源；
- 可能的 lifecycle 线索；
- 原文证据跨度。

它不直接决定最终 active/superseded。

\ ## Resolver：负责身份解析

输入表面引用和已有候选，输出：

- canonical entity；
- lifecycle 匹配；
- alias 记录；
- 匹配证据；
- 置信度；
- abstain。

\ ## Adjudicator：负责语义关系判断

判断新旧声明属于：

- supersedes；
- refines；
- contests；
- coexists；
- revives；
- unrelated。

\ ## Mechanical compiler：负责最终状态

根据：

- adjudication_key；
- 状态转移规则；
- 时序；
- 作用域；
- 来源规则；

确定当前 active 集合。

这一拆分会增加接口，但能显著改善可测试性。否则一次误判很难知道究竟是：

- 没提取到；
- 实体没对齐；
- 生命周期没对齐；
- 冲突分类错误；
- 状态编译错误。

---

\ # 五、下一阶段最优执行顺序

\ ## STEP 0：先恢复“仓库当前事实”

背景包明确指出历史快照不能视为当前仓库状态。因此接手后的第一步不应该直接改 schema，而应该生成一份机器可读的当前状态报告。

至少包括：

```text
current commit
schema version
extractor version
cleaner version
resolver version
graph_state checksum
latest applied turn
latest quarantined turn
node/edge counts
active/superseded counts
quarantine reason distribution
lint baseline
benchmark version
current metric report
```

这份报告应落盘，例如：

```text
reports/current_state_manifest.json
```

以后所有实验都引用该 manifest，而不是引用叙述文档中的历史数字。

---

\ ## STEP 1：冻结 benchmark v1

在继续调规则之前，必须防止对现有 15–20 条轨迹过拟合。

建议将数据分为：

- development：允许分析和调参；
- regression：每次提交运行；
- blind holdout：规则冻结后才揭晓；
- adversarial：专门构造 alias、late event、provenance 诱饵。

尤其要冻结：

- gold schema；
- baseline 实现；
- metric 脚本；
- 各数据集 hash；
- D1/D2 的精确定义。

否则指标提升可能只是不断适配同一批轨迹。

---

\ ## STEP 2：完成 lifecycle schema RFC，而不是马上写实现

针对上面九项形成明确的决策表。

重点不是文档篇幅，而是回答：

1. 谁分配 lifecycle_ref？
2. 谁分配 lifecycle_seq？
3. late event 如何处理？
4. provenance conflict 是否能触发失效？
5. partial 的最小表达是什么？
6. conditional 的条件作用域如何存储？
7. revival 如何编译？
8. legacy 数据如何兼容？
9. 哪些情况必须 quarantine？

这些问题没有写死之前，不建议实现。

---

\ ## STEP 3：实现最小 lifecycle 核心

第一版只解决已被数据证明的问题：

- 同实体、多生命周期；
- revival；
- provenance conflict 不再自动失效；
- out-of-order 的到达时间/生效时间分离；
- alias 对生命周期的解析。

暂时不要加入：

- 通用规则引擎；
- 任意逻辑条件表达式；
- 通用字段级 patch DSL；
- 跨项目知识合并；
- MemoryPack 生命周期同步。

Phase 1 的目标应是修正当前错误结构，而不是设计终极知识表示语言。

---

\ ## STEP 4：双轨 shadow replay

对同一批事件同时运行：

```text
旧裁定链路 → old graph state
新裁定链路 → shadow graph state
```

逐 checkpoint 比较：

- active set 差异；
- invalidation 差异；
- must_include 差异；
- quarantine 差异；
- assembler token 差异；
- 下游答案或动作差异。

新实现未过门槛前，不替换主链。

---

\ ## STEP 5：做消融实验

必须证明收益来自哪里。至少比较：

1. entity_ref only；
2. entity_ref + resolver；
3. entity_ref + lifecycle；
4. entity_ref + lifecycle + provenance separation；
5. 完整方案。

如果完整方案只比简单 resolver 提升很少，就应重新评估复杂度。

这是防止项目因为设计优雅而持续膨胀的关键。

---

\ ## STEP 6：验证下游任务收益

内部指标不是最终价值。

ContextLedger 最终必须证明，在相同 token 预算下，它能降低 Agent 的实际错误率。

建议设计三类长程任务：

\ ### 任务 A：需求反复修改

观察旧需求是否错误复活。

\ ### 任务 B：多轮实现与回滚

观察废弃方案、旧文件路径、旧接口是否污染后续动作。

\ ### 任务 C：后台异步工具执行

观察迟到 ToolResult、取消任务、重试结果是否破坏当前状态。

比较：

- full history；
- rolling summary；
- vector RAG；
- exact-surface last-write-wins；
- ContextLedger。

最终指标包括：

- 任务成功率；
- 废弃约束引用次数；
- 错误动作数；
- 必须约束遗漏率；
- token 消耗；
- 延迟；
- 人工干预次数。

> 如果 ContextLedger 只提升 Graph Set-F1，却不能减少下游错误动作，那么产品价值仍未被证明。

---

\ # 六、指标体系应如何调整

目前已有：

- invalidation precision/recall；
- active-set Set-F1；
- must_include recall。

这些是必要的，但还不够。

\ ## 1. 把错误成本纳入指标

ContextLedger 中，不同错误并不等价：

- 错误失效一条有效约束，可能造成严重执行事故；
- 漏掉一次失效，可能只是上下文中多一条旧信息；
- must_include 漏召回，可能直接让 Agent 违反关键要求。

建议引入加权风险：

```text
Critical false invalidation
Critical must_include miss
Ordinary false invalidation
Missed invalidation
Benign duplication
```

并把以下两项设为硬门槛：

- must_include recall 不低于 D1；
- 关键约束的 false invalidation 为零，或进入 quarantine 而不是主图。

---

\ ## 2. 单独报告 Resolver 指标

不要只通过最终 invalidation 指标间接观察 Resolver。

至少报告：

- canonical entity accuracy；
- lifecycle resolution accuracy；
- alias merge precision；
- alias merge recall；
- abstain precision；
- 因解析错误导致的下游误失效数量。

特别是 alias merge precision 应优先，因为错误合并可能让两个不同对象互相失效。

---

\ ## 3. 单独报告隔离质量

15/72 左右的隔离比例不一定代表坏事。关键要看：

- 隔离的是高风险歧义，还是正常事件；
- 隔离后是否可自动重试恢复；
- 隔离是否集中在某几种 schema 缺口；
- 是否出现 silent failure；
- quarantine 是否成为永久垃圾桶。

建议每次报告：

```text
quarantine rate
auto-recovery rate
manual-review rate
repeat-failure rate
reason distribution
silent-corruption count
```

隔离率可以阶段性较高，但 silent corruption 必须趋近于零。

---

\ # 七、关于 Assembler 的判断

Assembler 是项目能否产生实际价值的关键，不应被当作 Graph 的简单输出格式化器。

它至少要保证三件事：

\ ## 1. 强制约束不会被预算裁掉

`must_include` 不能与普通检索结果共同竞争 token。

建议预算顺序：

```text
reserved budget for must_include
→ current task state
→ immediate dependencies
→ recent tool outcomes
→ optional soft context
```

如果 must_include 超预算，应显式 fail 或降级，而不是静默截断。

---

\ ## 2. 所有注入内容都可解释

每个 assembler item 最好附带：

```text
why_included
source_node
relevance_path
authority
status
token_cost
```

这样发生 Agent 错误时，可以区分：

- Graph 状态错误；
- 检索没取到；
- 预算裁剪错误；
- 宿主没有真正注入；
- 模型忽略了已注入内容。

---

\ ## 3. 评测装配，而不只是评测存储

Graph 当前态正确，不意味着上下文一定正确。

应该增加：

- current-state retrieval recall；
- irrelevant-context ratio；
- stale-context leakage；
- must_include ordering；
- context token efficiency；
- downstream instruction adherence。

---

\ # 八、MemoryPack 和 OpenCode 现在应该怎么处理

\ ## MemoryPack：继续延期

当前不应投入主要精力建设 MemoryPack。

原因很简单：

- 核心价值尚在验证；
- 生命周期 schema 还未稳定；
- Pack 会引入额外陈旧窗口；
- Graph 与 Pack 一致性会增加新的验证维度；
- 软知识不是当前最高风险。

只有当 TaskGraph + Assembler 已证明下游收益，并且真实用户明确需要跨任务知识复利时，再进入 Phase 2。

---

\ ## OpenCode：只保留最窄集成

OpenCode 目前应被视为实验宿主，而不是产品方向。

建议：

- 只覆盖主会话链路；
- 使用稳定 wrapper 注入；
- 保留宿主原始上下文和 CL 上下文的对照日志；
- 先 shadow，再接管；
- 暂不覆盖子 Agent；
- 暂不做多宿主适配。

在 benchmark 和 lifecycle 核心稳定前，不建议为了宿主兼容性修改核心数据模型。

---

\ # 九、接下来明确不要做的事情

1. **不要现在实现 MemoryPack。**
2. **不要扩展更多宿主。**
3. **不要继续增加节点和边类型。**
4. **不要让 LLM 直接决定最终状态。**
5. **不要让 LLM 自由生成 sequence。**
6. **不要在同一批轨迹上持续调规则并宣称泛化提升。**
7. **不要用单一 Set-F1 掩盖关键约束被错误失效。**
8. **不要将 provenance conflict 直接等同于 invalidation。**
9. **不要用人工修 patch 的方式提高通过率。**
10. **不要在 schema 未稳定前优化全图 lint 的性能问题。**

目前正确性的重要性远高于性能。O(N) lint 是未来问题，错误状态进入主图是当前问题。

---

\ # 十、建议的 Phase 1 完成标准

我建议将 Phase 1 的封板条件定义为以下几组。

\ ## A. 可复现性

- 新 schema 下 patch replay 确定；
- graph_state 可稳定再生；
- migration 前后结果可审计；
- 所有工具、prompt、contract 都有版本；
- 无人工 patch 进入主图。

\ ## B. 语义正确性

- lifecycle fixture 全部通过；
- revival 轨迹无回归；
- provenance conflict 不再默认触发 full invalidation；
- late event 具有明确处理规则；
- alias 错误合并可被阻断或隔离；
- partial/conditional 不再整体误杀旧节点。

\ ## C. 安全性

- must_include recall 不低于 D1；
- 关键约束 false invalidation 为零，或全部被 quarantine；
- silent corruption 为零；
- quarantine 不污染主图；
- abstain 路径完整可运行。

\ ## D. 泛化性

- blind holdout 上仍有提升；
- 提升不是由单一数据形态贡献；
- 消融实验能说明 lifecycle/resolver 的独立收益；
- 指标脚本和数据集已冻结。

\ ## E. 下游价值

至少在一种真实长程 Agent 任务中证明：

- 比 full-history 或 RAG 更少引用失效信息；
- 在相同 token 预算下任务成功率更高；
- 或以更低 token 达到相同成功率；
- must_include 的下游遵循率没有下降。

---

\ # 十一、我对下一步唯一最高优先级动作的建议

如果只能选择一件事，我建议做：

> **冻结 benchmark v1，并在不修改主链的前提下，实现 lifecycle schema 的 shadow compiler，然后对全部历史轨迹进行双轨回放和误差归因。**

这一步能够同时回答：

- lifecycle_ref 是否真的解决问题；
- 指标提升是否可泛化；
- provenance、revival、late event 分别贡献多少；
- 新 schema 是否破坏确定性；
- quarantine 是否下降；
- 是否值得继续增加模型复杂度。

在这一步之前，不应扩大产品范围。

---

\ # 最终结论

我认为 ContextLedger **值得继续投入**，并且项目已经形成了一个有辨识度的技术内核：

> **它不是帮助 Agent 记住历史，而是帮助 Agent 维护一个可撤销、可裁定、可回放的当前世界状态。**

但项目当前正处于一个危险而关键的转折点：

- 如果继续扩展 Graph、Pack、宿主和产品形态，它可能演化成复杂但未证明价值的记忆框架；
- 如果收缩到 Resolver、Lifecycle、Adjudication、Benchmark 和下游错误率，它有机会成为真正可辩护的 Agent 状态基础设施。

我的建议是：

> **批准 lifecycle 方向，但补齐身份、时序、来源、状态转移和迁移契约；让 LLM 负责提出声明，让机械层负责分配身份与编译状态；冻结基准，使用 shadow replay 和 blind holdout 验证；在真实下游收益被证明前，继续冻结 MemoryPack 和多宿主扩展。**

这将是当前风险最低、信息增益最高、也最符合 ContextLedger 核心价值的一条执行路径。

# 用户：
请你阅读raw\projects\contextLedger\context_ledger_design_and_impliment_stage02.md，按照GPT-5.6-Sol建议实施，在执行前，先把当前的提交，并合并了，再开一个新的分支，然后开始实施
# 项目AI：
我这边已经核对完了：新分支正确、基线清单和 RFC 都落好了，目前只剩这 3 个 Stage02 新产物还没提交。下面我给你一个收束版结果，把“已经做完什么”和“下一步该怎么衔接”讲清楚。已按你确认的方案开始实施，而且 git 前置动作已经做完了：

- 已把之前工作区提交到 main
  - 提交： 890219b
  - 提交信息： Finalize Phase 0.5 benchmark and Phase 1 schema design draft
- 已从最新 main 新开分支：
  - phase1-lifecycle-stage02
这轮我按照 GPT-5.6-Sol 的建议，优先落了 STEP 0 和 STEP 2 ，没有贸然直接进真实实现。

已完成产物

1. 当前状态清单
    current_state_manifest.json
这份清单已经把 Stage02 需要的“仓库当前事实”钉住了，包括：

- 当前分支 / commit
- 当前 schema 契约位置
- graph_state.json 的 SHA256
- turn_counter = 84
- node / edge 数
- quarantine 分布
- 最新 lint 基线
- 当前 benchmark 口径与关键指标
另外我还补跑并落盘了当前 lint 基线：

- current_graph_lint_report.json
2. 完整版 lifecycle RFC
    05_phase1_lifecycle_schema.md
这次不再只是“加 3 个 optional 字段”的设计稿，而是补成了可评审 RFC，已经明确了：

- entity_ref / lifecycle_ref / adjudication_key 的职责拆分
- 生命周期身份不变量
- lifecycle_seq 不能由 LLM 自由生成
- observed_at / effective_at 双时态边界
- SUPERCEDES / COEXISTS / CONTESTS / REVIVES / UNRELATED
- provenance conflict 不得默认折叠为 full invalidation
- resolver 的 abstain
- legacy 兼容 / 迁移规则
- 必增 lint 规则
- 必备 replay fixtures
- benchmark 验收目标
当前分支未提交改动

现在 phase1-lifecycle-stage02 上还有 3 个未提交产物：

- 05_phase1_lifecycle_schema.md
- current_state_manifest.json
- current_graph_lint_report.json
我对下一步的建议

按 stage02 文档的顺序，现在最合适的是继续做这两件，而不是直接改主链实现：

1. 冻结 benchmark v1
    把 development / regression / blind holdout / adversarial 划开，避免继续在同一批轨迹上调参
2. 先补 lifecycle fixtures + shadow replay 设计
    先做：

   - revival
   - provenance conflict
   - late arrival
   - legacy migration
      这些最小夹具
      然后再让新旧裁决链并跑比较差异
这一步完成后，再进真实实现会稳很多。现在如果你要我继续，我建议下一轮直接做：

- benchmark freeze artifacts
- lifecycle fixtures
- shadow replay plan
而不是先改 reconcile/apply/assembler 主链。

# 军师AI(GPT-5.6-Terra):
## 总体评审

这份执行回复的**方向是对的，节奏也比“直接改主链”更稳健**：先固定当前事实、补齐 RFC、再冻结评测与设计 shadow replay，符合当前阶段应优先降低语义与评测风险的原则。

尤其值得肯定的是：

- 没有把 `lifecycle_ref/lifecycle_seq` 简化成“加字段即完成”；
- 已明确 LLM 不应自由分配生命周期序号；
- 已将 provenance conflict 与 invalidation 分离；
- 提出了 resolver abstain、双时态、迁移、lint、fixture 等必要契约；
- 明确暂不修改 reconcile/apply/assembler 主链，避免未经回放验证就引入不可逆复杂度。

但这份回复仍有一个问题：它主要是**“完成事项的叙述”**，而还不是一份足以批准进入下一轮的、可机械验收的执行交付。下一步应把它收束为明确的提交、清单、验收门槛和失败处置方案。

---

## 首先应要求其完成的收尾动作：提交 Stage02 产物

目前三个关键产物仍未提交：

- `05_phase1_lifecycle_schema.md`
- `current_state_manifest.json`
- `current_graph_lint_report.json`

这不应留到“下一轮顺手再提交”。建议要求项目 AI 先完成一个**只包含 Stage02 文档与基线产物的原子提交**，再启动 benchmark freeze 和 fixtures 工作。

建议提交信息类似：

```text
Freeze Stage02 repository baseline and lifecycle RFC
```

提交前必须报告并确认：

```text
git status --short
git branch --show-current
git rev-parse HEAD
git log -1 --oneline
git diff --check
```

提交后必须报告：

```text
new commit SHA
git status --short  # 应为空
base main commit SHA
merge-base(main, phase1-lifecycle-stage02) SHA
```

原因很简单：当前状态清单与 RFC 本身就是后续所有 shadow replay、实现和评测的依据。它们若仍是未提交工作区内容，就不是真正冻结的基线。

---

## 对“当前状态清单”的具体审查要求

项目 AI 说清单已钉住当前事实，这是正确目标；但你应要求它补充或确认以下内容，防止“清单写了历史数字，却没有形成可复现证据”。

### 必须区分“清单生成时的事实”与“历史背景数字”

尤其是：

```text
turn_counter = 84
node / edge 数
quarantine 分布
```

必须来自生成清单时实际读取的：

```text
graph/projects/abu_modern/graph_state.json
```

而不能只是复述背景包中恢复封板时的数字。

建议 manifest 每个关键统计项附带来源字段，例如：

```json
{
  "graph_state_path": "graph/projects/abu_modern/graph_state.json",
  "graph_state_sha256": "...",
  "graph_state_turn_counter": 84,
  "node_count": 165,
  "edge_count": 274,
  "derived_at_utc": "..."
}
```

若 `turn_counter=84` 确实是当前读取值，也应明确写为：

> 该值由当前 `graph_state.json` 实测得出，不是历史叙述快照。

### 应补充版本指纹

建议 manifest 至少还包含：

- `main_base_commit`
- `stage_branch_head_commit`
- `working_tree_clean_at_generation`
- Python / Node / 包管理器版本
- extractor prompt / contract / cleaner / resolver 的文件 hash 或版本号
- benchmark 数据集及 metric 脚本 hash
- `lint_baseline.json` 的 hash 与路径
- manifest 生成脚本及其版本或 hash
- 当前 quarantine 条目总数、按 reason 分类数、未解决条目数
- active / superseded / pending 或其他当前状态分布

这里最重要的是：**manifest 应能由脚本再生，而不是靠人工编辑维护。**

若当前是 JSON，建议同时提供对应生成命令或生成脚本路径；否则未来它会变成新的“叙述性真相源”。

---

## 对 RFC 的评审：可以批准进入“设计冻结前审查”，但尚不应直接称为实现就绪

从回复列出的内容看，RFC 已覆盖主要风险面，质量方向是好的。不过，要进入 fixtures 与 shadow replay 设计前，建议确认 RFC 中存在以下几个“可执行决策表”，而不只是原则描述。

### 需要明确的决策表

| 问题 | 必须写死的决策 |
|---|---|
| `lifecycle_ref` 分配者 | LLM 提议线索；Resolver 匹配或 abstain；机械层生成稳定 ID |
| `lifecycle_seq` 分配者 | 只能由机械层确定，不能由 LLM 输出最终值 |
| `observed_at` | 由 ledger step 或系统接收事件产生，单调且不可修改 |
| `effective_at` | 可缺失、可晚到、可不确定；其排序规则必须明确 |
| 晚到事件 | 是只影响未来编译结果，还是允许重算当前派生态；绝不能回写旧 patch |
| `CONTESTS` | 不直接使旧节点 superseded；进入待裁定、保守共存或依来源规则处理 |
| partial invalidation | Phase 1 是否统一要求声明原子化，而非支持通用字段级失效 |
| conditional invalidation | condition 最小 schema、缺 condition 时的处理方式 |
| revival | 以新事件和显式关系表达；不允许修改旧 patch |
| abstain | 是否 quarantine、是否创建 provisional node、是否允许进入 assembler |
| legacy 节点 | `adjudication_key` fallback 的版本化规则及退出计划 |

### 建议增加“明确不做”的范围

RFC 应有一个 `Non-goals for Phase 1` 小节，明确排除：

- 通用规则语言；
- 任意 JSON path / field-level patch DSL；
- 跨项目 lifecycle 合并；
- 自动解决所有来源冲突；
- MemoryPack 同步；
- 多宿主集成；
- 全量性能优化。

这样可以避免 lifecycle schema 从一次针对已知错误模式的修复，膨胀成通用知识表示系统。

---

## 对下一步排序的建议：认可，但应调整为四个明确阶段

项目 AI 建议：

1. benchmark freeze；
2. lifecycle fixtures；
3. shadow replay plan；
4. 再进真实实现。

这个顺序总体正确。我的建议是把它写得更严格一些：

### 阶段 A：先提交并锁定 Stage02

完成上文所述原子提交，确保工作树干净。

**通过条件：**

- Stage02 三个产物已提交；
- manifest 可由脚本再生；
- git diff 为空；
- 清单中的数字与当前 `graph_state.json` 实测一致。

### 阶段 B：冻结 Benchmark v1

这一步不能只创建几个目录。必须真正冻结：

```text
development
regression
blind_holdout
adversarial
```

并落盘以下内容：

- 每个 split 的 case ID 列表；
- 数据文件 hash；
- gold 标注 schema 版本；
- D1 / D2 baseline 的精确定义与实现版本；
- metric 脚本 hash；
- 当前旧链路的基线成绩；
- 哪些轨迹允许调参、哪些绝对不可查看或不可用于规则设计；
- benchmark 更新流程与版本号规则。

**重要建议：**
`lifecycle fixtures` 不应与 blind holdout 混在一起。fixtures 是机制级、白盒、预期确定的测试；holdout 是泛化评测。两者的失败含义完全不同：

- fixture fail：实现或契约错误；
- holdout fail：泛化不足、可能过拟合或设计假设错误。

### 阶段 C：先写 fixtures 和 shadow replay 规格，再写 lifecycle 主链代码

建议先实现最小 fixtures，至少覆盖：

1. 同一 entity 的两个不同 lifecycle 不互相误杀；
2. revival 恢复的正确派生；
3. provenance conflict 只产生 `CONTESTS`，不默认 full invalidation；
4. late arrival 下 `observed_at` 与 `effective_at` 的行为；
5. legacy node 的兼容与迁移；
6. alias 指向错误 lifecycle 时 Resolver abstain / quarantine；
7. sequence collision 或时间不确定时的保守处理；
8. replay 后 graph state 与 bundle 的确定性再生。

每个 fixture 应具备：

```text
input event stream
expected patches or expected semantic relations
expected graph state at checkpoints
expected active/superseded/pending set
expected quarantine result, if applicable
expected assembler must_include result, if applicable
```

不要仅写“应当通过”的自然语言说明。

### 阶段 D：定义 shadow replay 的可执行验收门槛

shadow replay 不能只是一份“旧新双跑比较”的计划文档。它应在实现前定义差异输出结构和判定规则，例如：

```text
old_state_hash
shadow_state_hash
checkpoint_id
node-level status diffs
relation diffs
must_include diffs
quarantine diffs
assembler token diffs
classification of each diff:
  expected_improvement
  expected_schema_change
  regression
  unexplained
```

并事先明确：

- 哪些差异允许；
- 哪些差异必须人工裁定；
- 哪些差异自动阻断切换；
- 什么指标门槛下可以进入主链替换候选阶段。

---

## 必须要求项目 AI 补上的“影子链路不变量”

在真实实现前，应明确以下不变量。否则 shadow replay 即使跑完，也无法判断其结果是否可信。

### 事件与 patch 不变量

- 原始事件不可改写；
- 历史 patch 不可改写；
- lifecycle 升级不得通过人工编辑旧 patch 完成；
- schema 迁移必须版本化、可回放；
- 所有 shadow 输出必须落在独立目录，不能污染主图；
- shadow 失败必须 quarantine 或终止，不允许“尽量生成一个结果”。

### 确定性不变量

同一输入、同一版本的：

- contracts；
- resolver；
- cleaner；
- extractor prompt；
- fixture；
- compiler；

必须产生相同的：

- patch 序列；
- graph state；
- context bundle；
- metrics。

如果 lifecycle 方案需要 LLM，那么至少要分开验证：

1. **固定 LLM 输出时，机械后端是否完全确定；**
2. **真实 LLM 输出时，前端语义波动造成了什么误差。**

不要把两种不确定性混在一次实验里。

### 安全不变量

- `must_include recall` 不低于 D1；
- critical constraints 不得被静默错误失效；
- `CONTESTS` 不得自动坍缩为 `SUPERCEDES`；
- Resolver 低置信度不能静默强行 merge；
- 新 lifecycle 方案不能增加 silent corruption；
- 任何降级必须可观测、可归因。

---

## 关于“暂不改主链”的补充建议

“先不改 reconcile/apply/assembler 主链”是正确的，但应避免误解为“完全不写代码”。

下一轮可以实现的代码应严格限于**旁路、可删除、无主图副作用**的部分，例如：

- benchmark freeze 校验脚本；
- fixture runner；
- shadow graph state compiler；
- 新旧状态 diff 工具；
- lifecycle schema validator；
- manifest regeneration script；
- shadow replay report generator。

不应做的包括：

- 改写正式 apply 行为；
- 将新 `adjudication_key` 接入正式 reconcile；
- 更改生产 assembler 的默认注入；
- 对已有 patch 做迁移式重写；
- 用人工 patch 修复 fixture。

这条边界应写入下一轮任务单。

---

## 我建议你给项目 AI 的直接执行指令

可以直接这样下达：

> 批准当前方向，但先不要进入主链实现。
>
> 第一，先将 `05_phase1_lifecycle_schema.md`、`current_state_manifest.json`、`current_graph_lint_report.json` 作为 Stage02 原子提交提交到 `phase1-lifecycle-stage02`，并报告 branch、HEAD、base main SHA、clean git status、`git diff --check` 结果。
>
> 第二，复核 manifest 中 `turn_counter`、node/edge、quarantine 等数值均由当前 `graph_state.json` 实测得出，并在 manifest 中保存源路径、SHA256、生成时间、生成脚本/命令、版本指纹及 benchmark/metrics hash；不得使用历史叙述快照替代当前状态。
>
> 第三，进入 Stage03 时仅做旁路产物，不修改正式 reconcile/apply/assembler 主链。依次交付：
> 1. benchmark v1 freeze manifest 与 split/hash 机制；
> 2. lifecycle fixture schema 与至少 8 类最小 fixture；
> 3. shadow replay executable spec，包括 diff schema、差异分类、阻断门槛和报告样例。
>
> 第四，明确 fixture 与 blind holdout 完全隔离；fixture 用于机制正确性，blind holdout 不得用于规则调参。
>
> 第五，在提交任何 lifecycle 主链实现前，先提交一份 Stage03 readiness report，逐项确认 RFC 中 lifecycle ID 分配、双时态排序、CONTESTS、abstain、legacy migration、revival、partial/conditional 的最小语义和 quarantine 行为都已经转换成可执行验收规则。

---

## 最终结论

项目 AI 的当前判断可以批准：**先冻结评测、补机制夹具、设计 shadow replay，不直接修改主链。**

但批准的前提是它先完成 Stage02 的原子提交，并把“我已经核对过”转化为：

- 可再生的 manifest；
- 带 hash 的冻结 benchmark；
- 可运行的 fixture；
- 可归因的 shadow diff；
- 预先写死的阻断门槛。

这样下一阶段即使发现 lifecycle 方案不成立，损失也是一组可回放、可解释的旁路实验，而不是被新语义污染过的主图。

# 项目AI-KIMI2.7:
已按 GPT-5.6-Terra 的评审意见执行完毕。Terra 的评审位于 [raw\projects\contextLedger\context_ledger_design_and_impliment_stage02.md](/D:/CCXXLESSON/contextledger/raw/projects/contextLedger/context_ledger_design_and_impliment_stage02.md:965) 第 965-1430 行，核心要求是：先原子提交 Stage02、把 manifest 做到可复现、再只做旁路产物，不碰主链。

**Stage02 收尾**

我把三个 Stage02 产物做了原子提交，并补了一个可再生的 manifest 生成脚本：

- [contracts/05_phase1_lifecycle_schema.md](/D:/CCXXLESSON/contextledger/contracts/05_phase1_lifecycle_schema.md)
- [reports/current_state_manifest.json](/D:/CCXXLESSON/contextledger/reports/current_state_manifest.json)
- [reports/current_graph_lint_report.json](/D:/CCXXLESSON/contextledger/reports/current_graph_lint_report.json)
- [graph/scripts/generate_state_manifest.py](/D:/CCXXLESSON/contextledger/graph/scripts/generate_state_manifest.py)

manifest 现在包含：graph_state 实测路径/SHA256、生成时间、生成脚本与 hash、runtime 组件（scripts/prompts/contracts）指纹、benchmark score/hash、quarantine 分布、lint baseline hash、git 状态快照，数字全部来自当前 [graph/projects/abu_modern/graph_state.json](/D:/CCXXLESSON/contextledger/graph/projects/abu_modern/graph_state.json)。

当前 git 状态：

- branch: `phase1-lifecycle-stage02`
- HEAD: `683d205`
- base main / merge-base: `890219b`
- `git status --short`: 空
- `git diff --check`: 无错误

**Stage03 旁路产物**

按 Terra 的四个阶段要求，依次交付了旁路产物，未修改 `reconcile_patch.py`、`apply_patch.py` 或 assembler 主链：

1. **Benchmark v1 freeze**
   - [graph/projects/abu_modern/benchmark/v1_freeze/benchmark_v1_freeze_manifest.json](/D:/CCXXLESSON/contextledger/graph/projects/abu_modern/benchmark/v1_freeze/benchmark_v1_freeze_manifest.json)
   - splits: development=7, regression=6, blind_holdout=2, adversarial=2
   - 校验脚本：[graph/scripts/validate_benchmark_v1_freeze.py](/D:/CCXXLESSON/contextledger/graph/scripts/validate_benchmark_v1_freeze.py)

2. **Lifecycle fixtures**
   - schema: [graph/projects/abu_modern/fixtures/lifecycle/fixture_schema.json](/D:/CCXXLESSON/contextledger/graph/projects/abu_modern/fixtures/lifecycle/fixture_schema.json)
   - 8 个 fixture：two_lifecycles_no_kill、revival、provenance_conflict、late_arrival、legacy_migration、alias_abstain、sequence_collision、replay_determinism
   - 校验脚本：[graph/scripts/validate_lifecycle_fixtures.py](/D:/CCXXLESSON/contextledger/graph/scripts/validate_lifecycle_fixtures.py)

3. **Shadow replay executable spec**
   - 主 spec：[graph/projects/abu_modern/shadow_replay/shadow_replay_spec.md](/D:/CCXXLESSON/contextledger/graph/projects/abu_modern/shadow_replay/shadow_replay_spec.md)
   - diff schema：[graph/projects/abu_modern/shadow_replay/diff_report_schema.json](/D:/CCXXLESSON/contextledger/graph/projects/abu_modern/shadow_replay/diff_report_schema.json)
   - 示例报告：[graph/projects/abu_modern/shadow_replay/example_diff_report.json](/D:/CCXXLESSON/contextledger/graph/projects/abu_modern/shadow_replay/example_diff_report.json)

4. **Stage03 readiness report**
   - [reports/stage03_readiness_report.md](/D:/CCXXLESSON/contextledger/reports/stage03_readiness_report.md)

**验证**

两个校验脚本都已通过：

```
python graph/scripts/validate_benchmark_v1_freeze.py   # PASSED
python graph/scripts/validate_lifecycle_fixtures.py    # PASSED
```

**下一步**

旁路规格已齐。接下来应做的是：实现 shadow adjudication 链，把这 8 个 fixture 和 benchmark v1 的各 split 跑通 shadow replay，待连续三次 `PASS` 且 diff 分类一致后，才进入主链替换。

# GPT-5.6-Terra:
## 总体判断

这份回复显示项目 AI **基本遵守了上一轮的边界要求**：

- Stage02 已经原子提交；
- manifest 从静态叙述升级为可生成、可校验的产物；
- Stage03 目前看起来仍是旁路设计与验证产物；
- 没有声称已修改 `reconcile_patch.py`、`apply_patch.py` 或正式 assembler 主链；
- 已开始把 benchmark、fixture、shadow diff 和 readiness report 变成显式文件，而不是继续停留在口头设计层。

因此，**可以批准进入“shadow adjudication 链的旁路实现阶段”**。

但不能因为两个 validator 显示 `PASSED`，就认为 Stage03 的机制已经得到验证，更不能把“连续三次 PASS”作为进入主链替换的核心门槛。当前已验证的更可能是：

> freeze manifest 和 fixture 文件在结构、引用、hash 或基本约束上自洽。

这不等于已经验证：

- 生命周期裁定语义正确；
- fixture 的预期状态真的能被 compiler 推导出来；
- shadow 链和旧链之间的差异可解释；
- benchmark 改进具有统计或泛化意义；
- 新逻辑不会降低 `must_include` 安全底线。

---

## 做得好的部分

### Stage02 的提交纪律是合格的

报告给出了：

```text
branch: phase1-lifecycle-stage02
HEAD: 683d205
base main / merge-base: 890219b
git status --short: empty
git diff --check: no errors
```

这比“工作区里已经做完”可靠得多。尤其是 manifest generator 被一起提交，说明当前状态清单开始具备**可再生性**，而不只是一次性的人工快照。

下一步仍应确认 `683d205` 是否确实包含全部 Stage02 与 Stage03 产物；不要只确认 HEAD 存在，而要保存本次提交的文件清单，例如：

```bash
git show --stat --oneline 683d205
git diff --name-status 890219b..683d205
```

这能证明旁路阶段确实没有意外改动正式主链文件。

### manifest 的升级方向正确

报告称 manifest 已包含：

- `graph_state.json` 的路径与 SHA256；
- 生成时间；
- manifest 生成脚本及 hash；
- scripts / prompts / contracts 等 runtime 组件指纹；
- benchmark score/hash；
- quarantine 分布；
- lint baseline hash；
- git 状态快照。

这已接近一个合格的“实验状态锚点”。下一步要确保它具备两个性质：

1. **可重复生成**：在同一 commit、同一输入图、同一环境下重跑，除生成时间等合理字段外，核心内容一致。
2. **可验证失败**：任一 graph state、contract、prompt、benchmark 数据、baseline 或脚本发生变化时，验证器必须明确报错，而不是仅重新生成一份看似合法的新 manifest。

### “先 shadow、后替换”仍然是正确节奏

项目 AI 没有直接把 lifecycle schema 塞进正式 `reconcile → apply → assembler` 路径，这是正确的。

当前最重要的工程目标不是“尽快让新 schema 生效”，而是：

> 在不污染现有主图、不重写历史 patch、不影响现有装配行为的前提下，证明新裁定模型确实减少结构性错误。

---

## 当前报告中最需要警惕的问题

### validator 通过，不等于 fixture 的语义通过

报告仅说明执行了：

```text
python graph/scripts/validate_benchmark_v1_freeze.py   # PASSED
python graph/scripts/validate_lifecycle_fixtures.py    # PASSED
```

需要项目 AI 明确每个 validator 的断言范围。

例如，`validate_lifecycle_fixtures.py` 可能只验证：

- fixture 文件是否符合 JSON schema；
- fixture ID 是否唯一；
- 必填字段是否存在；
- 文件 hash 是否匹配；
- expected 状态集合是否格式正确。

这些都很重要，但它们不验证：

```text
输入事件流
→ shadow extractor/resolver/adjudicator
→ patch / semantic relation
→ shadow compiler
→ 预期 checkpoint state
```

是否真的成立。

因此，进入下一步前应新增一个独立的、真正执行语义的 runner，例如：

```text
run_lifecycle_fixture_replay.py
```

其输出应至少逐 fixture 给出：

```json
{
  "fixture_id": "revival",
  "result": "PASS",
  "input_event_hash": "...",
  "runtime_fingerprint": "...",
  "checkpoint_results": [
    {
      "checkpoint_id": "cp_01",
      "expected_active": ["..."],
      "actual_active": ["..."],
      "expected_relations": ["REVIVES"],
      "actual_relations": ["REVIVES"],
      "status": "PASS"
    }
  ],
  "graph_state_hash": "...",
  "bundle_hash": "..."
}
```

**文件合法性校验**和**语义行为回放**必须是两层不同的测试，不能相互替代。

### “连续三次 PASS”不是充分的主链升级门槛

“连续三次 PASS 且 diff 分类一致”作为基本稳定性检查可以保留，但不能作为主要证据，原因是：

- 如果输入、代码、环境都固定，三次成功可能只是同一个确定性结果重复了三次；
- 如果模型参与 shadow adjudication，三次成功也不足以说明模型输出稳定或泛化；
- 三次都可能稳定地产生错误结果；
- 若 diff 分类是事后人工填写，“一致”不代表分类标准客观。

应该把“三次 PASS”拆成两个不同目的：

| 检查 | 它证明什么 | 不证明什么 |
|---|---|---|
| 同版本、同输入三次重跑 | 后端确定性、无随机漂移 | 语义正确性 |
| 不同环境或干净 checkout 重跑 | 可复现性、依赖锁定较充分 | 泛化能力 |
| fixture 预期结果通过 | 已知机制是否符合设计 | 真实轨迹上的收益 |
| blind holdout 提升 | 一定程度的泛化价值 | 生产任务收益 |
| 下游 Agent 对照实验 | 产品价值 | 所有边界条件都已覆盖 |

因此，主链替换的判断不能写成：

```text
连续三次 PASS → 替换主链
```

而应写成：

```text
确定性重跑通过
+ fixture 语义通过
+ regression 不回退
+ blind holdout 达到预注册门槛
+ must_include 安全红线不下降
+ critical false invalidation 为零或全部隔离
+ diff 无未解释的 blocker
+ 旁路不污染主图
→ 才可申请主链候选切换
```

### benchmark v1 的样本规模过小，尤其 blind holdout 只有 2 条

当前 split 为：

```text
development = 7
regression = 6
blind_holdout = 2
adversarial = 2
```

总计 17 条，与早期“15–20 条起步”的建议并不矛盾；但它只能算**机制验证起步集**，不能支撑强泛化结论。

其中最薄弱的是：

```text
blind_holdout = 2
```

两条轨迹可以用于发现明显回归，却无法可靠回答：

- lifecycle 是否普遍优于 entity-only；
- provenance 分离是否稳定改善 precision；
- late arrival 的收益是否真实；
- 是否只是恰好命中了两个熟悉模式。

建议项目 AI 不必立即扩张大规模 benchmark，但至少应完成以下审计：

1. 每个 split 是否覆盖关键机制类型；
2. 同一原始轨迹的不同 turn/checkpoint 是否被切到不同 split；
3. 同一 alias 模板、实体命名模板、事件模板是否泄漏到 holdout；
4. adversarial 是否独立于 development 规则设计；
5. 每个 split 的 invalidation 类型和风险级别分布；
6. holdout 是否在规则设计期间保持不可见或至少不可用于调参。

特别重要的是：

> **一个完整轨迹及其全部 checkpoint 必须属于同一个 split。**

否则模型或规则可能在 development 看到了同一故事的早期轮次，又在 holdout 上测试其后续轮次，造成严重泄漏。

---

## shadow replay 实现前必须补齐的契约

### shadow 链必须与正式主链物理隔离

“未修改主链”还不够；还需要保证 shadow 的运行结果不会通过共享目录、共享状态文件或共享缓存污染主链。

建议规定：

```text
正式图：
graph/projects/abu_modern/graph_state.json

shadow 图：
graph/projects/abu_modern/shadow_replay/runs/<run_id>/graph_state.json
```

并明确：

- shadow 不写正式 `graph_state.json`；
- shadow 不写正式 applied patch ledger；
- shadow 不改写 raw；
- shadow 生成的 patch、relation、state、bundle、report 全部放入 run-scoped 目录；
- shadow run ID、输入 hash、代码版本、runtime fingerprint 必须进入报告；
- shadow 失败时只能写失败报告或 quarantine，不能 fallback 到正式链。

### 先固定输入层，避免把所有不确定性混在一起

shadow adjudication 第一阶段不应同时验证真实 Extractor、真实 Resolver、真实 Adjudicator 和新 compiler。

建议至少分为两层：

```text
层 1：固定结构化声明 / 固定 resolver 输出
→ 验证 lifecycle adjudication + compiler 的机械确定性

层 2：真实 Extractor / Resolver 输出
→ 观察语义前端造成的误差、abstain 和 quarantine 行为
```

否则 shadow 出现差异时，无法判断问题来自：

- Extractor 漏提取；
- alias 解析错误；
- lifecycle 新建/匹配错误；
- adjudication 关系分类错误；
- observed/effective 时间排序错误；
- compiler 状态转移错误；
- assembler 预算或过滤错误。

### diff 分类必须预注册，而不是事后解释

shadow replay 最容易发生的一种“评测漂移”是：

> 先看到 diff，再把有利的 diff 解释成 expected improvement，不利的 diff 解释成 edge case。

因此，在真正跑 benchmark 前，必须在 spec 中写死：

- 哪些 diff 默认是 blocker；
- 哪些 diff 默认是 regression；
- 哪些 diff 可以是 expected schema change；
- 哪些 diff 必须人工 adjudication；
- 谁可以修改分类；
- 修改分类是否要产生版本化的规则变更；
- 未分类 diff 是否一律阻断。

建议最低限度的分类规则如下：

| diff 类型 | 默认处理 |
|---|---|
| `must_include` 从包含变为遗漏 | Blocker |
| critical active constraint 被错误置为 superseded | Blocker |
| `CONTESTS` 被直接折叠为 `SUPERCEDES` | Blocker |
| 低置信度 alias 被强制 merge | Blocker |
| 新链多保留一条旧非关键状态 | 待人工归因 |
| revival 从错误 inactive 变为 active | Expected improvement，仍须核对 gold |
| legacy fallback 结果变化 | 必须有迁移规则和 fixture 支持 |
| token 增长 | 非自动失败，但必须报告预算影响 |

---

## Stage03 readiness report 应接受的审查标准

项目 AI 提到已交付 readiness report，但没有给出结论细节。这个报告不应只是“文件都齐了”的 checklist，而应逐项回答下面的问题。

### RFC 决策是否已变成机器可测试规则

需要逐条列出并指向测试或 fixture：

- 谁生成 `lifecycle_ref`；
- 谁生成 `lifecycle_seq`；
- `observed_at` 和 `effective_at` 的字段来源、缺失策略、排序规则；
- late arrival 的回放行为；
- `SUPERCEDES / COEXISTS / CONTESTS / REVIVES / UNRELATED` 的状态后果；
- `CONTESTS` 的 assembler 可见性；
- resolver `abstain` 的 quarantine 处理；
- legacy fallback 的 schema version 边界；
- partial / conditional 的 Phase 1 最小支持范围；
- revival 是否通过新事件派生，而非改写旧 patch。

若某条目前还没有可执行测试，应标记为：

```text
NOT READY
```

而不是因为 RFC 已写到就标成已完成。

### 必须列出“进入实现仍未解决的问题”

真正有价值的 readiness report 应包含未决风险，例如：

- lifecycle ID 的生成格式与 collision 策略；
- effective time 缺失时的保守排序；
- 多个来源冲突但都具高置信度时的处理；
- legacy 与 lifecycle-v1 节点同桶相遇时的优先级；
- `partial` 是否仅允许原子命题拆分；
- quarantine 的自动恢复是否存在；
- shadow run 是否允许复用主链 resolver cache。

这些风险不需要在进入 shadow 实现前全部解决，但需要逐项有：

```text
owner
decision deadline
default-safe behavior
blocker / non-blocker classification
```

---

## 建议批准的下一轮任务边界

建议批准项目 AI 的下一步，但把任务名称从模糊的“实现 shadow adjudication 链”收紧为：

> **Stage04-A：实现无副作用、可确定性回放的 shadow lifecycle adjudication kernel。**

本轮允许做：

- shadow event/statement input adapter；
- shadow lifecycle resolver adapter；
- `adjudication_key` 分桶；
- `SUPERCEDES / COEXISTS / CONTESTS / REVIVES / UNRELATED` 关系输出；
- observed/effective 时间排序；
- shadow state compiler；
- fixture semantic replay runner；
- run-scoped shadow output；
- old-vs-shadow diff runner；
- benchmark 各 split 的只读执行器；
- 可再生报告与状态 hash。

本轮禁止做：

- 修改正式 `reconcile_patch.py`、`apply_patch.py` 或 assembler 默认路径；
- 改写已存在 raw、patch 或正式 graph state；
- 把 shadow 输出合并回正式图；
- 用人工补 patch 让 fixture 通过；
- 用 blind holdout 的失败案例调规则；
- 让 LLM 自由产生最终 `lifecycle_ref` 或 `lifecycle_seq`；
- 以“后续再解释”为由接受未分类 diff。

---

## 建议给项目 AI 的直接指令

> 批准进入 Stage04-A，但当前仅批准 shadow lifecycle adjudication 的旁路实现，不批准任何正式主链替换。
>
> 请先提交一份 Stage04-A implementation contract，明确 shadow 输入、输出目录、运行 ID、状态隔离、失败处理、runtime fingerprint、patch/graph/bundle hash 和禁止写入正式主图的机制。
>
> 然后实现 fixture semantic replay runner。该 runner 必须实际执行 shadow adjudication 与 shadow compiler，并逐 checkpoint 比较 expected relation、expected active set、expected quarantine、expected must_include；不得只验证 fixture 文件结构。
>
> benchmark v1 运行前，补充 split 审计：确认完整轨迹不跨 split、检查模板/alias 泄漏、报告各 split 的机制类型分布。blind holdout 不得参与规则调参。
>
> shadow diff spec 中须预先锁定 blocker、regression、expected schema change、manual adjudication 与 unexplained 五类差异的分类规则；任何 `must_include` 下降、critical false invalidation、`CONTESTS → SUPERCEDES` 自动坍缩、低置信度强制 alias merge，均为 blocker。
>
> “连续三次 PASS”仅作为确定性复现检查，不得作为主链替换的充分条件。主链候选切换前必须同时满足：fixture 语义通过、regression 无安全回退、blind holdout 达到预注册门槛、must_include recall 不低于 D1、critical false invalidation 为零或全部进入 quarantine、无未解释 blocker diff、shadow 输出完全未污染正式主图。
>
> 完成后请提交 Stage04-A report，逐 fixture、逐 split、逐 checkpoint 报告输入 hash、runtime fingerprint、state hash、bundle hash、diff 分类和未决风险；不要提交主链改动。

---

## 最终结论

这轮工作可以评价为：**工程治理和旁路准备合格，尚未形成 lifecycle 机制正确性的证据。**

项目 AI 的下一步方向是对的，但需要修正一个关键表述：

> 不是“跑通 8 个 fixture 和 benchmark、连续三次 PASS 后就进入主链替换”，而是“先证明 shadow kernel 在隔离条件下可确定性回放；再用冻结的 fixture、regression、holdout 和安全红线证明其语义收益；最后才申请主链候选切换。”




# 项目AI：
已按 [raw\projects\contextLedger\context_ledger_design_and_impliment_stage02.md](/D:/CCXXLESSON/contextledger/raw/projects/contextLedger/context_ledger_design_and_impliment_stage02.md:1850) 第 1850-1874 行评审 AI 的 Stage04-A 指令执行完毕。核心约束是：只做 shadow lifecycle adjudication 旁路实现，不批准主链替换。

**已交付产物**

1. **Stage04-A implementation contract**
   - [graph/projects/abu_modern/shadow_replay/stage04a_implementation_contract.md](/D:/CCXXLESSON/contextledger/graph/projects/abu_modern/shadow_replay/stage04a_implementation_contract.md)
   - 明确 shadow 输入/输出目录、run ID、状态隔离、失败处理、runtime fingerprint、patch/graph/bundle hash、禁止写入正式主图机制。

2. **Shadow lifecycle adjudication kernel（实际执行）**
   - [graph/projects/abu_modern/shadow_replay/scripts/shadow_lifecycle_adjudicator.py](/D:/CCXXLESSON/contextledger/graph/projects/abu_modern/shadow_replay/scripts/shadow_lifecycle_adjudicator.py)
   - [graph/projects/abu_modern/shadow_replay/scripts/shadow_compiler.py](/D:/CCXXLESSON/contextledger/graph/projects/abu_modern/shadow_replay/scripts/shadow_compiler.py)
   - [graph/projects/abu_modern/shadow_replay/scripts/shadow_bundle_builder.py](/D:/CCXXLESSON/contextledger/graph/projects/abu_modern/shadow_replay/scripts/shadow_bundle_builder.py)

3. **Fixture semantic replay runner**
   - [graph/projects/abu_modern/shadow_replay/scripts/fixture_replay_runner.py](/D:/CCXXLESSON/contextledger/graph/projects/abu_modern/shadow_replay/scripts/fixture_replay_runner.py)
   - 实际执行 shadow adjudication + compiler，逐 checkpoint 比对 expected relation、active set、quarantine、must_include，并生成 diff report 与 gate decision。

4. **8 个 fixture 回放结果**
   - 全部 `PASS`，两次回放 hash 一致（deterministic）。
   - 产物位于 `graph/projects/abu_modern/shadow_replay/runs/stage04a_*`。

5. **Benchmark v1 split 审计**
   - [graph/projects/abu_modern/benchmark/v1_freeze/split_audit_report.json](/D:/CCXXLESSON/contextledger/graph/projects/abu_modern/benchmark/v1_freeze/split_audit_report.json)
   - 确认：无轨迹跨 split、blind holdout 与 development 模板/alias 泄漏分数可接受、各 split 机制类型分布已记录。

6. **Shadow diff spec 更新**
   - [graph/projects/abu_modern/shadow_replay/shadow_replay_spec.md](/D:/CCXXLESSON/contextledger/graph/projects/abu_modern/shadow_replay/shadow_replay_spec.md)
   - 锁定五类差异：`blocker`、`regression`、`expected_schema_change`、`manual_adjudication`、`unexplained`；明确 `must_include` 下降、critical false invalidation、`CONTESTS→SUPERCEDES` 自动坍缩、低置信度强制 alias merge 均为 blocker。

7. **Stage04-A report**
   - [reports/stage04a_report.md](/D:/CCXXLESSON/contextledger/reports/stage04a_report.md)
   - 逐 fixture、逐 split、逐 checkpoint 报告输入 hash、runtime fingerprint、state hash、bundle hash、diff 分类和未决风险。

**当前 git 状态**

- branch: `phase1-lifecycle-stage02`
- HEAD: `943b3f7`
- base main / merge-base: `890219b`
- `git status --short`: 空
- `git diff --check`: 无错误
- 未修改任何主链文件（`reconcile_patch.py`、`apply_patch.py`、`build_context_bundle.py`、assembler、正式 `graph_state.json` 均未改动）

**结论**

Stage04-A 完成：shadow kernel 在隔离条件下可确定性回放，8 个 lifecycle fixture 语义通过，benchmark split 审计通过。但按评审 AI 的要求，**主链替换仍未批准**；下一步是 Stage04-B，把完整 benchmark v1 的 regression 与 blind holdout 跑通 shadow replay，并满足所有安全红线后才能申请主链候选切换。

# GPT-5.6-Terra：
## 总体裁定

**可以认可 Stage04-A 已完成，并批准进入 Stage04-B：冻结 benchmark v1 上的 shadow replay 评测。**

但这个批准仅表示：

> shadow lifecycle adjudication kernel 已具备隔离运行、机制级 fixture 回放、基础确定性验证和差异分类能力。

它**不表示** lifecycle 方案已在真实历史轨迹上证明收益，也不表示可进入正式主链替换。

项目 AI 的结论总体克制，尤其明确“主链替换仍未批准”，这一点是正确的。

## 本轮完成得好的地方

### 旁路边界看起来被遵守

报告明确声称未修改：

- `reconcile_patch.py`
- `apply_patch.py`
- `build_context_bundle.py`
- assembler
- 正式 `graph_state.json`

并且 shadow 输出位于：

```text
graph/projects/abu_modern/shadow_replay/runs/stage04a_*
```

这符合 Stage04-A 的核心要求：**新裁定语义只能在独立 run-scoped 目录中产生状态、bundle 和报告，不得污染正式图或历史 patch 链。**

不过，“未修改”不应仅靠口头说明。Stage04-B 开始前，应将以下命令输出写入报告或 CI 日志：

```bash
git diff --name-only 890219b..943b3f7
git diff --name-only 890219b..943b3f7 -- \
  graph/scripts/reconcile_patch.py \
  graph/scripts/apply_patch.py \
  graph/scripts/build_context_bundle.py \
  graph/projects/abu_modern/graph_state.json
```

第二条命令应为空；第一条命令应能显示新增内容均为 contracts、reports、shadow replay、fixture 或 benchmark 审计相关产物。

### fixture runner 已从“文件校验”升级为“语义执行”

这是本轮最重要的实质进展。

项目 AI 不再只是运行 JSON/schema validator，而是声称 runner 已执行：

```text
shadow adjudication
→ shadow compiler
→ checkpoint comparison
→ expected relation / active set / quarantine / must_include verification
→ diff report + gate decision
```

如果实现与报告一致，这意味着系统开始能验证以下关键问题：

- `REVIVES` 是否真的改变派生当前态；
- `CONTESTS` 是否没有被错误折叠为 `SUPERCEDES`；
- 多 lifecycle 是否不会互相误杀；
- late arrival 的处理是否符合已写死的规则；
- legacy fallback 是否有明确行为；
- alias 不确定性是否会正确 abstain 或 quarantine；
- state 和 bundle 是否可重放再生。

这比“RFC 写得完整”更接近真实工程证据。

### 差异分类已被预先固定

将 diff 固化为：

```text
blocker
regression
expected_schema_change
manual_adjudication
unexplained
```

并把下列情况定义为 blocker：

- `must_include` 下降；
- critical false invalidation；
- `CONTESTS → SUPERCEDES` 自动坍缩；
- 低置信度 alias 被强制 merge。

这是正确的安全姿态。尤其要坚持：

> **未分类 diff 默认不是“可接受差异”，而应是 `unexplained`，并阻断任何主链候选切换。**

### split 审计是必要动作

确认完整轨迹没有跨 split，能避免同一故事的前段进入 development、后段进入 holdout 的泄漏问题。

但报告里的“模板/alias 泄漏分数可接受”还不够严谨；“可接受”必须由预先写死的数值门槛、算法和审计输入来定义，不能由评测后主观判断。

## 当前仍未被证明的内容

### 8 个 fixture 全部通过，不等于真实语料上的正确性

fixture 是白盒机制验证：它们证明的是已知、人工定义的案例满足预期。

它们不能充分证明：

- 真实事件中的 entity/lifecycle 解析是否可靠；
- 非标准表述、含混指代、隐含条件下的关系判断是否正确；
- 从真实历史 patch/事件进入 shadow 输入适配器时是否发生语义丢失；
- 新 lifecycle 模型是否在真实轨迹上提升 invalidation precision/recall；
- 新模型是否造成更多 abstain 或 quarantine；
- bundle 的内容变化是否真正改善下游 Agent 行为。

所以 Stage04-A 应定性为：

> **shadow kernel 的机制正确性与隔离性初步成立。**

而不是“lifecycle 设计已验证”。

### “两次 hash 一致”只说明有限的确定性

两次回放 hash 一致是好信号，但它只能说明在当前输入、当前代码、当前运行环境下，至少重复两次未发生输出漂移。

Stage04-B 前应明确 hash 覆盖范围：

```text
input event / patch stream hash
fixture or case definition hash
runtime fingerprint hash
semantic relation output hash
shadow graph state hash
shadow bundle hash
diff report hash
```

还应至少做两类确定性验证：

1. **同一 checkout、同一输入、重复运行**：验证程序内确定性。
2. **干净 checkout 或独立工作目录、同一 commit、同一输入运行**：验证没有依赖未提交文件、缓存或本地环境残留。

若 shadow 链的某一段调用 LLM，则必须将它与机械核评测拆开：

- 固定结构化输入时，shadow adjudicator/compiler 必须完全确定；
- 接入真实 Extractor/Resolver 时，单独报告模型输出波动、abstain、quarantine 和下游错误归因。

不要把“机械核稳定”与“LLM 前端稳定”混成一个 PASS。

### Stage04-A report 中“逐 split”的表述需要澄清

报告说 `stage04a_report.md` “逐 fixture、逐 split、逐 checkpoint”报告结果，但同一报告又说下一步才是“把完整 benchmark v1 的 regression 与 blind holdout 跑通 shadow replay”。

这里有潜在表述歧义：

- 若 Stage04-A **尚未真正运行完整 benchmark shadow replay**，则报告不应写成“逐 split 报告 shadow 结果”；
- 它可以报告 split 审计、冻结状态、待运行 case 清单和预注册门槛；
- 但不能暗示 regression/holdout 已被实际评测。

建议在报告中清楚分为：

```text
Fixture execution results: executed
Benchmark split audit: executed
Development shadow replay: [executed / not executed]
Regression shadow replay: not executed
Blind holdout shadow replay: not executed
Adversarial shadow replay: [executed / not executed]
```

这很重要，因为评测状态必须可审计，不能让“审计过数据集”与“跑过数据集”混淆。

## Stage04-B 的正确目标

Stage04-B 不是“尽量跑出比旧链好的分数”，而是：

> 在不改变冻结 benchmark、冻结 diff 分类、冻结安全红线和不污染正式主图的条件下，测量 shadow lifecycle 链相对旧链的真实收益、退化和不确定性。

建议将本阶段命名为：

```text
Stage04-B: Frozen Benchmark Shadow Evaluation
```

其产物和验收必须与 Stage04-A 区分开。

## Stage04-B 开始前必须锁定的事项

### 锁定 benchmark 和运行配置

在首次跑 regression 前，提交或生成一份不可随意改写的 evaluation manifest，至少包含：

```text
benchmark version and split manifest hash
case IDs per split
gold annotation hash
metric script hash
old-chain output/state hash
shadow kernel commit SHA
runtime fingerprint
diff classification spec hash
gate rules version
run command
random seed / deterministic mode
timestamp
```

尤其应锁定：

- D1 `full_history_dump` 的具体实现；
- D2 `exact_surface_last_write_wins` 的具体实现；
- 当前正式旧链的基线；
- shadow 链使用的输入适配规则；
- `must_include` 的计算口径；
- critical constraint 的标注口径；
- 哪些事件或节点视为 quarantine。

如果这些在跑完后还能调整，评测结果就不具备可信的比较意义。

### 定义“模板/alias 泄漏可接受”的精确门槛

“可接受”必须替换为可验证规则。例如：

```text
- 同一 canonical entity 或同一 alias family 不得跨 development 与 blind_holdout；
- 同一事件模板的规范化指纹不得跨 development 与 blind_holdout；
- 若允许弱表层相似，则报告 Jaccard / embedding / n-gram 阈值与命中项；
- 任一人工判定的语义同构案例跨 split，视为 leakage；
- leakage 发现后，必须重新 split、重新生成 freeze manifest，并提升 benchmark version。
```

具体采用什么相似度算法可以由项目选择，但**门槛必须在评测前写死**。

### 固定 diff 的裁定流程

对于 `manual_adjudication`，必须明确：

- 谁进行人工裁定；
- 是否盲看“old/shadow”来源；
- 裁定使用什么 gold 或证据；
- 裁定结论如何记录；
- 是否能修改 benchmark gold；
- 若修改 gold，是否必须发布新 benchmark 版本并重新跑全套。

建议规则：

```text
manual_adjudication 不得直接计为 shadow 改进。
未裁定时，计入 unresolved；
任何 blocker 或 unexplained 都不得被手工“降级”为 expected_schema_change，
除非先修改版本化规则/fixture，再从头复跑相关评测。
```

## Stage04-B 的推荐执行顺序

### 先跑 development，但仅用于诊断

development split 可以用来发现：

- 输入适配遗漏；
- lifecycle key 分配异常；
- observed/effective 时间排序问题；
- `CONTESTS`、`COEXISTS`、`REVIVES` 的状态编译错误；
- shadow bundle 与预期 must_include 不一致；
- quarantine 过高或 silence failure。

但必须坚持：

> development 可用于诊断和规则修改；每次规则修改后，应提升 shadow implementation version，并重新跑 fixture 与 development。

不要在 development 跑完后直接看 holdout 再回头调规则。

### 冻结候选实现后，跑 regression

在 candidate commit 固定后：

- 重新跑全部 8 个 fixture；
- 跑 regression split；
- 对照旧链；
- 分类所有差异；
- 统计 invalidation P/R、active-set Set-F1、must_include recall、critical false invalidation、quarantine 变化；
- 生成逐 case、逐 checkpoint diff。

如果 regression 存在 blocker、未解释 diff 或安全红线退化，不应打开 blind holdout。

### regression 通过后，只运行一次 blind holdout 评测

blind holdout 只有 2 条，信息量有限，更应该防止被反复“试跑—调参—重跑”污染。

建议：

- holdout 运行前生成 sealed run manifest；
- 固定 candidate commit 与所有 hash；
- 运行一次；
- 若出现失败，记录为真实评测结果；
- 任何修改后必须视为新 candidate，最好新增或重新构造新的 holdout 才能声称独立泛化。

不建议反复查看这两条 holdout 的具体错误后持续调规则，再使用同一两条宣称泛化提升。

### adversarial split 应作为安全门，而非普通加分项

adversarial cases 的重点不是平均分，而是触发高风险错误：

- 低置信 alias 的强制合并；
- `CONTESTS` 错判替代；
- partial/conditional 被整体失效；
- late arrival 覆盖当前有效状态；
- revival 无目标或错目标；
- legacy 与 lifecycle-v1 混裁；
- must_include 被新筛选逻辑丢弃。

任何 adversarial blocker 都应阻断主链候选切换，即使总体 F1 提升。

## Stage04-B 的硬门槛建议

在现有项目红线基础上，建议将“可申请主链候选切换”的最低条件写成以下形式。

| 维度 | 最低要求 |
|---|---|
| 旁路隔离 | shadow 不写正式 raw、patch、graph state、bundle；证据完备 |
| 可复现性 | fixture 与 benchmark replay 在干净环境下 hash 一致 |
| fixture | 8 个已定义 fixture 全通过；新增修复对应的新 fixture |
| diff | 无 blocker；无 `unexplained` diff；所有 `manual_adjudication` 已留存裁定 |
| must_include | recall 不低于 D1，且不得低于正式旧链 |
| critical safety | critical false invalidation 为零；否则必须全部进入 quarantine 且不影响正式/候选 bundle |
| regression | 不出现预注册安全指标回退；核心指标改善或至少不劣于旧链 |
| blind holdout | 不低于预注册基线；结果仅作为有限证据，不夸大泛化 |
| adversarial | 无 blocker；`CONTESTS`、alias abstain、late arrival、revival 等安全用例无回归 |
| quarantine | 增量有归因；不得以大量 quarantine 换取表面 precision 提升 |
| 审计 | 所有输入、代码、输出、报告与裁定均带 hash 和 commit 指纹 |

其中，“核心指标改善”的阈值应在运行前定下。由于 holdout 很小，不建议设置看似精确但缺乏统计意义的微小提升要求；更合理的说法是：

- 安全红线必须不退；
- regression 上需有可解释、按错误类型分解的净改善；
- holdout 至少不能显示与该改善方向相反的严重回归；
- 没有证据时，结论应是“尚不足以切主链”，而不是“没有发现问题”。

## 对项目 AI 当前结论的修正

可以接受其最后一句的主旨，但建议将：

> “把完整 benchmark v1 的 regression 与 blind holdout 跑通 shadow replay，并满足所有安全红线后才能申请主链候选切换。”

修正为：

> “先在冻结 candidate 上完成 fixture 重跑与 regression shadow replay；只有在无 blocker、无未解释差异、must_include 与关键约束安全红线均不退化后，才可执行一次 sealed blind-holdout replay。随后结合 adversarial 结果、quarantine 变化、差异裁定与可复现性证据，申请主链候选切换评审；不得自动替换主链。”

“申请评审”比“进入替换”更准确。即使 Stage04-B 通过，也应先形成一个**候选切换包**，而不是直接改正式链路。

## 建议直接下达给项目 AI 的指令

> 批准 Stage04-A 完成，并批准进入 Stage04-B：Frozen Benchmark Shadow Evaluation。  
>
> 本阶段仍严格禁止修改正式 `reconcile_patch.py`、`apply_patch.py`、assembler 默认路径、正式 patch ledger、正式 `graph_state.json` 与正式 bundle。所有输出必须位于 run-scoped shadow 目录。  
>
> 在运行 benchmark 前，请先提交 Stage04-B evaluation manifest，冻结 benchmark split/hash、gold/hash、旧链基线、shadow candidate commit、runtime fingerprint、metrics 版本、diff spec hash、gate rules、运行命令与 deterministic 配置。  
>
> 请将 split audit 中“模板/alias 泄漏可接受”改为预先写死的算法、阈值、命中项和处理规则；并明确 Stage04-A 尚未执行的 benchmark split，不得将 split audit 表述为 benchmark replay 结果。  
>
> 执行顺序必须是：  
> 1. 固定 candidate 后重跑 8 个 fixture；  
> 2. 跑 development，仅用于诊断；规则变化后提升版本并重新跑 fixture/development；  
> 3. 冻结最终 candidate，跑 regression；  
> 4. regression 无 blocker、无 unexplained diff、must_include 不低于 D1 且关键约束无 false invalidation 后，执行一次 sealed blind-holdout run；  
> 5. 执行 adversarial 安全评测。  
>
> 每次运行需逐 case、逐 checkpoint 输出 input hash、runtime fingerprint、relation/state/bundle hash、旧新差异、diff 分类、quarantine 变化和 gate decision。  
>
> 连续重复运行仅用于证明确定性，不能替代语义正确性、泛化性或主链切换证据。最终仅可提交 Stage04-B evaluation report 和主链候选切换申请包；不得提交主链替换实现。

# 项目AI-KIMI2.7:
Stage04-B 已按评审 AI 的指令执行完毕。

**已修复的 3 个 fixture**
- `lc_legacy_migration`、`lc_revival`、`lc_two_lifecycles_no_kill` 现在全部 PASS。
- 修复点：调整了 `shadow_lifecycle_adjudicator.py` 中 `COEXISTS` 边的方向、把 `cancelled` 视为 terminal 状态、并在 adjudication_key 变化时正确发出跨键 `REVIVES` / `derived_from` 边。

**关键运行结果**
- 8 个 lifecycle fixture：全部 PASS，两次回放 hash 一致。
- benchmark split 审计：split integrity OK，blind holdout 与 development 隔离。
- `development`：BLOCK（1 blocker / 24 regressions）
- `regression`：BLOCK（2 blockers / 33 regressions）
- `adversarial`：BLOCK（0 blockers / 3 regressions）
- `blind_holdout`：**未执行**。按 Stage04-B 规则，regression 未过 gate 前不得启用 sealed holdout，已保留其完整性。

**已生成产物**
- [graph/projects/abu_modern/shadow_replay/stage04b_evaluation_manifest.json](/D:/CCXXLESSON/contextledger/graph/projects/abu_modern/shadow_replay/stage04b_evaluation_manifest.json) — 已填充分解哈希、runtime fingerprint、metrics_version 与各 split 运行结果。
- [reports/stage04b_report.md](/D:/CCXXLESSON/contextledger/reports/stage04b_report.md) — 完整 Stage04-B 评估报告。
- [graph/projects/abu_modern/shadow_replay/stage04b_main_chain_candidate_package.json](/D:/CCXXLESSON/contextledger/graph/projects/abu_modern/shadow_replay/stage04b_main_chain_candidate_package.json) — 主链候选切换申请包，状态为 `blocked`。

**隔离校验**
- 未修改 `reconcile_patch.py`、`apply_patch.py`、`build_context_bundle.py`、正式 `graph_state.json` 等主链文件。
- 所有 shadow 输出位于 `graph/projects/abu_modern/shadow_replay/runs/`。

**提交情况**
- 已提交：`afe0dc3` Stage04-B frozen benchmark shadow evaluation
- 已提交：`a0211a4` 删除临时测试文件
- 当前 `git status --short` 为空，HEAD 为 `a0211a4`，分支 `phase1-lifecycle-stage02`。

**结论**
- 主链候选切换 **未批准**：regression 仍未满足安全红线，blind holdout 也未解锁。下一步需要先改进 observation-to-event 适配器（特别是同一实体下多 claim / alias / 非失效场景的 adjudication_key 划分），再重跑 development → regression → sealed holdout。

# GPT-5.6-Terra：
## 项目AI指令：Stage04-B Blocker 归因与受限修复

确认当前 Stage04-B 结果为 **BLOCK**。不得执行 blind holdout，不得申请主链候选切换，不得修改正式主链、正式 patch ledger、正式 `graph_state.json`、正式 assembler 路径。

### 1. 先冻结失败证据，不立即改代码

将当前失败运行作为不可改写证据冻结，记录：

- `afe0dc3` 与 `a0211a4` 的完整 commit 指纹；
- 各 split 的输入 hash、runtime fingerprint、shadow state/bundle/diff report hash；
- 每个 blocker 和 regression 的 case ID、checkpoint、旧链结果、shadow 结果、gold 结果、diff 分类；
- 当前 fixture、benchmark、gold、metrics、diff spec、shadow kernel 的 hash。

不得通过修改已有 run report、gold、fixture expected output、split 定义或 diff 分类来消除失败。

### 2. 提交 Blocker Triage Report，先证明问题归因

新增旁路报告：

```text
reports/stage04b_blocker_triage_report.md
```

逐条分析全部 **3 个 blocker**，以及 regression 中按频率最高的至少 10 个代表性案例。每条必须包含：

```text
case_id
checkpoint_id
raw observation / source event
old-chain output
shadow adapter output
resolved entity_ref
resolved lifecycle_ref
adjudication_key
relation classification
expected gold state
actual shadow state
must_include impact
quarantine decision
root-cause layer
proposed minimal fix
```

`root-cause layer` 只能从以下枚举中选择：

```text
input_adapter
entity_resolution
lifecycle_resolution
adjudication_relation
observed_effective_time_ordering
shadow_compiler
bundle_assembly
gold_or_baseline_defect
unresolved
```

不得在没有逐例证据前，将问题笼统归因为“observation-to-event 适配器”。

### 3. 对“同一实体多 claim”建立明确的最小判定规则

在修改 adapter 前，补充一个版本化的旁路契约或 decision table，明确：

- **同一实体的多个 claim**：何时共享 `adjudication_key`，何时必须拆分；
- **alias**：何时可归并，何时必须 `abstain/quarantine`；
- **非失效场景**：何时输出 `COEXISTS` 或 `CONTESTS`，不得生成 `SUPERCEDES`；
- **跨 key revival**：触发条件、目标选择条件、找不到唯一目标时的保守行为；
- `cancelled` 作为 terminal 状态时，哪些事件可 `REVIVES`，哪些只能创建新 lifecycle；
- `COEXISTS` 边方向的语义定义，以及 compiler 是否依赖其方向。

该规则必须配套新增最小 fixture；不得只修改现有 8 个 fixture 以适配当前实现。

### 4. 修复范围严格限制为 shadow 旁路

允许修改：

- `shadow_replay` 下的 adapter、resolver adapter、adjudicator、compiler、bundle builder；
- shadow fixture、fixture runner、shadow report；
- benchmark 旁路执行脚本；
- 旁路 contracts/specs。

禁止修改：

```text
reconcile_patch.py
apply_patch.py
build_context_bundle.py
正式 assembler
正式 graph_state.json
正式 raw/patch ledger
benchmark v1 的 split 定义
blind_holdout 内容或 gold
```

任何新增或修改的规则必须在 development 轨迹和新增 fixture 上先被验证，不得先查看或运行 blind holdout。

### 5. 修复后执行顺序

每次候选修复必须使用新的 shadow implementation version / commit，并按以下顺序执行：

1. 重跑全部既有 8 个 fixture；
2. 运行新增 fixture；
3. 进行两次确定性回放，比较 relation、state、bundle、diff report hash；
4. 重跑 development；
5. 仅当 development 满足以下条件，才允许跑 regression：
   - 无 blocker；
   - 无 `unexplained` diff；
   - `must_include recall` 不低于 D1 且不低于旧链；
   - 无 critical false invalidation；
   - quarantine 增量可逐例归因，且不能以大规模 quarantine 换取表面 precision；
6. regression 同样满足上述条件后，才可申请一次 sealed blind-holdout run；
7. adversarial 必须在候选切换前无 blocker。

### 6. 关于现有 regressions 的处理要求

不得只报告总数。下一轮必须按根因层输出分布，例如：

```text
input_adapter: N
entity_resolution: N
lifecycle_resolution: N
adjudication_relation: N
compiler: N
baseline/gold defect: N
unresolved: N
```

并报告每类对以下指标的影响：

```text
invalidation precision / recall
active-set Set-F1
must_include recall
critical false invalidation
quarantine rate
```

若多数 regression 实际来自旧链与 shadow schema 的合法表达差异，必须保留为 `expected_schema_change` 的逐例证据；不得事后批量重分类。

### 7. 下一轮交付物

下一轮只提交以下内容：

- `stage04b_blocker_triage_report.md`；
- 最小 adjudication-key / multi-claim decision contract；
- 新增 fixture 及其语义回放结果；
- 修复后的 development replay report；
- 逐 case、逐 checkpoint diff 与根因分布；
- shadow 隔离证明与 git diff 文件清单；
- 明确 gate decision：`blocked` 或 `regression_ready`。

在 regression 尚未重新通过前，**禁止执行或查看 sealed blind holdout，禁止进行主链候选切换申请。**