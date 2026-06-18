## 修正后的整体课程设计压缩（基于后续定位修正）

### 课程总定位
**《从 Claude Code 到 Logic Graph：构建依赖感知的上下文管理器》**  
不再定位为单纯解读源码或还原 AI 思考，而是：**从 Claude Code 暴露的 Agent 工程线索出发，学习上下文管理、压缩、功能演化，并原创实验系统 Logic Graph——任务态上下文管理管线**。

**核心主线修正**：Claude Code 展示工业级应对上下文爆炸的手段；Logic Graph 不是通用压缩器，而是**任务态依赖索引与上下文结构化机制**。最终形成管线：  
`对话 → Graph Patch → TaskGraph → Context Pack → 主LLM`（以及 Memory 沉淀、多 Agent 协作、证据追踪、调试报告）。

---

### 课程结构（10讲，每讲定位已按后续修正）

#### 第0讲：导论——Claude Code 事件真正值得学的是什么
- 44个 feature flags 是理解系统演化的入口，上下文管理是核心战场。  
- 引出课程双线：Claude Code 的工程方法 + Logic Graph 的实验性回应。  
- 核心结论：Claude Code 暴露的是 Agent 工程方法论，而非单个功能。

#### 第1讲：门控体系——复杂 Agent 如何管理功能演化
- 六层门控（编译期、环境变量、远程实验、配置文件、API 能力、Kill Switch）。  
- 以 COORDINATOR_MODE 等为例追踪真实门控链路。  
- 迁移设计：为 Logic Graph 设计五层门控（建图、调试、GC、可视化、实验特性）。  
- 结论：门控是管理演化复杂性的架构能力。

#### 第2讲：上下文工程——Claude Code 如何在有限窗口中持续工作
- 上下文预算模型（固定开销 + 可变开销 + 净空间）。  
- 五层防御体系：源头控制 → 折叠压缩(Context Collapse) → 微压缩(MicroCompact) → 全量压缩(Auto Compact) → 应急压缩(Reactive Compact)。  
- 摘要强结构化（9个固定栏目）+ `<analysis>` 草稿区 + 禁止工具调用双保险。  
- 对 Logic Graph 启示：梯度响应、摘要作为消息、断路器、按语义单元分组；图结构可实现比无差别摘要更智能的压缩。

#### 第3讲：从 Micrograd 到 Logic Graph——上下文不是文本，而是依赖图
- Micrograd 的 `Value` 类（`_prev`, `_op`）启发依赖追踪。  
- Logic Graph 定位修正：**不是还原模型内部思维，而是记录任务中外部可验证依赖**。  
- 节点类型：UserGoal, Constraint, Fact, ToolResult, Decision, Summary, FinalAnswer。  
- 核心价值：回答“哪些旧信息不能丢”“前提变化后哪些结论失效”“工具错误后哪些答案受影响”。

#### 第4讲：让任务变成图——构建多轮对话的增量 Logic Graph（写入侧）
- **本讲定位**：用户对话 → Graph Patch → TaskGraph，回答“任务图怎么长出来”。  
- 任务级图 vs 轮次级图：一个任务一张图，每轮只做增量 Patch（new/updated/superseded）。  
- 启动时机：手动（如 `/task start`），后续可半自动/全自动。  
- 典型操作：通过 Graph Extractor Prompt 让 LLM（旁路小模型）输出结构化 Patch，Python 代码合并成 TaskGraph。  
- 最小可运行代码：Node, Edge, TaskGraph, GraphUpdater, Deduplicator, to_mermaid。  
- 核心原则：不删除被推翻节点，用 `superseded` 留下演化轨迹。

#### 第5讲：从 TaskGraph 到 Context Pack——把任务图喂回主 LLM（读取侧）
- **本讲定位修正**：不是压缩，而是 **TaskGraph → Context Pack → 主LLM**，回答“任务图怎么喂回去”。  
- Context Pack 是结构化任务上下文（current_focus, goals, active_constraints, current_decisions, relevant_facts, open_tasks, superseded_history），不是图 dump。  
- 从当前焦点（如最新 active OpenTask）向上游追踪依赖边（`depends_on`/`implements`/`serves`/`refines`），同时收集被 `invalidates` 边标记的旧方案。  
- 最小代码实现 `build_context_pack` + `context_pack_to_prompt`，注入主 LLM。  
- 核心价值：让主 LLM 明确知道当前有效约束、已推翻方案及原因，避免重蹈覆辙。

#### 第6讲：任务记忆沉淀——从 TaskGraph 到长期 Memory Store
- **本讲定位修正**：不是“压缩升级版”，而是跨任务、跨会话的**长期任务记忆沉淀与召回**。  
- 流程：任务阶段结束 → Memory Extractor 抽取长期记忆 → Memory Store；新任务时召回 → 生成 MemoryReferenceNode 进入新 TaskGraph → Context Pack。  
- 沉淀类型：GoalMemory, ConstraintMemory, PreferenceMemory, DecisionMemory, OpenTaskMemory, ErrorMemory, ArtifactMemory（可选）。  
- 不沉淀：临时推理、大段工具输出、已推翻方案、闲聊。  
- 生命周期：create, update, merge, invalidate, archive, delete。失效标记而非删除，留痕供后续参考。  
- 召回后通过 `memories_to_seed_nodes` 接入 TaskGraph，不走直接塞 prompt。

#### 第7讲：多 Agent 协作——TaskGraph 的边界与验证（重写版）
- **本讲定位**：解决多 Agent 时 TaskGraph 的一致性、边界性和可验证性。  
- 核心架构：Coordinator 基于 TaskGraph 为每个 Worker 生成 **Worker Context Pack**（子任务上下文）；Worker 只返回 **Result + Graph Patch**（不直接改图）；Coordinator 合并 Patch、处理冲突；Verifier 独立验证关键 Claim + Evidence，返回 Verification Patch。  
- 三种包：Worker Context Pack, Worker Result Package, Verification Pack。  
- Demo 延续 Minecraft：拆分 3 个 Worker → 生成 Context Pack → 返回 Patch → 合并时发现客户端命令与无 OP 权限冲突 → Verifier 验证 RCON → 更新 TaskGraph → 重新生成主 LLM Context Pack。  
- 核心原则：TaskGraph 单写入，Worker 多读取；广播式上下文爆炸被消除。

#### 第8讲：工具与文件系统——让工具结果成为可追踪的证据节点
- **本讲定位**（中等调整）：工具调用、文件产物、测试结果作为可追踪、可压缩、可失效的上下文证据。  
- 四类核心节点：ToolCallNode, ToolResultNode, FileArtifactNode（含版本哈希）, TestResultNode。  
- 大结果写盘 + 预览引用（preview + full_ref），连接第5讲压缩（可丢 preview，不可丢被依赖的 full_ref）。  
- 失效传播简化版：当工具结果错误或文件变化，标记 `tainted` 向下游传播。  
- Demo：根据 config.yaml 写代码 → 测试 → 修改 config.yaml → 下游节点变 tainted/suspect/invalid。  
- 核心结论：信息有来源，依赖有方向，文件有版本，结果能回查。

#### 第9讲：可观测性与调试——把 TaskGraph 管线变成可检查的 Debug Report
- **本讲定位重写**：不是“AI Reasoning Debugger”，而是 **TaskGraph 管线的工程调试器**。  
- 核心问题：系统输出错了，是 Extractor 抽错、Graph 合并错、Context Pack 漏、Memory 召回错，还是证据失效？  
- 六类可观测对象：Patch, TaskGraph Snapshot, Context Pack, Memory Recall Report, Evidence Index, Event Timeline。每类必须包含 `reason` 字段。  
- **本讲最重要部分**：Context Pack Trace——为 Pack 中每个条目增加 `included_reason` / `excluded_reason`，解释为何入选/排除。  
- 产出静态 **Task Context Debug Report**（含 conversation.md, patches.json, task_graph.json, context_pack.md, memory_recall.json, evidence_index.json, timeline.json, graph.mmd）。  
- 实时 UI 作为选做扩展。

#### 第10讲：总结与路线图——从课程原型到真实项目
- **本讲定位重写**：闭环前9讲形成完整工程管线；明确 Logic Graph“是什么、不是什么”；给出后续路线。  
- **明确定位**：Logic Graph 是**任务态上下文管理机制**，不是模型内部推理还原，不是通用聊天压缩器，不是 Compact 替代品，不是万能长期记忆，不是可上线的工业系统。  
- **最终 Demo（Minecraft 全流程）**：  
  用户提出任务 → Extractor 输出 Patch（目标/偏好/事实）→ 补充约束（一个键、无 OP 权限）→ Patch 新增 Constraint，标记旧客户端方案 superseded，新增服务端 RCON 决策 → Context Builder 生成 Context Pack（目标、有效约束、当前方案、已推翻方案）→ Memory 沉淀 → 新会话召回记忆 → 工具证据入图（读取配置、测试 RCON）→ Debug Report 解释为何建议 RCON 而非客户端命令。  
- **后续路线图**：  
  - 工程：封装 Python 包（extractor / graph / context_builder / memory / coordinator / evidence / debug_report / examples）。  
  - 产品：做成“Task Context Debugger for AI Agents”，卖点为主 LLM 可见上下文、漏掉约束、旧方案被推翻、工具证据支撑、多 Agent 合并。  
  - 研究：抽取准确率、Context Pack 对长任务完成率提升、Memory 过期冲突、多 Agent Patch 一致性。  
  - 教学：可打包成 AI Agent 工程课 / 上下文管理专题课。  
- **最终收束**：课程真正主线不是 Claude Code 的某个 flag，而是**复杂 Agent 系统如何管理任务状态**。Claude Code 展示了工业手段，Logic Graph 尝试回答：若显式记录目标、约束、决策、证据和被推翻方案，Agent 能否更稳定地继续工作。

---

### 技术产出（项目结构）
```
logic_graph_context_manager/
├── graph/               # Node, Edge, TaskGraph
├── extractor/           # Graph Patch Extractor (LLM prompt + schema)
├── context_builder/     # Context Pack from TaskGraph
├── memory/              # MemoryStore, recall, seed nodes
├── coordinator/         # Multi-agent context pack & patch merge
├── evidence/            # Tool/File/Test nodes, taint propagation
├── debug_report/        # Debug Report generator
├── visualizer/          # Mermaid / Graphviz
└── demo.py              # Minecraft end-to-end demo
```

---

### 核心价值总结（修正后）
1. **有热点入口**：Claude Code 的 flags 和上下文机制。  
2. **有工程深度**：门控、上下文压缩、预算、工具、记忆、多 Agent、可观测性。  
3. **有原创产出**：Logic Graph 作为任务态上下文管理管线，强调 **写入（Patch→TaskGraph）→ 读取（Context Pack）→ 长期记忆（Memory）→ 多 Agent 边界 → 证据追踪 → 调试报告** 的闭环。  
4. **最重要的路线修正（已落地）**：  
   - 原“依赖感知压缩” → 改为“任务图写入与读取”，压缩为副产物。  
   - 原“AI 推理调试器” → 改为“TaskGraph 管线调试器”。  
   - 原“通用上下文压缩” → 改为“任务态上下文管理，无任务不建图”。