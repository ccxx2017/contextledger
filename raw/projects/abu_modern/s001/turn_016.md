# 用户：
附件1(docs\architecture\overview.md)是我当前的量化系统的简介，上面的内容是正在实施的模块的工作总结，附件3(temporary_for_test\BDO组织推进\openclaw.md)是openclaw的简介，我的问题是：
1. Ticket B启动时的提示词很详细，那么实际用户通过飞书下达研究任务也要这么详细吗？如果用户只是用自然语言描述了一个研究任务，openclaw的智能体会严格的按照设计的那样去开展研究吗？
2. 最让我迷惑的是，我们设计了strategy-researcher这个智能体，但用户在飞书向智能体交待Ticket B的任务时，它如何知道自己的身份是strategy-researcher呢？它会把我们给它的那些schema文件，包括SKILL.md，TOOLS.md，scripts中的那些文件，尤其是prompts中的那些设定都会阅读吗？openclaw保证会走这些流程吗？
3. aos中的那些对它的身份宪法以及相关规则它是如何知晓的呢？
以上问题我希望你认真回答！
# Claude Opus4.7:
*Thinking...*

>  The user is asking some fundamental questions about how OpenClaw agents work—specifically whether they need highly structured input like the Ticket B template to follow a designed workflow, or if natural language descriptions are enough, and how agents actually know their assigned identity like "strategy-researcher."
> 
> The real issue here is that there's a gap between the documentation and the actual mechanics. OpenClaw does have a skills system where SKILL.md files get loaded automatically based on workspace configuration, but the agent's identity and the AOS charter aren't automatically injected into context just because they exist as markdown files in a repo. The agent needs to be explicitly configured with its workspace, and that workspace determines which skills are available. The agent identity itself has to be set up through the workspace routing mechanism—each agent is essentially a workspace configuration that gets invoked when inbound channels are routed to it. The real issue is that AOS exists as governance on paper, but OpenClaw doesn't inherently know about it—the Charter only shapes agent behavior if those constraints get encoded into SKILL.md. So the enforcement chain is: Charter → SKILL.md → agent context → actual behavior. Anything in the Charter that doesn't make it into SKILL.md instructions has no teeth. This is the gap between the system design and what the agent actually does.
> 
> Now I'm thinking through how to answer each question directly: the first one about detail levels, the second about how OpenClaw actually loads configuration and files, and the third about whether the Charter needs explicit engineering to matter. The user deserves a straightforward answer about what's automatic versus what requires intentional design.

这三个问题问到了**整个系统最关键的"纸面 vs 实际"裂缝**。我认真回答，不粉饰。

---

## 先把底层机制讲清楚：OpenClaw 实际是怎么运作的

你脑子里可能有一个模糊的假设：**"我把这些文件放对位置，智能体就会按设计运行。"** 这个假设**只有一半是对的**。

真实机制是：

- 每次用户在飞书发消息，OpenClaw 会组装一个 **context 包**喂给底层 LLM（DeepSeek / Claude / GPT 等）
- 这个 context 包里包含：系统提示词（由 SKILL 加载器生成）+ 工具描述 + 对话历史 + 本轮用户消息
- LLM 基于这个 context **概率性地**生成回复与工具调用
- **凡是没进 context 的文件，对智能体的行为就没有影响**

关键后果：**AOS 的 Charter、ticket_protocol.md 这些文件，OpenClaw 自身并不认识**。它们只是磁盘上的 markdown。它们之所以可能影响智能体行为，**仅仅是因为 SKILL.md 里指示智能体去读它们**，或者**你或项目 AI 在生成 SKILL.md 时把相关约束抄了一份进去**。

所以结论是：**SKILL.md 是唯一的"接口层"**，它是纸面制度和真实行为的唯一桥梁。Charter 里写了但 SKILL.md 没落地的条款，在运行时相当于不存在。

---

## Q1：用户在飞书下达任务要有多详细？

### 诚实答案：**不需要像工单模板那样详细，但信息必须足够智能体展开工作**

你在飞书可以直接说：

> @strategy-researcher 帮我研究一下"前面有趋势、一轮调整、结构紧凑、然后放量拉升"这种买点，看看在 A 股能不能做成策略

**但接下来会发生什么，完全取决于 SKILL.md / research_workflow.md 的设计**。可能的路径有三种：

**路径 A — 智能体直接开跑**。它会按 research_workflow.md 的 Phase 0→6 走，但因为你没给 universe、时间窗、成功标准等约束，它会**自己替你决定**（可能用默认沪深 300、默认 2020-2024、默认 sharpe 0.8 作为及格线）。风险：它的默认可能不是你想要的。

**路径 B — 智能体先反问澄清**。如果 SKILL.md 里明确写了"investigation 工单收到口语化需求时，必须先生成 draft ticket 发给 Boss 审批，审批后再执行"，它才会这样做。**但你现在的 SKILL.md 和 research_workflow.md 里并没有这一步**——Phase 1 直接是"工单校验"，假设工单已经成型。

**路径 C — 智能体凭 LLM 本能给出一个漂亮的回复，但不真的执行**。LLM 在缺少明确工具调用指令时，有很强的"对话式敷衍"倾向——它会跟你讨论这个形态多么经典、可以从哪几个维度研究，但不调用 call_builder.py。这是你最需要警惕的失败模式。

### 会严格按设计执行吗？

**不会严格，只会"倾向性"执行。**

LLM 跟随指令是概率的，不是命令式的。影响遵从度的因素：
- SKILL.md 越清晰、越短、越强制性措辞（"MUST"/"必须"/"禁止"），遵从概率越高
- 底层模型越强（Claude Opus / DeepSeek-V4-Pro），遵从概率越高；flash 类模型偏离概率明显更高
- context 越长（对话拉得久），对初始 SKILL.md 的注意力越弱——这叫 **instruction drift**
- 工具描述和 SKILL 描述越一致，调用越稳定；矛盾越多，智能体越会"自由发挥"

### 实操建议

为了让 Ticket B 这次真跑起来，我建议你**不要在飞书直接下口语化需求**，而是：

1. **把我起草的那份详细工单文件，直接作为工单 commit 到 aos_repo**
2. **在飞书里只说一句**：`@strategy-researcher 请处理 TKT-2026-00X，工单已在 aos/runtime/tickets/open/ 下`
3. 让智能体走 Phase 0（git pull）→ Phase 1（校验工单）→ ……

这样绕开了"口语化需求 → 工单"的翻译环节，把这个翻译工作**暂时留在你（Boss）这里**。等跑通一次后，你才有资格考虑是否要加一个"Phase -1：从飞书口语化需求生成 draft ticket"的预处理环节——那是 SKILL.md v0.3 该做的事。

---

## Q2：智能体如何知道自己是 strategy-researcher？它会读那堆文件吗？

### 身份的真实来源：OpenClaw workspace 配置，不是文件内容

OpenClaw 的多 agent 机制是这样的（参考你附件 3 的"Multi-agent routing"）：

- 你在 OpenClaw 里配置一个 **workspace**，名字叫 `strategy-researcher`（或你实际取的名字）
- 这个 workspace 绑定一组 **skills**（目录）和一个 **底层 LLM 账号**
- 你配置 **路由规则**：从飞书某个群 / 某个 @ 目标路由到这个 workspace
- 当消息进来时，OpenClaw 加载这个 workspace 的所有 skills，组装 system prompt

**所以"智能体知道自己是 strategy-researcher"的机制是**：workspace 名称 + 加载进来的 SKILL.md 第一段的身份声明（你 SKILL.md 开头那段"你是 strategy-researcher..."的文字）。**它不是通过"阅读 Charter"知道自己是谁，它是通过"被配置为这个 workspace"才成为这个身份的**。

### 文件读取实际情况

| 文件 | 是否自动进 LLM context | 说明 |
|---|---|---|
| `SKILL.md` | ✅ **会**，当技能激活时自动拼入 system prompt | 这是 OpenClaw 技能系统的核心机制 |
| `TOOLS.md` | ⚠️ **不一定**。取决于 OpenClaw 版本——有的版本会把同目录 .md 一起加载，有的只加载 SKILL.md | 更可靠的做法是在 SKILL.md 里显式 include 关键段落 |
| `scripts/*.py` | ❌ **不会**进 context。它们是**可调用的工具**，而非给智能体阅读的文档 | 智能体通过工具调用（类似 bash / subprocess）执行它们，看到的是 stdout |
| `prompts/research_workflow.md` | ❌ **默认不会**。这是你自己约定的资产，OpenClaw 不认识 | **必须智能体主动去读**才能进 context |
| `prompts/hypothesis_heuristics.md` | ❌ 同上 | 同上 |
| `prompts/report_template.md` | ❌ 同上 | 同上 |
| `aos/org/agents/agent-strategy-researcher.md` (Charter) | ❌ **完全不会**。OpenClaw 对 aos/ 目录毫无概念 | 同上 |
| `aos/runtime/tickets/open/TKT-*.md` | ❌ **不会**。工单要进 context 必须智能体主动 read | 同上 |

### 那 prompts 和 Charter 怎么真正生效？

**唯一靠谱的机制是：SKILL.md 在主流程中明确命令智能体去读它们。**

你的 SKILL.md 里应该有类似这样的指令（如果还没有，这就是最大漏洞）：

```
## 主流程 · Phase 0 启动
1. 读取 prompts/research_workflow.md 全文作为本次工单的行动手册
2. 读取当前工单 ${TICKETS_DIR}/TKT-XXX.md 全文
3. 按 research_workflow.md Phase 0 的指示执行 git pull
...
```

**如果 SKILL.md 没有"read prompts/research_workflow.md"这一句**，那么智能体在飞书收到"处理 TKT-xxx"时会怎么做？答案是：**基于 SKILL.md 里已经直接写进去的内容 + 它的 LLM 本能**。prompts 目录里那几份精心设计的文档会**沉睡在磁盘上，永远不进 context**。

### 建议你现在就做的一次核验

打开你刚 commit 的 SKILL.md v0.2.0，搜索这几个关键字：

- `research_workflow.md` — 有没有在主流程里被显式读取？
- `hypothesis_heuristics.md` — 有没有被显式告知在 Phase 3 读取？
- `report_template.md` — 有没有被显式告知在 Phase 5 读取？

**如果三个都有明确的 "读取 / load / include" 指令，那流程闭环了**。如果只是在"工具索引"段落被列出名字，那就是**挂在墙上的摆设**——智能体会看到它们存在但不会主动打开。

另外 Charter 里的条款（读写边界、HITL 阈值、deploy 禁用等），**必须在 SKILL.md 中再写一遍**。Charter 是给你和未来 org-maintainer 看的"制度文档"，**对 LLM 没有直接约束力**。

---

## Q3：AOS 的身份宪法（Charter）它如何知晓？

### 诚实答案：**默认完全不知晓。**

- OpenClaw 不扫描 aos/ 目录
- Charter 是 markdown 文件，对 LLM 而言等于磁盘深处的一段文字，除非被显式读入 context
- 所谓"Charter 约束智能体"是**设计意图层**的说法；在**运行时层**，约束只存在于 SKILL.md 注入的 system prompt 里

**Charter 的真正角色是什么**：

它不是给智能体直接读的（除非你刻意让它读）。它的真实角色是：

1. **给你和未来 Agent Org Maintainer 看的治理契约**——定义这个数字员工的职责边界
2. **作为写 SKILL.md 的蓝本**——SKILL.md 是 Charter 的"runtime 子集"，所有约束在 SKILL.md 里必须有对应落地
3. **Review 时的参照系**——当智能体跑歪了，你回头对照 Charter 判断是"SKILL.md 没落地"还是"Charter 本身有问题"

换句话说：**Charter 管的是"这个岗位的定义"，SKILL.md 管的是"这个岗位今天怎么干活"。前者是组织设计，后者是运行时指令**。

### 那有没有办法让 Charter 真的进 context？

有两种做法：

**做法 1（推荐）**：在 SKILL.md 里把 Charter 中对运行时有约束的条款**原文摘抄**进来——读写边界、HITL 阈值、禁用端点等。这是当前 SKILL.md 已经在做的事，只是需要你核验覆盖是否完整。

**做法 2（进阶）**：在 SKILL.md Phase 0 里加一条 `读取 ${CHARTER_PATH} 全文`。但我**不推荐**——原因是 Charter 文字风格对 LLM 来说太"宪法式"，不够操作性；而且会额外烧 token。SKILL.md 已经是 Charter 的工程化版本，让它同时读两遍是浪费。

---

## 一句话总结三个问题

> **在 OpenClaw 里，"智能体"不是读了一堆制度文件就获得身份和规则的"员工"；它是一个被 workspace 配置 + SKILL.md 注入 system prompt 的 LLM 会话。凡是没以某种方式进入 context 的文件，对它而言等于不存在。你设计的 AOS/Charter/prompts 这一整套纸面制度，只有通过 SKILL.md 这一个桥梁才能真正约束运行时行为——SKILL.md 写到哪儿，员工就自律到哪儿；SKILL.md 漏的，员工就漏的。**

---

## 我给你的即刻行动建议

在派出 Ticket B 之前，做一次 **SKILL.md 覆盖审计**：

1. 打开 `openclaw_skills/strategy_researcher/SKILL.md`
2. 逐条核对：Charter 中每一条读写边界、HITL 阈值、禁用规则，SKILL.md 里是否都有对应落地
3. 核对：主流程中是否显式命令智能体在 Phase 0/3/5 读取对应 prompts 文件
4. 核对：`${BACKEND_BASE_URL}` 等端点常量是否在 SKILL.md 里已经给出具体值（智能体不会自己去 quant_assistant 里找）
5. 核对：工单路径常量是否对齐 Ubuntu 侧实际目录（前面踩过的坑）

如果这次审计发现有漏的，就**先开一张 TKT-2026-00X-skill-gap-patch** 补完，再派 Ticket B。不然你派出去那张精心设计的工单，很可能遇上的是一个**只记得自己叫 strategy-researcher、却不记得自己该按 research_workflow.md 五轮循环的员工**——它会用 LLM 本能给你回一份文采飞扬的研究报告，但一次 call_backtest 都没真的调用。

这是这个阶段最容易踩的坑，也是你问这三个问题时，我听出来你已经在隐隐担心的那个坑。
