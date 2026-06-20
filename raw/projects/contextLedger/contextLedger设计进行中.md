# [COMPACTED]

## TaskGraph 任务态上下文管理系统架构与工程实现文档

### 一、 项目背景与核心定位

#### 1.1 问题背景
在复杂 AI Agent 系统中，随着 Agent 能力的增强，上下文窗口的消耗速度急剧增加。现有的上下文管理策略（如 Claude Code 的 Compact 机制）主要围绕“消息顺序”和“Token 数量”进行梯度压缩，缺乏对**信息重要性**和**任务依赖关系**的显式判断。这导致在长程任务中，关键约束可能被意外压缩，或被推翻的旧方案再次被模型误用。

#### 1.2 核心定位
TaskGraph 不是通用聊天压缩器，也不是模型内部推理的还原。它是一个**任务态上下文管理机制**，旨在显式记录任务的目标、约束、事实、决策、工具结果、文件产物及被推翻的方案，并将其转换为结构化、主 LLM 可直接使用的 Context Pack。

**核心工程原则**：
*   **任务态启动**：无明确任务不建图，只服务目标明确、约束持续、方案演化的任务型对话。
*   **写入/读取分离**：写入侧解决“图怎么长出来”，读取侧解决“图怎么喂给主 LLM”。
*   **不可变事件日志**：`patch*.json` 是不可变事件日志，`graph_state.json` 仅是编译产物，禁止手改。
*   **检索与正确性解耦**：Slice Builder 只负责省 Token（尽力召回），正确性由全图级机械校验（`entity_ref` 精确匹配）兜底。

---

### 二、 核心数据模型 (Schema)

#### 2.1 节点类型 (Node Types)
系统将任务上下文抽象为以下节点类型：
*   `UserGoal`：顶层用户目标。
*   `Constraint`：稳定约束条件。
*   `Fact`：客观事实或环境状态。
*   `Decision`：架构或方案决策。
*   `OpenTask`：待办事项或子任务。
*   `ToolResult` / `FileArtifact` / `TestResultNode`：外部工具、文件或测试产生的证据节点。

#### 2.2 节点状态与标识 (Schema 升级核心)
为了支持长程运行和机械冲突检测，节点必须包含以下关键字段：
*   **`entity_ref` (稳定标识)**：用于精确匹配同一实体（如工单号 `TKT-2026-003`、文件路径 `src/main.py`、API 路径）。抽象原则或无明确实体的节点填 `null`。
*   **`state` (状态枚举)**：闭合枚举值，如 `open`, `blocked`, `in_progress`, `implemented`, `deployed`, `resolved`, `cancelled`, `unknown`。
*   **`status`**：节点在图中的生命周期状态，主要为 `active`（有效）或 `superseded`（已废弃/被推翻）。

#### 2.3 边关系 (Edge Relations)
节点间的依赖与演化关系，合法枚举包括：
`refines` | `depends_on` | `supports` | `invalidates` | `implements` | `serves` | `produces` | `derived_from`

#### 2.4 Patch 结构定义
每轮对话抽取的结果为一个 Patch，包含：
*   `new_nodes`：新增节点。
*   `updated_nodes`：更新的节点。
*   `superseded_nodes`：被本轮新信息推翻/废弃的旧节点 ID 及原因。
*   `new_edges`：新增的依赖边（包含关键的 `invalidates` 边）。

---

### 三、 系统架构与工程管线 (Pipeline)

#### 3.1 整体数据流
```text
[用户对话] + [graph_state.json] 
   ↓ (build_graph_slice.py)
[extractor_context_pack.json] (有限切片，O(1) 体积)
   ↓ (build_extractor_prompt.py)
[Prompt] (System Rules + Slice + Turn Text)
   ↓ (LLM Extractor)
[patch.json] (不可变事件日志)
   ↓ (reconcile_patch.py) -> 失败则重试或隔离
[apply_patch.py] (机械合并)
   ↓
[graph_state.json] (编译态)
   ↓ (graph_lint.py) -> 后置质检
   ↓ (context_pack_builder.py)
[Context Pack] -> 喂给主对话 LLM
```

#### 3.2 冷启动与长程运行
*   **第 1 轮（冷启动）**：`graph_state.json` 为空。跳过 Slice 阶段，直接将对话原文 + System Prompt 喂给 Extractor 生成初始 Patch，Apply 后产生初始图。
*   **第 2 轮及以后**：`graph_state.json` 作为输入参与 Slice 生成。对话在管线中被使用两次：
    1.  在 `build_graph_slice.py` 中作为**检索 Query**，从全图挑出相关旧节点。
    2.  在 Extractor 中作为**抽取原料**，结合 Slice 生成新 Patch。

---

### 四、 核心模块与脚本实现

#### 4.1 写入侧：图切片与 Prompt 组装
##### `build_graph_slice.py` (Graph Slice Builder)
*   **功能**：从完整图和当前轮对话生成有限切片，防止 Extractor 上下文超限。
*   **机制**：从对话提取符号（工单号、路径等）和状态信号，对全图 active 节点打分。
*   **分组与上限**：将节点分为 `root_goals`, `standing_constraints`, `active_open_tasks`, `recent_nodes`, `symbol_hits`, `conflict_candidates` 等分组，**每个分组设硬上限**（如 active_open_tasks=12），确保切片总体积为 O(1)，不随全图线性增长。
*   **输出**：包含 `_runtime.next_node_id`，采用扁平 `nodes` 列表 + `group_node_ids` 引用，消除节点多份副本。

##### `build_extractor_prompt.py`
*   **功能**：组装最终 Prompt。
*   **机制**：分离 System Prompt（固定规则，可缓存）和 User Message（动态切片+对话）。序列化前自动剥离诊断字段 `retrieval_trace`。支持 `single`、`split`、`api-json` 输出模式。

#### 4.2 校验与合并侧：门禁系统
##### `reconcile_patch.py` (前置校验器)
*   **定位**：Apply 前的机械门卫，只读不写，校验 Patch 与当前图的自洽性。
*   **核心逻辑**：
    *   **`entity_ref` 强判定**：若新节点与全图某 active 旧节点 `entity_ref` 相同但 `state` 互斥（如 `blocked` vs `deployed`），则强制要求 Patch 中必须包含 `superseded_nodes` 声明和 `invalidates` 边。缺一则报 Error。
    *   **弱兜底**：无 `entity_ref` 时，使用文本相似度/关键词 Jaccard 匹配，仅产出 Warning，不阻断。
*   **输出**：JSON 报告，有 Error 则退出码为 1（可接入 CI 拦截）。

##### `apply_patch.py` (写入器)
*   **定位**：纯机械合并，不做语义推理。
*   **执行顺序**：深拷贝原图 → 应用 `updated_nodes` → 标记 `superseded_nodes` → 添加 `new_nodes`（ID 冲突报错） → 添加 `new_edges` → 更新 `turn_counter`。

##### `graph_lint.py` (后置质检器)
*   **定位**：Apply 后运行，校验全图结构与语义不变量。
*   **核心检查项**：
    *   基础结构：节点 ID 重复、边端点缺失、Relation 不合法。
    *   语义不变量：非根 UserGoal 的 active 孤立节点；同 `entity_ref` 下互斥 active state 共存；`invalidates` 边指向的节点未标记 `superseded`。
    *   生命周期：OpenTask 内容显示已完成但 state 非 `resolved`；`resolved` 状态仍为 active。
    *   规范性：含工单号/路径但缺 `entity_ref` 的节点输出 Warning。

#### 4.3 读取侧：Context Pack Builder
##### `context_pack_builder.py`
*   **定位**：将 TaskGraph 转换为主 LLM 可直接执行任务的结构化上下文包。
*   **Context Pack 结构**：包含 `task_id`, `current_focus`, `goals`, `active_constraints`, `current_decisions`, `relevant_facts`, `open_tasks`, `superseded_history`。
*   **读取逻辑**：从当前焦点（最新 active OpenTask）出发，沿 `depends_on/implements/serves/refines` 向上游追踪；同时扫描 `invalidates` 边，将推翻方案放入 `superseded_history`。
*   **输出**：生成 `context_pack.json` (机器可读) 和 `context_prompt.md` (人类/LLM 可读)。

---

### 五、 关键机制设计

#### 5.1 冲突检测与失效传播 (Invalidation)
*   **问题**：新事实（如“接口已实现”）与旧事实（如“接口阻塞中”）矛盾时，Extractor 可能漏判。
*   **解决**：
    1.  **Extractor Prompt 层**：强制要求“事实一致性反向检查”，扫描 Slice 中的 `conflict_candidates`。
    2.  **Reconcile 兜底层**：通过 `entity_ref` 精确匹配，若发现状态互斥且 Patch 未声明 `invalidates`，直接拦截报错。
*   **失效传播**：约束变化时，下游节点标记为 `suspect` 或 `invalidated`，而非简单级联删除，保留演化痕迹。

#### 5.2 失败处理与重试策略 (Quarantine 隔离)
*   **重试机制**：若 `reconcile_patch.py` 报错（如漏判 supersede），将结构化 Error 报告回填至 Extractor Prompt，触发重试（上限 N=2~3 次）。
*   **失败隔离**：若 N 次仍不通过，或 `graph_lint.py` 发现历史遗留脏图，**拒绝合并**。将问题 Patch 隔离记录到 `quarantine/turn_xxx_failed.json`，或挂 `needs_review` 节点。
*   **核心原则**：宁可漏记一轮，不可污染主图。主图必须保持干净状态。

#### 5.3 可观测性与调试 (Task Context Debugger)
*   调试对象是管线中间产物，而非模型内心推理。
*   生成静态 `Task Context Debug Report`，包含：Conversation, Patches, Graph 演化, Context Pack 构建 Trace, Evidence 支撑链, Timeline。
*   **Context Pack Trace**：记录每条信息入选或排除的具体 Reason，帮助回答“主 LLM 看到了什么、为什么看到、旧方案为何被推翻”。

---

### 六、 高级特性扩展

#### 6.1 长期记忆层 (Memory Store)
*   **定位**：任务结束后，跨会话的长期任务记忆沉淀。
*   **流转**：TaskGraph → Memory Extractor → Memory Store → 召回 → 新 TaskGraph 种子节点 → Context Pack。
*   **记忆类型**：Fact, Preference, Constraint, Decision, OpenTask, Error。
*   **沉淀原则**：保留长期目标、稳定约束、有效决策、踩坑记录；不沉淀临时推理、大段工具输出、被推翻方案、闲聊。

#### 6.2 多 Agent 协作
*   **Context Pack 隔离**：Coordinator 基于 TaskGraph 为各 Worker 生成最小的 `Worker Context Pack`。Worker 只看到自己需要的上下文，避免上下文广播。
*   **单点合并**：Worker 执行后只返回 `Result + Graph Patch`，不直接修改主图。由 Coordinator 统一合并 Patch，处理身份/内容/依赖冲突。
*   **独立验证**：Verifier 独立验证 Claim + Evidence，返回 Verification Patch。

#### 6.3 外部证据节点化
*   工具调用、工具结果、文件修改版本、测试结果均作为独立节点（如 `TestResultNode` 包含命令/状态/输出引用）进入 TaskGraph。
*   形成“信息有来源，依赖有方向，文件有版本，结果能回查”的证据链，支持后续压缩时的优先级判断和错误回溯。

## 系统整体价值判断

**核心结论**：系统没有致命的内在逻辑缺陷，核心架构自洽正确。真正限制价值的不是逻辑问题，而是两个边界问题——机械核（reconcile/apply/lint）夹在两片模糊的 LLM 膜之间。

**设计优势**：
- 三层防护（reconcile 检查增量 vs 全图、lint 检查全量状态）非冗余，各抓不同错误。
- “LLM 只负责提议（patch），机械层负责裁决”是最有价值的工程直觉，将正确性落在确定性代码上。
- `entity_ref` 强判定 + supersede/invalidate 语义，能正确处理“X 曾经为真、现在为假”，优于主流向量记忆方案（flat RAG 只能召回新旧两条让模型困惑）。

**结构性真相**：
- 入口膜（Extractor）：机械层只能保证一致性，不能保证真实性。`entity_ref` 由 LLM 分配，若同一实体不同轮命名不一致（`ticket-123` vs `issue#123`），强匹配会退化。
- 出口膜（压缩成 memory_pack）：即使图完全正确，有损压缩可能丢失关键约束，导致对话 LLM 犯错。
- **端到端可靠性 = 最弱那层膜的可靠性，而非机械核的可靠性。**

**产品价值**：
- **不适用**：通用聊天记忆（竞争激烈，简单 RAG + 时间衰减足够）
- **有实质价值**：长程、有状态、约束会演化的 agentic 任务（跑几百轮、目标/约束/任务有生命周期）。这是向量记忆崩掉的地方，而 supersede/invalidate/entity_ref 正是为此而生。
- 定位：面向“长程有状态 agent”的记忆基础设施，而非通用记忆产品。

**下一步建议**：
- 将注意力从机械核转移到两端膜。
- 评测入口：同一实体的 `entity_ref` 是否稳定。
- 评测出口：图里的关键约束是否 100% 进入 memory_pack。

**一句话**：引擎是好的，逻辑是对的；能否成为有价值的产品，取决于是否愿意把精力从“打磨引擎”转向“管好引擎两端那两道模糊的进出气口”。

## 系统领域价值与产品战略判断

### 一、三个领域价值不均等

判断标准：领域对“旧事实被新事实推翻且推翻关系重要”的依赖程度越高，系统价值越大。

- **量化交易项目开发**（契合度最高）：决策被频繁推翻（目标指标、因子有效性、数据源迁移），`entity_ref + invalidate` 能确保过期约束不污染上下文。最适合作为首战领域。
- **律师业务**（技术契合，需定位调整）：事实与约束演化强，但竞争激烈。独特价值在于**决策审计轨迹**（记录哪个判断被谁、因何推翻），这是 flat RAG 做不到的。定位应为“可审计的决策演化”而非记忆。
- **医生诊断咨询**（技术最契合，产品最危险）：鉴别诊断本质是 supersede 链条。但医疗责任极高，系统只能保证“自洽”不能保证“真实”，一个抽取错误即可酿成事故。不适合早期切入。

**结论**：量化开发优先，律师以“审计”角度次之，医疗留待成熟+人工复核。

### 二、产品战略：插件 vs 自建智能体 vs SDK

用户担忧：智能体平台会内置上下文管理，插件难被接受。这一判断正确且更为尖锐——平台将上下文视为核心能力，不愿外包。

**出路**：平台内置的是“通用浅层记忆”，而本系统解决的是“长程、有状态、领域演化的深层状态”。两者不在同一层次，后者平台做不好也不愿做。

**三条路径评估**：
- **路径A（插件嵌入别人平台）**：天花板低，受制于人，不宜作为主路。
- **路径B（自建垂直智能体）**：逻辑正确，但上下文系统会退化为内部模块，价值被锁在智能体是否能卖出。难度从“基础设施”跃升到“垂直应用创业”。
- **路径C（推荐）**：做“领域状态层 / Agent Memory Backbone”，定位为 **SDK/框架**，服务自行搭建长程 agent 的开发者。不与平台抢终端用户，错位竞争；核心资产（机械核 + invalidate 语义）直接成为卖点。

**可执行顺序**：用量化交易场景做一个垂直 agent 作为“活体 demo”，证明三个月长程项目中状态不崩、旧约束正确失效。然后将底层抽成 SDK，对外开放。

### 三、核心定位切换

**最有价值的差异化**不是“上下文管理”（红海词），而是 **“长程状态下的事实失效与决策演化审计”** 。对外表达应从“我做上下文管理”转向 **“我让 agent 在跑几个月之后，依然知道什么已经不成立了”**。
## 长对话二次压缩方法论

**用户问题**：常规轮次压缩（保留逻辑链条、去对话体、加标题）会随轮次累积膨胀，不适合长期作为上下文。能否进行二次精简？

**GPT-5.5方案**：采用二次压缩，核心转换——轮次压缩回答“之前发生过什么”（保留过程），二次压缩回答“现在AI必须知道什么”（保留状态）。

### 三层压缩机制
1. **轮次压缩**：归档用，保留逻辑链条与标题，去对话体。
2. **主题级压缩**：按主题合并为项目摘要（目标、代码状态、关键决策、废弃方案、待办、关键文件）。
3. **当前上下文交接单**：面向下次继续工作，结构包括当前目标、有效状态、已完成修复、关键约束、废弃方案、未解决问题、重要文件修改点、下一步优先级。

### 二次压缩核心原则
- 从“历史叙述”转向“当前状态”：仅保留最终结论，删除猜测、试错过程、已不影响后续的内容及大段代码。
- 已解决问题只保留“现象—根因—修复”。
- 单独列出“废弃方案”防AI重犯错误。
- 代码只留文件名、函数名、职责和关键修改点。

### 推荐提示词

**首次生成交接单**：将已有压缩内容压缩为“当前上下文交接单”，只保留继续工作必要信息，删除过程细节和代码主体，固定结构输出。

**更新交接单**：基于“已有交接单+新增压缩内容”合并更新，状态变更的旧内容移至废弃方案，已解决问题移至已完成修复。

**结论**：轮次压缩用于归档，交接单用于继续工作。定期将长压缩稿重写为交接单，可大幅降低token消耗，保障对话连续性。
## 一般性对话压缩改进方案

**用户**：询问Claude-Opus-4.8对GPT-5.5二次压缩方案的意见。

**Claude-Opus-4.8**：基本认同“过程归档、状态续作”的方向，但指出三点不足并提供改进。

### 三个主要问题

1. **模板太技术化**：原模板（代码状态、文件等）适合调试，不适合一般性对话（课程构思、写作、方案权衡）。建议分两类：技术类保留原模板，一般类只三块——当前讨论什么、已达成共识、悬而未决的分歧。

2. **牺牲了“脉络”**：用户明确要求保留整体脉络，而“只留状态删过程”恰恰删除了脉络。纯状态有界但不保留脉络，保留脉络的压缩会自然增长。解决：保留一条“细脊柱”——每大阶段只留一行转折（如“先A，因X放弃，转B”），脊柱增长是次线性的，其余细节压成状态。

3. **周期性重写不能根治增长**：建议改用有界结构——**稳定区**（上限固定：目标、约束、已闭环结论、细脊柱）+ **滚动区**（只保留最近N轮详细压缩）。每加一轮，最旧轮次折叠进稳定区（只抽脊柱一行+新结论），总长度趋于常数。

### 额外提醒：压缩要“可重入”

AI在已压缩内容上再压缩时，常会反向展开或加说明，导致不降反升。提示词必须明确：输入若已是压缩稿，只做合并去重，禁止复述、扩写、加说明。

### 推荐通用提示词（要点）

二次精简生成可长期续用的上下文底稿。规则：已闭环内容只留结论；每大阶段保留一行转折说明；输入若已是压缩稿只合并去重不扩写；区分有效/被推翻/待解决；输出分稳定区与近况区；近况区旧轮次折叠进稳定区。

### 结论

GPT-5.5方向正确，但模板偏技术且牺牲脉络。真正需要的是“固定稳定区+滚动近况区”的有界结构，并保留一条次线性增长的脉络脊柱。

## 对话原稿保存与检索策略（含修正意见）


### 用户问题

一次压缩会存档，原稿是否需保存？折叠内容必要时是否应可检索？

### GPT-5.5方案

**核心建议**：原稿作为冷存档证据库，不默认喂给大模型；一次压缩稿作为过程档案；二次压缩稿作为日常上下文；折叠内容需可检索但仅按需召回。

**四层管理**：
1. **原稿**：证据库，用于摘要不确定、结论争议、还原细节时回查。日常不给AI。
2. **一次压缩稿**：过程档案，保留完整逻辑链，日常不喂给AI，仅当二次压缩不够用时回查。
3. **二次压缩稿**：日常默认使用（稳定区+脊柱+近况区）。
4. **折叠内容**：设计为可检索，但仅在摘要模糊、AI重犯旧错、需恢复细节、结论受挑战、重新做高质量压缩时回查。

**文件体系**：
```
project_context/
  current/context_base.md        # 当前二次压缩
  rolling/recent_rounds.md       # 最近N轮一次压缩
  archive/compressed/            # 一次压缩存档
  archive/raw/                   # 原稿存档
  index.md                       # 索引
```

**索引示例**：含当前底稿路径、一次压缩路径、原稿路径、关键词、状态。

**实用原则**：日常续作用二次压缩；细节补充用一次压缩；事实核验/原话还原/重新压缩用原稿。保存与喂给模型是两回事，文件体系先用文件夹+索引，量大了再考虑向量检索。

---

### Claude-Opus-4.8 修正意见

不完全赞同，提出三点：

1. **反对三份并存（原稿+一次压缩+二次压缩）**  
   一次压缩稿是原稿的有损派生品，有原稿作为真相源即可，必要时可重生成一次压缩。建议只留两份：原稿（真相）+当前底稿（工作）。除非频繁需要回顾讨论过程，否则不必单独归档一次压缩稿。

2. **原稿应分级保存，不全量冷存**  
   已验证闭环的问题（如RCON去斜杠、GBK编码），日后争议概率极低，原稿价值接近零，可深埋或丢弃。只有未闭环、有争议、结论可能被推翻的段落才值得保留原稿。

3. **检索不依赖独立索引，由脉络脊柱兼任**  
   单独`index.md`会与正文各自演化、对不上，增加维护负担。应让脊柱直接当索引：每条脊柱（阶段行为+转向原因）后挂指向原稿位置的锚点，回查时按脊柱定位到具体决策，而非全文关键词搜索。

**落地提醒**：用户实际用.md附件协作，非完整文件系统。建议：清晰命名+脊柱锚点，不为存储结构增加额外负担。
## 闭环内容处理与长期记忆治理方案

**用户指出**：闭环内容不应直接丢弃，而应转化为技能或长期记忆，便于今后复用。当前手动维护是探索阶段，未来应由专门的智能体来做这类工作。

**Claude-Opus-4.8修正**：承认上一轮“闭环段可深埋”说法错误。核心反转——闭环不是丢弃理由，而是晶化成技能的资格。正确逻辑：未决段留原稿，闭环段才是提炼技能的原料。

### 三种记忆类型区分
- **情景记忆**：如何一步步调通的叙事，闭环后价值衰减。
- **语义记忆**：事实与结论（如“RCON命令不带斜杠”），随时可能复用。
- **程序记忆**：可执行技能（如“RCON乱码排查步骤”）。

### 筛选闸门
- 闭环 + 通用 → **技能**（跨场景复用）
- 闭环 + 具体仍相关 → **长期记忆/语义事实**
- 闭环 + 一次性不再相关 → 可深埋
- 未决 → 原稿保持可取

**技能的本质**：脱离原始语境，不依赖完整经历即可使用（context-decoupled）。

---

## 四层记忆治理协议（GPT-5.5最终方案）

### 层一：当前上下文底稿（日常喂AI）
含稳定区（目标、约束、结论、废弃项、未解决问题）、脉络脊柱（每阶段一行：做什么→为何转向→结果，带锚点）、近况区（最近N轮要点）。目标：让对话继续，不无限增长。

### 层二：长期记忆/语义事实
保存可复用的事实（如“RCON命令不能带斜杠”），含适用范围、来源、状态。积累可复用经验。

### 层三：技能库
技能卡格式：触发场景、操作步骤、已验证经验、适用边界、来源。将经验晶化为程序记忆，实现代际传播。

### 层四：原稿证据库
冷存档，不日常喂AI。作为最终证据、可追溯来源、重新压缩材料、争议核验依据。

### 一次压缩稿处理
项目活跃期保留方便回查；阶段闭环后折叠。若原稿完整，一次压缩稿非必需。最终长期维护的是底稿、长期记忆/技能、原稿证据。

### 闭环内容四分流规则
- 通用可复用 → 技能库
- 项目内长期有效 → 长期记忆
- 影响当前推进 → 保留在当前底稿
- 一次性过程细节 → 冷存原稿

### 按需召回顺序
当前底稿 → 长期记忆/技能库 → 脉络锚点 → 一次压缩稿 → 原稿。

### 最小落地结构
三个文件或一个“项目记忆包.md”包含：底稿、长期记忆、技能库、原稿索引/锚点。

---

## 补充与精简建议（Claude-Opus-4.8）

### 补充A：晶化触发时机
- **被动触发**：某轮明确“问题已验证/方案已定”时当场判一次分流。
- **主动触发**：近况区每满N轮，做一次集中晶化，清出已闭环轮次。

### 补充B：逆流/降级规则
已写入长期记忆或技能库的内容若被后续推翻，必须能降级：标记【已失效】并注明被哪条结论取代，而非静默删除。技能卡与事实条目应有“状态”字段（已验证/已失效/待复核），失效条目移入原稿证据层留痕。

### 补充C：手动期的真正产物——显式判定规则
每做一次分流/晶化，把判定规则显式写下来（什么进技能、什么进记忆、什么算一次性）。避免养成隐性、个人化的判断习惯。这份显式规则集才是真正能交给AOS智能体的东西，档案只是副产品。

### 精简建议
将面向AOS的六个细分角色压缩为2–3个（如“维护底稿/晶化记忆与技能/档案与检索”），标注为远期，当前不落地。
## 压缩体系可行性评估与分阶段执行方案

### 一、总体判断

**方案设计上已完备，唯一失败风险在于维护成本导致弃用。** 建议分阶段启动，先跑最小闭环。

### 二、分阶段执行方案

**第一阶段（前两周）：单项目试点，最小文件集**
- 三个文件：`记忆包_项目名.md`（含底稿/长期记忆/脊柱）、`技能库.md`（全局唯一）、`raw_日期_主题.md`（原稿）
- 裁剪掉一次压缩稿和独立index.md
- 每次对话后约5分钟固定动作：原稿存raw → 用统一维护提示词更新记忆包
- 技能卡草稿需人工审核后粘入技能库
- 判定日志记录在技能库.md末尾，每次一行

**第二阶段（两周后）：三个指标体检**
1. 底稿长度是否趋于稳定（若仍线性增长，折叠规则未执行）
2. 长期记忆和技能库是否被实际调用（若从未使用，晶化闸门过松）
3. 是否回查过raw（回查找不到位置则加密脊柱锚点粒度）

### 三、四个实操问题解答

**1. 项目结构**：技能库和判定日志是全局资源，独立置于顶层目录；项目记忆包和raw跟随具体项目。

**2. 命名**：全局层可用`memory_governance/`；项目层`记忆包_项目名.md`；raw沿用`raw_日期_主题.md`。

**3. 记忆包组成**：记忆包.md实际包含四个部分（稳定区、脉络脊柱、近况区、长期记忆），其中近况区=最近3轮的一次压缩（详细压缩），本轮压缩稿是新产生尚未进库的增量，二者是存量与增量关系，不重复。

**4. raw文件粒度**：按主题/对话线一个文件，一个raw文件对应一条完整讨论线，内部用`## 轮次NNN`分节。

### 四、单轮数据流操作备忘

**完整生命周期**：原对话 → 一次压缩（临时桥稿，不落盘）→ 现有记忆包+本轮压缩稿→喂入维护提示词 → 模型同时做三件事（纳入本轮、折叠最旧轮+四分流、产出技能卡草稿）

**四分流规则**：通用可复用→技能卡草稿；项目内长期有效→长期记忆；仍影响推进→稳定区；一次性细节→不保留。

### 五、定稿版维护提示词要点

附件一为现有记忆包全文（存量），附件二为本轮压缩稿（增量）。规则：只合并去重更新；本轮压缩稿原样纳入近况区；近况区超过3轮时折叠最旧轮（脊柱追加一行+四分流+删除详细压缩）；新旧冲突时旧条目标记已失效并注明取代；只输出更新后记忆包全文+技能卡草稿。

### 六、试点三件套

- `记忆包_项目名.md`（顶部贴数据流备忘+四节模板）
- `技能库.md`（顶部贴维护提示词+末尾判定日志）
- `raw_日期_主题.md`（每轮随手存）

## 记忆治理仓库目录结构推荐

**用户**：计划新建`memory_governance`仓库，统一管理多个项目（taskgraph、abu_modern等）的记忆，询问最佳目录结构。

**Claude-Opus-4.8推荐**：

```text
memory_governance/
├── README.md                     # 使用说明+数据流备忘
├── 技能库.md                     # 全局唯一，跨项目复用（末尾含判定日志）
├── _templates/                   # 全局模板
│   ├── 维护提示词.md
│   └── 记忆包模板.md
└── projects/                     # 项目资产层
    ├── taskgraph/
    │   ├── 记忆包_taskgraph.md
    │   └── raw/
    └── ...（其他项目同结构）
```

**设计原则**：技能库跨项目复用放根目录；加`projects/`层隔离全局与项目资产；raw单独子文件夹，锚点路径为`raw/raw_日期_主题.md#轮次NNN`。

---

## 三个决策与风险防范

**用户**：询问是否加`projects/`层、全局技能库是否可行、是否建`skills_local.md`。

**Claude-Fable-5**：
- 加`projects/`层：要（项目多，平铺混乱）
- 全局技能库：成立，但需技能卡加【来源】字段，两周体检时看是否被来源项目之外用过
- 不建`skills_local.md`：避免预防性设计，真正需要时再加

**三个风险与对策**：
1. **单一事实源扩散**：备忘只住README，提示词只住`_templates/`，数字只在提示词出现一次
2. **全文重写静默丢内容**：提示词加“未涉及的节和条目逐字保留”，人工核对时只数行数（新≥旧）
3. **raw文件名锚点不可变**：日期为主题线开始日，建立后永不改名

---

## 最终结构与铁律

**确定结构**：README为唯一备忘之家，技能库含【来源】字段，`_templates/`为规则唯一真源，项目资产住`projects/`。

**四条关键改动**：
1. README唯一备忘，数字以维护提示词为准（单向引用）
2. 技能卡新增【来源】字段（用于两周体检验证跨项目复用）
3. 维护提示词补“存量逐字保留+行数核对”
4. raw文件名定死为起始日，永不改名

---

## 收口稿核心内容

**README**：三铁律——单一事实源（规则只住提示词）、存量逐字保留+行数核对（新≥旧）、raw文件名永不改名。锚点格式：`raw/raw_<起始日>_<主题>.md#轮次<NNN>`。

**维护提示词**：每累计3轮触发折叠；不扩写；存量逐字保留（只允许追加`【已失效】`）；方法论级进全局技能库（须含【来源】）；记忆包四节（概览/长期记忆/脊柱/开放问题）。输出前自检行数≥上一版（失效除外）。
## 折叠入库操作澄清

**用户问题**：每次折叠需提供哪些输入文件；为何输出只有记忆包全文，技能如何形成。

**Claude-Opus-4.8解答**：

**输入文件（每次折叠）**：当前项目记忆包全文（存量）、本轮raw段落（或未归档时的原始对话）、全局技能库全文（参照判断晶化）。注意`_templates/`下的规则文件不喂给模型，规则已写在提示词中。

**输出改为双产物**：产物A为记忆包全文（必出，全文重写+行数核对），产物B为技能追加片段（仅当有方法论级内容时输出，采用append模式不重写全文防静默修改）。新技能卡必须含`source:`字段，并在脊柱锚点后附轻指针。

---

## 输入文件清单修正

**用户指出**：`_templates/maintenance_prompt.md`是折叠操作指令本体，必须喂给模型。

**Claude-Opus-4.8承认错误，确认正确输入为4份**：维护提示词（规则指令）、一次压缩后的对话内容（桥稿或raw原文）、当前项目记忆包全文（存量）、全局技能库全文（参照）。建议将清单补入README。

---

## 记忆治理方案收尾总结与问题澄清

**关键设计变更**：早期“近况区（最近3轮）”已取消，“3轮”含义从保留窗口变为折叠节奏——每满3轮触发折叠，记忆包只存状态和脊柱，细节全在raw。

**问题1：raw存什么**：存原始对话原文（按主题线一个文件，内部`## turnNNN`分节），不能存有损压缩稿。数据流中`raw`为证据库。

**问题2：是否先做一次压缩**：是，但作为临时桥稿不落盘。完整折叠动作：取3轮raw原文→做标准轮次压缩（桥稿）→4份输入喂模型→获取双产物→桥稿丢弃。3轮极短时可跳过桥稿直接喂raw。

**问题3：存量长压缩稿如何处理**：做一次性“首场折叠”冷启动。将附件存为raw（标注“原稿未存”），4份输入中“新料”即整份附件，记忆包用空壳，产出第一版记忆包和首批技能卡。之后进入标准节奏。

---

## “支流与水池”架构

**用户新想法**：记忆治理应同时具备“支流”（时间维度的情景记忆，回答“进行到哪了”）和“水池”（领域知识积累的语义记忆，回答“关于X知道什么”）。

**Claude-Fable-5确认**：对应记忆科学的二分。现有体系已含水池胚胎（技能库、长期记忆），但目前仅为平面列表，未来需引入wiki结构（概念页、交叉引用、lint检查）。

**触发信号**：某项目长期记忆超二三十行、领域事实跨项目重复、概念查询需求出现时再升格为wiki。当前仅需在README末留远景钩子。核心价值是“折叠作为河口”的输运机制。
## 记忆治理方案矛盾修复

**用户指出**：`maintenance_prompt.md`引用了README中的锚点格式和铁律，但LLM看不到README导致断链；prompt声称结构来自模板但LLM不知道模板；空模板与空记忆包矛盾。

**Claude-Opus-4.8承认根因**：prompt必须自包含，LLM执行所需规格都应内联进prompt。

**修复方案**：
1. 重写`maintenance_prompt.md`为自包含版：锚点格式、四节结构、执行规则全部内联；首场记忆包不存在时按四节定义从零生成；删除所有对README/template的引用。
2. 删除`memory_pack_template.md`（冗余，结构唯一权威已移至prompt）。
3. 调整README铁律1：LLM执行规格只住`maintenance_prompt.md`，面向人内容只住README，互相引用只指路不复制。

---

## memory_pack是否可直接作为对话上下文

**用户询问**：`memory_pack.md`是最终提交给对话LLM的上下文，还是需再加工。

**Claude-Opus-4.8回答**：`memory_pack`是“准上下文”，大部分可直接喂，但**脊柱节需加工**——其中的锚点（`raw/...#turn003`）是给人和检索系统的，对话LLM无法访问raw文件，属死字符串。应保留脉络文字、去掉锚点。

**推荐投影方案**：从memory_pack生成只含“概览+长期记忆+开放问题+脊柱（去锚点）”的临时只读上下文，不落盘，与折叠流水线隔离。建议将规则写入README数据流节，区分两种读者（折叠LLM看全四节、日常对话LLM看投影）。
## 两种上下文机制的价值比较

**用户问题**：比较 TaskGraph 与 memory_pack 两种上下文管理机制的价值。

**Claude-Opus-4.8 纠正**：用户标注反了——附件1（`maintenance_prompt.md`）是 memory_pack 折叠式机制；附件2（`extractor-prompt-template.md`）才是 TaskGraph 机制。

### 两者差异：结构化 vs 叙事化

- **TaskGraph（高精度，低完整度）**：通过节点、边、`entity_ref`、`state`、`invalidates` 做机械化事实失效。最强能力——长程状态下精确判定“什么约束被哪个新事实推翻”。但抓不住软性知识（偏好、方法论、叙事语感），且对抽取错误脆弱。
- **memory_pack（高完整度，低精度）**：保留叙事、软知识、方法论晶化、有可读性。但存在“误差单调累积”，失效依赖 prose 级标记，无机械保证。

### 判断

**更有价值的核心是 TaskGraph 的 `entity_ref + invalidates` 机制**——因为它稀缺、难复刻、可辩护，是蓝海差异点。折叠式叙事压缩满大街都是。

**但 TaskGraph 单独无法成为独立产品**。它是“发动机”，memory_pack 是“驾驶舱”。

### 风险与建议

当前并行维护两套独立有损压缩系统，会产生**双源漂移**（图说“方案 A 已 superseded”，memory_pack 却写着“采用方案 A”）。这不是双保险，是双倍漂移面。

**正确架构**：定主从，而非二选一。
- **TaskGraph 为事实与状态的唯一权威源**（什么成立、被推翻、任务状态），因为只有它有机械失效保证。
- **memory_pack 退化为派生视图 + 软知识容器**：渲染叙事（脊柱锚点指向图节点）+ 存放图装不进的软料。不再独立判定事实失效。

让“同一条事实的正文只在一处”，将 memory_pack 规则6（长期记忆与技能库只能一处持有正文）提升到架构层。
## TaskGraph与memory_pack的结合策略

**用户问题**：两者如何结合？还是分开开发，以后再结合？

**Claude-Opus-4.8 结论**：**现在分开开发，但立刻钉死边界契约；数据流先不接。** “分开发以后再说”和“现在就接”都错误，正确路径是：人分开、接口定死、线以后连。

### 为什么现在不接线

两个系统都还在变动中（TaskGraph 的 `invalidates` 可靠性未验证，memory_pack 的“3次折叠”关卡未过）。两个未定型系统耦合，调试成本相乘，无法定位错误源。必须等其中一个（如 TaskGraph）独立稳定后，才能接线。

### 为什么“以后再说”同样危险

分开期间，两套系统各自从 raw 独立判定事实失效，会各自长出硬化的事实裁决逻辑（图用 `invalidates`，memory_pack 用 `[DEPRECATED]`）。跑几个月后，两者成为两个互相打架的真源，合并将变成重写+对账，成本极高。漂移不是合并时才发生，而是分开期间一天天累积的。

### 现在零成本钉死契约

在 `maintenance_prompt.md` 中加一条责任保留声明：长期记忆节对“某事实是否仍成立”不做独立终审，事实失效的权威判定将迁移至 TaskGraph。折叠器内的 `[DEPRECATED]` 属过渡脚手架，不得在其上叠加复杂冲突消解逻辑。此举防止折叠器过度投资终将被拆的逻辑。

同时约定 join key：两套系统都已有锚点（图的 `n_NNNN`，包的 `raw/xxx#turnNNN`），共享 raw 锚点 + turn 号作为连接键，将来映射才可接。

### 将来接线的方向

节奏天然决定上下游：extractor 每轮跑（高频），折叠器每 3 轮跑（低频）。合并后折叠器不再从 raw 判定事实（图已做），而是：渲染图增量为可读叙事（脊柱锚点指回图节点 ID），并从 raw 捞取图装不进的软知识（偏好、方法论、skills）。图是事实与状态的真源，memory_pack 退化为派生视图 + 软知识容器。

### 扣动扳机的关卡

用与“3次折叠”同构的硬关卡：当图的 `invalidates` 在多次真实冲突上正确触发（状态互斥迁移准确捕获，无漏废误废），才将折叠器接到图上。在此之前接线，会把图的 bug 无声灌进 memory_pack。

**一句话**：人和逻辑现在分头跑，契约和 join key 现在焊死，数据流等图失效机制验过关再连。分开期间防止各自长出第二真源——靠一段责任声明掐死在萌芽里。
## 责任声明位置与项目合并判断

### 一、责任声明加在哪

**约束**：`maintenance_prompt.md` 开头有“封闭世界铁律”——执行者不能参照外部文档，因此声明不能写成“去参照 TaskGraph”，必须是一条**自足的负向边界**（告诉折叠器“不归你管，别在上面用力”），而非“你要去和图对齐”。

**位置**：建议**新增规则 9**，不塞进规则 2。规则 2 的职责是“别静默丢条目”，`[DEPRECATED]` 仅是工具；要约束的是 `[DEPRECATED]` 的**语义边界**，与规则 2 的留痕职责不同，混入会使其变浑。

**草案**：
> **9. 职责边界（事实失效不在本场终审，过渡声明）**。本折叠器对“某条事实/状态是否仍然成立”**不做独立终审**；该权威判定终将上移至独立的结构化事实层。当前长期记忆节内的 `[DEPRECATED]` 标记属**过渡脚手架**，仅用于满足规则 2 的留痕与本场独立运行，**不得在其上叠加复杂的冲突消解/状态机/多版本裁决逻辑**。遇到事实疑似失效时按规则 2 留痕即可，不自行扩展裁决规则。

“TaskGraph”替换为“独立的结构化事实层”，使声明在封闭世界内仍成立，执行者无需看见那一层也能执行。

### 二、是否合并文件夹

**概念层**：是，它们是一个产品的两个组成部分——图是发动机（事实与失效真源），memory_pack 是驾驶舱（派生视图 + 软知识池）。

**物理层**：合并，但形式是 **monorepo + 清晰分模块**，而非混杂文件。形态：项目根下含 `taskgraph/` 和 `memory_governance/` 两个独立模块，并新开 `contracts/` 存放两者共同依赖的契约——raw 格式规范、锚点格式、turn 号约定、join key 定义、以及责任边界声明的权威出处。

**合并的承重理由**：给契约唯一的家，防止两套独立仓库各自维护规范导致“两个规范真源”的漂移。

**三条不越的边界**：
1. **合并目录 ≠ 合并代码逻辑**：人和逻辑分头跑、数据流等图验过关再连，完全不变。
2. **不提前耦合数据流**：过早耦合代码，调试成本相乘的警告依然有效。
3. **不必这周搬文件**：先以共享 markdown 立起 `contracts` 并指定唯一出处，物理合并是便利性优化而非正确性前提。

**一句话**：概念上它们早就是一个项目；物理上该并成 monorepo，但承重理由是“让契约只有一个家”；并目录的同时，代码隔离和“图先验过关再连数据流”的纪律一条不松。

## monorepo命名与Git迁移方案

**命名建议**

首选：**`contextledger`**（上下文账本）。"ledger"自带逐条记账、可追溯、有真源的含义，对应整套设计的灵魂——图是权威账本，memory_pack是视图，脊柱锚点是审计链。备选：`longgraph`（长程+图）、`statekeep`（状态守护）、`recall-engine`。

模块结构：`contextledger/graph`（原taskgraph）和 `contextledger/governance`（原memory_governance），`contracts/` 和 `raw/` 放根目录。

---

**Git方案：必须纠正的认知错误**

用户原计划：新建monorepo根目录不`git init`，两个子仓各自独立搬迁。这个方案有问题——根目录下的 `contracts/`、`README.md`、`raw/` 将无人做版本管理，而 `contracts/` 恰恰是最需要单一真源、最该被严格追踪的部分。

**三种方案对比：**

| 方案 | 做法 | 优缺点 |
|---|---|---|
| **A（不推荐）** | 根不init，子仓独立 | 搬迁零摩擦，但 contracts/ 裸奔 |
| **B（可用但重）** | Git submodule | 保留独立历史，但操作繁琐，迭代期负担重 |
| **C（推荐）** | `git subtree` 合并为单一历史 | 一个.git管全部，契约与代码原子提交，历史完整保留 |

**建议采用方案C**。既然两模块已被定为一个产品的组成部分，共享一份契约，那么在同一个git历史中原子地一起提交是自然的延伸——改契约同时改两端代码，一个commit搞定，不会出现“契约更新了但某个仓还在旧版本”的漂移。这与一路强调的“防双真源漂移”是同一原则，只是落到版本层。

**落地命令**：
```bash
git init contextledger
cd contextledger
git subtree add --prefix=graph <taskgraph路径> main
git subtree add --prefix=governance <memory-governance路径> main
# 新建 contracts/、README.md、raw/ 并正常 git add
```

**一句话**：名字用 `contextledger`；但别做“根不init、两子仓独立”——那会让 `contracts/` 裸奔。用 subtree 合并为单一历史，把“版本各自独立”这个历史包袱一并放下。
## monorepo命名与Git迁移方案

**命名建议**

首选：**`contextledger`**（上下文账本）。"ledger"自带逐条记账、可追溯、有真源的含义，对应整套设计的灵魂——图是权威账本，memory_pack是视图，脊柱锚点是审计链。备选：`longgraph`（长程+图）、`statekeep`（状态守护）、`recall-engine`。

模块结构：`contextledger/graph`（原taskgraph）和 `contextledger/governance`（原memory_governance），`contracts/` 和 `raw/` 放根目录。

---

**Git方案：必须纠正的认知错误**

用户原计划：新建monorepo根目录不`git init`，两个子仓各自独立搬迁。这个方案有问题——根目录下的 `contracts/`、`README.md`、`raw/` 将无人做版本管理，而 `contracts/` 恰恰是最需要单一真源、最该被严格追踪的部分。

**三种方案对比：**

| 方案 | 做法 | 优缺点 |
|---|---|---|
| **A（不推荐）** | 根不init，子仓独立 | 搬迁零摩擦，但 contracts/ 裸奔 |
| **B（可用但重）** | Git submodule | 保留独立历史，但操作繁琐，迭代期负担重 |
| **C（推荐）** | `git subtree` 合并为单一历史 | 一个.git管全部，契约与代码原子提交，历史完整保留 |

**建议采用方案C**。既然两模块已被定为一个产品的组成部分，共享一份契约，那么在同一个git历史中原子地一起提交是自然的延伸——改契约同时改两端代码，一个commit搞定，不会出现“契约更新了但某个仓还在旧版本”的漂移。这与一路强调的“防双真源漂移”是同一原则，只是落到版本层。

**落地命令**：
```bash
git init contextledger
cd contextledger
git subtree add --prefix=graph <taskgraph路径> main
git subtree add --prefix=governance <memory-governance路径> main
# 新建 contracts/、README.md、raw/ 并正常 git add
```

**一句话**：名字用 `contextledger`；但别做“根不init、两子仓独立”——那会让 `contracts/` 裸奔。用 subtree 合并为单一历史，把“版本各自独立”这个历史包袱一并放下。
## memory-governance 模块命名评估

**用户问题**：原独立项目 `memory-governance` 的名称作为合并后的模块名是否合适。

**Claude-Opus-4.8 结论**：作为独立项目名没问题，但作为合并后的模块名不合适——问题在于用整体使命命名了局部。

`memory-governance`（记忆治理）描述的是整个产品在做的事——管理长程记忆、决定事实失效。但合并后，真正做“治理/裁决”的核心是 `graph`（事实与失效的真源），而原 `memory-governance` 已降级为“驾驶舱 + 软知识池 + 派生视图”，不再是裁决者。继续叫 `governance`，等于让交出裁决权的模块顶着“裁决”之名，且会与 repo 整体命名造成混淆。

**改名建议**：描述它实际职能——渲染图增量为叙事 + 承载软料。建议 `pack/`（产物叫 memory_pack，名实相符），与 `graph/` 配对形成“事实层 + 叙事层”的对子。备选：`digest`、`narrative`。

**连带洞察**：若采用 subtree 合并单一历史，旧独立项目名作为“项目名”本就不再存在，只剩子目录名，命名问题自然消解。纠结名称本身，常是“独立项目”心智惯性的残留信号。

**一句话**：`memory-governance` 描述的是整个产品的使命，不适合命名已被降级的子模块；改叫 `pack/` 与 `graph/` 配对，名实相符，同时清理残留心智。
## 下游消费环节的装配设计

**用户问题**：graph和pack最终要为下游LLM提供上下文，它们（及可能的wiki检索）如何结合？

**Claude-Opus-4.8 核心判断**：装配的本质不是拼接，而是**带预算的选择性检索 + 冲突时的权威序**。拼接会导致上游压缩的成果在下游被原样恢复，毁掉整个产品。

### 装配的四层分层（按新鲜度与触发方式）

1. **常驻基线（push）**：pack的概览、硬约束、核心偏好，每轮必进，小且稳定。
2. **任务相关当前状态（从graph拉取）**：根据本轮问题查询相关子图节点及其经失效裁定后的当前状态。query驱动，不整本喂。
3. **软知识（从pack拉取）**：与本轮相关的skills、方法论、偏好，按相关性检索。
4. **深检索（从wiki/RAG拉取）**：仅当前三层不足时触发，最静态、最按需。

新鲜度梯度：图最新（每轮）→ pack次之（滞后≤2轮）→ wiki最静态。

### 冲突处理：用内容切分消除，而非权威序兜底

朴素方案是“图赢包输”（权威序），但更干净的解法是让**冲突面不存在**：图独占事实与状态，pack独占软料（偏好/技能/叙事）。这即pack规则6“任一知识只在一处持正文”的跨存储延伸。装配时去对应位置拉取，零冲突。

### 一个开放式岔路：pack叙事层是否直接喂给下游？

倾向答案：**不直接喂**。事实由图的结构化当前状态供给（最新、无歧义），pack叙事更多供人阅读和当索引。下游LLM从pack拿的只是图装不下的软料。此设计可暂存为开放问题，不必现在拍死。

### 脊柱锚点的复用

为审计自审建的脊柱（锚点+反向指针）在装配时可复用为**检索索引**：装配器用当前问题沿脊柱导航到对应节点ID和raw段。一结构两用，投资更值。

### 装配器本身是第三个模块

装配由当前query驱动，需先有**路由步**：将query解析为检索意图（查哪些节点、要哪些技能、是否下探wiki）。新的`assembler/`模块是query时运行的只读组件，与`graph/`、`pack/`并列，待图失效机制验过关后再建。

### 纪律

想远但别现在建assembler。它消费的是图的当前状态——若图失效机制未验过关，装配会满怀信心地把错误事实喂下游且无声。一切等`invalidates`在真实冲突上验对再做。

## 目录结构调整建议

当前结构已有不错的骨架，但存在三个需要调整的隐患：

### 隐患1（最重）：raw 数据有两个家，违反单一真源

`graph/original_dialogs/` 和 `pack/projects/taskgraph/raw/` 都存放原始对话。raw 是整个体系的最底层真源，必须只有一份。

**修正**：
- 根目录建 `raw/`，所有原始对话归到此处
- `graph/original_dialogs/` → 改为存放指向根 `raw/` 的指针/ID
- `pack/projects/*/raw/` → 同理改为指针，不存正文

### 隐患2（心智残留）：`pack/projects/` 里包含 `taskgraph` 和 `memory_governance`

在 contextledger 中，`taskgraph` 已是 `graph/` 模块本身，`memory_governance` 已是 `pack/` 模块本身。它们不是 pack 要服务的“项目”，不该被列在 `pack/projects/` 下。真正被服务的下游项目是 `abu_modern`、`career_consult`、`minecraft_agent`、`open_skywing_lab` 等。

**修正**：从 `pack/projects/` 删除 `taskgraph` 和 `memory_governance` 两个自指条目。

### 隐患3：根目录缺 `contracts/` 和 README

根布局应为 `graph/ + pack/ + raw/ + contracts/ + README.md`。当前 `contracts/` 缺失，这是图与包之间契约的唯一真源。

**修正**：建 `contracts/` 目录（占位即可），补齐根 `README.md`。

### 先确认 git 状态（避免嵌套仓库吞文件）

请执行以下命令并告知结果：
```bash
git status
ls graph/.git pack/.git   # 检查子目录是否还有独立 .git
```

如果 `graph/` 和 `pack/` 内仍有独立 `.git`，而根也已 init，则根仓库会把它们当作 gitlink，文件不会被真正追踪，`contracts/`、`raw/`、根 README 将裸奔。

### 动作顺序

1. 查 git 状态（避免嵌套仓库风险）
2. 根目录建 `raw/`，合并两处 raw 数据，模块内改存指针
3. 从 `pack/projects/` 删除 `taskgraph` 和 `memory_governance`
4. 根目录建 `contracts/`（占位）和 `README.md`

## raw迁移检查与contracts契约内容

**用户**：确认 `graph/.git` 和 `pack/.git` 不存在，无嵌套仓库。已在根下创建 `raw` 目录，将原 `pack/projects` 移入 `raw`，尚未删除 `taskgraph` 和 `memory_governance`，请求给出 `contracts` 内容。

**Claude-Opus-4.8**：先暂停确认——`pack/projects` 内不只有 raw 对话，还有 `memory_pack.md`（派生叙事）。若整体迁移，派生物已混入 `raw`，违反“raw 只存真源”原则。请核验并修正。但不阻塞 contracts。

**contracts 结构**：
```
contracts/
  README.md
  01_raw_anchors.md   [STABLE]
  02_ownership.md     [STABLE]
  03_graph_schema.md  [PROVISIONAL]
  04_assembly.md      [PLACEHOLDER]
```

**各文件核心内容**：
- **01_raw_anchors.md**：raw ID 格式 `<project>/<session>/<turn>`，指针指向 raw 不复制正文，raw 只读且不可回改。
- **02_ownership.md**：知识正文只能存在于三处之一——graph 节点（事实/状态）、pack 叙事（概览）、pack 技能（软料），其余只能引用不得重述。判断口诀：“是否会被后来事实推翻”——会则归 graph，否则归 pack。
- **03_graph_schema.md**（PROVISIONAL）：定义节点与边结构、失效语义（invalidates），标注验证完成前下游不得依赖。
- **04_assembly.md**（PLACEHOLDER）：装配环节前置闸——等 03 的 invalidates 语义在真实冲突上验证通过后方可启用。

**底层纪律**：01 和 02 为 STABLE（已验证），03 标 PROVISIONAL，04 写死前置闸——将“失效机制未验不过不装配”写入契约本身。

## compact 中间层设计评估与契约建议

**用户**：根目录下已创建 `raw/projects/` 存放原始资料，计划再创建 `compact/projects/` 存放一次压缩结果，作为 pack 环节的原料，以 raw 为唯一事实源。

**Claude-Opus-4.8**：方向对——raw 太杂，中间垫一层降噪是工程上正确的。但必须钉死契约，否则 compact 会变成体系里的**第四个真源**。

### 核心铁律：compact 是派生物，不是真源

唯一安全定义：**compact = f(raw)**，纯函数产物，可随时删掉、由 raw 重新生成。不持有 raw 里没有的信息。

危险的诱惑：人在做“一次压缩”时手痒注入判断、加注释、做取舍——这些信息 raw 里没有，于是 compact 偷偷成为真源，且与 graph/pack 抢归属。规则：压缩只做无损或可逆的降噪（删寒暄、去重复、结构化），**不得注入新信息、不得下判断**。判断属于 graph 或 pack，不属于 compact。

### 具体隐患：反向指针断链

contract 01 规定 graph 节点 `source` 指向 `(raw_id, span)`。但管线变成 raw → compact → 抽取，抽取读 compact 拿到的 span 是 compact 的偏移，不是 raw 的偏移。脊柱锚点断了。

**解法**（二选一）：
- **推荐**：compact 每段携带源自的 `raw_id + raw span`，抽取时将 compact span 翻译回 raw span 再写入节点。反向指针永远落到 raw，compact 对下游透明。
- 备选：节点 source 同时记 `compact_id` 和 `raw_id`，但真源判定仍以 raw 为准。

### 幂等要求

“一次压缩”必须记录：源 raw_id 列表、压缩 prompt 版本、模型、时间。能重放才叫派生物，否则就是偷偷固化的真源。

### 契约更新

新增 `contracts/05_compact.md [PROVISIONAL]`，要点：
1. compact = f(raw) 纯派生物
2. 不得注入新信息或判断
3. 必须带可重放 manifest

同时在 01_raw_anchors.md 中补充：经 compact 抽取时，span 必须翻译回 raw 偏移。

**一句话**：加 compact 层是对的（给 pack 降噪降成本），但必须钉成 raw 的纯函数派生物——不准注入判断、必须带可重放 manifest、反向指针一律翻译回 raw 偏移；否则它会变成双真源的还魂版，脊柱当场断链。

## 目录命名与结构建议

两个问题：**compact vs pack 确实会混，改名；raw/projects 和 compact/projects 不是臃肿，是对齐，该保留。**

### compact → normalized

`compact` 和 `pack` 语义边界会糊——两者都是中间加工层，名字又都以 p... 开头，时间久了目录会混淆。建议改名为 **`normalized`**，精确表达你做的事（去寒暄、去重复、结构化=归一化），且隐含“无损/可逆”，与“不得注入判断”的契约呼应。`distilled` 也可，但听上去像已提炼精华，易诱人塞判断。

### 两层 `projects` 不是冗余

`raw/projects/X/...` 对应 `normalized/projects/X/...`，**路径同构是可追溯、可重放的物理保证**。给定一个 normalized 文件，把路径中 `normalized` 换成 `raw` 就能找到源文件。削掉这个同构，就要靠额外索引维护映射，反而更脆。重复的是骨架，不是内容。

**真正该防的臃肿**是预建大量空的占位目录。解法：按需生成——某个项目过了 normalized 环节，才在 `normalized/projects/` 下长出对应目录。

**一句话**：`compact` 改名为 `normalized`；两层 `projects/` 保留并行骨架，目录按需生成而非预建空壳。
## raw 与 normalized 目录定位

**用户问题**：raw 和 normalized 是否都只有 `projects/` 文件夹，还是也需要存放其他文件？

**Claude-Opus-4.8**：两者职责不同，答案不同。

### raw/：几乎只有 projects/

raw 是 append-only 真源，美德是“笨”。理想状态下 `raw/` 下只有 `projects/`。唯一值得加的是一个 `_index`（或 `manifest`），登记每个 raw 文件的 ID、会话、写入时间、只读校验和（hash）。作用是防篡改证据——文件被手抖修改，hash 对不上立刻暴露。除此之外 raw 不该有任何加工痕迹，连 README 都尽量克制。

### normalized/：顶层只有 projects/，但每个叶子目录带 manifest

normalized 是 f(raw) 的产物，契约要求可重放。因此每个产物需附带“我是怎么生成的”元数据。**manifest 应贴身存放**：`normalized/projects/X/session/` 中，降噪内容与 `*.manifest.json`（含源 raw_id 列表、压缩 prompt 版本、模型、时间、raw→normalized 的 span 映射）放在一起。不把 manifest 抽到 `normalized/manifests/` 另立一摊，否则又制造一个需要路径匹配的平行结构。

### 拦一个风险

不要把脚本、config、log 塞进 raw 或 normalized。这些属**工具层**（归 `graph/scripts/` 或根 `tools/`）。两层只装“数据 + 证明数据可信/可重放的最小元信息”。一旦脚本和日志混入，就得重新分辨哪些是数据哪些是工具。

**一句话**：raw/ 下基本只有 projects/，顶多加一个 `_index` 作防篡改证据；normalized/ 顶层也只有 projects/，但每个叶子目录里“内容 + manifest”成对存放。别把 manifest 抽成平级目录，更别把脚本/log/config 塞进这两层——工具归工具区。
## 合并设计评估与当前行动点

我已阅读完taskgraph和memory_governance的完整背景材料。一个之前没说透但对合并最关键的点：**taskgraph和memory_governance不是两条平行管线被硬并到一个repo，它们其实共享同一层——normalized。** 这才是干净合并的支点。

### 两条管线在normalized层汇合

- **graph侧**：raw → slice → extractor → patch → reconcile → apply → graph_state → context_pack（每轮，高频）
- **pack侧**：raw → 一次压缩桥稿 → maintenance_prompt折叠 → memory_pack + skills（每3轮，低频）

合并后在normalized上对齐：
```
raw → normalized → ┬→ [graph extractor管线]（高频，锚回raw）
                   └→ [pack折叠管线]（低频，锚回raw）
```
normalized成为两个消费者共享的“降噪后输入”，两边都锚回raw。

### 概念归宿映射

| 原memory_governance概念 | contextledger归宿 |
|---|---|
| `记忆包_X.md` | `pack/projects/X/memory_pack.md`（派生视图，非真源） |
| `技能库.md` | `pack/skills.md`（软料，contract 02合法正文持有处） |
| `_templates/维护提示词.md` | `pack/_templates/`（pack私有规则） |
| `raw_日期_主题.md#轮次NNN`锚点 | 改用contract 01的raw_id（两套锚点必须统一） |
| “一次压缩桥稿”（不落盘） | **被normalized取代** |
| `[DEPRECATED]`事实失效逻辑 | 过渡脚手架，接图时退役（已由规则9/contract 02约束） |

### 三件现在必须拍的事

1. **raw/污染**：原`memory_governance/projects/X/`同时装有`记忆包_X.md`（派生）和`raw/`（真源）。搬入raw/后，需确认是否存在`raw/projects/X/记忆包_X.md`和`raw/projects/X/raw/...`嵌套。正确收尾：`raw/projects/X/`只留原始对话，`记忆包_X.md`拎回`pack/projects/X/`，嵌套的`raw/`拍平上来。

2. **锚点方案统一**：pack用的是`文件名#轮次NNN`，contract 01用的是`<project>/<session>/<turn>`。contract 01是STABLE、是合并权威，pack的脊柱锚点须折算到raw_id。

3. **normalized取代一次压缩桥稿**：桥稿当年做成“不落盘”是因为没有干净的持久中间层；现在normalized就是这一层。但桥稿“保留逻辑链条”带了判断，而normalized契约钉死**不准注入判断**——那份判断要上移到折叠步（maintenance_prompt），normalized只做无损降噪。

### 纪律

上面是**目标态**。数据流现在不接——图的`invalidates`没在真实冲突上验过关之前，pack折叠步不能消费图。在那之前两条管线各跑各的，只把normalized层和contract焊好。

请确认重构后的实际目录树（尤其raw/和pack/下），我据此给出精确搬移清单和contracts需补的条目。

## contextledger 目录结构反馈与修正

**整体评价**：结构骨架对路，raw嵌套已解、normalized按需生成、contracts五份到位。但存在**一个会埋雷的定位错误**和两个待补的洞。

---

### 主要问题

#### 1. `normalized/projects/abu_modern/raw_2026-06-12_compression.md` 放错层（最急）

该文件同时踩三条线：  
- 它是“首场折叠冷启动”的一次压缩稿，177KB 远大于 `raw/projects/abu_modern/` 六个 turn 的总和，**不可能从这些 turn 降噪而来**。  
- normalized 契约要求 `f(raw)` 且可删除重生成，但此文件**没有 raw 源，无法再生**，属于不可再生的来源记录。  
- 放在“可安全删除的派生层”是危险的——一旦有人清空 normalized 重跑，该文件永久丢失。

**修正**：移回 `raw/projects/abu_modern/`（或对应的正确项目），文件头加一行“本文件为一次压缩稿，原稿未存，按 source-of-record 对待”，名称去掉 `compression` 歧义。  
**前置确认**：该文件主题是否确实属于 abu_modern？若属于 taskgraph，则归属需调整。

#### 2. `pack/` 缺少 `projects/`，memory_pack 无家可归

`pack/` 目前只有全局资产（`_templates`、`skills.md`、`README`、`MAINTENANCE_LOOP`），缺 `pack/projects/X/`。按目标态，每个项目的 `memory_pack.md` 应落在 `pack/projects/X/memory_pack.md`。不用预建空壳，但第一次折叠时落点必须是 `pack/projects/X/`，不可混入 raw 或 normalized。

#### 3. `contracts/05_nomalized.md` 几乎空壳且文件名拼错

文件仅 99 字节，装不下三条核心契约（`normalized=f(raw)`、不得注入判断、必须带可重放 manifest 及 span 翻译回 raw 偏移）。  
**修正**：改名为 `05_normalized.md`，补写完整契约；同时确认 `01_raw_anchors.md` 是否已含“经 normalized 抽取时 span 必须翻译回 raw 偏移”条款，缺则补上。

---

### 补充说明

- **`raw/projects/taskgraph` 和 `memory_governance` 不必删**：它们存放设计两个系统时的原始对话日志，是合法 raw 证据。之前“删自指条目”针对的是 `pack/projects/` 下的模块自指，raw 层不受影响。
- **`temp/`**：确认已在 `.gitignore` 中且无正式产物滞留。若有未归位的真源，需拎出。

---

### 动作清单（确认归属后执行）

1. 核对 177KB 文件的主题归属 → 移入 `raw/projects/<正确项目>/`，加头部定性声明，从 normalized 删除。
2. 补写 `05_normalized.md`（改名+补全三条契约+span 翻译条款）。
3. 核验 `01_raw_anchors.md` 是否包含 span 翻译回 raw 偏移的条款，缺则补。
4. 记录 memory_pack 落点规则：`pack/projects/X/memory_pack.md`，待第一次折叠时按需创建。
5. 确认 `temp/` 已 gitignore 且无真源滞留。

## 契约检查与设计对话归档建议

**用户问题**：将contracts所有文件附上，并询问`temp/`中存放的本项目设计对话是否应移至根目录下新建有意义名称的文件夹。

**Claude-Opus-4.8 核心建议：不要新建根目录，而是将它变为一个“被服务的项目”**

设计这套系统的对话本身，正是一段长程、有状态、约束不断演化的对话。它不应逃逸在raw/normalized/graph/pack纪律之外，而应是**第一个dogfood项目**：

```
raw/projects/contextledger/<session>/turn_NNN.md
```

与abu_modern、minecraft_agent完全平级，走相同管线。好处有三：
1. **不破契约**：新开`temp/`或`design_notes/`等于在四层之外再造一个“家”，违反“每份内容只有一个家”的铁律。
2. **自举验证**：这些设计对话中充满真实冲突（compact改名、raw嵌套、177KB归属），是验证`invalidates`语义最理想的零成本测试集。
3. **呼应设计基调**：手动期的产物将来是交给数字员工的SOP，让系统管理自己的诞生史，正是理念最干净的落地。

**建议动作**：把`temp/`中的内容归入`raw/projects/contextledger/`，原来`raw/projects/taskgraph`和`memory_governance`作为前身对话保留，不删。

---

**契约文件检查结果**

| 文件 | 状态 |
|---|---|
| `01_raw_anchors.md` | ✅ span翻译回raw偏移已补上 |
| `02_ownership.md` | ✅ 扎实完整 |
| `03_graph_schema.md` | ⚠️ PROVISIONAL，占位合理 |
| `04_assembly.md` | ⚠️ PLACEHOLDER，占位合理 |
| `05_nomalized.md` | ❌ 几乎空白（仅99字节），且文件名拼错 |

**必须修正的契约问题**：
1. `contracts/README.md` 表格漏列05，需补上一行。
2. 文件名 `05_nomalized.md` 拼错 → 改为 `05_normalized.md`。
3. `01_raw_anchors.md` 末尾“经 **nomalized** 抽取”同样拼错。
4. `05` 内容需补全为完整的normalized派生契约（定义、三条铁律、manifest存放规则）。

**一句话**：设计对话别开新根目录，归入 `raw/projects/contextledger/` 作dogfood项目，同时修掉README漏列05、两处 `nomalized` 拼错、05契约几乎空白这三个洞。
## graph 文件夹结构修正

用户纠正：graph 不是跨项目的全局图，而是每个项目各自独立的图，项目之间不会交叉。因此 graph 里确实需要 `projects/`，但需区分哪些归项目、哪些留根共享。

**分界原则**：是否绑定某一张具体图。

- **进 `graph/projects/<project>/`（每项目一份）**：`graph_state.json`（图真源）、`graph_slices/`、`reports/`、`quarantine/`、`patches/`、`run/`（若记录运行态）
- **留根下（全局共享，与具体图无关）**：`scripts/`、`tests/`、`prompts/`（模板）、`graph_state.seed.json`（新图初始化模子）、`env`、`.gitignore`、`README.md`

**预期布局**：
```
graph/
  scripts/  tests/  prompts/          # 全局机件
  graph_state.seed.json               # 新图模子
  README.md  .gitignore  env
  projects/
    abu_modern/
      graph_state.json                # 该图真源
      graph_slices/ reports/ quarantine/ patches/
    open_skywing_lab/
      graph_state.json
      ...
```

**纪律**：按需生成，不预建空壳（与 normalized 一致）。根下旧的 `graph_state.json` 需归位到对应项目，勿留作“假全局图”。`raw_id = <project>/<session>/<turn>` 前缀保留，作用改为**溯源锚点**（指向 raw 源），而非图内分区。

## ContextLedger 项目架构与设计白皮书

### 一、 项目定位与核心价值
**ContextLedger（上下文账本）** 不是通用的聊天记忆压缩器，而是面向“长程、有状态、约束会演化的 Agentic 任务”的**领域状态层 / Agent Memory Backbone**。
*   **核心痛点**：在长程任务中，旧事实被新事实推翻（如工单状态变更、方案被替代、约束失效）。传统的向量记忆（Flat RAG）或简单的摘要压缩无法处理“事实失效”，会导致过期约束污染上下文。
*   **核心价值**：通过结构化的 `entity_ref` 与 `invalidates` 语义，实现**长程状态下的事实失效与决策演化审计**。让 Agent 在运行数月后，依然精确知道“什么约束已经不成立了”。
*   **产品战略**：不与智能体平台竞争“通用浅层记忆”，而是作为 SDK/框架，服务自行搭建长程 Agent 的开发者。首选切入领域为**量化交易项目开发**（决策被频繁推翻、因子演化强），其次为**律师业务**（决策审计轨迹）。

### 二、 双系统融合架构 (Monorepo)
项目由两个核心模块组成，共享底层数据与契约，采用 Monorepo 架构管理。
1.  **Graph（事实与状态层 / 发动机）**：高精度、低完整度。事实与状态的**唯一权威裁决源**。通过节点、边、`entity_ref`、`state`、`invalidates` 做机械化的事实失效判定。
2.  **Pack（叙事与软料层 / 驾驶舱）**：高完整度、低精度。退化为**派生视图 + 软知识容器**（偏好、方法论、技能）。不独立判定事实失效，仅渲染图增量为可读叙事，并存放图装不进的软料。

**融合纪律**：
*   **定主从**：Graph 是事实真源，Pack 是派生视图。同一知识的正文只能在一处持有（规则6）。
*   **防漂移**：在 Pack 的折叠规则中加入“职责边界声明”，明确事实失效的权威判定上移至 Graph，Pack 内的 `[DEPRECATED]` 仅为过渡脚手架。

### 三、 核心数据模型 (Graph Schema)
#### 1. 节点 (Node)
*   `node_id`: 唯一标识。
*   `type`: `UserGoal | Constraint | Fact | ToolResult | Decision | FileArtifact | OpenTask`
*   `content`: 节点内容。
*   `entity_ref`: **核心机制**。稳定实体标识（如工单号、API路径、文件路径）。用于机械精确匹配，判定“同一实体”。无法确定则填 `null`。
*   `state`: 归一化状态枚举（`open | blocked | in_progress | implemented | deployed | resolved | cancelled | unknown | null`）。
*   `status`: `active | superseded | done`。

#### 2. 边 (Edge) 与失效语义
*   `relation`: `refines | depends_on | supports | invalidates | implements | serves | produces | derived_from`
*   **事实失效 (Invalidation)**：当新事实使旧节点不再成立（状态互斥），旧节点必须标记为 `superseded`，并添加 `{ "source": "新ID", "target": "旧ID", "relation": "invalidates" }` 边。

### 四、 数据管线与目录结构
#### 1. 物理目录结构 (单一真源原则)
```text
contextledger/
├── raw/               # 唯一事实真源 (Append-only，不可回改)
│   └── projects/      # 原始对话/资料
├── normalized/        # 纯函数派生层 (f(raw)，无损降噪，可安全删除重生成)
│   └── projects/      # 附带 manifest 和 span 映射
├── graph/             # 事实与状态层
│   ├── scripts/       # 全局机械校验脚本
│   ├── prompts/       # Extractor 模板
│   └── projects/      # 每个项目独立的图状态 (graph_state.json, patches/, slices/)
├── pack/              # 叙事与软料层
│   ├── _templates/    # 折叠规则
│   ├── skills.md      # 软知识
│   └── projects/      # 每个项目的 memory_pack.md
└── contracts/         # 跨模块契约 (唯一真源)
```

#### 2. 三条核心管线
*   **写入管线 (高频/每轮)**：`Raw` → `Normalized` → `Graph Slice` → `Extractor (LLM)` → `Patch` → `Reconcile` → `Apply` → `Graph State` → `Lint`
*   **折叠管线 (低频/每N轮)**：`Raw` → `Normalized` → `Maintenance Prompt (LLM)` → `Memory Pack`
*   **装配管线 (按需/Query驱动)**：`Graph State` (当前状态) + `Pack` (软料) → `Assembler` → `Context Pack` → `主 LLM`

### 五、 核心工程机制 (长程运行保障)
为解决 LLM 抽取的模糊性与长程图膨胀问题，系统采用 **“LLM 提议，机械层裁决”** 的三层防护架构。

#### 1. Graph Slice (O(1) 上下文控制)
*   **定位**：只负责省 Token，**不负责正确性**。
*   **机制**：根据当前轮对话提取符号（工单、文件），从全图检索相关节点。每个分组（如 `active_open_tasks`, `conflict_candidates`）设有**硬上限**，确保 Extractor 的上下文规模恒定，不随全图线性增长。

#### 2. Reconciliation Pass (事后校验 / 事前拦截)
*   **脚本**：`reconcile_patch.py` (Apply 前运行，只读)。
*   **机制**：用全图数据复核 Patch 的自洽性。核心依赖 `entity_ref` 精确匹配。
*   **强判定**：若 Patch 新增节点与全图 Active 节点 `entity_ref` 相同且 `state` 互斥，但 Patch 未声明 `superseded` 和 `invalidates`，直接报 **Error** 阻断。
*   **弱兜底**：无 `entity_ref` 时，仅做文本相似度 Warning。

#### 3. Graph Lint (全图质检)
*   **脚本**：`graph_lint.py` (Apply 后运行，只读)。
*   **机制**：检查全局不变量。包括：孤立 Active 节点、`invalidates` 指向未 `superseded` 的节点、同一 `entity_ref` 下互斥的 Active State、OpenTask 生命周期异常等。

#### 4. 失败处理与隔离 (Quarantine)
*   **有界重试**：Reconcile/Lint 失败时，将结构化 Error 回填 Prompt 重试（上限 N=2~3 次）。
*   **失败隔离**：超限仍失败，则拒绝合并，将 Patch 隔离至 `quarantine/` 目录。**宁可漏记一轮，绝不污染主图**。

### 六、 契约体系 (Contracts)
`contracts/` 目录是防止双系统漂移的唯一权威约束：
1.  **01_raw_anchors.md [STABLE]**：Raw ID 格式规范；经 Normalized 抽取时，Span 必须翻译回 Raw 偏移，确保脊柱锚点不断链。
2.  **02_ownership.md [STABLE]**：知识正文归属权。判断口诀：“是否会被后来事实推翻？”——会则归 Graph，否则归 Pack。
3.  **03_graph_schema.md [PROVISIONAL]**：节点/边结构与失效语义定义。验证完成前下游不得依赖。
4.  **04_assembly.md [PLACEHOLDER]**：装配环节前置闸。等 Graph 失效机制在真实冲突上验证通过后方可启用。
5.  **05_normalized.md [STABLE]**：Normalized 必须是 `f(raw)` 纯派生物；不得注入新信息或判断；必须带可重放 Manifest。

### 七、 Extractor Prompt 设计原则
*   **分离缓存**：System Prompt 包含固定的 Schema 规则与生命周期判定逻辑（支持 Prompt Caching）；User Prompt 仅注入当前 Slice 与本轮对话。
*   **事实一致性反向检查**：强制要求 LLM 扫描 Slice 中的 `conflict_candidates`，若发现 `entity_ref` 相同且 `state` 互斥，必须输出 `superseded` 和 `invalidates`。
*   **命名契约**：严格规范 `entity_ref` 的命名（如文件用原文，组件用 snake_case，未分配工单填 `null`），防止因命名不一致导致强匹配退化。

## ContextLedger 架构评审

### 总体判断

这是一个**思想成熟度远高于一般"agent memory"项目**的设计。你识别出了正确的硬问题——长程任务中事实的撤回（retraction）而非仅仅是压缩与检索——并在该确定的地方坚持确定性裁决、在该认怂的地方制度化认怂（契约门控、PROVISIONAL/PLACEHOLDER标记）。

但它的可靠性目前架在一根**脆弱且唯一的支柱**上，而那根支柱本身由LLM浇铸。以下是我认为最关键的五个结构性风险。

---

### 一、致命依赖：`entity_ref` 的"确定性"是幻觉

你的机械裁决层全部押在 `entity_ref` 精确匹配上。但 `entity_ref` 由 Extractor LLM 分配，而非来自确定性系统。

真实场景中，同一实体可能被命名成：
- `src/auth/login.py` vs `auth/login.py`
- `TKT-2026-003` vs `ticket-003`
- 该填工单号时填了 `null`

一旦发生，你的"强判定"**静默降级**为文本相似度弱兜底——而这正是你试图摆脱的那种模糊机制。

**失败模式不对称**：漏匹配（false negative）不报错。两个本应冲突的节点各自作为 Active 共存，过期约束污染上下文——即你立项要解决的那个问题，从后门溜了回来。

**建议**：在 Extractor 和 Reconcile 之间插入一层**实体解析/规范化层**（per-project `entity_registry`），做路径归一、别名映射、大小写/分隔符折叠，新 `entity_ref` 先过注册表对齐再进入裁决。

---

### 二、`state` 互斥关系从未被定义

你的失效判定核心是"`entity_ref` 相同且 `state` 互斥"。但全文没有定义**互斥关系本身**。

- `implemented` vs `deployed` 是**先后**关系，不是互斥
- `in_progress` vs `blocked` 常常**并存**
- 互斥语义依赖 `node type`：`Constraint` 的失效逻辑和 `OpenTask` 的状态机不是一回事

**建议**：建立显式的**状态转移/互斥矩阵**（按 node type 分别定义），而不是把它隐含在 Reconcile 脚本的判断里。这是决定 Reconcile 误杀还是漏放的核心规则。

---

### 三、失效模型过于简化：二值、整体、单调

当前模型中，失效是 `node → superseded` 的整体替换。但长程任务中：

- **部分失效**：新事实只推翻旧节点的某个子句，整体 supersede 会连带丢掉仍有效的部分
- **条件/时序失效**：约束"在 X 之前有效"或"仅在配置 A 下成立"——没有一等公民的**有效时间维度**
- **可逆/非单调**：被 superseded 的约束可能后续某轮重新生效（需求回滚、方案复活）

尤其对"决策演化审计"这个核心卖点，**双时态（bitemporal）** 是必要的：valid-time（事实何时为真）与 transaction-time（系统何时记录）。append-only patches 隐含了后者，但没有做成可查询的一等维度。

---

### 四、Graph Slice 的"只省 token 不负责正确性"在 `entity_ref` 失效时是空话

你声称 Slice 只管省 Token、Reconcile 用全图兜正确性。这个分工**只在 `entity_ref` 可靠时成立**。

链路：Slice 靠符号检索召回，硬上限可能驱逐真正冲突的节点 → Extractor 没有线索提议 invalidation → Reconcile 用全图补救，但强判定依赖 `entity_ref` 精确匹配。

当 `entity_ref` 为 null 或不一致时，**两道防线在同一个洞上对齐了**。这也是为什么第一节的 entity resolution 是头号优先级。

---

### 五、验证缺口：决定项目生死的地方是空的

你用契约门控制度化"未验证就别依赖"。但验证标准从未定义。

失效机制的核心是一对相互拉扯的指标：
- **召回率**：漏掉的 supersede → 过期污染
- **精确率**：误判的 supersede → 错杀仍有效的事实（更隐蔽、更致命）

**建议**：在 04_assembly 启用之前，先建立一个**带 ground-truth 的失效轨迹回放基准**（几十条人工标注的失效事件 + "第 N 轮哪些仍有效"的标准答案），把 precision/recall 作为 PROVISIONAL → STABLE 的硬门槛。

---

### 六、若干较次要但需正视的隐患

- **全图 lint 的可扩展性**：raw append-only + superseded 只增不减 → 全图线性膨胀。lint 每次 apply 后跑全图是 O(N) per turn。需要增量 lint + 归档/压实。
- **每轮成本**：normalize → slice → Extractor LLM → reconcile → apply → lint，失败重试至 3 次。光记账就可能 1–4 次 LLM 调用，税很重。
- **Extractor 的角色冲突**：同一次调用里既要慷慨抽取，又要做怀疑式反向检查。两种倾向相互打架。
- **缺少置信度/出处权重**：ToolResult 是硬证据，用户随口一句是软陈述，但在模型中平权。
- **量化交易作为切入点**：因子演化很大程度上是**代码**，已活在 git + MLflow/W&B 中。律师/审计（决策演化本身就是文本）可能才是更贴合架构本质的滩头阵地。

---

### 最终判断

这是一份思想深度扎实的设计，但你最硬的那块机械裁决，其根基踩在 LLM 分配的 `entity_ref` 上——这在你立项要解决的那个病灶上留下了一个结构性的、静默的漏洞。

在完成以下四件事之前，这套系统的"确定性"在数学上是有缺口的：
1. 补上实体解析/规范化层
2. 把 state 互斥关系形式化（按 type 定义矩阵）
3. 为失效引入时间/部分/可逆维度（至少从双时态开始）
4. 建立失效 precision/recall 的回放基准

**如果只挑一件事先做**：entity resolution + state 互斥矩阵 + 小型失效回放基准捆在一起——它们共同决定你的强判定到底是真机械还是伪机械。其余（双时态、增量 lint、成本优化）可在那之后迭代。

# [/COMPACTED]

