## turn001
用户：
好的，在应用这套上下文机制前，我希望最后确定一下，请你阅读完整个附件(projects\memory_governance\raw\raw_2026-06-12_compression.md)的内容，再根据570-593行关于记忆治理方案收尾总结与问题澄清部分进行确认，给出执行这套机制的工作流，我会按照这个执行
Claude-Opus-4.8:
*Thinking...*

>  I need to pull together the full attachment and review the memory management solution summary section to understand what they're asking for, then create a concrete, executable workflow they can actually follow through. Continuing to map out the workflow—the fold process takes four inputs and produces two outputs: the full memory_pack rewrite (with a line count verification to ensure nothing's lost except deprecated items) and skill card fragments to append. The system enforces three core rules: single source of truth across files, stock preservation with line counting, and raw files never get renamed. For the cold start scenario, I save the initial attachment as raw, run one fold to establish the baseline memory_pack and first skill batch, then shift to standard cadence where every three rounds triggers a fold, feeding the LLM the maintenance prompt, compressed round content, full memory_pack, and skills file.

读完了整份附件。按 570–593 行那节(收尾总结与三个澄清)做最终确认,核心三点先钉死:

**确认一(raw 存什么)**:raw 存**原始对话原文**,按主题线一个文件,内部 `## turnNNN` 分节,是证据库不是压缩稿。数据流里 raw 那一步是 `archive` 不是 `fold`。

**确认二(要不要先一次压缩)**:要,但它是**临时桥稿、不落盘、喂完即丢**。3 轮很短时可跳过桥稿、直接喂 raw 原文。

**确认三(你手上这份附件怎么入场)**:走一次性**首场折叠冷启动**,不按 3 轮节奏回放历史。

下面是你照着执行的工作流,分成"首场冷启动"(只做一次)和"标准循环"(往后每次)。

---

## 第一部分:首场折叠(冷启动,仅一次)

你现在手上这份附件就是存量,用它建立 taskgraph 记忆包的第一版基线。

**步骤 1 · 落 raw**
把这份附件存为 `projects/taskgraph/raw/raw_2026-06-12_compression.md`,文件顶部加一行标注:`本文件为一次压缩稿,原始对话未留存`。这是既成事实,铁律只保护此后的新增内容。

**步骤 2 · 备齐 4 份输入,喂折叠 LLM**
- `_templates/maintenance_prompt.md`(指令本体)
- **新料** = 整份附件(它本身已是覆盖全部历史轮次的压缩稿,无需再做桥稿)
- `memory_pack.md` = 空壳(首场不存在,让模型按 prompt 里"四节"定义从零生成)
- `skills.md` = 空(或仅含表头)

**步骤 3 · 接收双产物**
- **产物 A** = memory_pack 全文(四节:概览 / 长期记忆 / 脊柱 / 开放问题)。这是你的**行数基线**。
- **产物 B** = 第一批技能卡草稿。从这份附件里大概率能晶化出:可重入压缩、存量逐字保留+行数核对、单一事实源、全局资产只追加、折叠作为河口的输运机制等方法论级技能。

**步骤 4 · 人工入库**
memory_pack 直接落盘(首场无旧版可比,跳过行数核对);技能卡逐张审核后 append 进 `skills.md`,每张必须带 `source: taskgraph`;在 `skills.md` 末尾判定日志写一行(如 `2026-06-12:首场冷启动晶化 N 张方法论卡`)。

冷启动到此结束。

---

## 第二部分:标准循环(往后每次对话)

**随手动作(每轮结束)**
把本轮原始对话 append 进当前主题线的 `raw_<起始日>_<主题>.md`,用 `## turnNNN` 分节。这是独立动作,不叫入库。

**触发(攒满 3 轮)**
注意:这里的"3 轮"是**折叠节奏**不是保留窗口——满 3 轮触发一次折叠,记忆包只存状态和脊柱,细节全在 raw,没有近况区。

**折叠动作(满 3 轮时)**
1. 取这 3 轮 raw 原文,做一次标准轮次压缩(保留逻辑链、去对话体、加标题),产出**桥稿**(临时,不落盘)。3 轮很短可跳过、直接喂 raw 原文。
2. 备齐 4 份输入:`maintenance_prompt.md` + 桥稿(新料) + `memory_pack.md`全文(存量) + `skills.md`全文(参照)。
3. 接产物 A(记忆包全文)和产物 B(新技能卡或"本轮无新增")。
4. **人工核对**:数产物 A 的「长期记忆」节和「脊柱」节行数,新 ≥ 旧(`[DEPRECATED]` 例外),通过则整体替换 memory_pack;技能卡审核后 append 进 skills(带 source);判定日志写一行;桥稿丢弃。

**开新会话时的喂法**
`memory_pack.md` + 上次折叠后尚未折叠的 raw 段落(最多 2 轮)。记忆包保持有界,不与 raw 重复。

**给日常对话 LLM 的投影(可选轻加工)**
若把记忆包喂给一般对话(非折叠),用去锚点投影:概览 + 长期记忆 + 开放问题原样 + 脊柱(仅脉络句、剥掉 `raw/...#turn` 锚点)。只读、不回写。token 宽松时也可整份直喂。

---

## 一页速记(贴你桌面)

> **每轮**:原对话 → append 进 raw(`## turnNNN`)
> **满 3 轮**:raw → 桥稿(临时)→ 喂〔prompt + 桥稿 + memory_pack + skills〕→ 产物A(记忆包全文,核行数后整体换)+ 产物B(技能卡,审核后 append)→ 丢桥稿
> **开新会话**:memory_pack + 未折叠的尾部 raw(≤2 轮)
> **铁律**:① 规则数字只住 prompt ② 长期记忆/脊柱行数新≥旧 ③ raw 永不改名

---

有一处要提醒你:整套流程里**只有折叠 LLM 看 maintenance_prompt 和全四节,README 永远不喂给任何模型**。你执行时别把 README 当输入塞进去,它纯粹是给你自己看的运维手册。

按这个执行即可。建议你**先把第一部分首场折叠跑完**,因为它会生成你的第一版 memory_pack 和行数基线——没有基线,后面铁律2的"新≥旧"核对就无从比起。跑完首场后,如果产出的记忆包四节结构或技能卡字段你觉得需要微调,现在正是定型的最后窗口。
