# 用户：
好的，我们现在已经进入了很关键的构建阶段了，请你一定要考虑周全，准确的实施，就按照你的建议进行
# Claude Opus4.7:
*Thinking...*

>  用户要求我按建议执行，先交付 P0 版本——一个基于 TOOLS.md 的精简版本。我需要仔细考虑根 TOOLS.md 的结构：它应该作为路由和分诊层而非工具清单，包含三个技能模块（duty_reporter、quant_assistant、strategy_researcher），并配置相应的分诊规则。
> 
> 现在我在思考全局约束应该包含什么。从原文中，有些原则虽然源自特定技能但具有普遍意义——比如工具调用失败时避免穷举试错，这可以降级为建议；而"每次查询实时执行脚本"和"高风险操作需确认"则是真正的全局适用原则。那些特定的错误语义（如 backend_unreachable）应该留在各技能的 TOOLS.md 中。我正在起草根文件的结构，定义技能地图和分诊逻辑...
> 
> Generating markdown structure... 我需要理清分诊规则的表达方式，让 LLM 看到系统提示时能自然理解并执行。关键是确保全局约束清晰——特别是禁止写入 memory/ 目录，但要明确标注 strategy_researcher 在特定错误码下的授权重试例外。后端地址和脚本参数必须回迁到各技能的私有 TOOLS.md，而"失败不穷举试错"这条规则应该作为全局约束，因为 strategy_researcher 的自动重试是有明确触发条件的、属于规则的授权例外。我先输出 P0 版本给用户审核，这样能确保基础框架正确后再处理后续的 AGENTS.md 冲突问题。 现在我在完善 P0 的技能分诊规则和全局约束部分。分诊逻辑按优先级排序，命中即停；全局约束涵盖文件写入边界、实时执行、高风险操作确认、删除恢复机制和错误处理原则，这些对所有技能统一生效。
> 
> 我注意到原根目录 TOOLS.md 中的量化相关内容（后端地址、鉴权、脚本参数、错误语义表、专属规则）已经迁移到各技能私有的 TOOLS.md，所以需要提醒用户确保 skills/quant_assistant/TOOLS.md 已完整补充这些内容。
> 
> 我应该给出验证方法，并按照用户"按照建议进行"的指示只输出 P0 版本。
> 
> 实际上，用户上传的根 TOOLS.md 本质上就是 quant_assistant 的专属配置文件，被错误地放在了根目录，所以最干净的做法是直接把它移到 skills/quant_assistant/TOOLS.md，然后在根目录创建新的路由层 TOOLS.md。
> 
> 现在要开始写回复，记住用户要求简短直接、可验证，并提供完整可粘贴的文本。

好。P0 按两步走，因为根 TOOLS.md 当前的内容**本来就是 quant_assistant 的技能私有内容被误放到了根目录**——文件开头自己都写了"这份文件只放当前环境特定的信息，配合 SKILL.md 使用"。所以最干净的处理不是"删改内容"，而是**搬家 + 新建**。

## 步骤 1：把当前根 `TOOLS.md` 整体搬到 `skills/quant_assistant/TOOLS.md`

执行前先确认一件事（30 秒就能查）：

```bash
ls -la ~/.openclaw/workspace/skills/quant_assistant/TOOLS.md
```

- **如果该文件不存在**：直接 `mv ~/.openclaw/workspace/TOOLS.md ~/.openclaw/workspace/skills/quant_assistant/TOOLS.md`，搬家完成，不丢内容。
- **如果该文件已存在**：先 `diff` 两份，把根目录这份里多出来的内容手工合并进去，再删根目录那份（用 `trash`，不要 `rm`）。

**请你先做这一步并把 `ls` 结果告诉我**，再决定 mv 还是 merge。这一步不能猜。

## 步骤 2：在工作区根目录新建路由层 `TOOLS.md`

以下是完整替换文本，直接粘贴到 `~/.openclaw/workspace/TOOLS.md`：

```markdown
# TOOLS.md

本文件是工作区工具路由层，**不列具体工具**。
具体脚本、后端地址、环境变量、错误码语义一律以各技能目录下的
`skills/<name>/TOOLS.md` 为准。

## 技能地图

当前工作区注册三个技能：

- `skills/duty_reporter/`      — 值班日报员：ticket 扫描、健康巡检、日报生成
- `skills/quant_assistant/`    — 量化助手：飞书口语化单次指令下的策略构建 / 部署 / 下单
- `skills/strategy_researcher/` — 策略研究员：工单驱动的迭代式策略研究与回测

每个技能的 `SKILL.md` 是该技能被激活时的最高行为权威。

## 技能分诊

按以下顺序判定当前应激活哪个技能，**命中即停，不继续匹配**：

1. 输入包含 `TKT-*` 工单编号 **且** 工单字段中 `intent_type=investigation`
   → `strategy_researcher`
2. 由 cron/定时任务触发，且任务类型属于 ticket-scan / health-probe / daily-report
   → `duty_reporter`
3. 用户在飞书中以自然语言直接下达单次指令（构建策略 / 部署 / 下单 / 查询实例等）
   → `quant_assistant`
4. 以上均不匹配
   → 不激活任何技能，先向用户澄清意图，不要凭经验猜选

**切换约束**：同一会话已激活某技能后，不要中途切换。若确需切换，先完成当前
SKILL.md 的收尾动作（报告产出、状态归档），再显式切换。

## 全局约束（高于技能私有规则）

以下条款对所有技能一律生效：

1. **写文件边界**：不得私自创建或修改 `memory/`、根目录 `MEMORY.md`、根目录其它
   `*.md`（除非用户显式要求）。只允许写入被激活 SKILL.md 明确授权的路径。
2. **实时执行**：每次查询 / 状态读取均应实际调用脚本，不复述上一轮输出，不凭记忆
   臆测当前状态。
3. **高风险确认**：真实下单、部署到实盘、删除或覆盖持久化数据前，必须得到用户明确
   确认或工单中的显式授权字段。
4. **可恢复优先**：删除使用 `trash` 而非 `rm`。
5. **失败不穷举**：工具调用返回错误时，默认把错误码与错误信息原样返回给用户，等待
   下一步指令；禁止盲目轮换 API 路径、参数或脚本。
   - **授权例外**：技能 SKILL.md 中若明确定义了对特定错误码的自动处置策略
     （例如 `strategy_researcher` 对 `DATA_MISSING_SYNC_REQUIRED` 的自动剔除重试），
     按该技能规则执行。

## 已迁出本文件的内容

以下内容已从本文件移除，回到 `skills/quant_assistant/TOOLS.md`：

- 量化后端地址、鉴权环境变量
- `query.py / strategy_builder.py / strategy_deploy.py / order_execute.py` 的参数与命令模板
- 错误语义表（backend_unreachable / http_error / strategy_semantics_mismatch /
  confirmation_required / insufficient_quota）
- "回测只能走 strategy_builder 或 `/backtests/execution-config`"等专属规则

如需引用这些内容，请读取 `skills/quant_assistant/TOOLS.md`。
```

## P0 完成后的验证（行为级，不是嘴上级）

做完步骤 1 + 2，跑一次烟测。**不要**问"你是谁"这类嘴上题。改成下面两题：

**烟测 A（分诊）**
> 在飞书随便发一句："帮我查一下当前有哪些实例在跑。"

观察点：
- 它应在 trace 中 `read_file skills/quant_assistant/SKILL.md`（命中分诊规则 3）
- **不应**先去读根 `TOOLS.md` 寻找 `query.py instances` 的命令模板（因为根里已经没这些了，它只能去 quant_assistant 的私有 TOOLS.md 找）
- 如果它仍能正确调用 `python3 scripts/query.py instances`，说明搬家 + 新路由层工作正常

**烟测 B（污染是否清除）**
> 在飞书发："最近 BTC 这波结构怎么看？"

观察点：
- 根 TOOLS.md 被清空后，这类闲聊应**不再触发** quant_assistant 的 `strategy_builder.py`
- 期望行为：澄清意图或纯自然语言回答，而不是强行把闲聊塞进策略构建脚本

两个烟测都过，P0 视为完成，我再出 P1（IDENTITY.md + AGENTS.md）。

## 需要你现在回我的两件事

1. `ls -la ~/.openclaw/workspace/skills/quant_assistant/TOOLS.md` 的输出——决定搬家方式（mv 还是 merge）
2. 你是否同意在 P0 完成、烟测 A/B 通过后再启动 P1；中间如果烟测失败，我们先排查而不是继续推进

等你回复这两点。
