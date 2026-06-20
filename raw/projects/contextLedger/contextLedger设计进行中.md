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

## 图膨胀问题与切片方案

**用户问题**：每轮将完整 `graph_state.json` 喂给 Extractor 会导致模板膨胀，长程任务中上下文超限且准确性下降，这是 TaskGraph 方案的核心瓶颈。

**AI 确认**：正确方向是引入 **Graph Slice Builder**——不再喂全图，只喂“本轮相关的图切片”。Extractor 只读取经过检索和压缩的 slice，而非完整 `graph_state.json`。

**架构改造**：
- 原流程：`完整 graph_state.json + 本轮对话 → Extractor → patch.json`
- 新流程：`完整 graph_state.json + 本轮对话 → Graph Slice Builder → extractor_context_pack.json → Extractor → patch.json`

**Extractor 实际需要的信息**（固定大小）：
- `root_goals`（顶层目标）、`standing_constraints`（关键约束）、`active_open_tasks`、`recent_nodes`（最近2-3轮）、`relevant_nodes`（检索匹配）、`conflict_candidates`（可能被推翻的旧节点）、`next_node_id`（程序提供）

**切片筛选规则（简单可落地）**：
1. **符号匹配**：从本轮对话提取工单号、文件路径、API 路径、脚本名等，在全图中检索包含这些符号的节点。
2. **状态词匹配**：本轮出现“已完成/已实现/close”时，检索旧节点中的“open/阻塞/待确认”。
3. **最近窗口**：永远带上最近2-3轮的节点。
4. **顶层目标和约束**：长期保留少量压缩后的顶层目标。

**模板修改**：将“当前已有 TaskGraph：{完整 graph_state.json}”改为“当前相关 TaskGraph Slice：{extractor_context_pack.json}”，并提示 Extractor 只基于提供的 slice 判断，不臆造旧节点。

**结论**：完整图是数据库，不是 prompt。Extractor 只能读 slice。这是长程运行的必要架构拐点。

## 图切片准确性问题的核心修正

**用户问题**：担心 `build_extractor_context` 生成的图切片不准确或失真，导致整个 TaskGraph 出错。

**Claude-Opus-4.8 确认**：用户担忧正确。关键词切片的最大风险不是太大，而是**漏召回（false negative）**——若本轮信息应推翻某旧节点但切片未包含它，Extractor 会创建重复节点或漏掉 invalidate，误差随轮次累积成**图漂移**，且难以自愈。词面匹配对“同一实体不同措辞”召回极差，与模板要求的语义对齐任务自相矛盾。

**核心修正**：将“检索”与“正确性保证”彻底解耦。切片 builder 只负责 best-effort、偏召回、省 token；正确性由独立的、对**全 active 节点集**运行的机械校验保证（不消耗 token）。

**四层防护（按重要性排序）**：
1. **结构化 entity key**（最上游）：节点增加 `entity_ref`、`state` 等字段，将状态迁移从语义问题降级为精确匹配问题。
2. **检索偏召回**：embedding 相似度 + 关键词，宁可多带不漏。
3. **后处理 reconciliation pass**：Extractor 输出后，对每个新节点与**全部 active 节点**做 embedding 近重复检测 + entity_ref 冲突检测，输出 warning。
4. **图不变量 lint**：编译后检查同一 entity_ref 无冲突状态节点、无孤儿、invalidates 指向的节点必须 superseded，使漂移可观测。

**兜底信心**：patch 日志是 ground truth，`graph_state.json` 只是编译态。即使切片出错，可从日志重编译修复。关键验证点：故意让切片漏掉某节点，看 reconciliation 和 lint 能否抓出漏召回。

**结论**：方向正确且必须走，但绝不能令切片 builder 承担正确性。正确性应交给机械校验和不变量 lint，使失真从“污染整个图”降级为“可检测提示”。

## 课程设计简要大纲（吸收上面讨论的方法论更新）

### 课程名称
**从 Claude Code 到 Task Graph：重建 AI Agent 的任务态上下文工程**

### 课程定位
- 不是通用聊天压缩器，不是 Compact 替代品，不是模型内心还原，不是万能长期记忆。
- 在任务态内，显式记录目标、约束、事实、决策、工具结果、文件产物、记忆引用、被推翻方案，并转换为主 LLM 可用的结构化 Context Pack。

### 核心工程管线
```
用户对话 → Graph Slice Builder → Graph Extractor → patch*.json（不可变事件日志）
→ Patch Applier（机械合并）→ graph_state.json（编译态）
→ Context Builder → context_pack.json / context_prompt.md → 主 LLM
```
扩展：TaskGraph → Memory Extractor → Memory Store → 召回 → 新 TaskGraph → Context Pack  
多 Agent：Worker Context Pack → Worker Result + Patch → Coordinator 合并  
证据：Tool/File/Test → TaskGraph → Context Pack / Debug Report

### 第4–9讲横切原则
1. **任务态启动**：无任务不建图，只服务目标明确、约束持续、方案演化的任务型对话。
2. **写入/读取分离**：第4讲（图怎么长出来），第5讲（图怎么喂回主 LLM）。
3. **Patch 是源头，graph_state 是编译产物**：patch*.json 不可变，graph_state.json 只能由 patch 重编译，禁止手改。
4. **Extractor 读 Graph Slice，不读完整图**：完整图是数据库，不是 prompt。
5. **Slice 不承担正确性保证**：Slice 只负责尽量召回；正确性由 entity_ref、state、reconciliation、lint 等机械校验兜底。
6. **语义判断归 Extractor，机械合并归 Applier**：superseded_nodes、invalidates 由 Extractor 输出；Applier 只合并，不做语义推理。
7. **Context Builder 只读，不回写图**：可检测冲突、降级展示，但不修改 TaskGraph。
8. **手动流程是自动化流程的可观察版本**：手动复制文件、运行脚本是自动化管线的透明形态，不是临时旁路。
9. **外部证据节点化**：工具调用、工具结果、文件版本、测试结果都应进入图，成为可追踪、可失效、可回查的证据节点。
10. **调试对象是管线中间产物**：第9讲调试 Patch、TaskGraph、Context Pack、Memory Recall、Evidence、Timeline，不解释模型内心。

### 课程大纲

#### 第0讲：导论——从 Claude Code 到 Task Graph
- 核心问题：复杂 Agent 系统如何在有限上下文中保持任务连续性？
- 产物：课程总地图，Task Graph 初步概念图。

#### 第1讲：门控体系——复杂 Agent 如何控制功能演化
- 核心问题：复杂系统如何让实验功能、安全性和稳定性共存？
- 产物：Task Graph 原型门控表，功能开关分层设计。

#### 第2讲：上下文工程——Claude Code 如何管理有限窗口
- 核心问题：Agent 越能干，为什么越容易耗尽上下文？
- 产物：Claude Code 上下文工程流程图，Task Graph 的问题入口。

#### 第3讲：从 Micrograd 到 Task Graph
- 核心问题：能否像计算图追踪数值依赖一样，追踪任务上下文依赖？
- 产物：Task Graph 基础数据模型（节点类型、关系），简单依赖图示例。

#### 第4讲：写入侧——从对话到 Graph Patch，再到 TaskGraph
- 核心问题：任务图如何从多轮对话中持续长出来？
- 产物：Graph Extractor Prompt，示例 patch 文件，patch applier，graph_state.json。

#### 第5讲：读取侧——从 TaskGraph 到 Context Pack
- 核心问题：TaskGraph 如何变成主 LLM 能直接使用的任务上下文？
- 产物：context_pack_builder.py，context_pack.json，context_prompt.md。

#### 第6讲：长期记忆——从 TaskGraph 到 Memory Store
- 核心问题：任务结束后，哪些信息值得长期保留，并在新任务中召回？
- 产物：Memory Extractor Prompt，Memory Store 简化实现，MemoryReferenceNode 注入示例。

#### 第7讲：多 Agent 协作——Worker Context Pack 与 Patch 合并
- 核心问题：多个 Agent 协作时，如何避免上下文广播、冲突放大和图状态失控？
- 产物：Worker Context Pack 模板，Worker Result Package 模板，多 Agent Patch 合并流程图。

#### 第8讲：工具、文件与测试——让外部证据进入 TaskGraph
- 核心问题：工具结果、文件修改和测试结果如何成为可追踪的任务证据？
- 产物：Evidence Node 数据结构，工具结果入图示例，文件版本依赖链。

#### 第9讲：可观测性——Task Context Debugger
- 核心问题：系统输出错了，如何判断问题出在抽取、合并、读取、召回、证据，还是图漂移？
- 产物：Task Context Debug Report，Mermaid 图，Context Pack Trace，Reconciliation/Lint 报告。

#### 第10讲：总结与路线图——完整任务态上下文系统闭环
- 核心问题：Task Graph 最终形成了一套怎样的 Agent 上下文工程方案？
- 产物：完整课程项目结构，最终 Demo 流程，工程/产品/研究/教学路线图。
## 第4.5课教案：TaskGraph 长程运行补强——Context Pack、Reconciliation 与 Graph Lint

**本课定位**：补基础设施课。解决原流程中完整 `graph_state.json` 随轮次膨胀导致 Extractor 上下文超限、准确性下降的问题。不补此课，后续无法长程运行。

**核心改造**：
- 不再将完整图喂给 Extractor，而是生成有限的 `extractor_context_pack.json`
- Slice Builder 只负责省 token，正确性由全图级 `reconcile_patch.py` 和 `graph_lint.py` 兜底
- `patch*.json` 是不可变事件日志，`graph_state.json` 是编译产物

**新增文件**：
- `build_extractor_context.py`：从 `graph_state.json` 和本轮文本生成切片（含 root_goals、standing_constraints、active_open_tasks、recent_nodes、symbol_hits、conflict_candidates 等）
- 修改 Graph Extractor Prompt：将“完整图”改为“当前相关切片”，要求优先检查 conflict_candidates，不臆造旧节点
- `reconcile_patch.py`：机械检查新节点与全图 active 节点的重复、状态冲突，漏掉 superseded/invalidates 则报 warning
- `graph_lint.py`：检查 relation 合法性、invalidates 指向、孤立节点、同一实体状态冲突、OpenTask 生命周期

**验收标准**：
1. 正常 Slice：turn6 应输出 superseded_nodes 含 n_0045 及 invalidates 边
2. 故意漏召回（切片不含 n_0045）：Extractor 若漏掉 supersede，reconcile 必须报错
3. Lint 通过：无同一工单 open 与已实现并存等冲突

**实施提示**：可交由项目 AI 按上述文件列表和规则实现，并用 n_0045/n_0047 案例做 fixtures 验证。
## 方案可行性评价

**用户**：询问上述第4.5课方案是否可行。

**Claude-Opus-4.8 评价**：整体可行、结构对路，但存在一个**关键漏洞**——`reconcile_patch.py` 如何判定“同一实体”？教案未明确机制（embedding 或词面匹配均有缺陷），导致兜底层可能犯与 slice builder 相同的 false negative 错误。

**核心缺失**：此前确定的最高优先级修正——为节点添加结构化 `entity_ref` 和 `state` 字段——在教案中完全消失。有了 `entity_ref`，冲突判定降级为机械精确匹配，可靠且廉价。

**建议最小改动**：
1. 新增 schema 升级步骤：节点增加 `entity_ref`、`state`
2. `reconcile_patch.py` 分两路：有 `entity_ref` 用精确匹配（强保证），无则用 embedding 相似度（弱兜底）
3. 在教案中明确这一先后关系

**结论**：补上 `entity_ref` 后方案才真正闭环。其余部分（context pack、prompt 改造、graph lint、给项目 AI 的提示词）均可行。

## 第4.5课教案修改要点（基于Claude-Opus-4.8评价）

**核心漏洞**：原方案中 `reconcile_patch.py` 判定“同一实体”的机制缺失，导致兜底层可能重蹈 slice builder 的 false negative 覆辙。

**修复方案**：补上 `entity_ref` / `state` 结构化字段，将冲突判定降级为机械精确匹配。

### 具体修改位置与内容

1. **新增 Schema 升级节**（在“建议新增文件”之前）：节点增加 `entity_ref`（如 `"TKT-2026-003"`）和 `state`（如 `"blocked"`/`"deployed"`）。`reconcile_patch.py` 通过相同 `entity_ref` 精确匹配发现冲突。

2. **修改本课目标**：增加“通过 `entity_ref`/`state` 把同一实体判定结构化”和“Reconciliation 靠结构化引用兜底而非语义猜测”。

3. **修改最小闭环流程**：在 `graph_state.json` 后增加 `schema upgrade: entity_ref / state` 步骤。

4. **修改 Context Pack Builder**：检索优先级改为 `entity_ref` 精确匹配 > 显式 node_id > 词面匹配。从本轮文本提取可结构化的 `entity_ref`。

5. **修改 Graph Extractor Prompt**：要求为新节点填写 `entity_ref` 和 `state`，优先检查 `conflict_candidates` 中相同 `entity_ref` 的状态冲突，输出 `superseded_nodes` 和 `invalidates`。

6. **修改 Reconciliation Pass**：对带 `entity_ref` 的新节点，与全图相同 `entity_ref` 的 active 旧节点做状态冲突检查；无 `entity_ref` 的仅弱兜底（warning）。冲突但 patch 未处理则 error。

7. **修改 Graph Lint**：检查相同 `entity_ref` 下互斥 state 是否同时 active；对明显可追踪但缺 `entity_ref` 的节点输出 warning。

8. **修改验收标准**：测试2要求即使 slice 漏掉旧节点，`reconcile_patch.py` 仍能通过 `entity_ref` 检测冲突并报 error。新增测试4：缺少 `entity_ref` 的弱兜底。

9. **修改项目 AI 实施提示词**：增加 schema 升级为第0步，要求 `entity_ref` 精确召回优先，fixtures 中 n_0045/n_0047 必须带 `entity_ref`。

10. **修改本课结论**：正确性由结构化 `entity_ref`、全图级 reconciliation 和 lint 共同保证，没有 `entity_ref` 则兜底不硬。

11. **建议课名**：加入“Entity Ref”或改为“实体级正确性兜底”。
## TaskGraph Extractor 模板（压缩版）

**角色**：你不是回答用户，只从本轮输入抽取 Graph Patch，输出合法 JSON，无解释。

**前提**：当前提供的是系统筛选的上下文切片 `extractor_context_pack.json`（非完整图）。不能假设看到完整图，不能臆造未提供的旧节点 ID，只能引用切片中或本轮新建的节点 ID。遗漏的全图冲突由 `reconcile_patch.py` 检查。

**职责**：
- 抽取新增事实、目标、约束、决策、产物、任务
- 与切片中 active 节点对齐
- 优先检查 `conflict_candidates`
- 对同一 `entity_ref` 的状态冲突输出 `superseded_nodes` 和 `invalidates`
- 为可长期追踪的新节点尽量填写 `entity_ref` 和 `state`

---

### 一、节点类型
`UserGoal | Constraint | Fact | ToolResult | Decision | FileArtifact | OpenTask`

### 二、节点结构
```json
{
  "node_id": "n_0001",
  "type": "...",
  "content": "...",
  "entity_ref": "稳定标识或null",
  "state": "open|blocked|in_progress|implemented|deployed|resolved|cancelled|unknown|null",
  "status": "active"
}
```
- **entity_ref**：工单号、API路径、文件路径等，用于机械匹配。无法确定则 `null`，不伪造。
- **state**：优先使用枚举，状态归一化（如 `open` 归并 `未完成/todo`，`implemented` 归并 `已实现`）。无状态含义则 `null`，不确定则 `unknown`。

### 三、更新节点结构
```json
{
  "node_id": "n_0001",
  "changes": {"content": "...", "entity_ref": "...", "state": "...", "status": "..."},
  "reason": "..."
}
```
- 补充细节保持 `active`；待办完成改 `resolved`；被推翻应放 `superseded_nodes` 而非仅更新。
- 缺 `entity_ref` 时可补。

### 四、废弃节点结构
```json
{ "node_id": "n_0001", "reason": "..." }
```
只能引用当前切片中的旧节点。新事实推翻旧节点时：旧节点入 `superseded_nodes`，新节点创建，并加 `invalidates` 边。

### 五、边结构
```json
{ "source": "n_0001", "target": "n_0002", "relation": "refines|depends_on|supports|invalidates|implements|serves|produces|derived_from" }
```
含义：`refines`细化，`depends_on`依赖，`supports`支撑（非严格依赖），`invalidates`推翻，`implements`实现，`serves`服务，`produces`产生，`derived_from`来源于。

### 六、Patch 总结构
```json
{
  "task_id": "...",
  "turn_id": 1,
  "new_nodes": [],
  "updated_nodes": [],
  "superseded_nodes": [],
  "new_edges": []
}
```
无变化则数组空，不省略字段。

### 七、节点 ID 规则
- 新节点使用系统提供的 `next_node_id` 递增
- 不能复用已有 ID，不能臆造旧 ID
- `superseded_nodes` 只引用切片中旧节点
- `new_edges` 的 source/target 只引用切片中已有节点或本轮新节点

### 八、当前切片结构（示例）
```json
{
  "task_id": "...", "turn_id": 1, "next_node_id": "n_0001",
  "root_goals": [], "standing_constraints": [], "active_open_tasks": [],
  "recent_nodes": [], "symbol_hits": [], "conflict_candidates": [],
  "recent_edges": [], "retrieval_trace": {}
}
```
**优先检查 `conflict_candidates`**。检索优先级：`entity_ref`精确匹配 > 显式 node_id > 词面匹配 > 最近节点 > 关键词。

### 九、抽取规则
- 只抽新增、变化、被推翻信息
- 不重复创建已有节点
- 不执行请求、不给建议、不解释，只输出 JSON
- 新节点必须至少有一条边连接（除根 `UserGoal`）
- 可长期追踪节点尽量填 `entity_ref`/`state`，无法确定则 `null`/`unknown`
- 不把普通描述当 `entity_ref`
- 不假设切片是完整图

### 十、节点生命周期判定
对每个候选信息与切片中 active 节点对齐，选以下之一：
1. **SAME_ENTITY_MORE_DETAIL**：同一实体、补充细节 → `updated_nodes`（不新建）
2. **REPLACES_OLD_ENTITY**：使旧节点不再成立、状态互斥 → 旧节点 `superseded_nodes`，新节点 `new_node`，加 `invalidates` 边
3. **DEPENDS_OR_SUPPORTS_EXISTING**：新信息是原因/依据/约束/结果等 → 新建节点，用边连接
4. **NEW_ENTITY**：无法与现有节点建立上述关系时，才新建（除根目标外需有边）

### 十一、禁止事项
- 不因措辞变化重复建节点
- 不让同一实体同时存在多个 active 或互斥状态
- 不建孤立节点（除根目标）
- 不臆造切片外的旧节点 ID
- 不把普通描述当 `entity_ref`
- 不输出 JSON 外解释

### 十二、事实一致性反向检查
输出前扫描切片中 active 节点（尤其 `conflict_candidates`），检查本轮信息是否与旧节点描述同一实体（优先用 `entity_ref`）。若 `entity_ref` 相同且 `state` 互斥，必须视为冲突。即使未明确说“推翻”，也必须输出 `superseded_nodes` 和 `invalidates` 边。

### 十三、必须识别的状态迁移
1. **工单状态**：旧 `open/blocked/in_progress` → 新 `implemented/deployed/resolved` → 旧节点 superseded，新节点 invalidates
2. **阻塞失效**：旧“A 阻塞 B” → 新“A 已实现” → 旧阻塞节点 superseded
3. **接口明确化**：旧“待确认格式” → 新“格式已明确” → 更新或 superseded
4. **方案替代**：旧“方案 A” → 新“方案 B” → 旧 superseded，新 invalidates
5. **路径替代**：旧“路径 A” → 新“路径 B” → 旧 superseded

### 十四、invalidates 边要求
创建推翻旧事实的新节点时必须添加：
```json
{ "source": "新ID", "target": "旧ID", "relation": "invalidates" }
```
`reason` 写明状态迁移原因。

### 十五、输出前自检
- 字段完整、只 JSON、无解释
- 节点 type 合法，含 `entity_ref`/`state`
- 可追踪节点尽量填了 `entity_ref`
- relation 合法
- 旧节点 ID 来自切片
- 优先检查了 `conflict_candidates`
- 同 `entity_ref` 互斥状态已处理
- 被推翻节点同时有 `superseded_nodes` 和 `invalidates`
- 新节点无孤立（除根目标）

### 十六、当前输入
```json
{{extractor_context_pack_json}}
```
`task_id`: `{{task_id}}`  
`turn_id`: `{{turn_id}}`  
`next_node_id`: `{{next_node_id}}`  
本轮对话：`{{turn_text}}`

**请只输出 Graph Patch JSON。**
## 第4.5课模板长度问题与精简版

**用户**：感觉模板过长（15kb/4000 token），放入 graph slice 和对话后会更大，担心 Extractor 模型遵从指令能力下降。

**Claude-Opus-4.8 确认**：判断正确。长模板每轮运行成本高、稀释核心指令注意力，且存在明显冗余（状态迁移→superseded+invalidates 规则重复至少四遍）。合理目标是保留全部语义约束，删除重复表述和冗长示例，压缩至原 40% 左右。

**精简版完整模板**（约原 40% 长度）：

```markdown
你是 Task Graph Extractor。

```
你的任务不是回答用户、不解决问题、不给建议。
你只从本轮输入中抽取 TaskGraph 的增量补丁 Graph Patch，并只输出合法 JSON。

重要前提：
当前提供的不是完整 TaskGraph，而是本轮相关上下文 Slice。
你只能引用 Slice 中已出现的旧节点 ID，或本轮新建的节点 ID；
不得臆造未提供的旧节点 ID。全图级遗漏由后续 reconcile 检查。
```

## 一、节点类型 (type)
UserGoal | Constraint | Fact | ToolResult | Decision | FileArtifact | OpenTask

## 二、节点结构
new_nodes:
```json
{
  "node_id": "n_0001",
  "type": "<上述七种之一>",
  "content": "节点内容",
  "entity_ref": "稳定实体标识，无则 null",
  "state": "open|blocked|in_progress|implemented|deployed|resolved|cancelled|unknown|null",
  "status": "active"
}
```
updated_nodes:
```json
{ "node_id": "n_0001", "changes": { "content": "...", "entity_ref": "...", "state": "...", "status": "active|superseded|resolved" }, "reason": "为什么更新" }
```
superseded_nodes:
```json
{ "node_id": "n_0001", "reason": "为什么废弃" }
```
new_edges:
```json
{ "source": "n_0001", "target": "n_0002", "relation": "refines|depends_on|supports|invalidates|implements|serves|produces|derived_from" }
```

## 三、entity_ref 与 state
- entity_ref：用于机械判断同一实体。可填工单号/API路径/文件路径/脚本名/课程编号/模块名/节点编号。可长期追踪节点必须尽量填写；无法确定填 null；禁止普通描述性文本。
- state 归一化：未完成/待实现/todo/pending→open；阻塞/卡住/依赖未完成→blocked；进行中→in_progress；已实现/代码已完成→implemented；已部署/已上线/已落盘→deployed；已完成/已验证/closed/done→resolved；取消/废弃→cancelled；有状态含义但判断不了→unknown；无状态含义→null。

## 四、Patch 总结构（顶层字段不可省略）
```json
{ "task_id": "task_xxx", "turn_id": 1, "new_nodes": [], "updated_nodes": [], "superseded_nodes": [], "new_edges": [] }
```

## 五、ID 规则
新节点从系统给的 next_node_id 起递增；不复用、不臆造旧 ID；superseded_nodes 与边的 source/target 只能引用 Slice 中已有节点或本轮新节点。

## 六、生命周期判定（先对齐 Slice 中所有 active 节点，尤其 conflict_candidates）
对每个候选信息只能选一种动作：
1. SAME_ENTITY_MORE_DETAIL：同一实体仅更具体/更准确 → updated_nodes，不新建。
2. REPLACES_OLD_ENTITY：使某 active 节点不再成立、被替代、状态互斥 → 旧节点入 superseded_nodes + 新建 new_node + 加 invalidates 边。
3. DEPENDS_OR_SUPPORTS_EXISTING：是旧节点的原因/依据/约束/实现/结果/子任务/支撑 → 新建 new_node 并用边连接。
4. NEW_ENTITY：无法与任何 active 节点建立上述关系时才新建；除根 UserGoal 外，新节点必须至少有一条边连入图。

## 七、事实一致性反向检查（关键）
按优先级判同一实体：entity_ref 精确匹配 > node_id > 文件/API/工单号词面 > 最近节点 > 关键词。

若 new_node.entity_ref == old_node.entity_ref 且 state 互斥，即视为冲突；即使用户未明说“推翻/废弃”，也必须 superseded 旧节点并加 invalidates 边。

必须捕获的互斥迁移（旧→新）：
- open/blocked/in_progress/pending/todo → implemented/deployed/resolved
- “A 阻塞 B” → “A 已实现/部署/完成”
- “接口返回格式待确认” → “返回格式已明确”
- “采用方案 A” → “改用 B / A 不可行”
- “文件/目录位于 A” → “改为 B”

invalidates 边格式：
```json
{ "source": "新节点ID", "target": "旧节点ID", "relation": "invalidates" }
```
reason 须写明状态迁移原因。

## 八、硬性禁止
不因措辞变化重复建节点；同一任务/决策/约束/entity_ref 不得有多个互斥 active 版本；除根 UserGoal 外不得有孤立节点；不引用 Slice 外的旧 ID；只输出 JSON，无任何解释文字。

## 九、输入
当前 Slice：{{extractor_context_pack_json}}
task_id：{{task_id}}　turn_id：{{turn_id}}　next_node_id：{{next_node_id}}
本轮对话：{{turn_text}}

请只输出 Graph Patch JSON。

**附加建议**：可将第一至八节作为可缓存固定前缀（prompt caching），每轮仅第九节变化，进一步降低成本和延迟。
## 模板输入占位符处理

**用户**：指出模板第九项中的 `{{extractor_context_pack_json}}`、`{{turn_text}}` 等占位符手动无法提供。

**AI解释**：占位符不是供人理解的，而是程序注入变量。推荐方式：调用脚本在每轮运行前替换为真实内容。人工测试时可直接粘贴真实 JSON 和对话文本。

**改进建议**：将第九项改写为“输入区，由调用方每轮注入”，并把 `task_id`、`turn_id`、`next_node_id` 都放进 `extractor_context_pack_json` 中，避免重复传递。

## Claude-Opus-4.8 对模板占位符处理的意见

**核心判断**：GPT-5.5 的解释正确——`{{...}}` 是模板占位符，需由脚本每轮替换或人工粘贴。

**两点不同意见**：

1. **不应将可变输入放在模板第九节**，而应拆分为：第一至八节（固定规则）放入 system prompt 作为可缓存前缀；第九节（Slice + 对话）作为 user message 每轮构建。占位符无需写在模板中，代码拼装即可。

2. **关于合并 ID**：`task_id`、`turn_id` 可放入 `extractor_context_pack_json`，但 `next_node_id` 是运行时计数器，不应混入 context pack。应分开维护，拼 user message 时再合并。

**结论**：把第九节从模板删除，让每轮代码动态构建 user message。

## 用户架构方案与Claude-Opus-4.8评价

**用户方案**：删除模板第九节，第1-8节作为system模板；graph slice和每轮对话分别存放文件；用脚本组装，CLI传入三个参数（slice文件、对话文件、轮次），手动粘贴到网页大模型，未来改用API。

**Claude-Opus-4.8评价**：整体可行，但需修正三点：
1. **遗漏`next_node_id`**：组装脚本应自动从slice文件中扫描最大node_id并加1，无需手动传参。
2. **turn_id可从文件名解析**：若对话文件已含轮次编号（如`turn_012.txt`），无需单独传参，避免冗余和出错。
3. **手动粘贴需适配system/user输入框差异**：脚本应支持两种输出模式——单框拼接（适合只有单个输入框的网页）和双框分离（适合支持system字段的界面）；上API时再切换。

**命名建议**：`extractor_system.md`（固定规则），`turn_XXX.txt`（对话切片），`slice_XXX.json`（图切片），`build_extractor_prompt.py`（组装脚本）。核心原则：不让任何每轮变化的值靠人脑记忆。

## 两个核心脚本实现（压缩版）

### 实现原则
- 先实现最小可用版，不做复杂 embedding
- `build_graph_slice.py`：从完整 `graph_state.json` 和 `turn_xxx.md` 生成 `slice_xxx.json`
- `build_extractor_prompt.py`：从 `extractor_system.md`、`slice_xxx.json`、`turn_xxx.md` 组装最终 prompt
- `next_node_id` 由 `build_graph_slice.py` 从完整图计算，写入 `_runtime.next_node_id`

### 1. `build_graph_slice.py` 核心逻辑
- 解析 `graph_state.json` 的 nodes/edges
- 从 `turn_xxx.md` 提取符号（工单号、文件路径、API 路径、节点 ID 等）、状态信号（open/blocked/implemented/deployed 等）
- 对每个 active 节点打分（显式 ID 匹配 > entity_ref 匹配 > 关键词重叠）
- 按类别筛选节点：`root_goals`、`standing_constraints`、`active_open_tasks`、`recent_nodes`、`symbol_hits`、`conflict_candidates`
- 限制每类数量（默认 5~16 不等）
- 输出切片 JSON，包含 `_runtime.next_node_id` 及 `retrieval_trace`

### 2. `build_extractor_prompt.py` 核心逻辑
- 读取 `extractor_system.md`（固定规则）和切片 JSON 及对话文本
- 从切片 `_runtime` 提取 `next_node_id`，若无则从切片内容扫描最大节点 ID +1 兜底
- 构建 user message：包含 `task_id`、`turn_id`、`next_node_id`、切片 JSON、对话文本
- 支持输出模式：
  - `single`：system + user 拼成一块（适合只有单一输入框的网页）
  - `split`：分两段输出
  - `api-json`：输出 `{"messages": [{"role":"system"}, {"role":"user"}]}`，供 API 使用

### 使用示例
```bash
# 生成切片
python build_graph_slice.py --graph graph_state.json --turn original_dialogues/turn_006.md --out graph_slices/slice_006.json

# 组装最终 prompt（手动粘贴）
python build_extractor_prompt.py --system extractor_system.md --slice graph_slices/slice_006.json --turn original_dialogues/turn_006.md --mode single --out prompts/extractor_turn_006.md

# 输出 API 格式
python build_extractor_prompt.py ... --mode api-json
```
## Claude-Opus-4.8 对两个脚本的最终意见

**整体判断**：可以落地，方向正确（`next_node_id` 从全图计算写入 `_runtime`）。

**两处必须修改**：

1. **实质修改**：`build_extractor_prompt.py` 中，序列化 user message 前应剥掉 `retrieval_trace`（诊断字段对抽取无用，仅增 token）。修改位置：`split_runtime_from_pack` 函数末尾增加 `pack.pop("retrieval_trace", None)`。

2. **小 bug**：`build_graph_slice.py` 和 `build_extractor_prompt.py` 中 `turn_id = args.turn_id or ...` 会导致 `turn_id=0` 被短路。应改为 `turn_id = args.turn_id if args.turn_id is not None else parse_turn_id(...)`。

**可选不改**：节点可能同时出现在多个列表造成 token 重复，但影响不大，可接受。

**验收依赖**：turn6 中 n_0045 需带有 `entity_ref`（如 `TKT-2026-003`），确保能被 `TICKET_RE` 命中并进入 `conflict_candidates`。
## reconcile_patch.py 实现

**用户要求**：实现 `reconcile_patch.py`。

**脚本核心功能**：机械校验，不调用 LLM。输入 `graph_state.json` 和 `patch.json`，基于完整图做一致性检查。`entity_ref` 精确相等是强判定，无 `entity_ref` 时只做弱兜底 warning。

**主要校验逻辑**：
- 解析 `superseded_nodes`、`invalidates` 边（兼容多种格式）
- 对新节点与全图 active 节点进行：
  1. 精确重复检查（内容、type、state 完全一致）
  2. 同一 `entity_ref` 下状态冲突检查（缺失 supersede 或 invalidates 则 error）
  3. 无 `entity_ref` 时弱兜底（内容相似度、关键词 Jaccard、可选 embedding 余弦相似度），仅 warning
- 输出报告含 errors/warnings，默认 errors 非零则退出码 1

**使用方式**：
```bash
python reconcile_patch.py graph_state.json patch.json --out report.json
```

**验证示例**：若全图有 `n_0045`（entity_ref=`TKT-2026-003`, state=`blocked`），patch 新增 `n_0047`（同 entity_ref, state=`deployed`）且缺少 supersede 和 invalidates，报告会输出两个 error。
## Claude-Opus-4.8 对 `reconcile_patch.py` 的评审

**总体判断**：赞同。实现抓住了核心——同一实体判定靠 `entity_ref` 精确相等，弱兜底只出 warning，可独立运行、接 CI、错误返回非零退出码，方向正确。

**五处需改进**：

1. **`invalidates` 匹配太松**（可能假阴性）：`has_invalidates` 中 `old_id in invalidated_old_ids` 允许任意新节点 invalidate 即通过，应优先用精确配对 `(new_id, old_id)`，仅在 source 缺失时才退化。

2. **状态冲突依赖双方 state 非空**：若旧节点缺 `state` 而新节点有 `deployed`，冲突检查会静默跳过。应对同 `entity_ref` 但 state 缺失的情况补 warning。

3. **性能问题**：弱兜底分支中每个新节点都对全部 active 旧节点重复做 tokenization 和相似度计算。应预计算缓存。

4. **entity_ref 命中后跳过弱兜底是盲区**：新节点有 ref 但旧节点 ref 缺失或写错时，完全不做弱匹配。这是规格边界，非 bug，但应知晓。

5. **缺少 superseded 节点存在性校验**：patch 可声称 supersede 一个不存在或已 inactive 的节点，应补 warning。

**认可的设计取舍**：将“缺 superseded”和“缺 invalidates”拆成两条独立 error，要求二者都具备才算正确处理，比规格字面更严，值得肯定。

**结论**：修好前两点（invalidates 精确配对、state 缺失 warning）后即可放心进 CI。
## 第六步：graph_lint.py 实现

**用户要求**：继续实现 `graph_lint.py`（在 patch 应用后运行，检查全图结构与语义不变量，不调用 LLM，出错返回非零退出码）。

**GPT-5.5 给出的实现核心功能**：

- **relation 合法性检查**：关系必须在预定义集合内（refines/depends_on/supports/invalidates/implements/serves/produces/derived_from）。若图中有自定义 relation enum，则优先使用。
- **节点存在性与重复**：检查节点 ID 缺失或重复，边 source/target 存在性。
- **孤立节点检查**：除根 UserGoal 外，不允许 active 节点 degree 为 0。
- **invalidates 边检查**：被 invalidates 指向的节点必须标记为 `superseded`。
- **同一 entity_ref 状态冲突**：相同 `entity_ref` 下不允许存在互斥的 active state（如 open 与 deployed 共存）。
- **OpenTask 生命周期**：已完成的任务应使用 `resolved` 状态，不允许仍为 active；内容明显完成但状态不是 resolved 时警告。
- **缺失 entity_ref 警告**：对包含工单号、文件路径、API 路径等内容的 OpenTask/Fact/Constraint 节点，若缺少 `entity_ref` 则警告。
- **状态值警告**：使用非最小状态枚举值时警告。

**输出**：JSON 格式报告，包含 errors/warnings。默认 errors 存在时退出码为 1（可被 CI 阻断），可选 `--fail-on-warning` 将 warning 也视为失败。

**使用示例**：
```bash
python graph_lint.py graph_state.json --out report.json
```

## 课程文档修改意见（根据实现调整）

**用户**：要求 Claude-Opus-4.8 根据最近实现的脚本（`build_graph_slice.py`、`reconcile_patch.py`、`graph_lint.py`）审查原有课程文档是否需要修改。

**Claude-Opus-4.8 结论**：整体结构没问题，但存在命名不一致、流程图缺步骤、文档描述落后于实现等问题，需修改。

### 必须修改项

1. **命名不一致**：全文混用 `extractor_context_pack.json`、`slice_xxx.json`、`Context Pack Builder`。建议统一产物文件名为 `extractor_context_pack.json`，标题与脚本名可保留差异，但说明清楚。

2. **第二节流程图缺“应用 patch”步骤**：原流程 `reconcile_patch.py → graph_lint.py` 缺少中间的 `apply patch`。正确应为：`reconcile_patch.py`（事前校验）→ `apply patch` → `graph_lint.py`（事后体检）。

3. **第七、八节乱码/重复**：第七节第5条末尾重复“s,并添加 invalidates 边”，删除多余字符。第八节第5、6条重复且残缺，建议删除第6条，保留第5条并修正格式。

### 建议修改项（文档落后于实现）

4. **第九节补充 `graph_lint.py` 实际检查项**：
   - 状态值校验：`state` 不在最小枚举内输出 warning。
   - 细化 OpenTask 检查：`state=implemented/deployed` 仍 active 报 error；`state=resolved` 仍 active 报 error；内容启发式完成但未 resolved 只报 warning。
   - 基础结构校验（重复 node_id、悬空边、缺端点）应在文档中提及。

5. **Markdown 格式**：代码围栏误用 `python` 的改为 `json` 或 `text`；文件树缩进统一。

### 无需修改部分

第九节 relation 枚举、互斥状态列表（open/blocked/implemented/deployed/resolved/cancelled，排除 in_progress/unknown）与实现完全一致；第五节故意保留旧流程对比无需改动。

## reconcile_patch.py 定位澄清

**用户质疑**：原设计中 `reconcile_patch.py` 是“事后校验”，但 Claude-Opus-4.8 又称它为“事前拦截”，矛盾。

**解释**：参照系不同。时间线：`Extractor → reconcile_patch → apply patch → graph_lint`。

- 以 **Extractor** 为参照：reconcile 在其**之后**，用完整图复核 patch → “事后校验”（原设计口径）
- 以 **apply patch** 为参照：reconcile 在其**之前**，拦截错误 → “事前拦截”

建议统一按原设计文档（参照 Extractor）称为“事后校验”，避免歧义。

**分工本质**：
- `reconcile_patch`：校验 **patch 相对于旧图**是否自洽（缺 superseded/invalidates 则报错）
- `graph_lint`：校验 **应用后的新图**是否违反全局不变量（孤立节点、互斥 state 等）

## reconcile/lint 失败处理与重试策略

**用户**：reconcile_patch 或 graph_lint 不通过会怎样？理解是回到流程起点重走，但一直不通过怎么办？

**Claude-Opus-4.8**：需有重试上限 + 降级兜底。

**两类失败性质不同**：
- `reconcile_patch` 失败（Extractor 漏判 superseded/invalidates）→ 重走有意义，将错误报告回填 prompt 再生成
- `graph_lint` 失败需区分：本轮 patch 引入的冲突可重试；历史遗留脏图（孤立节点、悬空边）重试无效，需人工介入

**有界重试循环**：
```
Extractor → patch → reconcile → (fail & attempt<N) → 错误报告回填 prompt → 重试
                              → pass → apply → graph_lint → (fail & 本轮引入) → 回填重试
```
- N 建议 2~3 次
- 错误报告需结构化（如 `MISSING_INVALIDATE`、`expected_supersede`、`reason`）

**N 次仍不过：降级，不污染主图**
- 推荐：拒绝合并 + 隔离记录到 `quarantine/` 文件夹或挂 `needs_review` 节点，主图保持干净状态（宁可漏记一轮，不可污染）
- 更激进但高风险：部分应用通过校验的节点，仅隔离冲突部分（教学阶段不建议）

**文档补充建议**：在第八、九节后补“实现五：失败处理与重试策略”，明确 error 结构化回填、重试上限 N、超限降级隔离，才算真正闭环。

## 第4.5课教案：TaskGraph长程运行补强——Context Pack、Reconciliation与Entity-Ref兜底（压缩版）

### 一、本课定位
基础设施补强课。解决完整`graph_state.json`随轮次膨胀导致Extractor上下文超限、准确性下降问题。不补则系统无法长程运行。

### 二、本课目标
- Extractor每轮只看有限切片（省token）
- 用全图级机械校验（entity_ref精确匹配）保证正确性
- 失败处理：有界重试+失败隔离，不污染主图

### 三、核心改造概念
- **Slice Builder只负责省token，不负责正确性**。正确性由两道全图机械校验兜底：`reconcile_patch.py`（应用前复核patch自洽性）、`graph_lint.py`（应用后校验全局不变量）。
- **`entity_ref`是兜底能“硬”的前提**。无entity_ref则判定退化为语义匹配，会犯与slice相同的false negative错误。有entity_ref（工单号、路径等）可精确匹配。

### 四、最小闭环流程
```
完整graph_state + turn_xxx.md
 → build_graph_slice.py → extractor_context_pack.json（含_next_node_id）
 → build_extractor_prompt.py → 组装system+user（剥retrieval_trace）
 → Extractor（LLM）→ patch.json
 → reconcile_patch.py（事后校验，用完整图复核patch自洽性）
   ├─ pass → apply patch → 新graph_state
   │          → graph_lint.py（应用后校验全局不变量）→ 完成
   └─ fail → 结构化error回填prompt，重试（上限N次）→ 超限则隔离到quarantine/
```
- reconcile定位：以Extractor为参照是“事后校验”，以apply为参照是“事前拦截”。统一用“事后校验”口径。
- reconcile校验patch相对旧图是否自洽（缺superseded/invalidates）；lint校验应用后新图是否违反不变量（孤立节点、互斥state等）。

### 五、Schema升级（第0步）
节点增加`entity_ref`（稳定标识，无则null）和`state`（枚举：open/blocked/in_progress/implemented/deployed/resolved/cancelled/unknown/null）。fixtures（如n_0045/n_0047）必须带entity_ref。

### 六、文件与脚本说明
- `extractor_system.md`：固定规则（前八节），可缓存。
- `build_graph_slice.py`：从完整图+turn生成切片，提取符号、打分、分类限量，`next_node_id`从全图计算写入`_runtime`。
- `build_extractor_prompt.py`：组装system+user，支持single/split/api-json模式，序列化前剥`retrieval_trace`。
- `reconcile_patch.py`、`graph_lint.py`：机械校验关卡。

### 七、Reconciliation Pass（reconcile_patch.py）
- 输入：完整graph_state + patch.json
- 对带entity_ref的新节点，与全图相同entity_ref的active旧节点做状态冲突检查。若entity_ref相同且state互斥（如blocked→deployed），而patch未supersede旧节点或未加invalidates边，报error。
- 无entity_ref节点仅弱兜底（相似度、关键词），产出warning。
- 关键实现：invalidates须精确配对`(new_id, old_id)`；状态冲突不依赖双方state非空，缺state时补warning；检查superseded节点是否存在且active。

### 八、Graph Lint（graph_lint.py）
- 应用后运行，校验不变量：relation合法；节点ID不重复、边端点存在；除根UserGoal外无active孤立节点；invalidates目标须为superseded；同一entity_ref无互斥active state；OpenTask完成状态检查；可追踪内容缺entity_ref则warning。有error退出码非零。

### 九、失败处理与重试策略
- reconcile失败（Extractor漏判）→ 重走有意义，将结构化error回填prompt。
- lint失败：若是本轮引入的冲突可重试；若是存量历史脏图则人工介入，不进重试循环。
- 重试上限N=2~3次。超限则**拒绝合并+隔离**：patch不进主图，写入`quarantine/turn_xxx_failed.json`或挂`needs_review`节点。主图保持干净（宁可漏记一轮，不可污染全图）。
- 不推荐“部分应用”（风险高），教学阶段不做。

### 十、验收标准
1. 正常切片：turn6输出n_0045的superseded+invalidates。
2. 故意漏召回：切片不含n_0045，但新节点带entity_ref，reconcile仍能通过entity_ref精确匹配检测冲突并报error。
3. Lint通过：无同一entity_ref互斥state共存。
4. 弱兜底：无entity_ref节点产出warning。
5. 失败处理：持续漏判时，N次重试后隔离到quarantine，主图未污染。

### 十一、实施提示
- 第0步：schema升级（entity_ref/state）。
- 检索与冲突判定以entity_ref精确匹配优先。
- fixtures必须带entity_ref。
- next_node_id从全图计算写入_runtime；turn_id从文件名解析，注意0值不被短路。
- 序列化前剥retrieval_trace。
- 核心：不让每轮变化的值靠人脑记忆，正确性由全图机械校验+失败隔离保证。

### 十二、本课结论
长程运行正确性 = 结构化entity_ref/state + 全图级reconciliation与lint + 有界重试+失败隔离。Slice只省token不保正确；无entity_ref兜底不硬；无失败隔离闭环不完整。三者齐备，TaskGraph方可长程运行而不超限、不失真。
## 第4.5课闭环验证技能文件（压缩版）

**用户**：要求将第4.5课教案形成“技能文件”（执行提示词），供项目AI执行并验证教案、脚本和模板是否可以闭环。

**GPT-5.5**：同意，建议文件名 `prompts/taskgraph_4_5_closure_skill.md`。

### 技能文件核心内容

**角色与目标**：项目AI基于当前目录执行验证第4.5课闭环。不重新设计方案，检查并最小修改脚本和模板。

**约束**：不破坏原`graph_state.json`，先备份；测试用fixtures；未通过reconcile/lint的patch不合并；缺少apply patch则补最小实现；阻塞原因写入报告。

### 验证步骤摘要

1. **检查项目结构**：确认目录、脚本、模板文件存在。
2. **检查提示词分工**：`extractor_system.md`只含固定规则；`taskgraph_extractor_template.md`为合成后的完整context。
3. **检查graph_state schema**：节点需含`entity_ref`/`state`，关键节点（如n_0045）带实例。
4. **验证`build_graph_slice.py`**：生成切片含`_runtime.next_node_id`，`conflict_candidates`优先召回相同`entity_ref`节点。
5. **验证`build_extractor_prompt.py`**：支持single/split/api-json模式，输出不含`retrieval_trace`，无手动占位符。
6. **准备reconciliation fixtures**：创建坏patch（缺少superseded/invalidates）和好patch。
7. **验证`reconcile_patch.py`**：坏patch报错（缺supersede+invalidates），好patch通过。`invalidates`匹配用精确配对。
8. **补齐apply patch阶段**：若无则补`apply_patch.py`，实现合并patch并输出新图。
9. **验证`graph_lint.py`**：好图通过，坏图（同entity_ref互斥状态同时active）报错。
10. **验证弱兜底warning**：缺entity_ref的冲突仅warning，不阻断。
11. **验证失败处理**：失败不污染主图，重试上限N，超限隔离到`quarantine/`。
12. **最终验收标准**：共12项全部满足。

### 输出报告

生成`reports/taskgraph_4_5_closure_report.md`，包含总结结论、检查清单、测试结果、问题列表、修改记录、最终建议。

**执行原则**：完整闭环（切片→prompt→patch校验→应用→lint→隔离），不因通过测试而放宽校验，宁可隔离不污染主图。
## Claude-Opus-4.8 对技能文件的最终意见

**总体判断**：大体可行，可拿去执行，但需先修改一处破坏性风险。

**必须改（会破坏源文件）**：第五步将组装结果 `--out` 直接写入固定模板 `prompts/taskgraph_extractor_template.md`，会覆盖原文件。应改为输出到 per-turn 文件如 `extractor_turn_006.md`。

**建议改（影响结论可信度）**：
1. **区分验证与实现**：若 `apply_patch.py` 本不存在而是本次新建，结论应是“部分通过”而非“闭环成立”，报告需强制标注。
2. **未跑真实 Extractor**：测试使用手工 fixture patch，未验证 LLM 抽取质量。结论应收紧为“校验/兜底链路闭环成立，真实 Extractor 端到端尚未验证”。
3. **健壮性补丁**：先探测脚本实际参数签名，不一致时报错；turn_006 不存在时自动选已有轮次。

**最终结论**：第1点改完后即可放行，其余建议同步加入以免报告误导。
## 技能脚本验证范围澄清与建议

**用户确认**：技能脚本实际是验证流程而非完整执行闭环，缺少真正Extracting环节。询问是否需要先手动跑完真实流程，还是可用伪造结果验证。

**Claude-Opus-4.8**：你**不需要先手动跑真实流程**，但验证只覆盖部分步骤。

- **第六至十一步（reconcile/apply/lint/quarantine）**：使用手工伪造的fixture patch（与你的对话无关），验证校验基础设施能否正确拦截/放行patch。
- **第四、五步（slice生成+prompt组装）**：会使用你提供的`turn_006.md`等对话，但只验证prompt能拼出来，**从未真正发给大模型执行Extracting**。

**结论**：脚本验证的是“校验与兜底基础设施”闭环（切片生成、prompt拼装、坏patch拦截、好patch通过、失败隔离），**不验证真实Extractor端到端产出质量**。报告结论应明确为“校验链路闭环成立，真实Extractor端到端尚未验证”。

**建议**：若需验证完整闭环（含LLM抽取），需补一步：将拼出的prompt真发给Extractor模型，拿到真实`patch_006.json`，再喂入后续流程。可帮助补充该段。
## 第4.5课验证报告与后续迁移建议

**项目AI执行结果**：第4.5课闭环验证完成，结论“部分通过”。校验/兜底链路闭环成立，但有两个关键问题：1）历史图全部33个节点缺失`entity_ref`/`state`，强判定无法发挥作用；2）真实Extractor端到端未验证。各步骤结果：slice生成、prompt组装、reconcile坏/好patch、apply_patch、graph_lint好/坏图、弱兜底均通过；quarantine部分通过（有目录脚本但缺自动控制器）。已备份主图，未污染。

**GPT-5.5判断**：结论准确，基础设施基本闭环。建议下一步先做历史图迁移：为可追踪节点补充`entity_ref`（文件路径、工单号等；抽象原则填null）和`state`（限枚举值），生成迁移候选文件，经`graph_lint`校验通过后不自动替换，仅建议人工确认。之后再进行真实Extractor端到端验证和pipeline自动化。当前状态划分为：A阶段（基础设施验证，部分通过）、B阶段（历史迁移）、C阶段（端到端验证）、D阶段（自动化）。
## Claude-Opus-4.8 对迁移建议的修正意见

**核心分歧**：不赞同将完整历史迁移严格排在真实Extractor运行之前。

**赞同之处**：诊断准确，四阶段拆分、不覆盖主图、state用枚举、entity_ref不强行填充抽象节点等原则正确。

**反对理由**：
1. 迁移本身就是一次未经验证的LLM抽取任务。在未见过真实Extractor产出前，先对33个节点做迁移是顺序拧的。
2. entity_ref标错比标漏更危险——标多或标错会制造假冲突，拦阻合法patch。迁移前应通过真实Extractor跑一轮了解其命名风格，以便历史回填与未来产出对齐。

**建议顺序调整**：
- 先做**1轮真实Extractor冒烟测试**（非6轮），目的不是验证强兜底，而是钉死输入输出契约（entity_ref命名、字段完整性），为迁移提供规范。
- 再执行历史迁移（按冒烟得到的命名口径）。
- 最后做完整强路径端到端验证（6轮）和自动化（D阶段）。

**额外提醒**：报告中`apply_patch.py`和`quarantine_patch.py`均为“本次新建”，尚未经过多轮实战检验，不应默认其已可靠，需列入后续被检验清单。
## 单轮冒烟测试最小执行指令（压缩版）

**目的**：获取一份真实 patch，观察 Extractor 输出契约和 entity_ref 命名风格。不进主图、不写 patch 日志、不做通过/不通过裁决。

**步骤**：

1. **隔离工作区**：创建空种子图 `smoke/taskgraph_contract/graph_state.seed.json`（`{"nodes":[], "edges":[], "next_node_id":"n_0001"}`）

2. **生成 slice**（用 turn_001）：
   ```bash
   python scripts/build_graph_slice.py --graph smoke/.../graph_state.seed.json --turn original_dialogs/turn_001.md --out smoke/.../slice_001.json
   ```
   （先探测脚本参数签名，不一致则报错）

3. **组装 prompt**：
   ```bash
   python scripts/build_extractor_prompt.py --slice slice_001.json --turn turn_001.md --mode api-json --out smoke/.../prompt_001.md
   ```
   检查 `retrieval_trace` 已剥离、`next_node_id` 在内、token 量可控。

4. **手动抽取**：将 prompt 发给 Extractor 模型，响应原样保存为 `smoke/.../patch_001.smoke.json`（不用 `patch_001.json`）。

5. **契约核对**（不应用 patch）：
   - 合法 JSON？有无额外文字？
   - 顶层结构、op 类型是否与 schema 一致？
   - node_id 是否从 `next_node_id` 顺序分配？
   - **entity_ref 命名**：文件/路径/工单号形式？抽象原则是否用 `null`？同对象命名是否自洽？
   - state 是否在闭合枚举内？
   - 字段完整性，有无多余字段？
   - supersede/invalidates 处理是否符合预期？

6. **reconcile 观察**（可选，只做信息用途）：
   ```bash
   python scripts/reconcile_patch.py --graph graph_state.seed.json --patch patch_001.smoke.json
   ```

**产出**：`contract_notes.md`，记录 Extractor 实际 patch 结构、entity_ref 命名规范、state 使用值、问题清单及需在 prompt 中纠正的点。

**边界**：不替换主图、不进 patch 日志、不下结论。拿到命名口径后，再据此做历史图迁移，避免命名对齐错误造成假冲突。

## 第1轮冷启动与第2轮后流程差异

**用户**：询问第1轮对话时 `graph_state.json` 的来源，是否应先由第1轮生成，第2轮起才用 `build_graph_slice.py`。

**项目AI**：确认用户理解正确。第1轮是冷启动，`graph_state.json` 不存在（或为空）。`build_graph_slice.py` 依赖已有图做节点召回和打分，第1轮无旧节点，无需（也无法）走 slice 流程。正确流程应为：第1轮直接跳过 slice，将对话原文 + system prompt 喂给 Extractor → 生成 `patch1.json` → apply patch → 生成初始 `graph_state.json`。`graph_state.json` 从来不是一次性生成的终产物，而是“当前已 apply 的所有 patch 的合并视图”。从第2轮起，`graph_state.json` 才作为输入参与 slice 生成。
## 第1轮冷启动解释与冒烟种子图修正

**用户**：询问第1轮 `graph_state.json` 的来源，及其与 `build_graph_slice.py` 的关系，并引用项目AI的解释，要求 Claude-Opus-4.8 评价是否正确。

**Claude-Opus-4.8 评价**：项目AI的概念解释正确——`graph_state.json` 是已 apply 的所有 patch 的合并视图，第1轮无历史节点，应跳过 slice 直接让 Extractor 生成初始节点并 apply 后才产生图；第2轮起该图才作为 slice builder 的输入。用户的直觉“先用第1轮生成图，第2轮起切片”符合设计意图。

**两处必须修正/补充**：
1. **种子图 schema 不一致**：项目AI读出的真实 schema 是 `{"task_id":"...", "nodes": {}, "edges": []}`（nodes 为字典），而之前冒烟指令中的种子用的是 `{"nodes": [], "next_node_id": "n_0001"}`。应让项目AI直接给出最小合法空图（含所有必填字段，nodes 用字典，不手写 next_node_id），以真实 schema 为准。
2. **冒烟是沙盒，不要重造真实图**：当前已有33个节点的 `graph_state.json` 不动。空图冒烟仅用于观察 Extractor 从零开始的命名契约，并非重新执行生产第1轮。跑 slice 和 build_extractor_prompt 仍有价值（验证脚本在空输入上不崩、管道正常）。
## 单轮冒烟测试结果与 entity_ref 命名规范

**用户**：完成冒烟测试第四步，生成了 `patch_001.smoke.json`。

**Claude-Opus-4.8 评价**：结构健康，node_id 顺序正确，state 闭合，superseded/updated 为空合理。但存在**四点必须纠正**的问题：

1. **entity_ref 命名不一致**：文件路径用原文（✅），组件名有 `duty_reporter`（slug）和 `Strategy Research Agent`（自然语言带空格）混用，工单用 `TKT-2026-XXX` 占位符（❌ 不稳定）。
2. **工单占位符问题**：未分配的真实 ID 应填 `null`，禁止 `XXX`。
3. **多余 `status: "active"` 字段**：与 `state: "open"` 冗余，需确认是否在 schema 内或禁止。
4. **FileArtifact vs OpenTask 归类摇摆**：生产文件的任务被标为 FileArtifact，需统一。

**建议**：迁移历史 33 个节点前，先回改 Extractor prompt，强制 entity_ref 规范：文件路径用原文，组件/Agent 用 snake_case slug，工单未分配填 null，抽象节点填 null，移除 status 字段。同时确认 reconcile/apply 脚本接受的 patch 结构是 `new_nodes/...` 分类格式而非 op-list。

**下一步**：将观察整理为 `contract_notes.md`，作为历史迁移的命名基准。

## 冒烟测试第五步结果与契约验证

**项目AI检查**：确认 `reconcile_patch.py` 和 `apply_patch.py` 都基于 `new_nodes/updated_nodes/superseded_nodes/new_edges` 分类结构，无需 op-list。但用户提供的 `patch_001.smoke.json` 被 markdown 代码块包裹，导致 `json.load()` 解析失败。需去掉首尾的 ```json 和 ``` 标记，改为纯 JSON。

**用户执行第五步结果**：修复后运行 reconcile 和 apply 均通过。reconcile 报告显示 `graph_nodes: 0`、`active_graph_nodes: 0`、`errors: 0`、`warnings: 0`；apply 成功输出 `graph_state.after_001.json`。

**Claude-Opus-4.8 解读**：
- **证明的**：patch 四分类结构与两个脚本契约对齐，端到端管道（slice→prompt→抽取→reconcile→apply）全程贯通。唯一真实阻塞是 markdown 包裹，需回 prompt 禁止（要求裸 JSON）。
- **未证明的**：空图测试没有旧节点，未触及冲突检测和 entity_ref 召回逻辑。apply 机械地保留了 `Strategy Research Agent`、`TKT-2026-XXX`、`status` 等脏模式，命名问题未被纠正。
- **建议补一步**：对 `after_001.json` 运行 `graph_lint.py`，验证 lint 是否能捕获 status 外字段、entity_ref 带空格、占位符等问题。若全部放过，说明兜底层有盲区。
## graph_lint 结果解读与下一步判断

**用户执行**：对 `graph_state.after_001.json` 运行 `graph_lint.py`，输出 `ok: true`，`errors: 0`，`warnings: 1`。警告内容：节点 `n_0011`（类型 OpenTask）内容中包含可识别实体线索（`ticket_id`），但缺少 `entity_ref`。

**Claude-Opus-4.8 解读**：
- lint 在正常工作，这是兜底层第一次主动发现潜在问题。警告不是错误，而是问：这个 ticket 实体是否应该被追踪？
- 这正是冒烟阶段确定的规则——“带 ticket_id 的任务应尽量有 entity_ref”在执行验证。

**需做的判断（二选一）**：
- **情况 A**：该 ticket 是真实、会被反复引用的实体 → Extractor 漏给了 entity_ref（真问题）。应回 `extractor_system.md` 收紧规则（明确“含 ticket_id 的 OpenTask 必须生成 entity_ref”），然后重抽本轮（利用现有 seed 和快照）。
- **情况 B**：该 ticket 只是顺嘴提及，不构成需追踪的实体 → lint 是误报，规则过敏感。可调低 lint 触发条件或接受无害 warning。

**下一步**：用户需提供 `n_0011` 节点的完整 JSON，由 Claude-Opus-4.8 判断属于 A 还是 B，再决定重抽或放行。无论哪种，这次 lint 拦截证明了 entity_ref 兜底线是活的。
## 切片为何仍需原始对话（第二轮起）

**用户疑问**：从第2轮开始已有 `graph_state`，生成 `slice` 时为何仍需 `original_dialogs/turn_002.md`？对话不是已经作为独立部分喂给 Extractor 了吗？是否冗余？

**项目AI解释**：切片不是“按轮次归属切图”，而是“按对话内容从全图做相关性检索”。原始对话提供显式 node_id、符号匹配（文件名、工单号等）、状态信号（“已完成”“阻塞”），作为检索 query。没有对话，脚本不知道本轮关心哪些节点，只能盲选。

**Claude-Opus-4.8 澄清**：用户理解的“对话已作为独立部分喂给 Extractor”没错，但对话在管道中**被用了两次，功能不同**：
1. **在 `build_graph_slice.py` 中**：对话作为**检索查询**，用于从全图机械地挑出与本轮相关的旧节点（省 token 的前置过滤）。全图本身不含“相关性”信号，必须依赖本轮对话定义。
2. **在 Extractor 中**：对话作为**抽取原料**，从中提取新节点、新边、状态变化。slice 则作为上下文背景，帮助避免重复、正确连边、发现冲突。

**比喻**：会议记录员——本轮对话是此刻发言，完整 graph_state 是旧笔记。记录员要翻到相关旧页，必须先听懂此刻话题（第一次用对话做索引），然后同时看着发言和旧笔记写新记录（第二次用对话做内容）。两次使用并非冗余，而是两个正交任务。

**结论**：从第2轮起，对话两次都省不掉——少了第一次，slice 无从定义相关性；少了第二次，Extractor 没有可抽内容。Slice Builder 只省 token，不负责正确性。
## slice 体积问题诊断与修复方案

**用户发现**：第2轮 slice_002.json 比第1轮 graph_state.json 更大（4.6KB → 11.6KB），认为违背 slice 初衷，怀疑脚本有问题。

**项目AI诊断**：根因是 `build_graph_slice.py` 将同一节点完整复制到多个分组（root_goals、active_open_tasks、recent_nodes 等），12个 unique 节点产生28份副本。修复方案：改为扁平 `nodes` 列表 + `group_node_ids` 只存 ID 引用，体积回到合理范围，且消除“多份副本不一致”隐患。

**Claude-Opus-4.8 评价**：诊断正确，修复方向批准。但需补充两点：

1. **预期校准**：小图（12节点）场景下，各分组上限之和远大于节点数，slice 会覆盖全图，即使去重后体积也和原图相当，不会显著变小。slice 的压缩价值在数百上千节点时才显现。这不是 bug，是规模未到。

2. **额外风险**：`build_extractor_prompt.py` 无需改，但 **Extractor（LLM）** 是否依赖“分组内直接读节点内容”？改为 ID 引用后，LLM 需做 join。需核验 `extractor_system.md` 中关于 slice 和 conflict_candidates 的措辞，确认没有假设“分组内是完整内容”，以防冲突识别能力静默退化。

**元教训**：空图冒烟测试未暴露此问题，说明空图测试有盲区。建议将 slice 结构在非空图上的体积/去重加入回归检查清单。

**结论**：批准修复，但需同时：
- 重置预期（小图 slice 不小是正常的）
- 核验 `extractor_system.md` 原文，确认无隐含格式依赖
## slice 上下文恒定性与分组上限检查

**第一问：是否需等 patch_002 才能判断 Extractor 是否适应 ID 引用结构？**

分两层：
- **静态检查**（无需 patch）：读取 `extractor_system.md` 中描述 slice 的措辞，若声称“分组内含完整节点内容”，则改 ID 引用后字面失真。这一步立即做。
- **行为检查**（需 patch 比对）：验证 LLM 是否因 ID-join 漏判冲突。但即使漏判，`reconcile_patch.py` 的全图 `entity_ref` 精确匹配仍会兜底，属于召回下降而非正确性失守，非阻塞项。

**第二问：大图下 Extractor 的组装上下文规模是否保持恒定？**

**目标正确**：各分组均有容量上限 → slice 节点数 ≤ Σcap = 常数 → 总上下文有上界，不随全图线性增长。这正是 slice 设计的核心。

**但前提是每个分组都有硬上限，尤其 `active_open_tasks`、`standing_constraints`、`root_goals`**。若某分组无上限（如开放任务无限累积），上下文仍会随项目增长，破坏恒定目标。

**解法**：你的架构已支持设上限——全图 `reconcile` 兜底保证正确性，即便切片因上限砍掉某些节点、Extractor 漏判冲突，reconcile 仍能用全图 `entity_ref` 精确匹配抓回冲突。因此**敢设上限，依赖兜底**，两者互相成全。

**立即行动**：检查 `build_graph_slice.py` 中每个分组（尤其是 `active_open_tasks`）是否都设了硬上限。若某个无上限，需补充并依赖 reconcile 兜底。
## 课程文档检查与执行清单

**用户**：要求项目AI阅读课程设计文档中1590-1791行，给出可检查和执行的点。

**项目AI检查结果**：

### ✅ 已完成的检查
1. **分组上限检查**：所有分组均有硬上限（root_goals=5, standing_constraints=8, active_open_tasks=12, recent_nodes=16, symbol_hits=16, conflict_candidates=16, recent_edges=30）。slice节点总数被钉死在73个以内，上下文O(1)目标成立。Claude-Opus-4.8担心的active_open_tasks无上限不存在。
2. **extractor_system.md措辞**：第66行只说“对齐Slice中的active节点”，未假设分组内含完整内容，改为ID引用安全。

### 🔧 可执行的修改
将`build_graph_slice.py`从“分组存完整节点”改为“扁平nodes + group_node_ids”，消除重复存储。项目AI已执行，效果：体积从11,642降至7,312字节（减小37%），节点从28份副本降为12个唯一。纯节点+边内容（3,913）已小于原图（4,626）。slice略大于原图因元数据（group_node_ids、retrieval_trace、_runtime），小图下正常，大图时占比趋近0。

### 👤 需用户手动执行（非阻塞）
结构改完后，手动跑一轮真实抽取（如turn_002），对比patch输出，确认Extractor对conflict_candidates的冲突识别能力无退化。即使退化，reconcile全图兜底会用entity_ref精确匹配抓回，属于召回下降而非正确性失守。
## slice_002.json 行数差异说明

**用户**：重新生成 `slice_002.json` 后，发现其行数（271行）比上一轮 `graph_state.json`（148行）更多，询问是否符合预期。

**项目AI确认**：符合预期，但原因是**结构性差异**，不是 bug。

**行数差异根因**：JSON 格式不同
- `graph_state.json`：`nodes` 为字典 `{"n_0001": {...}}`，node_id 作 key，每个节点 1-2 行
- `slice_002.json`：`nodes` 为列表 `[{"node_id": "n_0001", ...}]`，node_id 作字段，每个节点 5-7 行（缩进+换行），外加 `status` 字段和 `group_node_ids` 分组引用

**实际喂给 LLM 的内容对比**（已剥离 `retrieval_trace`、`_runtime`）：
- 原图：3,764 字符，283 词
- slice：4,613 字符，343 词
- 差值：+849 字符（+23%），+60 词（+21%）

**关键判断**：
- 小图（N=12，cap 总和=73）：压缩率 ≈ min(12,73)/12 ≈ 1，slice 与原图大小相近是正常的规模效应，不是修复失败。
- 大图（N=200）：原图约 40,000+ 字符（O(N)），slice 仍被 cap 钉在约 8,000 字符（O(1)），优势才显现。

**优化建议**：不建议进一步优化。当前 21% overhead 换来的是**有界上下文保证**，且 `group_node_ids` 对 Extractor 的 conflict 识别有价值。slice 的真正价值是“大图有界”，不是“小图更小”。
## slice 检索轴心澄清与双 LLM 区分

**用户困惑**：TaskGraph 是否以最早 root-nodes 为根过滤后续对话？多 root 下，slice 是每个 root 单独切还是整体作为对话 LLM 的 context？

**Claude-Opus-4.8 指出矛盾**：用户前半句说“以 root 为根过滤”，后半句说“以当前对话关键字检索”——**后半句正确，前半句错误**。slice 的检索轴心是**当前轮对话**（通过正则提取符号），`root_goals` 只是附带的有界分组，不是过滤支点。“任务依赖”指节点间的边结构（依赖、约束、推翻），而非“与 root 相关才保留”的过滤。

**关键区分（问题根源）**：系统有**两个 LLM**：
- **Extractor LLM**：吃 `slice + 当前轮`，产出 patch。slice 是为它准备的，临时、每轮重建、有界。
- **对话 LLM**：吃的是 `memory_pack/skill`（整张图的压缩稿），不是 slice。

因此用户问的“slice 是否提交给对话 LLM”——**不是**。slice 只给 Extractor。

**per-root slice 是否有用？**
- **对 Extractor**：不应 per-root 拆，应取 union（整体）。冲突可能跨 root，分开会导致漏判跨 root 冲突。当前设计（turn-driven union）正确，且即使 slice 漏掉，reconcile 全图兜底也会抓回。
- **对对话 LLM**：per-root 聚焦裁剪是可行的未来特性，但这是另一条管线，目标不同（省 token 提升对话质量 vs 不漏冲突），不应与抽取 slice 混用。

**per-root 不能替代 O(1) 保证**：单个 root 子树仍可能无限增长，上下文恒定依然依赖每个分组有硬上限（如 `active_open_tasks` 的 cap）。

**结论**：slice 轴心是当前轮，不是 root。多 root 下 Extractor 需要整体 union，冲突跨 root 由 reconcile 兜底。per-root 聚焦更适合对话 LLM，但需与抽取管线分离。

## reconcile_patch.py 的作用时机

**用户问题**：`reconcile_patch.py graph_state.json patches/patch_002.json` 是在合并前比对还是合并后比对？

**项目AI回答**：是在 **apply（合并）之前** 比对。

- `reconcile_patch.py` 只读 `graph_state.json` 和 `patch.json`，不修改图。
- 它提取当前图的 active 节点，与 patch 中的新节点做冲突检查（node_id 冲突、内容重复、entity_ref 状态冲突等）。
- 正确位置：`LLM Extractor → patch → reconcile（前置校验）→ apply_patch → graph_lint`

**与 `apply_patch.py` 的区别**：

| | `reconcile_patch.py` | `apply_patch.py` |
|---|---|---|
| 是否修改图 | ❌ 只读 | ✅ 修改/输出新图 |
| 输入 | 当前图 + patch | 当前图 + patch |
| 输出 | 报告（errors/warnings） | 新图 |
| 顺序 | apply 之前 | apply 之后 |
| 目的 | 校验 patch 与全图一致性 | 合并 patch 进图 |

如果 reconcile 报错，应先修 patch，再 apply。
## reconcile_patch.py 工作原理

**定位**：纯机械的 patch 前置校验器，不调用 LLM，不修改图。在 `apply_patch.py` 合并前，扫描 `patch` 中的新节点与完整图，提前发现重复、冲突和遗漏的废弃声明。

**输入输出**：
- 输入：`graph_state.json`（当前图）、`patch.json`（待应用 patch）
- 输出：报告（含 `ok`、`summary`、`errors`、`warnings`、`entity_ref_matches`、`resolved_conflicts`、`weak_matches`）

**核心检查逻辑**（对每个 `new_node`）：

1. **自身格式检查**：缺 `node_id`、`patch` 内重复 ID → error
2. **与当前图冲突**：ID 已存在、内容/type/state 完全重复 → error
3. **`entity_ref` 强判定**（核心）：
   - 同 `entity_ref` + 相同 state + 高相似度 → warning（可能重复）
   - 同 `entity_ref` + 不同 state → 视为冲突，要求 patch 同时声明 `superseded_nodes` + `invalidates` 边，缺一报 error
4. **无 `entity_ref` 弱兜底**：仅用文本相似度匹配 → warning，不强制阻断

**解析的 patch 字段**：`new_nodes`、`superseded_nodes`、`new_edges`（找 `invalidates`）、`invalidates` 显式列表、节点内部 `invalidates/supersedes`

**设计原则**：
- 只读不写
- 全图兜底（不依赖 slice）
- `entity_ref` 精确匹配优先（强判定）
- 无 `entity_ref` 仅 warning
- 有 error 退出码 1（可被 CI 拦截）

**一句话**：`reconcile_patch.py` 是 apply 前的机械门卫，确保入库 patch 不自相矛盾。

## apply_patch.py 与 graph_lint.py 工作原理

**apply_patch.py（写入器）**：纯机械合并，不调用 LLM。将 `patch.json` 应用到当前图，生成新图。处理顺序严格：先深拷贝原图 → 规范化 nodes/edges → 依次应用 `updated_nodes`（更新）、`superseded_nodes`（标记废弃）、`new_nodes`（新增，ID 冲突则报错）、`new_edges`（添加边，兼容多种端点写法）→ 更新 `turn_counter` → 输出新图（可选快照）。关键特性：只做机械合并，顺序重要（先 superseded 再 new 避免 ID 冲突）。

**graph_lint.py（后置质检器）**：patch 应用后运行，检查全图结构/语义不变量，只读不写。检查项包括：
- 节点基础结构：缺 ID、重复 ID（error）；state 不在枚举内（warning）
- 边基础结构：缺 relation、relation 不合法、缺端点、端点不存在（error）
- `invalidates` 语义：指向不存在或未标记 `superseded` 的节点（error）
- active 图语义：非根 UserGoal 的 active 孤立节点（error）；同 `entity_ref` 下互斥 active state（error）
- OpenTask 生命周期：完成后 state 非 `resolved`、`resolved` 仍 active（error）；内容似完成但未 `resolved`（warning）
- `entity_ref` 建议：含工单号/路径等可识别内容但缺 `entity_ref`（warning）

输出报告，有 error 退出码 1（`--fail-on-warning` 可令 warning 也退出 1，`--no-fail` 总是 0）。

**Pipeline 位置**：`reconcile_patch.py`（apply 前，只读）→ `apply_patch.py`（写入新图）→ `graph_lint.py`（apply 后，只读）。三者分工明确：前置校验、写入、后置质检。

## reconcile_patch.py 与 graph_lint.py 的区别

用户认为两者都需要输入图，只是时机不同，似乎差不多，质疑是否需要 graph_lint.py。

**KIMI2.7 解释**：两者检查对象不同，不是重复防护。

| | reconcile_patch.py | graph_lint.py |
|---|---|---|
| 检查对象 | patch vs 当前图（增量） | 当前图本身（全量状态） |
| 核心问题 | “这个 patch 能安全 apply 吗？” | “当前这张图本身合法吗？” |
| 依赖输入 | graph + patch | 只要 graph |
| 运行时机 | apply 之前 | apply 之后（或任意时刻） |

**为什么 reconcile 替代不了 lint？**

1. **apply 过程可能引入 bug**：reconcile 只读原始 patch，不读 apply 后的结果。lint 能抓住 apply 产生的错误（如 invalidates 边指向未 superseded 的节点、边指向不存在节点等）。
2. **历史累积问题**：多轮 apply 后可能慢慢出现孤立 active 节点、同 entity_ref 不同 state 的 active 节点、已完成仍 active 的 OpenTask 等——这些不是本轮 patch 造成的，reconcile 看不到。
3. **图结构完整性**：lint 检查 node_id 重复、relation 合法性、孤立节点、OpenTask 生命周期等与有无 patch 无关的全局不变量。

**比喻**：
- reconcile = 进货前检查新货是否和库存冲突
- apply = 把货搬进仓库
- lint = 搬完后检查整个仓库货架是否整齐、有没有放错、有没有过期

没有 lint，仓库慢慢变乱；没有 reconcile，可能进错货。两者缺一不可。它不是“多一张防护网”，而是不同层级的防护（进货前、搬运时、搬运后）。

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
# [/COMPACTED]

