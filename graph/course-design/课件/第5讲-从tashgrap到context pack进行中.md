# [COMPACTED]
**用户目标**：用户有一个基于计算图思想的LLM上下文依赖追踪与动态管理的原创方案（受Micrograd启发），希望将其与Claude Code的44个feature flag系列课程结合。用户询问AI是否可行。

**AI核心结论**：非常可行，且是聪明的结合。二者共同回答“复杂Agent系统如何在有限上下文中保持一致性、可追踪性”。建议将课程从“解读Claude Code”升级为“从Claude Code出发，提出并实现自己的上下文管理方案”，实现三个层次：热点入口、方法论深度、原创实验。

**关键决策与结合方式**：
- 否定“硬拼接”。肯定双线互相增强：Claude Code的flags提供现实工程参照系，用户的图方案提供原创理论与实验主线。
- 强烈建议采用“固定三段式”每讲结构：①现实问题（从Claude Code某组flag切入）→ ②抽象问题（上升为通用Agent/LLM问题）→ ③用户的图方案（作为解释或改进路径）。
- 语气区分：讲Claude Code时用“暗示”“推测”“工程角度看”；讲自己方案时用“提出可实验的替代框架”“验证思路”。
- 风险提醒：不要过度承诺flag为已发布功能，用户方案是否更优需实验证明。

**最匹配的5个主题联动**：
1. **上下文压缩**（REACTIVE_COMPACT等）→ 提出dependency-aware compaction而非黑盒摘要。
2. **大输出写盘与引用**（FILE_PERSISTENCE等）→ 将写盘对象作为图节点或子图摘要，按依赖回溯激活上下文。
3. **记忆系统**（TEAMMEM等）→ 将记忆表示为事实/决策/摘要/任务/约束节点及依赖边。
4. **多Agent协作**（COORDINATOR_MODE等）→ 每个Agent局部子图，共享公共祖先，传递必要依赖子图。
5. **可解释推理与教学演示**（ULTRATHINK等）→ 将图方案包装为AI reasoning debugger、依赖可视化器。

**课程总结构建议**：分为两层（解读层+构建层），8-10讲模块。总题推荐：“从Claude Code到Logic Graph：重建AI Agent的上下文工程”或“Claude Code在怎么‘记忆’和‘思考’？我们试着做一个可解释版本”。

**后续行动**：AI可提供A. 完整课程总纲（8-10讲）、B. 第一讲完整脚本、C. 核心概念课程地图。用户下一步可要求A。

**用户目标**：用户要求AI提供“A. 课程总纲”，即基于Claude Code的44个feature flags和用户原创的基于计算图的上下文依赖追踪方案，设计一套完整的视频课程结构。

**AI输出核心内容**：交付了一份完整课程总纲，课程名称为《从Claude Code的Feature Flags到Logic Graph：重建AI Agent的上下文工程》。

**课程定位**：不是单纯解读Claude Code，也不是只讲抽象想法，而是将两者结合：从顶级Agent产品暴露的工程线索出发，抽象出“上下文工程”问题，再提出并验证基于计算图的显式依赖追踪方案。

**课程目标**（三层收获）：
1. 看懂顶级Agent系统在解决什么问题（长上下文、多Agent、记忆、工具、观测、门控）。
2. 建立“上下文工程”思维（上下文不仅是聊天记录，需要压缩、写盘、引用、预算、裁剪）。
3. 跟随完成原创原型（ReasoningNode、推理图、图式剪枝、对比实验）。


**课程结构（10讲）**：

- **第0讲 导论**：建立总问题意识，从Micrograd的Value类联想到上下文依赖图，介绍课程从“解读他人”走向“构建自己”。
- **第1讲 门控体系**：讲解编译期flag、运行期开关、内部beta多重门控；延伸至Logic Graph未来需要的门控；输出门控分层表。
- **第2讲 上下文管理**：基于REACTIVE_COMPACT、HISTORY_SNIP、FILE_PERSISTENCE、TOKEN_BUDGET等flags，指出线性窗口的缺陷，引出ReasoningNode和图依赖概念。
- **第3讲 Micrograd启发**：从Value类的`_prev`、`_op`、`trace()`类比到ReasoningNode，定义原型数据结构（content、prev_nodes、op等），强调显式依赖与隐式attention的区别。
- **第4讲 第一阶段PoC**：设计Prompt让LLM输出结构化推理步骤（JSON schema），解析并构建图，用graphviz渲染；关联DUMP_SYSTEM_PROMPT等flags。
- **第5讲 图驱动的上下文GC**：定义active/dormant/garbage/summary/external reference节点，实现backward trace、subgraph retention、垃圾回收；与sliding window对比实验（token消耗、正确率等）；课程标志性创新点。
- **第6讲 记忆系统**：基于TEAMMEM、MEMORY_SHAPE_TELEMETRY、KAIROS等，将记忆分为FactNode、TaskNode、DecisionNode、ConstraintNode等，定义边类型（derived_from、supports、contradicts等）；演示事实修改后的影响传播。
- **第7讲 多Agent协作**：基于COORDINATOR_MODE、FORK_SUBAGENT、VERIFICATION_AGENT等，提出每个Agent持有局部子图，coordinator只传递必要依赖子图，验证代理独立运行。输出多Agent图协议草图。
- **第8讲 工具与执行器**：基于MCP_SKILLS、WEB_BROWSER_TOOL等，定义ToolCallNode、ToolResultNode、FileArtifactNode等，引入外部状态依赖和溯源。演示工具结果错误时结论失效。
- **第9讲 可解释性与产品化**：基于PERFETTO_TRACING、SHOT_STATS、ULTRATHINK等，将原型产品化为AI Reasoning Debugger、Context Graph Profiler；设计UI蓝图（对话+实时图+统计）。
- **第10讲 总结与未来路线**：完成课程闭环，总结Claude Code flags启示、上下文工程是核心壁垒、图结构的价值；列出后续推进方向（PoC、Demo、对比实验、开源、教学落地）。

**AI设计的第0讲教案核心内容（60分钟线上课，初中生受众）**：

- **教学目标**：知识上了解Claude Code、Feature Flag概念、上下文重要性、Logic Graph思想来源；思维上建立“从工程痕迹逆推设计意图”的能力；兴趣上通过真实源码激发对AI底层的好奇心。

- **教学过程（60分钟）**：

  1. **开场（8分钟）**：讲述Claude Code源码还原事件发现80+编译期标志（其中44个具有架构意义），类比为“拿到学霸草稿纸看到解题思路痕迹”。

  2. **Feature Flags——复杂系统的隐藏控制面板（18分钟）**：
     - 概念（5分钟）：Feature Flag类比家庭配电箱，Claude Code的flag是编译期特性，代表有意架构决策。
     - 屏幕共享看源码（8分钟）：展示项目目录结构 → 打开`cli.tsx`搜索`feature(`关键字 → 打开`compact.ts`找到`REACTIVE_COMPACT`相关代码。
     - 44个flag全景分类导览（5分钟）：按上下文与记忆类（7个）、多智能体协作类、自主代理类、推理规划类、可观测性类、安全权限类、工具执行器类快速介绍。强调上下文管理类flag数量最多、分布最广，是课程核心战场。

  3. **为什么“上下文”是AI Agent最难的仗（12分钟）**：
     - 什么是上下文（3分钟）：用贪吃蛇项目对话例子说明。
     - 滑动窗口的缺陷（4分钟）：线性窗口按时间丢弃，会丢失逻辑依赖的关键前提。
     - Claude Code的应对策略组合（5分钟）：解释REACTIVE_COMPACT（压缩摘要）、HISTORY_SNIP（精确片段引用）、FILE_PERSISTENCE（写盘+指针）、TOKEN_BUDGET（分配预算）、STREAMLINED_OUTPUT（精简输出）。指出这些虽优于滑动窗口，但都不按语义依赖关系决策。

  4. **从Micrograd到Logic Graph——让推理拥有“血缘档案”（14分钟）**：
     - Micrograd的`Value`类设计（5分钟）：用`a=3,b=2,c=a+b,d=c*4`例子，展示`Value`存储`data`、`_prev`（前驱）、`_op`（运算），形成有向无环图。类比为“血缘档案”。
     - 类比到AI推理（5分钟）：AI推理步骤也是线性文本，缺少依赖关系。提出`ReasoningNode(content, prev_nodes, operation_type)`，使对话变成推理依赖图（Logic Graph）。
     - 图结构优势举例（4分钟）：用三角形几何题推理图（条件→判断→计算面积→第二问半径）对比滑动窗口错误丢弃，展示图式反向追踪只保留依赖链上的节点，可安全移除不相关节点。

  5. **课程路线图与总结（8分钟）**：
     - 两条线索如何交织（3分钟）：44个flags → 上下文管理是核心战场 → 现有方案局限 → Micrograd启发 → Logic Graph作为实验性回应。
     - 后续课程预告（3分钟）：第1讲门控体系，第2讲五大上下文策略，第3讲构建ReasoningNode，第4讲原型演示，第5讲图式GC，第6-9讲记忆/多Agent/工具/可观测性，第10讲总结。
     - 课后任务（2分钟）：浏览44个flag文档挑3个感兴趣的思考解决什么问题；思考“只能保留5条信息时的保留规则设计”。

- **本讲核心结论**：Claude Code的44个开关表明上下文管理是AI Agent最核心的工程战场，Logic Graph方案试图引入显式语义依赖追踪作为新武器。需诚实说明目前仅为思路和原型，未经过大规模验证。

**关键决策与用户要求落地**：
- “从计算图到Logic Graph”部分改用更形象的类比：血缘档案、推理步骤的“父母”关系、几何题依赖链例子。
- Feature Flags结合源码演示：明确展示目录、搜索`feature(`关键字、打开具体文件；第0讲以分类导览和少量示例（REACTIVE_COMPACT等）作为“开胃菜”，不深入讲实现。
- 开场导入保留了吸引力和“草稿痕迹”类比。

**用户目标**：要求AI根据课程总纲给出第1讲教案（主题：门控体系）。用户提示AI可让项目AI调查Claude Code源码细节后，再基于调查结论编写教案。

**AI响应**：未直接输出教案，而是提出先进行5项必要的源码调查，要求用户将以下提示词交给项目AI执行，获取真实代码细节后再撰写第1讲教案。同时给出了第1讲的教案骨架供用户参考意图。

---

**5项源码调查任务**：

1. **`feature()`函数实现机制**：查找定义文件/函数签名/编译期或运行时行为/打包产物形态/2-3个调用片段。

2. **`betas.ts`完整内容**：导出内容/beta特性定义/`USER_TYPE === 'ant'`使用方式/beta header构造与API附加环节/引用关系。

3. **多层门控典型路径（以COORDINATOR_MODE为例）**：`feature('COORDINATOR_MODE')`调用位置/环境变量`CLAUDE_CODE_COORDINATOR_MODE`读取位置/两层组合逻辑（AND或其他）/是否还有第三层门控/完整门控流程图（可用KAIROS补充）。

4. **运行期配置系统实现**：配置加载来源/数据结构/消费方式/优先级机制/2-3个配置项使用示例。

5. **所有门控模式分类统计**：编译期门控、环境变量门控、用户类型门控、配置文件门控、API能力门控等，各自出现次数、2-3个代码示例、控制级别。

---

**第1讲教案骨架预览**：

- **环节1 回顾与引入**：从第0讲“44个开关”提出核心问题——复杂系统如何设计开关体系。
- **环节2 源码实证**：展示编译期、环境变量、用户类型、配置文件、API Header五种门控模式，用真实代码体现“层”。
- **环节3 案例深挖**：追踪COORDINATOR_MODE或KAIROS完整门控链路，画出决策树，理解多条件组合。
- **环节4 迁移设计**：为Logic Graph原型设计五层次开关（建图、调试、GC、可视化、实验特性）。
- **环节5 总结与任务**：门控体系是管理演化复杂性的架构能力。

---

**用户目标**：要求AI基于已完成源码调查（第1讲所需的5项调查结果），输出第1讲完整教案（主题：门控体系）。用户已提供调查结果（包含feature()实现、betas.ts、COORDINATOR_MODE链路、运行期配置、门控模式统计等详细数据）。

**AI响应**：基于调查结果，写出了完整的第1讲教案（45-55分钟），核心内容如下：

- **课程定位**：从“有什么隐藏功能”转向“系统如何管理82个编译期flag、828次feature()调用”。核心问题：“一个处于持续演化中的复杂Agent系统，如何让新功能和稳定性共存？”
- **六层门控模型**（逐层用真实代码讲解）：
  - L0 编译期门控（`feature()`，Bun bundler替换为常量，决定代码是否存在；82个flag，KAIROS出现154次）
  - L1 环境变量门控（`process.env.XXX`，`USER_TYPE==='ant'`出现357次，区分内外部用户）
  - L2 远程实验门控（GrowthBook/Statsig，`tengu_*`灰度，`_CACHED_MAY_BE_STALE`设计）
  - L3 配置文件门控（`claude.json`/`settings.json`，用户持久化偏好）
  - L4 API能力门控（beta header + model capability，适配不同provider/模型版本）
  - L5 Kill Switch（`DISABLE_*`系列，45+个，紧急降级）
- **案例深挖**：追踪COORDINATOR_MODE的完整门控链路（L0+L1+简化模式开关+GrowthBook实验），画决策树；补充KAIROS flag族的OR关系。
- **迁移设计**：为Logic Graph原型设计五层门控（编译期、环境变量、远程配置、用户配置、能力检测、Kill Switch），列出五个核心开关（ENABLE_REASONING_NODES等）及其默认值。

**输出状态**：教案已完整交付，无需进一步行动。用户可继续要求第2讲教案或调整本讲内容。
**当前任务**：用户准备制作第2讲教案（主题：上下文工程），要求AI先进行源码调查。用户已自行给出六个详细的调查任务提示词，要求项目AI按此调查，并将调查结果提交给AI，以便AI撰写第2讲教案。

**六个调查任务要点**：

1. **Compact系统完整架构**：找出所有compact相关文件、触发模式（手动/auto/reactive）及触发条件阈值、核心算法、摘要prompt内容、消息历史变化方式、`REACTIVE_COMPACT`和`CACHED_MICROCOMPACT`的控制路径、失败处理逻辑。

2. **CONTEXT_COLLAPSE和HISTORY_SNIP实现**：分别查明两个flag控制的代码路径、行为含义（折叠/截断/摘要替换）、两者交互关系与优先级、触发时机（每次API调用前？compact前后？）。

3. **Token计数与上下文预算管理**：计数方式（客户端估算还是API countTokens）、窗口大小确定逻辑、token接近上限时的决策链（collapse→compact→硬截断）、`TASK_BUDGETS_BETA_HEADER`作用、`CONTEXT_1M_BETA_HEADER`和`has1mContext()`使用条件。

4. **System Prompt组装与上下文占用**：构建函数、动态片段、所占token及控制机制、compact时system prompt是否变化、MCP工具schema注入影响。

5. **工具输出与大型内容管理**：工具输出大小限制与截断逻辑、大文件读取策略、bash输出处理、compact中工具输出的处理方式、`CONNECTOR_TEXT`和摘要beta header作用。

6. **上下文管理完整生命周期**：从首条消息到窗口填满→压缩→继续对话，按时间顺序描述消息进入、API请求前准备、响应处理、工具结果处理、紧凑前维护、压缩后重建。每个阶段标出涉及的feature flag、环境变量、配置项。

**下一步**：用户要求项目AI执行上述调查并提供结果；AI收到调查结果后，将基于真实代码撰写第2讲完整教案。

**用户任务**：用户提供了“上下文工程源码调查报告.md”（较近内容），AI基于该调查报告撰写了第2课完整教案（主题：上下文工程），并要求按一贯原则进行压缩。

**AI核心输出（第2课教案要点压缩）**：

- **课程定位**：Claude Code如何在有限上下文窗口中维持无限长对话。核心命题：Agent越能干，记忆消耗越快。上下文管理是整个Agent架构的地基。

- **上下文预算模型**：上下文窗口200K~1M。固定开销（System Prompt+工具Schema）不可压缩；可变开销（消息历史+工具交互）是压缩主战场；净空间预留20K tokens输出。简单截断会破坏API格式不变量且信息价值不均。

- **五层防御体系**（梯度响应，信息损失递增）：
  - **L1 源头控制**：工具输出截断（单结果50K字符，消息级200K，绝对上限400K字节）。超限内容持久化到磁盘（tool-results目录），上下文仅放2KB预览+`<persisted-output>`标签。文件读取≤256KB/25K tokens，Bash默认30K字符硬上限150K。
  - **L2 折叠压缩（Context Collapse）**：`feature('CONTEXT_COLLAPSE')`，每次API调用前将连续搜索/读取操作折叠为摘要消息。启用时替代auto compact（在90%窗口提交，95%阻塞）。
  - **L3 微压缩（MicroCompact）**：`feature('CACHED_MICROCOMPACT')`，距最后assistant消息>60分钟或缓存工具结果超阈值时触发。处理特定高消耗工具输出，清理本地消息或修改API缓存（`cache_edits`）。
  - **L4 全量压缩（Auto Compact）**：token使用量超过有效窗口-13K（如200K窗口→167K）时触发。调用LLM生成结构化摘要（`COMPACT_PROMPT`九部分模板），输出上限20K tokens，禁止工具调用。消息按API轮次分组，保留最近组、摘要较早组。重建后消息列表为`[boundary_marker, summary_message, kept_messages, attachments, hooks]`。
  - **L5 应急响应（Reactive Compact）**：`feature('REACTIVE_COMPACT')`，API返回413错误时触发，紧急压缩后重试。是最后安全网。

- **Compact系统核心机制**：
  - 触发决策链：全局禁用检查、`CONTEXT_COLLAPSE`跳过、递归防护、token估算（精确计数→Haiku回退→字符/4估算）、阈值比较。
  - 消息分组：按API轮次分组，保证tool_use与tool_result成对。
  - 保留决策：`adjustIndexToPreserveAPIInvariants()`确保分割点不破坏API格式。
  - 摘要生成：仅对被选中的较早消息组调用LLM，输出`<analysis>`+`<summary>`，后提取`<summary>`。
  - 断路器：连续失败≥3次停止自动触发。
  - 降级链：会话内存压缩（增量式，需会话内存文件、新增≥10K tokens和≥5个文本块）→ 传统压缩。
  - 会话内存压缩：`lastSummarizedMessageId`机制，增量摘要合并，信息保留度更高。

- **完整生命周期**：用户消息 → API请求前上下文组装（system prompt、折叠、截断、token估算）→ 响应返回（解析thinking/text/tool_use，更新token计数）→ 工具执行（源头控制、持久化、微压缩检查）→ 超阈值触发compact（含会话内存压缩或传统压缩）→ 重建消息列表 → 继续对话。Token使用量呈锯齿形：增长→压缩下降→再增长。

- **可迁移设计模式（对Logic Graph启示）**：
  1. 梯度响应架构（多级手段）而非单一策略。
  2. 摘要作为消息（可被后续压缩）而非系统提示（固定开销）。
  3. 断路器模式防止无限重试。
  4. 按语义单元（API轮次）分组保护完整性。
  5. 多源token估算回退（精度换可用性）。
  特别启示：Logic Graph可利用图结构为节点赋予不同保留优先级，实现比无差别摘要更智能的压缩。

- **关键阈值速查**：`AUTOCOMPACT_BUFFER_TOKENS=13K`，`WARNING_THRESHOLD_BUFFER_TOKENS=20K`，`MANUAL_COMPACT_BUFFER_TOKENS=3K`，`MAX_TOOL_RESULT_BYTES=400K`，`DEFAULT_MAX_RESULT_SIZE_CHARS=50K`，`BASH_MAX_OUTPUT_DEFAULT=30K`，`COMPACT_MAX_OUTPUT_TOKENS=20K`，`MODEL_CONTEXT_WINDOW_DEFAULT=200K`。

- **关键门控**：`CONTEXT_COLLAPSE`、`HISTORY_SNIP`、`REACTIVE_COMPACT`、`CACHED_MICROCOMPACT`、`CONTEXT_1M_BETA_HEADER`、`TASK_BUDGETS_BETA_HEADER`、`SUMMARIZE_CONNECTOR_TEXT_BETA_HEADER`、`DISABLE_AUTO_COMPACT`等。

- **源码文件索引**：`autoCompact.ts`、`compact.ts`、`microCompact.ts`、`grouping.ts`、`sessionMemoryCompact.ts`、`contextCollapse/index.js`、`query.ts`、`context.ts`、`tokens.ts`、`tokenEstimation.ts`、`toolResultStorage.ts`、`toolLimits.ts`等。

**输出状态**：教案已完整交付。下一步可继续第3讲（工具系统）的调查或教案撰写。

**用户补充**：提供了 `src/services/compact/prompt.ts` 源码文件（对应第2课第三幕中Compact Prompt模板）。

**AI基于源码的校正结论**：Claude Code的Compact是一个**强约束、强结构化、明确禁止工具调用**的摘要流程。核心要点：

- **9个固定栏目**：Primary Request and Intent、Key Technical Concepts、Files and Code Sections、Errors and fixes、Problem Solving、All user messages、Pending Tasks、Current Work、Optional Next Step（源码硬编码要求）。
- **禁止工具调用为激进双保险**：`NO_TOOLS_PREAMBLE`（首部强警告）+ `NO_TOOLS_TRAILER`（结尾再提醒），防止模型在compact单轮中误调用工具。
- **`<analysis>` 是草稿区（drafting scratchpad）**：用于提升摘要质量，但`formatCompactSummary()`会将其剥离，不进入后续上下文。设计思想：允许模型“多想一点”，但不保留思考成本。
- **`formatCompactSummary()` 三步处理**：删除`<analysis>` → 提取`<summary>`内容并替换为`Summary:`开头的纯文本 → 压缩多余空行。
- **摘要作为用户消息注入**：`getCompactUserSummaryMessage()`生成continuation message，内含摘要和是否保留最近消息、是否抑制追问、是否提供转录文件路径等控制参数。支持三种续接模式：可回查原始转录、标记最近消息原样保留、强指令继续任务而不承认中断。
- **Partial compact有两种语义**：`from`模式（仅总结最近新增消息，更早的retained context仍在）和`up_to`模式（总结前缀完整历史，摘要前置到继续会话开头，后接保留的最近消息）。

**对第2课教案的修正建议**：将原有“9部分结构化摘要”表述升级为强结构化模板；明确`<analysis>`为scratchpad；将摘要注入描述为continuation payload而非简单用户消息；区分partial compact的两种方向语义。

**工程价值点**：强no-tools双保险、允许分析不保留分析、摘要作为续接payload、partial compact有方向语义。

**后续选项**：AI可提供①第2课第三幕源码校正版重写稿、②继续源码调查形成完整调用链、③将`prompt.ts`单独整理为教学化提炼（源码解读+设计意图+可迁移模式+对Logic Graph启示）。
**第3课教案压缩：从Micrograd到Logic Graph——用依赖图管理AI任务上下文**

**课程定位**：承接第2讲（Claude Code上下文工程），指出现有压缩策略仍围绕“消息顺序”和“token数量”，缺乏对信息重要性和依赖关系的判断。本讲引入用户原创方案**Logic Graph**：将Agent任务中的用户目标、约束、工具结果、文件修改、决策、摘要显式组织成依赖图。任务是建立学生对“图式上下文管理”的第一层理解。

**核心问题**：AI的最终答案依赖哪些可观察的信息？能否追溯依赖的用户需求、文件内容、工具结果？能否判断哪些旧信息不能丢、前提变化后哪些结论失效、工具结果错误后哪些答案受影响？**追踪的不是模型内部思维，而是外部可记录的任务依赖关系。**

**Micrograd启发**：每个计算结果不是孤立的，而是带血缘档案（`_prev`前驱、`_op`操作）。类比到AI任务，将关键对象建模为`ContextNode`（含`content`、`prev_nodes`、`operation_type`、`node_type`、`metadata`）。示例：用户需求+约束+工具结果→判断→修改方案→最终答复，形成依赖图。

**Logic Graph改进上下文管理的四个问题**：
1. **哪些旧信息不能丢**：保留当前任务依赖链上的节点，而非仅保留最近消息。
2. **哪些内容可安全压缩**：节点状态分为active、dormant、summarized、external、garbage、invalidated。只压缩依赖链之外的节点。
3. **前提变化的影响传播**：当约束变更，标记依赖该约束的所有下游节点invalidated。
4. **工具结果错误的回溯**：`ToolResultNode → DecisionNode → FinalAnswerNode`，错误沿依赖边传播。

**课堂案例**：语音识别小工具的多条约束（包括“孩子只能按一个键”），展示依赖图如何确保关键约束不被压缩丢弃。

**与Claude Code的关系**：Claude Code的Compact是**执行层**（token不够时压缩上下文），Logic Graph是**决策层**（判断保留/摘要/丢弃）。二者不是互斥，而是组合成**依赖感知压缩**。

**第4讲教案压缩：让任务变成图——构建多轮对话的增量Logic Graph**

**本讲定位**：承接第3讲（Logic Graph记录外部可验证依赖），本讲确立“一个任务=一张持续更新的图，每轮对话=一次Graph Patch”。目标是让学生理解：何时启动建图、每轮只做增量补丁不重建全图、重复节点用Upsert+superseded标记。

**核心概念**：
- **任务级图 vs 轮次级图**：错误做法是每轮建新图（大量重复）。正确做法是TaskGraph持续存在，每轮产生Patch（含new_nodes、updated_nodes、superseded_nodes）合并进图。
- **启动时机**（本讲只实现手动模式）：用户输入`/task start`显式创建；半自动或全自动后续课程再讲。
- **节点类型**（7种）：UserGoal、Constraint、Fact、ToolResult、Decision、FileArtifact、OpenTask。节点状态：active / superseded / done。
- **Patch结构**：包含task_id、turn_id、new_nodes、updated_nodes、superseded_nodes（含原因）、new_edges。

**典型操作示例（三轮Minecraft AI Agent任务演化）**：
- 第1轮：用户提出目标（中文控制Minecraft）。系统创建TaskGraph，Patch1新增UserGoal节点和Fact，建立refines边。
- 第2轮：用户要求写命令映射器、用客户端斜杠命令。Patch2新增Decision节点，建立serves/implements边。去重器避免重复创建已有UserGoal。
- 第3轮：用户指出孩子账号无OP权限，推翻客户端方案，改用服务端RCON。Patch3新增Constraint节点和替代Decision节点及OpenTask，将旧Decision节点标记为superseded（不删除，留痕），新增invalidates边。

最终TaskGraph展示节点状态变化，体现“图是长出来的，被推翻的节点留痕可回溯”。

**最小可运行代码**（Python）：
- 定义`Node`（node_id, type, content, created_at_turn, status）、`Edge`、`TaskGraph`（nodes字典, edges列表）、`GraphStore`（内存存储）、`Deduplicator`（基于type+content归一化去重）、`GraphUpdater.apply_patch`（处理superseded→改状态；new_nodes带去重和id重映射；updated_nodes更新内容；new_edges映射后添加）。`to_mermaid`函数生成可视化。
- 运行示例：依次应用三个patch，最终节点数8，边数6，其中n_0005为superseded状态。

**本讲核心原则**：一个任务一张图；每轮只做Patch不做全量重建；被推翻节点不删，用superseded留下演化轨迹。

**与下一讲衔接**：第5讲将利用TaskGraph找到当前任务的依赖链，实现依赖感知压缩（active节点+关键Decision强保留，superseded节点弱摘要，旁支Fact摘要或丢弃）。

用户询问：是否存在一个旁路程序监听用户与主LLM的对话，并根据规则调用另一个大模型来生成Logic Graph。AI确认用户理解基本正确，并拆解为三种架构：

1. **旁路监听+独立LLM抽取**（最常见）：主对话LLM正常回答用户；另有一个Graph Extractor程序监听对话，调用另一个（通常更便宜的）小模型提取JSON格式的Graph Patch，再由GraphUpdater合并进TaskGraph。优点：解耦，抽取失败不影响主对话；缺点：多一次LLM调用，成本约为主对话30%-60%。
2. **主LLM自己顺手输出Patch**：通过function calling/structured output，主模型在回答用户的同时额外输出结构化JSON。优点：省一次调用，成本低；缺点：主模型分心可能影响回答质量。
3. **混合架构**（真实产品最常见）：轻量Patch由主模型顺手输出，复杂Patch由旁路小模型批量抽取，推翻/冲突检测等用规则程序不走LLM。

AI直接回答：是的，有另一个程序监听对话；它既用规则（如去重、superseded检测、边合法性校验）也用LLM（语义抽取）；抽取不一定非要另一个LLM，可以是独立小模型或主模型。第4讲教案中的代码仅实现了规则部分（GraphUpdater、Deduplicator），未实现LLM抽取模块；完整系统应增加GraphPatchExtractor，调用一个LLM客户端（建议用便宜模型）。主对话LLM可完全不感知图的存在。

**用户疑惑**：第4讲教案中的典型3轮操作如何执行？直接把用户话语给大模型，模型不会主动创建依赖图。最小可运行代码是什么意思？它会产生依赖图吗？这节课究竟该怎么操作？

**AI澄清**：

1. **执行机制**：不是把用户原话直接丢给主对话模型，而是通过一个**Graph Extractor Prompt**，让大模型明确执行“抽取依赖图Patch”的任务，而非回答用户或执行任务。每轮输入需附带已有TaskGraph摘要，模型才知上下文和推翻对象。

2. **最小可运行代码的含义**：代码本身**不理解自然语言**，只负责将已写好的Patch JSON合并成TaskGraph并输出Mermaid图。它验证的是“Patch可合并为演化图”，而非“自然语言→图”。自然语言→Patch需要额外的大模型调用。

3. **课堂真实操作流程**（建议改为训练旁路Graph Extractor）：
   - 老师提供Extractor Prompt（规定输出格式、节点类型、禁止执行任务）。
   - 学生将第1轮用户话语+空图摘要放入Prompt → 大模型输出Patch1 → 手动/程序填入代码。
   - 第2轮需携带已有图摘要 → 模型输出Patch2。
   - 第3轮需携带更新后的图摘要 → 模型输出Patch3（含superseded）。
   - Python代码合并三个Patch → 输出Mermaid图 → 粘贴到Mermaid Live查看。

4. **三种课堂操作方案**：
   - **A. 最低成本手工版**：人工复制用户话语到Extractor Prompt，复制Patch到Python，适合入门演示。
   - **B. 标准工程版**：用API自动调用LLM Extractor，程序自动构造Prompt、获取Patch、合并，适合进阶。
   - **C. 真实产品版**：旁路监听，主模型回答用户，旁路小模型抽取Patch，第4讲不实现。

5. **对第4讲的修改建议**：目标应明确为“输入三轮用户对话 → 通过Extractor Prompt生成三个Patch → 程序合并成TaskGraph”，而非“学生直接与大模型聊三轮”。教学操作清单应包含11步（从发Prompt到Mermaid看图）。

**核心结论**：第4讲的正确操作不是让大模型帮用户做Minecraft Agent，而是让大模型扮演Graph Extractor，只抽取每轮对话中的任务依赖Patch；Python最小代码只负责合并Patch成图。

**用户质疑**：Logic Graph仅在识别到任务时才建图，不是通用上下文压缩机制，是否还有价值？

**AI确认**：用户判断完全正确。Logic Graph不是通用压缩器，而是**任务态上下文压缩机制**（或“面向任务执行过程的依赖保真机制”）。没有任务时不启动，因为闲聊缺乏目标、约束、决策、依赖等结构。

**价值所在**：它的价值不在于压缩所有聊天，而在于压缩**任务型对话**（如做系统、写课程、调试bug、设计Agent等），保留目标、约束、决策、方案演化、待办、依赖等**任务结构**。普通摘要容易压扁这些结构，Logic Graph的优势是保真。

**三层架构建议**：
- 第一层：Recent Context（保留最近几轮原始对话）
- 第二层：Session Summary（普通聊天做轻量摘要）
- 第三层：Task Logic Graph（识别到任务后维护任务图）

Logic Graph不取代所有上下文管理，只负责最有结构价值的部分。

**课程定位修改建议**：
- 原说法“Logic Graph用来做上下文压缩”太大，应改为“Logic Graph不是通用对话压缩器，而是任务过程的结构化压缩骨架，只在进入任务态后启动”。
- 第5讲标题从“用Logic Graph压缩上下文”收窄为“用Logic Graph压缩**任务上下文**”或“用任务图保留关键依赖，降低长任务上下文压力”。

**核心结论**：没有任务不必建图，有任务图才有价值。Logic Graph是任务执行的结构化记忆，不是所有聊天的通用记忆。
**用户质疑**：第5讲中“token不够时根据TaskGraph判断保留/摘要/丢弃”的说法不准确。第4讲已明确Logic Graph只在任务态启动，第5讲不应重复建图时机，也不应主要讲压缩。用户要求澄清第4讲与第5讲的定位差异。

**AI核心修正**：

- **第4讲定位（写入侧）**：用户对话 → Extractor → Graph Patch → TaskGraph。回答“任务图怎么长出来”，产物是TaskGraph。
- **第5讲定位（读取侧）**：TaskGraph → Context Builder → Task Context Pack → 主LLM。回答“任务图怎么喂回主LLM”，产物是Task Context Pack（结构化任务上下文包，而非“压缩后的聊天记录”）。

**关键决策**：
- 第5讲标题应从“用Logic Graph压缩上下文”改为**“从TaskGraph到Context Pack：把任务图喂回主LLM”**或**“让图重新变成上下文——Task Context Pack的生成”**。
- 第5讲不应以token不够为主线，而应以**构建Context Pack**为主线：从OpenTask出发，追踪依赖边，提取当前目标、有效约束、当前决策、OpenTask、相关事实，并将superseded节点单独列项（防止主LLM继续使用被推翻方案）。
- 原第5讲中token预算、节点状态打分等内容应弱化或移到扩展部分，不作为主线。

**与第4讲的衔接**：第4讲结尾原话“第4讲让图长出来，第5讲用图压上下文”应改为**“第4讲让图长出来；第5讲让图重新变成主LLM能使用的任务上下文”**或**“第4讲讲写入TaskGraph；第5讲讲读取TaskGraph”**。

**后续行动**：按新定位重写第5讲教案，核心Demo延续第4讲的Minecraft TaskGraph，生成示例Context Pack（含当前任务、目标、有效约束、当前有效决策、已推翻方案及原因、相关事实）。

**第5讲教案压缩：从TaskGraph到Context Pack——把任务图喂回主LLM**

**本讲定位**：完成读取侧——将第4讲生成的TaskGraph转换为主LLM可继续执行任务的结构化上下文包（Task Context Pack）。不再讨论建图时机、自然语言抽取、token压缩（分别属第4讲、第2讲）。核心问题：当一个任务已被TaskGraph跟踪后，如何整理成主LLM能直接使用的上下文？

**与第4讲分工**：
- 第4讲（写入侧）：用户对话 → Graph Patch → TaskGraph，回答“任务图怎么长出来”。
- 第5讲（读取侧）：TaskGraph → Context Builder → Task Context Pack → 主LLM，回答“任务图怎么喂回主LLM”。

**学习目标**：理解不能直接把整张图塞入Prompt（图结构对LLM不友好、active/superseded混用、无阅读顺序、图会变大）；能实现`build_context_pack(task_graph, current_focus_id)`，区分active与superseded节点，生成结构化包；能将包转换为Prompt片段注入主LLM。

**课时90分钟**：回顾第4讲(5')→为什么不能直接塞图(10')→定义Context Pack(15')→从当前焦点读取依赖链(20')→最小代码实现(25')→注入主LLM(10')→总结扩展(5')。

**Task Context Pack定义**：结构化字段包含task_id、current_focus、goals、active_constraints、current_decisions、relevant_facts、open_tasks、superseded_history。不是聊天摘要或图dump，而是继续任务所需的状态。

**从焦点读取依赖链**：当前焦点（如最新active OpenTask）出发，沿`depends_on`/`implements`/`serves`/`refines`向上游追踪；同时收集`invalidates`边将被推翻方案放入superseded_history。强调：边既记录演化也指导读取。

**最小代码实现**：提供`latest_active_open_task`、`trace_upstream`（允许关系集）、`collect_superseded_history`、`build_context_pack`、`context_pack_to_prompt`。使用第4讲Minecraft例子的图，演示生成Context Pack，并指出若`active_constraints`为空，需在建图时补充`depends_on`边（新方案依赖约束），这体现“读取倒逼建图质量”。

**注入主LLM**：将Context Pack转换为Markdown风格的Prompt片段，附加约束说明（不采用已推翻方案、遵守约束、围绕当前焦点）。对比有无Context Pack时模型缺失的信息（为什么用RCON、旧方案被推翻、权限约束等）。

**总结与扩展**：Logic Graph的第一价值不是压缩token，而是组织任务状态。当上下文紧张时，Context Pack可替代大量原始历史，但它是常规读取产物，非紧急压缩。扩展：图太大时可按焦点读子图、分层（active强保留、superseded只留原因）、大型结果外置。

**评分标准**：能区分TaskGraph与Context Pack、选择合理焦点、字段完整、superseded不混入当前决策、能通过边解释读取原因。

**与下一讲衔接**：第6讲讨论哪些任务节点应沉淀为长期记忆（FactNode、ConstraintNode、DecisionNode等）。

**核心三句话**：TaskGraph不是直接塞Prompt的内容；Context Pack才是主LLM继续执行任务的上下文；第4讲讲写入图，第5讲讲读取图。

**用户请求**：基于前5讲整体课程设计（作为附件提供），重新审视第6讲教案，判断是否需要修改。若改动较大则给出重新思考后的结果。

**AI判断**：需要**较大修改**。原因：原第6讲出发点错位——将第5讲理解为“依赖感知压缩”，但前5讲最新定位中第5讲已改为“TaskGraph → Context Pack → 主LLM”（读取任务图），而非压缩上下文。第6讲应相应调整。

**修改后第6讲定位**：
- 第4讲：任务图长出来（写入侧）
- 第5讲：任务图整理成Context Pack喂给主LLM（读取侧）
- **第6讲：任务结束后，哪些任务信息沉淀为长期Memory Store，并在新任务中召回**

**保留的原内容价值**：摘要记忆vs结构化记忆对比、记忆节点类型（Fact/Preference/Constraint/Decision/Task/Error）、生命周期（create/update/merge/invalidate/delete）、失效传播、记忆召回。需修改三点：①不将第6讲定位为第5讲压缩的升级版，而是“长期沉淀层”；②Memory仍服务于任务态（项目、约束、决策、踩坑、待办），非通用聊天记忆；③召回路径改为：Memory → TaskGraph → Context Pack → 主LLM，而非直接塞入prompt。

**Memory与TaskGraph/Context Pack的关系**：
- TaskGraph：当前任务的依赖结构，生命周期为任务内
- Context Pack：当前任务喂给主LLM的上下文包，动态构建
- Memory Store：跨任务、跨会话的长期任务记忆，长期存在
- 流程：用户对话 → Graph Extractor → TaskGraph → Context Builder → Context Pack → 主LLM；任务阶段结束后，TaskGraph → Memory Extractor → Memory Store；新任务时，Memory Store → Recall → 新TaskGraph种子节点 → Context Pack。

**值得沉淀的节点类型**：长期目标、稳定约束、当前有效决策、用户偏好、未完成任务、踩坑记录。不应沉淀：临时推理步骤、大段工具输出、已被推翻的方案、闲聊、不稳定猜测。

**记忆节点类型**（六类）：FactMemory、PreferenceMemory、ConstraintMemory、DecisionMemory、OpenTaskMemory、ErrorMemory。可选加ArtifactMemory（重要文件路径）。

**记忆生命周期**：create、update、merge、invalidate、archive、delete。重点是记忆可更新、可撤销、可追溯。

**失效传播**：发生在Memory Store和TaskGraph两层之间。当约束变化时，不应简单级联删除，而是：invalid → downstream suspect → 需要重新确认。

**召回机制**：记忆不是直接塞入prompt，而是先召回到新TaskGraph（生成MemoryReferenceNode），再由第5讲Context Builder生成Context Pack。

**课堂Demo建议**：延续Minecraft场景，分Session 1（提出目标与约束）、Session 2（补充权限限制，更新决策）、Session 3（下次会话召回记忆），展示沉淀→更新→召回闭环。

**最终判断**：不建议维持原第6讲教案，需按上述方向重写。原教案技术模块可保留，但主线应从“从摘要记忆到结构化任务记忆”调整为“从TaskGraph到长期任务记忆，再召回到新的TaskGraph”。

**第6讲完整教案压缩：任务记忆沉淀——从TaskGraph到长期Memory Store**

**本讲定位**：第4讲（写入侧：对话→TaskGraph），第5讲（读取侧：TaskGraph→Context Pack→主LLM），第6讲解决：任务结束后，哪些内容值得长期记住，并在新任务中召回。**不是讲压缩，而是讲任务记忆的长期沉淀与召回。**

**核心流程**：
- 会话1：用户提出任务 → TaskGraph记录过程 → 任务阶段结束 → Memory Extractor抽取长期记忆 → Memory Store保存。
- 会话2：用户继续任务 → Recall召回相关记忆 → 生成新TaskGraph种子节点 → Context Builder生成Context Pack → 主LLM继续工作。

**Memory vs TaskGraph vs Context Pack**：
- TaskGraph：记录当前任务的目标、约束、决策、依赖，生命周期任务内。
- Context Pack：每次给主LLM的动态上下文包。
- Memory Store：跨任务、跨会话保存稳定任务记忆（长期存在）。

**值得沉淀的记忆类型**（6+1类）：
- GoalMemory（长期目标）、ConstraintMemory（稳定约束）、PreferenceMemory（用户偏好）、DecisionMemory（当前有效决策）、OpenTaskMemory（未完成任务）、ErrorMemory（踩坑/失败经验）、ArtifactMemory（重要文件路径，可选）。
- 不沉淀：临时推理、大段工具输出、已推翻方案（作为当前方案）、闲聊、不确定猜测。

**Memory数据结构**：memory_id、type、content、status（active/suspect/invalid/archived/deleted）、source_task_id、source_node_ids、tags、confidence、supersedes、invalidates。

**生命周期操作**：create、update、merge、invalidate、mark_suspect、archive。**失效不是删除，而是留痕**（标记invalid+记录原因），后续Context Pack中放入superseded_history，让LLM知道为什么旧方案不可行。

**召回机制**：通过tags检索，召回结果生成**MemoryReferenceNode**进入新TaskGraph，再由第5讲Context Builder生成Context Pack，**不直接塞入主LLM**。

**课堂Demo（延续Minecraft）**：
- Session1：用户提出目标与约束 → 沉淀GoalMemory、ConstraintMemory、PreferenceMemory。
- Session2：用户补充权限限制 → 新增ConstraintMemory、DecisionMemory、ErrorMemory，invalidate旧DecisionMemory。
- Session3：用户回来继续 → 召回相关记忆 → 生成种子节点 → 输出Context Pack（含目标、约束、决策、已推翻方案及原因、待办）。

**Memory Extractor Prompt模板**（旁路抽取器）：只抽取任务记忆类型，不回答问题；输出new_memories、updated_memories、invalidate_memories；临时信息不保存。

**最小代码**：`MemoryStore`类提供add_memory、invalidate_by_content、recall；`memories_to_seed_nodes`将召回记忆转换为MemoryReferenceNode。强调代码只做存储和召回，不涉及自然语言理解。

**评分标准**：记忆类型准确、不乱记、能处理失效、能召回、能接入TaskGraph、能生成Context Pack。

**与下一讲衔接**：第6讲解决单个用户长期任务记忆；第7讲进入多Agent协作时的TaskGraph归属和Memory共享问题。

**本讲核心三句话**：
- TaskGraph记录任务过程。
- Context Pack服务当前生成。
- Memory Store保存跨会话的长期任务记忆。

**第7讲重新审视结论**：需要较大修改。原方向“多Agent不广播全量上下文，而是传必要子图”正确，但与第4-6讲最新定位不匹配：第5讲已是“TaskGraph→Context Pack”，而非图式压缩；Worker不应直接修改图，应返回Patch；Memory Store需纳入边界设计；Verifier应验证Claim+Evidence Pack。

**重写版第7讲核心内容**：

**本讲定位**：解决多Agent协作时TaskGraph的一致性、边界性和可验证性。Coordinator基于TaskGraph为不同Worker构造最小Worker Context Pack；Worker只返回结果和Graph Patch；Coordinator统一合并；Verifier独立验证关键Claim。

**核心架构**：用户对话 → Graph Extractor → TaskGraph → Coordinator（为Worker A/B/C生成Context Pack）→ Worker返回Result+GraphPatch → Patch Merge/Conflict Check → 更新TaskGraph → Verifier接收Claim+Evidence Pack → 验证Patch → TaskGraph → Context Builder → 主LLM。原则：TaskGraph单写入，Worker多读取。

**三种上下文包**：
- **Worker Context Pack**：给Worker的子任务上下文（子任务目标、相关目标、有效约束、当前决策、必要事实、已推翻方案、边界限制）。
- **Worker Result Package**：结构化返回（summary、claims、graph_patch）。
- **Verification Pack**：验证Claim+Evidence，输出supports/contradicts/insufficient。

**角色重新定义**：
- Coordinator：拆任务、分发、合并、调度验证，可合并Patch。
- Worker：执行子任务，只返回WorkerResult+GraphPatch。
- Verifier：独立验证Claim+Evidence，返回Verification Patch。
- Graph Extractor：抽取Patch。
- Memory Store：由Coordinator召回，不直接暴露给Worker。

**课堂主线**：
- 广播式多Agent的问题（token爆炸、错误传播、幻觉放大）。
- 从TaskGraph生成Worker Context Pack（`build_worker_context_pack`伪代码）。
- Worker返回Graph Patch而非直接改图（含new_nodes、new_edges、依赖边检查）。
- Patch合并与冲突处理（身份冲突、内容冲突、依赖冲突；合并协议伪代码）。
- Verifier独立验证关键Claim（只看Claim+Evidence，写回Verification Patch）。
- 课堂Demo延续Minecraft场景：拆3个Worker → 生成Context Pack → 返回Patch → 合并 → 冲突发现（客户端命令与无OP权限）→ Verifier验证RCON → 更新TaskGraph → 重新生成主LLM Context Pack。

**本讲核心结论**：单Agent时代核心是TaskGraph写入与读取；多Agent时代核心是不同Agent只能看到自己的Context Pack；TaskGraph必须单点合并，Worker只能提交Patch，Verifier只看证据。**不建议维持原第7讲教案**，应改为上述重写版。

**第8讲教案重新审视结论**：需要中等幅度调整。原主干（工具结果节点化、文件节点化、失效传播）正确，但Verifier与taint传播写得太重，易偏离主线。修订后聚焦：**工具调用和文件系统如何进入Logic Graph，成为可追踪、可压缩、可失效的上下文证据**。

**修订重点**：
- 主线改为：工具调用 → 工具结果 → 文件产物 → 测试结果 → 依赖边 → 压缩与失效。Verifier重放可作为后半段扩展，不压过主线。
- 增加**TestResultNode**（命令、状态、passed/failed、输出引用），体现测试结果作为关键证据。
- 弱化“证据能重放”，强化“证据能追踪”。核心表述改为：信息有来源，依赖有方向，文件有版本，结果能回查。

**修订后第8讲结构（90分钟）**：
1. **0-10' 问题引入**：工具结果仅作为文本的缺陷（截断、依赖不清、版本不明、失效难追踪）。
2. **10-30' 四类核心节点**：ToolCallNode、ToolResultNode、FileArtifactNode（含版本哈希）、TestResultNode。强调大结果写盘+预览引用，不塞入上下文。
3. **30-45' 工具输出写盘与引用回填**：小结果内联，中/大结果保存文件/对象存储，只给preview+full_ref。连接第5讲压缩（可丢preview，不可丢被依赖的full_ref）。
4. **45-60' 文件版本与代码修改追踪**：示例Read→ToolResult→Decision→Write→FileArtifact→Test→FinalAnswer，展示依赖链。
5. **60-75' 失效传播**（简化版）：当工具结果错误或文件变化，标记tainted并向下游传播。给出`taint()`伪代码，不深入Verifier细节。
6. **75-85' Demo**：根据config.yaml配置数据库→写代码→测试→修改config.yaml→观察下游节点变tainted/suspect/invalid。
7. **85-90' 总结**：工具、文件、测试结果都是可追踪节点。本讲解决“外部证据如何进入依赖图”。

**最终判断**：原第8讲不需要推翻，但需降重Verifier，增强Tool/File/Test三类工程节点，使之与第5-7讲衔接更顺。
**第9讲重新审视结论**：需要较大修改。原方向“可观测性与调试”正确，但不应做成“AI Reasoning Debugger”或实时UI调试器，而应调整为**TaskGraph管线调试**——观察Graph Patch、TaskGraph、Context Pack、Memory Recall、工具证据等工程对象，定位错误来自抽取、合并、上下文构建、召回还是证据失效环节。

**核心定位修正**：第9讲不是解释模型内部推理，而是**把Logic Graph系统中看不见的中间产物变成可检查、可回放、可验证的调试界面**。核心问题：系统输出错了，是Extractor抽错、Graph合并错、Context Pack漏、Memory召回错，还是工具证据失效？

**与前8讲衔接**：
- 第4讲 Graph Patch → 观察节点/边抽取是否正确
- 第5讲 Context Pack → 观察哪些节点入选、哪些排除及原因
- 第6讲 Memory Store → 观察召回是否准确、是否过期
- 第7讲 多Agent → 观察Worker上下文与Patch合并
- 第8讲 工具/文件/测试 → 观察证据链与失效状态

**学习目标**：看懂中间产物；判断错误环节；为每个保留/排除/推翻/召回/合并记录reason；能用最小UI或静态报告展示任务状态；能回答主LLM看到了什么、为什么看到这些、旧方案为何被推翻、工具证据支撑了哪些结论。

**核心产物（本讲先做静态报告，非实时UI）**：`Task Context Debug Report`，含conversation.md、patches.json、task_graph.json、context_pack.md、memory_recall.json、evidence_index.json、timeline.json、graph.mmd。

**课堂结构（90分钟）**：
- 0-10' 引入：错误例子（明明有无OP权限约束，模型仍建议客户端命令），判断可能出错环节（抽取/图连接/上下文构建/旧方案未正确排除/记忆召回过期）。
- 10-25' 定义六类可观测对象（Patch、TaskGraph Snapshot、Context Pack、Memory Recall Report、Evidence Index、Event Timeline）。每类必须含reason字段。
- 25-45' **Context Pack Trace**（本讲最重要）：给Context Pack中每个条目增加`included_reason`和`excluded_reason`，解释为何入选/排除。调试上下文包比调试最终回答更重要。
- 45-60' TaskGraph可视化（用Mermaid，区分active/superseded/invalid/memory/tool evidence节点状态）。
- 60-75' 事件时间线（任务状态变化，每个事件含turn、event类型、target、reason）。
- 75-85' 完整Demo（Minecraft场景），学生检查四件事：约束是否进图？旧方案是否superseded？Context Pack是否含有效约束？最终方案是否依赖工具证据？
- 85-90' 总结三句话：可观测性看上下文系统而非模型思维；调试重点是中间产物而非最终答案；可信系统能解释信息保留/排除的原因。

**对原第9讲的保留与修改**：
- 保留：事件总线、时间线、节点详情面板、payload_ref解引用、taint/invalid展示、Diff模式。
- 修改重点：从“AI Reasoning Debugger”改为“Task Context Debugger”；实时WebSocket UI降为选做，先做静态Debug Report；Token曲线降为辅助，核心是Context Pack Trace；taint传播保留但作为第8讲延伸；Time Travel作为高级扩展。

**最终判断**：原第9讲“可观测性”方向保留，但要从“炫酷图调试器”重写为“TaskGraph到Context Pack的工程调试器”，服务于整套课程的闭环（第4讲长图 → 第5讲生成包 → 第6讲沉淀记忆 → 第7讲多Agent边界 → 第8讲工具证据 → 第9讲被看见、检查和调试）。

**第10讲教案压缩（总结与路线图）**  
本讲需较大修改。原第10讲基于早期设定（依赖感知压缩/AI推理调试器），但前9讲已调整为**任务态上下文管理管线**（对话→Graph Patch→TaskGraph→Context Pack→主LLM，以及Memory沉淀、多Agent协作、工具证据、Debug Report）。本讲核心三任务：①闭环前9讲成完整工程管线；②明确定位“是什么、不是什么”；③给出后续工程/产品/研究/教学路线图。

**核心定位修正**：主线不再是“依赖感知压缩”或“AI推理调试器”。压缩只是副产物（Context Pack结构化更短，缓解上下文压力）。调试对象不是模型思维，而是工程对象（Patch抽取、TaskGraph合并、Context Pack遗漏、Memory召回过期、工具证据支撑、节点排除正确性）。最终定义：**Logic Graph是任务态上下文管理机制**，通过TaskGraph记录目标/约束/事实/决策/工具结果/文件产物/记忆引用/被推翻方案，通过Context Pack结构化状态喂给主LLM。它不是模型内部推理还原，不是通用聊天压缩器，不是Compact替代品，不是万能长期记忆，不是可上线的工业系统。

**前9讲分工回顾**：第0-3讲问题意识与概念；第4讲写入侧（Patch→TaskGraph）；第5讲读取侧（TaskGraph→Context Pack）；第6讲长期沉淀（Memory Store与召回）；第7讲多Agent协作（Worker Context Pack+Patch合并）；第8讲工具证据（Tool/File/Test节点）；第9讲可观测性（Debug Report）；第10讲系统闭环。

**最终Demo（延续Minecraft场景）**：用户提出任务→Extractor输出Patch（目标/偏好/事实）→补充约束（一个键、无OP权限）→Patch新增Constraint，标记旧客户端方案superseded，新增服务端RCON决策→Context Builder生成Context Pack（目标、有效约束、当前方案、已推翻方案）→Memory沉淀→新会话召回记忆→工具证据入图（读取配置、测试RCON）→Debug Report解释为何建议RCON而非客户端命令。强调没有TaskGraph会重复旧方案，没有Context Pack会漏关键信息，没有Memory下次会丢失，没有Debug Report无法定位错误层。

**下一步路线图**：  
- 工程路线：封装成Python包（extractor/graph/context_builder/memory/coordinator/evidence/debug_report/examples）。  
- 产品路线：做“Task Context Debugger for AI Agents”，卖点为主LLM可见上下文、漏掉约束、旧方案被推翻、工具证据支撑、多Agent结果合并。  
- 研究路线：抽取准确率、Context Pack对长任务完成率提升、Memory过期冲突、多Agent Patch一致性、失效传播策略。  
- 教学路线：可打包成AI Agent工程课/上下文管理专题课/Logic Graph实战课。

**最终收束**：课程真正主线不是Claude Code或某个feature flag，而是**复杂Agent系统如何管理任务状态**。Claude Code展示工业应对上下文爆炸的手段，Logic Graph尝试回答：若显式记录目标、约束、决策、证据和被推翻方案，Agent能否更稳定地继续工作。

## 第5讲教案：从TaskGraph到Context Pack——把任务图喂回主LLM（压缩版）

**本讲定位**：完成读取侧——将第4讲生成的TaskGraph转换为主LLM可继续执行任务的结构化上下文包（Task Context Pack）。不再讨论建图时机、自然语言抽取、token压缩（分别属第4讲和第2讲）。

**第4讲与第5讲分工**：第4讲解决“任务图怎么长出来”（写入侧）；第5讲解决“任务图怎么喂回主LLM”（读取侧）。TaskGraph是内部记忆结构，Context Pack才是主LLM的任务上下文。

**学习目标**：说清不能直接塞整张图；理解Context Pack作用；能根据当前焦点从图中提取目标、约束、决策、事实、待办；区分active与superseded；实现`build_context_pack()`；转换为Prompt片段。

**课时90分钟**：回顾(5')→为何不能直接塞图(10')→定义Context Pack(15')→从焦点读依赖链(20')→最小代码(25')→注入主LLM(10')→总结(5')。

### 为什么不能直接塞整张图
1. 图结构对模型不友好（需额外推理）。
2. active和superseded混用，模型可能误用旧方案。
3. 图没有天然阅读顺序。
4. 图会越来越大，无法全量塞入。

### Task Context Pack定义
结构化字段：`task_id`、`current_focus`、`goals`、`active_constraints`、`current_decisions`、`relevant_facts`、`open_tasks`、`superseded_history`。它是“当前任务继续执行所需的目标、约束、决策、事实、待办和历史变更说明”，不是聊天摘要或图dump。

### 从当前焦点读取依赖链
当前焦点（如最新active OpenTask）出发，沿`depends_on`/`implements`/`serves`/`refines`向上游追踪；同时扫描`invalidates`边收集被推翻方案放入`superseded_history`。边既记录演化也指导读取。

### 最小代码实现（核心片段）
定义`Node`(id,type,content,status)、`Edge`、`TaskGraph`。函数：
- `latest_active_open_task`
- `trace_upstream`（沿允许关系集递归/迭代）
- `collect_superseded_history`（找invalidates边）
- `build_context_pack`：组合上述，按类型分组放入相应字段，仅保留active节点
- `context_pack_to_prompt`：转换为Markdown风格Prompt片段

**关键教学点**：若图中约束未进入Context Pack，说明缺少从新方案到约束的`depends_on`边——读取倒逼建图质量。示例中改进边关系后有效约束被正确包含。

### 注入主LLM
将Context Pack作为系统提示或上下文字段插入主LLM，附加强约束：不采用已推翻方案、遵守约束、围绕焦点推进。

### 总结与扩展
Logic Graph第一价值不是压缩token，而是组织任务状态。Context Pack是任务态常规读取产物，上下文紧张时可替代大量原始历史。扩展：图太大时可按焦点读子图、分层保留（active强保留，superseded只留原因）。

**核心三句话**：TaskGraph不是直接塞Prompt的内容；Context Pack才是主LLM继续执行任务的上下文；第4讲讲写入图，第5讲讲读取图。

## 第5讲代码读取方式修正

**用户指出**：`context_pack_builder.py` 中手写 `graph.nodes` 和 `graph.edges` 的做法不合理。第4讲已将 TaskGraph 保存为 `graph_state.json`，第5讲应直接读取该文件，而非让用户手动拆解。

**AI 修正**：同意并给出修正版代码，核心改动如下：

1. **新增 `load_task_graph_from_json(path)`**：读取第4讲持久化的 `graph_state.json`，还原 `TaskGraph` 对象。
2. **命令行入口默认读取 `graph_state.json`**：支持手动指定焦点 ID。
3. **演示代码改为**：
   ```python
   graph = load_task_graph_from_json("graph_state.json")
   pack = build_context_pack(graph)
   ```
4. **教学判断**：手写 Minecraft 示例只能作为最小测试 fixture，不能作为主流程。第5讲必须消费第4讲的产物，否则割裂两讲链路。

**工程原则**：第4讲生成并保存 `graph_state.json`，第5讲读取它生成 Context Pack。不再手工构造图。
## 第5讲输出方式修正

**用户指出**：不应仅将 Context Pack 打印到控制台，而应写入文件，方便手动复制粘贴，同时与后续工程化自动化流程保持一致（手动流程仅是自动化的可观察版本，不应割裂）。

**AI 修正**：同意并给出写入文件的方案：

1. **新增 `write_context_outputs()`**：将 `context_pack.json`（机器可读）和 `context_prompt.md`（人类可读/供 LLM 复制）写入当前目录。
2. **修改 `__main__`**：调用写入函数，输出文件路径及下一步操作提示（手动阶段复制 md 文件；自动化阶段直接读取同一文件提交给 LLM）。
3. **教学口径调整**：从“复制控制台输出”改为“打开 `context_prompt.md` 复制全文”，确保手动与工程化使用同一条数据链路。

**核心原则**：手动不是临时旁路，而是自动化前的可观察版本。

## 第5讲输出检查与修正

**用户**：执行 `context_pack_builder.py` 后发现 `context_prompt.md` 行数无变化，怀疑输出不正确，并附上 `graph_state.json` 和 `context_prompt.md`。

**AI 诊断**：确认输出不完全正确。当前焦点 `n_0049` 依赖 `n_0044`、`n_0036`，但图中相关节点 `n_0045`（阻塞链）、`n_0046`（文件位置）、`n_0047`（API已实现）、`n_0048`（返回格式）未被纳入上下文，因为现有算法仅沿上游追踪并扩展 UserGoal 邻居，遗漏了当前焦点链路周围的二级细节节点（如 refinement/support 节点）。

**解决方案**：替换 `collect_relevant_node_ids` 函数，增加 `expand_incoming_neighbors`（反向吸收指向已选节点的节点，最多2轮），使 `n_0047`、`n_0048` 等通过 `refines/derived_from/supports` 边被纳入。

**附加问题**：图中 `n_0045`（阻塞中）与 `n_0047`（已实现）状态冲突，应标记 `n_0045` 为 `superseded` 或增加 `invalidates` 边，否则 LLM 困惑。

## 第5讲输出验证与图状态修正

**用户**：根据建议修改后输出新的 `context_prompt.md`，询问是否符合预期。

**AI 确认**：基本符合预期。二级节点（n_0037、n_0038、n_0040、n_0041、n_0045、n_0046、n_0047、n_0048）已被正确纳入，解决上一版遗漏问题。

**仍存在问题**：`context_prompt.md` 同时包含两条冲突事实：“当前阻塞链：TKT-2026-003处于open状态”与“TKT-2026-003已实现”。这非 Builder 错误，而是 `graph_state.json` 中 `n_0045` 应标记为 `superseded`，并增加 `n_0047 --invalidates--> n_0045` 边。修改后冲突事实将移入“已推翻或废弃内容”部分。

**最终判断**：算法改进有效，剩余问题属于图状态更新机制。

## graph_state.json修改方式纠正

**用户指出**：直接修改 `graph_state.json` 不正确，因为它是上游 patch 拼接的产物，不应作为编辑入口。

**AI 确认并修正**：正确做法是通过 patch 系统表达状态变更——追加新 patch（如 `patch9.json`），在其中标记 `n_0045` 为 `superseded`、增加 `n_0047 invalidates n_0045` 边，然后重新运行 `apply_patches.py` 和 `context_pack_builder.py`。

**工程化原则**：`graph_state.json` 是编译产物，不应手改。数据链路为 `patch*.json → patch_applier.py → graph_state.json → context_pack_builder.py → context_prompt.md`。手动阶段也应遵循“新增 patch → 重新生成 → 重新构建”流程，与自动化保持一致。

## patch修改合理性纠正与信息需求

**用户指出**：graph_state.json是patch拼接产物，而patch本身也有上游生成方式（如对话理解/记忆抽取流程），直接手改patch同样不合理。

**AI承认错误**：需要了解patch的完整生成链路才能判断正确修正入口。问题本质是“事实推翻关系应在哪一层产生”。

**AI请求补充信息**：
1. patch的生成方式（手动/LLM总结/自动脚本/每轮对话输出）
2. patch是否不可变事件日志（追加式纠错 vs 允许改写历史）
3. patch生成提示词/规则（是否要求识别superseded_nodes、invalidates边）
4. apply_patches.py或等价合成代码（如何处理new_nodes/updated_nodes/superseded_nodes）
5. 期望的“事实过期”判断层级（patch生成阶段/applier阶段/context builder阶段）

**AI修正后的结论**：不应直接改graph_state.json，也不应直接改旧patch；正确做法是回到patch生成机制，确定由生成器输出还是后处理程序补全冲突消解。

## patch问题定位需求

**用户询问**：是否需要项目AI先定位具体哪个patch/哪轮对话出问题，还是只需提供任意一个生成patch的prompt模板。

**AI回答**：建议先定位具体patch/轮次（问题可能是某一轮语义判断漏掉了superseded/invalidates）。定位后需提供：①该轮生成patch的prompt模板；②该轮对话原文或摘要；③实际生成的patch文件。若模板每轮相同，通用模板也可，但精准判断需要出问题那一轮的对应信息。

## 问题解决方案

**核心冲突**：`n_0045`（TKT-2026-003阻塞）与 `n_0047`（已实现）同时存在，修正入口在哪？

**正确方案**：分层处理，不手改编译产物或旧 patch。

**第一层（根本解决）**：Patch 生成器（Graph Extractor）在将对话转为 Patch 时必须识别语义冲突，输出 `superseded_nodes` 和 `invalidates` 边。需检查/改进其 Prompt 模板。

**第二层（兜底保护）**：Context Builder（第5讲）只读检测冲突，将矛盾旧状态移入 `superseded_history` 并附加说明，不回写图。

**职责分工**：
- Patch生成器：语义理解，应输出冲突消解 ✅
- patch文件：不可变事件日志，追加新patch ❌
- Patch Applier：机械合并，不做语义判断 ❌
- graph_state.json：编译产物，禁止手改 ❌
- Context Builder：只读兜底（检测+降级），不回写图 ⚠️

**下一步**：先提供 Graph Extractor 的 Prompt 模板，确认生成方式（LLM/规则/手动），再追加 `patch9.json` 走正确流程。

## 诊断结果摘要

**项目AI检查结论**：
1. **Graph Extractor Prompt缺少事实冲突检测指令**——这是`n_0045`与`n_0047`矛盾共存的直接原因。现有Prompt以新节点为中心，未要求扫描图中已有active节点检查矛盾。规则示例仅覆盖“旧方案被用户否定”，未涵盖“新事实自动使旧事实失效”。
2. **Patch生成方式**：LLM通过Graph Extractor Prompt逐轮生成，属于“旁路监听+独立LLM抽取”架构的手工教学版（用户手动粘贴对话和图状态→LLM输出Patch→手动保存）。

**核心诊断**：问题本质是Extractor职责边界缺少矛盾检测。LLM仅在用户明确否定旧方案时输出`superseded_nodes`，但在新事实与旧事实矛盾（如工单open→已实现）时不会主动检测。

**两层修复建议**：
- **Extractor Prompt层（根本）**：新增“事实一致性反向检查”——强制扫描图中所有active节点，若本轮新信息与某旧节点描述同一实体且状态矛盾，必须输出`superseded_nodes`和`invalidates`边。
- **Patch Applier层（兜底校验，只报不改）**：合并后扫描矛盾状态，输出warning.json但不自动修改。

**下一步需用户提供**：①Patch的生成方式（手动用某模型还是自动化程序）；②出问题的完整Patch JSON及对应对话原文；③希望LLM做实体识别+矛盾检测，还是Applier规则硬匹配。
## 用户问题与AI诊断

**用户问题**：
- 手动将 `graph_state.json` 和对话粘贴到模板 `taskgraph压缩模板.md`，交给网页版 Deepseek-v4 生成 Patch，但不知道哪个 Patch（patch1.json~patch8.json）有问题。
- 请求对“第3点”（Prompt 教 LLM 做实体识别+矛盾检测 vs Applier 规则硬匹配）给出建议。

**AI 诊断**：
- 问题出在 **patch1、patch4、patch5、patch7**，它们使用了模板中未定义的 relation `"supports"`（模板只允许 `refines | depends_on | invalidates | implements | serves | produces | derived_from`）。
- 具体非法边：
  - patch1: `n_0004(Fact) → n_0002(UserGoal): "supports"`
  - patch4: `n_0034(Fact) → n_0002(UserGoal): "supports"`
  - patch5: `n_0046(Fact) → n_0034(Fact): "supports"`
  - patch7: `n_0050(Fact) → n_0036(Decision): "supports"`

**建议（对第3点的回应）**：
AI 未直接回答“矛盾检测 vs 规则硬匹配”，而是针对 `supports` 问题给出两种方案：
- **方案 A（推荐）**：修改模板，将 `supports` 加入合法 relation 列表（语义上可表示“支撑某事实或决策”，区别于 `serves` 服务于目标）。
- **方案 B**：修复 4 个 Patch，将非法边改为模板中已有 relation（如 `serves`、`derived_from`、`refines`）。

**注意**：AI 未就“实体识别+矛盾检测”与“规则硬匹配”给出明确建议，仅解决了 relation 非法问题。用户可能需要进一步追问。

## 工作流修正建议

**用户目标**：验证工作流正确性，而非修补既有结果（不补patch9、不改graph_state.json）。

**AI诊断**：问题在于Graph Extractor Prompt。现有规则“新信息使旧节点不再成立时需输出superseded_nodes”太抽象，LLM只在用户明确否定旧方案时执行，不会主动识别工单状态冲突（如“open”→“已实现”）。

**模板修改方案**：
1. **新增“事实一致性反向检查规则”**：强制扫描图中active节点，检测同一实体（工单/接口/文件/方案/阻塞链）的状态迁移。包括：工单open→已实现、阻塞失效、接口明确化、方案替代、文件路径变更等场景，必须输出superseded_nodes和invalidates边。
2. **将`supports`加入合法relation枚举**（原为`refines|depends_on|invalidates|implements|serves|produces|derived_from`），定义语义为“支撑某事实/决策/目标但不是严格依赖”。

**验证方法**：用turn6（n_0047出现的那轮）的graph_state+对话原文，重新跑新版模板，检查是否输出n_0045被superseded及invalidates边。
## patch6验证结果与微调建议

**用户**：提供按新版模板生成的patch6（turn_id=6），询问是否符合预期。

**AI确认**：核心符合预期。关键部分正确：`superseded_nodes`包含`n_0045`（阻塞事实失效），`new_edges`包含`n_0047 invalidates n_0045`。说明“事实一致性反向检查”规则已生效。

**两个小问题**：
1. `n_0052`类型不理想：内容混有“可以close”（状态判断）和“建议记录返回类型”（待办）。建议拆分为`OpenTask`（记录返回类型），或不单独建节点。
2. `n_0049`可能应为`Decision`而非`Fact`：内容涉及架构原则（采用markdown-native输出），若作为设计原则保留应改为`Decision`类型。

**结论**：工作流验证通过（新事实自动识别并推翻旧阻塞事实）。下一步微调模板：提醒Extractor将“建议/下一步”优先抽成`OpenTask`而非`Fact`。
# [/COMPACTED]

