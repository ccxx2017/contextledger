# ContextLedger 项目背景包（新AI接手用）

## 第一部分整体压缩：折叠器与记忆治理设计演进

- **核心问题**：该章记录早期“长对话二次压缩/折叠器”的设计探索，主要围绕如何从轮次压缩转向状态保留、如何区分情景/语义/程序记忆、如何分阶段落地记忆治理协议展开，发生于 ContextLedger 的 TaskGraph 架构定型之前。
- **结论**：该章与当前 Graph/Pack/Assembler 主线相关性较低，但以下机制已被吸收：
  1. “状态优先于历史”原则——等价于 Graph 作为当前信念态权威。
  2. 四分流规则（通用→技能库/项目内→长期记忆/当前→底稿/一次性→冷存）——等价于 Graph/Pack/raw 分流。
  3. append-only + 检索面过滤——继承为 patch append-only + 装配按 status=active 过滤。
  4. 稳定区+滚动区有界结构——为 Assembler 的 L1 常驻基线 + L2–L4 按需检索提供前驱直觉。


## TaskGraph 任务态上下文管理系统架构与工程实现文档

- **核心问题**：TaskGraph 的数据模型、系统架构、核心管线是什么？
- **结论**：TaskGraph 是任务态上下文管理机制，核心原则为：任务态启动（无明确任务不建图）、写入/读取分离、patch 为不可变事件日志、graph_state 为编译产物。数据模型含节点（UserGoal/Constraint/Fact/Decision/OpenTask/ToolResult/FileArtifact）、边（refines/depends_on/supports/invalidates/implements/serves/produces/derived_from）、entity_ref（稳定标识）、state（领域状态）、status（active/superseded）。管线为：Slice→Extractor Prompt→LLM Extractor→patch→reconcile→apply→lint→Context Pack。


## 系统整体价值判断

- **核心问题**：TaskGraph 系统是否有致命缺陷？价值在哪里？
- **结论**：无致命内在缺陷，核心架构自洽。真正限制价值的是两个边界问题——机械核（reconcile/apply/lint）夹在两片 LLM 膜（Extractor 分配 entity_ref、压缩成 memory_pack）之间。端到端可靠性 = 最弱那层膜的可靠性，而非机械核的可靠性。产品价值不适用于通用聊天记忆，但长程有状态 agentic 任务有实质价值，其中 entity_ref + invalidates 是向量记忆崩掉的地方。


## 两种上下文机制的价值比较

- **核心问题**：TaskGraph 与 MemoryPack（折叠器）两种机制的价值如何比较？
- **结论**：TaskGraph（结构化）最强能力是精确失效判定，但抓不住软知识；MemoryPack（叙事化）保留软知识但无机械失效保证。**更有价值的是 TaskGraph 的 entity_ref + invalidates 机制**——稀缺、难复刻、可辩护。但 TaskGraph 单独无法成为独立产品，它是“发动机”，MemoryPack 是“驾驶舱”。正确架构为定主从：TaskGraph 为事实与状态唯一权威源，MemoryPack 退化为派生视图+软知识容器。


## 下游消费环节的装配设计

- **核心问题**：Graph 和 Pack 如何结合为下游 LLM 的最终上下文？
- **结论**：装配是带预算的选择性检索 + 冲突时的权威序，非拼接。四层分层：L1 常驻基线（push）、L2 任务相关当前态（从 Graph 拉取）、L3 软知识（从 Pack 拉取）、L4 深检索（wiki/RAG）。冲突处理用内容切分消除（Graph 独占事实/状态，Pack 独占软料），而非权威序兜底。装配器是第三个模块，由当前 query 驱动，需先有路由步。脊柱锚点可复用为检索索引。


## ContextLedger 项目架构与设计白皮书

- **核心问题**：ContextLedger 的整体架构、契约体系、工程机制是什么？
- **结论**：项目定位为“长程 Agent 任务的领域状态层与记忆基础设施”。架构为双系统融合（Graph + Pack），四层存储（raw/TaskGraph/MemoryPack/Assembler），三条管线（写入/折叠/装配）。核心工程机制：Slice（O(1)上下文控制）、Reconcile（事前拦截，entity_ref 精确匹配）、Lint（全图质检）、Quarantine（失败隔离）。契约体系（contracts/）为防漂移的唯一权威约束。Extractor Prompt 设计原则：分离缓存（System 固定可缓存，User 仅注入 Slice+对话）、事实一致性反向检查、命名契约。


## MemoryPack 的必要性评估：增值层，非核心引擎

- **核心问题**：MemoryPack 是否不可或缺？
- **结论**：MemoryPack 不是不可或缺的。最小闭环仅 raw → TaskGraph → Assembler，Pack 可暂缓。核心价值（事实失效追踪）完全由 TaskGraph 承载。删除 MemoryPack 丢失的是“知识复利”（方法论/偏好/跨项目复用），而非“状态追踪”。MemoryPack 是第二曲线，使系统从“状态追踪工具”升级为“知识复利平台”，但此升级可选。Phase 1 仅实现 TaskGraph + Assembler，Phase 2 视需求决定是否引入 MemoryPack。


## ContextLedger 的形态定位：框架无关的状态层库，而非智能体或插件

- **核心问题**：ContextLedger 应该是插件、自建智能体，还是其他形态？
- **结论**：否定“插件 vs 自建智能体”的二分。ContextLedger 不应做成智能体（差异化会失焦），也不应做成封闭产品的插件（拿不到最终装配权）。正确形态为**框架无关的状态层库/SDK**，暴露两个钩子：`ingest(event)` 和 `assemble(goal/query) → context`，目标客户为在可编程编排层自建长程 agent 的开发者。must_include 保证迫使必须拥有最终装配权。MCP 适合 L3/L4“建议式软知识”的接入面，但硬保证（L2 当前态 + must_include）仍需库内深集成。


## ContextLedger 对后台自动执行智能体的适配性分析

- **核心问题**：ContextLedger 是否适用于无轮次对话、后台默默自动执行的智能体？
- **结论**：适用，且更刚需——后台场景无人兜底，“废案不死”代价直接导致系统崩溃。但需修正：轮次不是可替换的 I/O 外壳，而是白皮书整个正确性模型免费搭载的并发控制点和读快照点。后台场景需将“轮次”泛化为“协调者每观测到一个事件”（发出调度/收到返回/超时/取消/改派）为独立 ledger step。需补充：输入源泛化为结构化事件日志、并发与异步处理（单写者串行化 apply）、ToolResult 为一等公民、Assembler 触发从 Query-driven 转为 Action-driven。


## 用开源 Agent 作为验证宿主的方案评估

- **核心问题**：是否可以用开源 Agent（如 OpenCode）作为 ContextLedger 的验证载体？
- **结论**：方向正确且务实。但前提修正：大多数开源 Agent 没有干净可插拔的“记忆模块”，需要接管的是**最终上下文装配点**。集成形态：理想为 Hook 式（宿主暴露装配钩子），次选为 Fork 切除式。宿主选择标准：有定义良好的装配接缝、任务本身为长程会暴露记忆失效。OpenCode 领域正确，但需确认是否存在可接管的上下文装配钩子。执行建议：先并行影子模式（只读不写），确认有效后再做接管。


## 对补充调查结论的最终裁定与实施方向

- **核心问题**：OpenCode 的注入点调查结论是什么？如何实施？
- **结论**：对 opencode 会话主链，CL 的 per-turn 注入可行。native-runtime 不构成阻塞，experimental transform 可用但不建议作为长期稳定主入口。实施上选择 `LLM.run(...)` wrapper 作为主注入点，比 experimental transform 更稳定，覆盖 AI SDK 与 native-runtime 分流前主路径。子 agent 分阶段处理：MVP 阶段只覆盖主会话循环，第二阶段再覆盖 agent.ts 子 agent 路径；project-copy.ts 排除在外。范围定为主会话链路优先，可进入最小改造实施方案阶段。


## ContextLedger 架构评审：高成熟度设计下的结构性风险与改进路径

- **核心问题**：设计存在哪些结构性风险？
- **结论**：致命依赖——entity_ref 由 LLM 生成，命名不一致会使强判定静默降级。需补 Entity Resolver 层。模型不完备：state 互斥关系未形式化定义，失效被建模为“二值、整体、单调”，无法覆盖部分/条件/时序/可逆失效。Graph Slice 与 Reconcile 的防护缺口在同一处对齐（entity_ref 为共同支点）。Pack 派生视图存在陈旧窗口。验证缺口：缺少失效 precision/recall 的基准。工程隐患：全图 lint O(N) per turn、每轮 LLM 调用成本、Extractor 角色冲突、缺少置信度/出处权重。首要行动：entity resolution + state 互斥矩阵 + 失效回放基准三者捆绑推进。


## 项目必要性的再确认与条件

- **核心问题**：项目是否还值得做？
- **结论**：值得做，所列缺陷是“工程未完成”而非“此路不通”。该项目要解决的问题客观存在且未被很好解决，现有方案（Flat RAG、滚动摘要）结构上无法处理 retraction。抽象正确性成立。应停下的条件：目标为立即服务量化交易生产环境、低估工程量、存在现成够用的替代方案而未调研。下一步最有价值的是构建**失效回放基准**——同时回答：比 Flat RAG 好多少、缺陷补到哪算够、现有竞品在同一基准上的表现。


## 失效回放基准的最小标注 Schema 设计

- **核心问题**：失效回放基准用什么结构标注？
- **结论**：Schema 含 entities（canonical_entity/aliases/type）、turns（events 含 event_id/surface_ref/content/state/provenance/confidence）、gold_invalidations（含 invalidation_type: full/partial/conditional/revival）、gold_non_invalidations（显式负样本）、checkpoints（指定轮次应 active/superseded 集合）。指标：失效判定层 P/R（按类型分层报告）、实体解析层（alias 不一致导致漏匹配数量）、状态查询层 Set-F1。起步建议：标注 15–20 条轨迹，覆盖矩阵填满（四种失效类型各≥3，alias 陷阱≥5，provenance 冲突≥3，non-invalidation 诱饵≥1/3）。


## 项目AI（Orchestrator）单轮操作手册（精炼版）

- **核心问题**：项目AI（Orchestrator）每轮应如何操作？
- **结论**：Orchestrator 只做三件事：按序调用脚本与 Extractor、读结构化结果（pass/fail + error）、按手册走控制流。不做机械检查、不做语义抽取、不手改 patch、不手写 Extractor Prompt。主流程：STEP 0 启动分支（冷启动用 seed，否则用当前 state）→ STEP 1 切片 → STEP 2 组装 Prompt → STEP 3 调用 Extractor → STEP 4 Reconcile（P4 关卡，fail 回填重试最多 N 次）→ STEP 5 Apply → STEP 6 Lint（P5 关卡，区分本轮引入 vs 存量问题）→ STEP 7 终态移交。收尾自检五项：未改写 Raw、未 Apply 未过 Reconcile 的 Patch、产物落本项目目录、未手动编辑 Patch/Prompt、Lint Fail 已完成归属判定。


## Phase 0 正式封板：全链可复现验证通过，停止判据全部满足

- **核心问题**：Phase 0 验证了什么？封板条件是什么？
- **结论**：项目AI完成 turn_005 三项验收：全链重建（turn_001→004 patch 链从 seed 确定性重放）、bundle 可再生（字节级一致）、runbook 固化四条经验。机制矩阵已填满（写入两类+装配三分支+state gate+待裁定→裁定演化），全链确定性可复现，有 runbook。Phase 0 正式封板。5 轮按计划停止。后续唯一触发条件锁死为 patch 重放不确定或 bundle 再生漂移（按 bugfix 处理，不计入新用例）。


## Phase 0.5 正式封板，13个FP全部归位，进入Phase 1

- **核心问题**：Phase 0.5 封板条件是什么？关键发现是什么？
- **结论**：项目AI补全 provenance_conflict 和 alias_trap 的 invalidation 分形态数据，13 个假阳性全部归位（partial:2, conditional:2, revival:2, provenance_conflict:3, non_invalidation_decoy:2, out_of_order_late:2, alias_trap:0, full:0）。结论修正为：partial/conditional/revival/provenance/decoy/out_of_order 共同构成低 precision，属整体失效裁定偏激进。Phase 0.5 正式封板。provenance 贡献 3 个 FP 为单形态最高项，Phase 1 保守化裁定从该线先动手边际收益最大。


## Phase 1-prep评估：机械核已验证，但extractor链路零次真实执行是当前最高风险盲区

- **核心问题**：Phase 1-prep 是否完成？最高风险是什么？
- **结论**：项目AI 已完成 Preflight Closure Checklist 10 项准备：checkpoint 定于 turn_004、extractor 调用契约补齐、retry N 写入 contract、目录约定落盘、Resolver 最小接口落地、Assembler v1 移除 phase0_manual 硬编码、priority 迁移留备份、L1/L2 机械判定脚本可用、contracts 索引修正、scratch dry-run 验证 reconcile→apply→lint→quarantine 路径。但**extractor 链路从未真实运行**（dry-run 用人造 patch，未跑 build_graph_slice→build_extractor_prompt→invoke_extractor）。进 turn_004 前须加两道闸：闸 1——turn_004 作为 extractor 首次冒烟测试，设人工检视点；闸 2——4 个 L2 存量问题固化为 lint_baseline.json 持久基线。


## 全自动重跑完成：可审计性恢复，隔离机制正常运行

- **核心问题**：全自动执行中暴露的违规如何修复？当前状态如何？
- **结论**：此前全自动执行中出现两项违反基础契约的操作——运行中修改清洗器（破坏 patch 链确定性）、手动补 patch 提交主图（违反 quarantine 原则）。已执行完整恢复：回滚至 turn_011（清洗器变更前 checkpoint），固定清洗器版本，严格 quarantine-only 模式，不手动修 patch。批量执行 turn_012–084：成功提交 57 轮，隔离 15 轮（~20.8%），隔离轮次未污染主图。**注意：原文中的 `turn_counter=84, nodes=165, edges=274` 是该次恢复封板时的历史快照，不应视为仓库当前实时计数；接手时应以最新 `graph/projects/abu_modern/graph_state.json` 为准。** 可审计性恢复，全自动模式正常运行。


## schema设计启动：基于revival/provenance缺口的扩展方案已产出

- **核心问题**：为什么启动 schema 设计？设计方向是什么？
- **结论**：候选收敛验证确认 invalidation P/R 从 0.550/0.579 提升至 0.609/0.737，active-set Set-F1 从 0.856 提升至 0.898，must_include recall 保持 1.000，revival 轨迹完全修复。此处评测基线必须记住：`D1 = full_history_dump`，`D2 = exact_surface_last_write_wins`；其中 `must_include recall` **不得低于 D1** 是项目红线，当前为与 D1 打平、优于 D2。三个 Q 问题已回答。schema 设计条件成熟。产出设计稿 `05_phase1_lifecycle_schema.md`：新增节点可选字段 lifecycle_ref/lifecycle_stage/lifecycle_seq，adjudication_key（= lifecycle_ref ?? entity_ref）取代 entity_ref 作为冲突检测分桶键，使 round5.* 这类同一生命周期拆成多个 entity_ref 的单流推进成为一等表达。待确认后进入实现阶段。
