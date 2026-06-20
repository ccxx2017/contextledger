# ContextLedger 项目架构与设计白皮书

## 一、 项目定位与核心价值
**ContextLedger（上下文账本）** 不是通用的聊天记忆压缩器，而是面向“长程、有状态、约束会演化的 Agentic 任务”的**领域状态层 / Agent Memory Backbone**。
*   **核心痛点**：在长程任务中，旧事实被新事实推翻（如工单状态变更、方案被替代、约束失效）。传统的向量记忆（Flat RAG）或简单的摘要压缩无法处理“事实失效”，会导致过期约束污染上下文。
*   **核心价值**：通过结构化的 `entity_ref` 与 `invalidates` 语义，实现**长程状态下的事实失效与决策演化审计**。让 Agent 在运行数月后，依然精确知道“什么约束已经不成立了”。
*   **产品战略**：不与智能体平台竞争“通用浅层记忆”，而是作为 SDK/框架，服务自行搭建长程 Agent 的开发者。首选切入领域为**量化交易项目开发**（决策被频繁推翻、因子演化强），其次为**律师业务**（决策审计轨迹）。

## 二、 双系统融合架构 (Monorepo)
项目由两个核心模块组成，共享底层数据与契约，采用 Monorepo 架构管理。
1.  **Graph（事实与状态层 / 发动机）**：高精度、低完整度。事实与状态的**唯一权威裁决源**。通过节点、边、`entity_ref`、`state`、`invalidates` 做机械化的事实失效判定。
2.  **Pack（叙事与软料层 / 驾驶舱）**：高完整度、低精度。退化为**派生视图 + 软知识容器**（偏好、方法论、技能）。不独立判定事实失效，仅渲染图增量为可读叙事，并存放图装不进的软料。

**融合纪律**：
*   **定主从**：Graph 是事实真源，Pack 是派生视图。同一知识的正文只能在一处持有（规则6）。
*   **防漂移**：在 Pack 的折叠规则中加入“职责边界声明”，明确事实失效的权威判定上移至 Graph，Pack 内的 `[DEPRECATED]` 仅为过渡脚手架。

## 三、 核心数据模型 (Graph Schema)
### 1. 节点 (Node)
*   `node_id`: 唯一标识。
*   `type`: `UserGoal | Constraint | Fact | ToolResult | Decision | FileArtifact | OpenTask`
*   `content`: 节点内容。
*   `entity_ref`: **核心机制**。稳定实体标识（如工单号、API路径、文件路径）。用于机械精确匹配，判定“同一实体”。无法确定则填 `null`。
*   `state`: 归一化状态枚举（`open | blocked | in_progress | implemented | deployed | resolved | cancelled | unknown | null`）。
*   `status`: `active | superseded | done`。

### 2. 边 (Edge) 与失效语义
*   `relation`: `refines | depends_on | supports | invalidates | implements | serves | produces | derived_from`
*   **事实失效 (Invalidation)**：当新事实使旧节点不再成立（状态互斥），旧节点必须标记为 `superseded`，并添加 `{ "source": "新ID", "target": "旧ID", "relation": "invalidates" }` 边。

## 四、 数据管线与目录结构
### 1. 物理目录结构 (单一真源原则)
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

### 2. 三条核心管线
*   **写入管线 (高频/每轮)**：`Raw` → `Normalized` → `Graph Slice` → `Extractor (LLM)` → `Patch` → `Reconcile` → `Apply` → `Graph State` → `Lint`
*   **折叠管线 (低频/每N轮)**：`Raw` → `Normalized` → `Maintenance Prompt (LLM)` → `Memory Pack`
*   **装配管线 (按需/Query驱动)**：`Graph State` (当前状态) + `Pack` (软料) → `Assembler` → `Context Pack` → `主 LLM`

## 五、 核心工程机制 (长程运行保障)
为解决 LLM 抽取的模糊性与长程图膨胀问题，系统采用 **“LLM 提议，机械层裁决”** 的三层防护架构。

### 1. Graph Slice (O(1) 上下文控制)
*   **定位**：只负责省 Token，**不负责正确性**。
*   **机制**：根据当前轮对话提取符号（工单、文件），从全图检索相关节点。每个分组（如 `active_open_tasks`, `conflict_candidates`）设有**硬上限**，确保 Extractor 的上下文规模恒定，不随全图线性增长。

### 2. Reconciliation Pass (事后校验 / 事前拦截)
*   **脚本**：`reconcile_patch.py` (Apply 前运行，只读)。
*   **机制**：用全图数据复核 Patch 的自洽性。核心依赖 `entity_ref` 精确匹配。
*   **强判定**：若 Patch 新增节点与全图 Active 节点 `entity_ref` 相同且 `state` 互斥，但 Patch 未声明 `superseded` 和 `invalidates`，直接报 **Error** 阻断。
*   **弱兜底**：无 `entity_ref` 时，仅做文本相似度 Warning。

### 3. Graph Lint (全图质检)
*   **脚本**：`graph_lint.py` (Apply 后运行，只读)。
*   **机制**：检查全局不变量。包括：孤立 Active 节点、`invalidates` 指向未 `superseded` 的节点、同一 `entity_ref` 下互斥的 Active State、OpenTask 生命周期异常等。

### 4. 失败处理与隔离 (Quarantine)
*   **有界重试**：Reconcile/Lint 失败时，将结构化 Error 回填 Prompt 重试（上限 N=2~3 次）。
*   **失败隔离**：超限仍失败，则拒绝合并，将 Patch 隔离至 `quarantine/` 目录。**宁可漏记一轮，绝不污染主图**。

## 六、 契约体系 (Contracts)
`contracts/` 目录是防止双系统漂移的唯一权威约束：
1.  **01_raw_anchors.md [STABLE]**：Raw ID 格式规范；经 Normalized 抽取时，Span 必须翻译回 Raw 偏移，确保脊柱锚点不断链。
2.  **02_ownership.md [STABLE]**：知识正文归属权。判断口诀：“是否会被后来事实推翻？”——会则归 Graph，否则归 Pack。
3.  **03_graph_schema.md [PROVISIONAL]**：节点/边结构与失效语义定义。验证完成前下游不得依赖。
4.  **04_assembly.md [PLACEHOLDER]**：装配环节前置闸。等 Graph 失效机制在真实冲突上验证通过后方可启用。
5.  **05_normalized.md [STABLE]**：Normalized 必须是 `f(raw)` 纯派生物；不得注入新信息或判断；必须带可重放 Manifest。

## 七、 Extractor Prompt 设计原则
*   **分离缓存**：System Prompt 包含固定的 Schema 规则与生命周期判定逻辑（支持 Prompt Caching）；User Prompt 仅注入当前 Slice 与本轮对话。
*   **事实一致性反向检查**：强制要求 LLM 扫描 Slice 中的 `conflict_candidates`，若发现 `entity_ref` 相同且 `state` 互斥，必须输出 `superseded` 和 `invalidates`。
*   **命名契约**：严格规范 `entity_ref` 的命名（如文件用原文，组件用 snake_case，未分配工单填 `null`），防止因命名不一致导致强匹配退化。
