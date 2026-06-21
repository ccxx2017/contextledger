## 课程设计初期阶段

**用户目标**：将基于计算图的LLM上下文依赖追踪原创方案（受Micrograd启发）与Claude Code的44个feature flag系列课程结合，询问AI是否可行。

**AI结论**：非常可行，建议将课程从“解读Claude Code”升级为“从Claude Code出发，提出并实现自己的上下文管理方案”，实现热点入口、方法论深度、原创实验三层次。否定硬拼接，采用三段式每讲结构（现实问题→抽象问题→图方案）。课程总纲10讲，题为《从Claude Code的Feature Flags到Logic Graph：重建AI Agent的上下文工程》。

---

## 第0讲教案

**用户目标**：要求AI提供第0讲教案。

**AI输出**：60分钟线上课，初中生受众。教学目标：了解Claude Code、Feature Flag概念、上下文重要性、Logic Graph思想来源。教学过程：开场（源码还原事件）→ Feature Flags概念与源码演示（18分钟）→ 上下文管理问题（12分钟）→ Micrograd到Logic Graph类比（14分钟）→ 课程路线图（8分钟）。核心结论：44个开关表明上下文管理是AI Agent核心工程战场。

---

## 第1讲源码调查

**用户目标**：要求AI根据课程总纲给出第1讲教案（门控体系），提示AI可先调查Claude Code源码细节。

**AI响应**：先提出5项源码调查任务（feature()实现、betas.ts内容、COORDINATOR_MODE门控路径、运行期配置、门控模式统计），要求用户将调查提示词交给项目AI，获取真实代码细节后再撰写教案，同时给出教案骨架供参考。

---

## 第1讲教案

**用户目标**：基于已完成源码调查，输出第1讲完整教案。

**AI输出**：45-55分钟，核心问题“持续演化中的复杂Agent系统如何让新功能和稳定性共存？”六层门控模型（编译期L0→环境变量L1→远程实验L2→配置文件L3→API能力L4→Kill Switch L5），逐层用真实代码讲解。案例深挖COORDINATOR_MODE完整门控链路。为Logic Graph原型设计五层迁移门控。结论：门控体系是管理演化复杂性的架构能力。

---

## 第2讲源码调查

**用户目标**：用户准备制作第2讲教案（上下文工程），自行给出六个详细调查任务（Compact系统架构、CONTEXT_COLLAPSE/HISTORY_SNIP、Token计数与预算、System Prompt组装、工具输出管理、上下文管理完整生命周期），要求项目AI执行调查并提供结果，供AI撰写教案使用。

**用户任务**：用户提供了“上下文工程源码调查报告.md”，AI基于调查结果撰写第2课完整教案，并按一贯原则压缩。

**后续状态**：教案已完整交付，用户可继续要求第3讲或调整。

## 第2课教案核心内容（压缩版）

**课程定位**：Claude Code在有限上下文窗口中维持无限长对话。核心命题：Agent越能干，记忆消耗越快。上下文管理是整个Agent架构的地基。

**上下文预算模型**：窗口200K~1M。固定开销（System Prompt+工具Schema）不可压缩；可变开销（消息历史+工具交互）是压缩主战场；净空间预留20K tokens。

**五层防御体系**（梯度响应，信息损失递增）：
- **L1 源头控制**：工具输出截断（单结果50K字符，消息级200K，绝对上限400K字节）。超限内容持久化到磁盘，上下文仅放2KB预览+`<persisted-output>`标签。文件读取≤256KB/25K tokens，Bash默认30K字符硬上限150K。
- **L2 折叠压缩（Context Collapse）**：`CONTEXT_COLLAPSE`，每次API调用前将连续搜索/读取操作折叠为摘要消息。在90%窗口提交，95%阻塞。
- **L3 微压缩（MicroCompact）**：`CACHED_MICROCOMPACT`，距最后assistant消息>60分钟或缓存工具结果超阈值时触发。
- **L4 全量压缩（Auto Compact）**：token使用量超过有效窗口-13K时触发。LLM生成结构化摘要，输出上限20K tokens，禁止工具调用。消息按API轮次分组，保留最近组、摘要较早组。
- **L5 应急响应（Reactive Compact）**：API返回413错误时触发，最后安全网。

**Compact核心机制**：触发决策链（全局禁用→CONTEXT_COLLAPSE跳过→递归防护→token估算→阈值比较）→消息分组（保证tool_use与tool_result成对）→保留决策（`adjustIndexToPreserveAPIInvariants`）→摘要生成（`<analysis>`+`<summary>`，后提取`<summary>`）→断路器（连续失败≥3次停止）→降级链（会话内存压缩→传统压缩）。

**完整生命周期**：用户消息→上下文组装→响应返回→工具执行→超阈值触发compact→重建消息列表→继续对话。Token使用量呈锯齿形。

**可迁移设计模式**：梯度响应架构、摘要作为消息（可被后续压缩）、断路器模式、按API轮次分组、多源token估算回退。Logic Graph可利用图结构为节点赋予不同保留优先级。

---

## 第2课源码校正（prompt.ts）

**用户补充**：提供 `src/services/compact/prompt.ts` 源码文件。

**AI校正结论**：Claude Code的Compact是强约束、强结构化、明确禁止工具调用的摘要流程。

- **9个固定栏目**：Primary Request and Intent、Key Technical Concepts、Files and Code Sections、Errors and fixes、Problem Solving、All user messages、Pending Tasks、Current Work、Optional Next Step（源码硬编码要求）。
- **禁止工具调用为激进双保险**：`NO_TOOLS_PREAMBLE`（首部）+ `NO_TOOLS_TRAILER`（结尾），防止模型在compact单轮误调用工具。
- **`<analysis>`是草稿区**：用于提升摘要质量，但`formatCompactSummary()`会剥离，不进入后续上下文。
- **`formatCompactSummary()`三步处理**：删除`<analysis>`→提取`<summary>`→压缩多余空行。
- **摘要作为continuation message注入**：`getCompactUserSummaryMessage()`生成，内含摘要和控制参数。支持三种续接模式。
- **Partial compact有两种语义**：`from`模式（仅总结最近新增消息）和`up_to`模式（总结前缀完整历史）。

---

## 第3课教案：从Micrograd到Logic Graph

**课程定位**：承接第2讲，指出现有压缩策略仍围绕“消息顺序”和“token数量”，缺乏对信息重要性和依赖关系的判断。引入**Logic Graph**：将用户目标、约束、工具结果、文件修改、决策、摘要显式组织成依赖图。

**核心问题**：AI的最终答案依赖哪些可观察信息？能否追溯依赖的用户需求、文件内容、工具结果？能否判断哪些旧信息不能丢、前提变化后哪些结论失效？追踪的不是模型内部思维，而是外部可记录的任务依赖关系。

**Micrograd启发**：每个计算结果带血缘档案（`_prev`前驱、`_op`操作）。类比到AI任务，将关键对象建模为`ContextNode`（含`content`、`prev_nodes`、`operation_type`、`node_type`、`metadata`）。

**Logic Graph改进上下文管理的四个问题**：
1. 哪些旧信息不能丢——保留依赖链上的节点。
2. 哪些内容可安全压缩——节点状态分active、dormant、summarized、external、garbage、invalidated，只压缩依赖链之外的节点。
3. 前提变化的影响传播——标记依赖该约束的所有下游节点invalidated。
4. 工具结果错误的回溯——错误沿`ToolResultNode→DecisionNode→FinalAnswerNode`传播。

**与Claude Code的关系**：Compact是执行层（token不够时压缩），Logic Graph是决策层（判断保留/摘要/丢弃），二者组合成依赖感知压缩。

## 第4讲教案（压缩版）

**定位**：一个任务=一张持续更新的图，每轮对话=一次Graph Patch。目标是建立学生对“图式上下文管理”的第一层理解。

**核心概念**：
- **任务级图 vs 轮次级图**：错误做法是每轮建新图。正确做法是TaskGraph持续存在，每轮产生Patch合并进图。
- **节点类型（7种）**：UserGoal、Constraint、Fact、ToolResult、Decision、FileArtifact、OpenTask。状态：active / superseded / done。
- **Patch结构**：含task_id、turn_id、new_nodes、updated_nodes、superseded_nodes（含原因）、new_edges。

**示例（三轮Minecraft演化）**：第1轮创建目标→第2轮新增决策→第3轮约束推翻旧方案、标记superseded并留痕。体现“图是长出来的，被推翻节点可回溯”。

**最小可运行代码**（Python）：定义Node/Edge/TaskGraph、GraphStore、Deduplicator、GraphUpdater.apply_patch（处理superseded改状态、new_nodes去重映射、updated_nodes更新、new_edges添加），to_mermaid生成可视化。

**执行机制澄清**：不是把用户原话直接丢给主对话模型，而是通过Graph Extractor Prompt让大模型执行“抽取依赖图Patch”的任务。每轮输入需附带已有TaskGraph摘要。

**三种操作方案**：①手工版（适合入门演示）；②工程版（API自动调用LLM）；③产品版（旁路监听，第4讲不实现）。

**用户质疑与AI确认**：Logic Graph是**任务态上下文压缩机制**，不是通用压缩器。没有任务时不启动，因闲聊缺乏目标、约束、决策等结构。价值在于压缩任务型对话，保留目标、约束、决策、方案演化、待办、依赖等结构。不取代所有上下文管理，只负责最有结构价值的部分。

**架构建议**：三层——Recent Context（最近几轮）、Session Summary（普通聊天轻量摘要）、Task Logic Graph（任务态结构化记忆）。

---

## 第5讲定位修正

**用户质疑**：第5讲不应重复建图时机，也不应主要讲压缩。

**AI修正**：
- **第4讲（写入侧）**：用户对话→Extractor→Graph Patch→TaskGraph，回答“图怎么长出来”。
- **第5讲（读取侧）**：TaskGraph→Context Builder→Task Context Pack→主LLM，回答“图怎么喂回主LLM”。产物是结构化任务上下文包，而非压缩后的聊天记录。

**标题修正**：从“用Logic Graph压缩上下文”改为“从TaskGraph到Context Pack：把任务图喂回主LLM”。不以token不够为主线，而以构建Context Pack为主线。

## 第5讲教案（压缩版）

**本讲定位**：完成读取侧——将TaskGraph转换为Task Context Pack喂给主LLM。不讨论建图时机、抽取、token压缩。核心问题：TaskGraph如何整理成主LLM直接使用的上下文？

**第4/5讲分工**：第4讲写入（对话→Patch→图），第5讲读取（图→Context Pack→主LLM）。

**学习目标**：理解不能直接塞整张图（结构不友好、active/superseded混用、无阅读顺序、图变大）；实现`build_context_pack`区分active/superseded生成结构化包；转换为Prompt片段注入主LLM。

**课时90分钟**：回顾(5')→不能塞图(10')→定义Context Pack(15')→读取依赖链(20')→代码实现(25')→注入主LLM(10')→总结(5')。

**Context Pack定义**：结构化字段含task_id、current_focus、goals、active_constraints、current_decisions、relevant_facts、open_tasks、superseded_history。是继续任务所需的状态，非聊天摘要或图dump。

**读取依赖链**：从当前焦点（最新active OpenTask）沿`depends_on/implements/serves/refines`向上游追踪，收集`invalidates`边将推翻方案放入superseded_history。边既记录演化也指导读取。

**最小代码实现**：提供`trace_upstream`、`collect_superseded_history`、`build_context_pack`、`context_pack_to_prompt`。若`active_constraints`为空，需在建图时补充`depends_on`边——体现“读取倒逼建图质量”。

**注入主LLM**：转为Markdown Prompt片段，附加约束（不采用推翻方案、遵守约束、围绕焦点）。对比有无Context Pack时模型缺失的信息。

**核心结论**：Logic Graph第一价值是组织任务状态，非压缩token。Context Pack是常规读取产物，非紧急压缩。

**核心三句话**：TaskGraph不是直接塞Prompt的内容；Context Pack才是主LLM继续执行的上下文；第4讲写入图，第5讲读取图。

---

## 第6讲定位修正

**用户请求**：基于前5讲重新审视第6讲教案。

**AI判断**：需**较大修改**。原第6讲将第5讲误解为“依赖感知压缩”，但第5讲已改为“TaskGraph→Context Pack→主LLM”读取任务图，非压缩上下文。

**修改后第6讲定位**：任务结束后，哪些任务信息沉淀为长期Memory Store，并在新任务中召回。

**修改要点**：
1. 不将第6讲定位为第5讲的压缩升级版，而是“长期沉淀层”
2. Memory服务于任务态（项目、约束、决策、踩坑、待办），非通用聊天记忆
3. 召回路径：Memory→TaskGraph→Context Pack→主LLM，非直接塞入prompt

**三层关系**：
- TaskGraph：当前任务依赖结构（任务内）
- Context Pack：动态构建给主LLM的上下文
- Memory Store：跨任务/会话的长期任务记忆

**流程**：对话→Extractor→TaskGraph→Context Pack→主LLM；任务阶段结束→Memory Extractor→Memory Store；新任务→Recall→新TaskGraph种子节点→Context Pack。

**可沉淀**：长期目标、稳定约束、当前有效决策、用户偏好、未完成任务、踩坑记录。**不沉淀**：临时推理、大段工具输出、被推翻方案、闲聊、不稳定猜测。

**记忆节点类型**（六类）：FactMemory、PreferenceMemory、ConstraintMemory、DecisionMemory、OpenTaskMemory、ErrorMemory。生命周期：create/update/merge/invalidate/archive/delete。

**失效传播**：约束变化时，invalid→downstream suspect→需重新确认，非简单级联删除。

**Demo**：Minecraft三会话（提出→补充权限→召回），展示沉淀→更新→召回闭环。

## 第6–10讲课程定位修正与重写（压缩版）

**第6讲定位**（已定稿）：任务记忆沉淀层——任务结束后，哪些内容值得跨会话长期保留并在新任务中召回。流程：TaskGraph → Memory Extractor → Memory Store → 召回 → 新TaskGraph种子节点 → Context Pack → 主LLM。记忆类型六类（Fact/Preference/Constraint/Decision/OpenTask/Error），生命周期含invalidate/archive，失效传播为suspect而非级联删除。Demo延续Minecraft三会话展示沉淀—更新—召回闭环。

**第7讲重写**（多Agent协作）：原方向正确但与第4–6讲定位不匹配。重写后：Coordinator基于TaskGraph为各Worker生成最小Worker Context Pack；Worker只返回Result+Graph Patch，不直接改图；Coordinator统一合并Patch并处理身份/内容/依赖冲突；Verifier独立验证Claim+Evidence，返回Verification Patch。核心原则：TaskGraph单写入，Worker多读取；单Agent时代是写入/读取，多Agent时代是不同Agent只看到自己的Context Pack，TaskGraph必须单点合并。

**第8讲调整**（工具/文件/测试证据）：原主干正确，但Verifier/taint写得太重。修订聚焦“外部证据如何进入依赖图”，主线：工具调用→工具结果→文件产物→测试结果→依赖边→压缩与失效。增加TestResultNode（命令/状态/passed/failed/输出引用），弱化“证据能重放”强化“证据能追踪”。核心表述：信息有来源，依赖有方向，文件有版本，结果能回查。

**第9讲重写**（可观测性）：从“AI Reasoning Debugger”调整为“TaskGraph管线调试”——观察Patch、TaskGraph、Context Pack、Memory Recall、工具证据等中间产物，定位错误来自抽取、合并、构建、召回还是证据失效。核心产物为静态`Task Context Debug Report`（含conversation/patches/graph/context_pack/memory_recall/evidence/timeline），重点做**Context Pack Trace**（每条信息入选/排除均有reason），帮助回答“主LLM看到了什么、为什么看到这些、旧方案为何被推翻、证据支撑了哪些结论”。

**第10讲总结**：闭环前9讲为完整任务态上下文管理管线，明确定位——Logic Graph是任务态上下文管理机制，通过TaskGraph记录目标/约束/事实/决策/工具结果/文件产物/记忆引用/被推翻方案，通过Context Pack喂给主LLM。它不是模型内心推理还原，不是通用聊天压缩器，不是Compact替代品，不是万能长期记忆。最终Demo延续Minecraft展示完整闭环。后续路线：工程封装为Python包、产品化为Task Context Debugger、研究评测抽取准确率/Context Pack完成率/失效传播策略、教学可打包为实战课。

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

## 第4.5课模板长度问题与精简版

**用户**：感觉模板过长（15kb/4000 token），放入 graph slice 和对话后会更大，担心 Extractor 模型遵从指令能力下降。

**Claude-Opus-4.8 确认**：判断正确。长模板每轮运行成本高、稀释核心指令注意力，且存在明显冗余（状态迁移→superseded+invalidates 规则重复至少四遍）。合理目标是保留全部语义约束，删除重复表述和冗长示例，压缩至原 40% 左右。

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