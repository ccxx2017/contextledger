# memory_governance

跨项目记忆治理仓库。全局资产（skills、templates）住根目录，项目资产住 `projects/<project>/`。

## 一、数据流

每场对话结束后，按以下单向流动维护，不跨步、不回灌：

original dialog
  └─(archive)→ raw（按主题线归档，内部分 ## turnNNN）
        └─(crystallize)→ memory_pack（项目内）/ skills（方法论级，全局）

- **raw** 是唯一的原始沉淀层，逐轮追加，只增不改。
- **memory_pack** 是项目的可工作记忆，含四节（见 `_templates/memory_pack_template.md`）。
- **skills** 是全局唯一、跨项目复用的方法论卡片集合。
- 折叠节奏（每 N 轮触发一次）以 `_templates/maintenance_prompt.md` 为准，本文件不复制该数字。

### 一次折叠喂给模型的 4 份输入

数据流是面向人的概念流向；真正每次折叠喂给模型的是以下 4 份，缺一不可：

1. `_templates/maintenance_prompt.md` —— 指令本体，模型靠它知道本场怎么做。
2. 本轮 raw 段落的一次压缩桥稿(临时产物,不落盘);轮次较短时可直接喂 raw 原文。
3. `memory_pack.md` —— 待更新的项目存量全文（首场为空壳模板）。
4. `skills.md` —— 待参照的全局技能库全文，供判断是否晶化新卡并避免重复造卡。

四种角色：规则(1) 指挥模型，把新料(2) 折进存量(3)，同时参照全局(4) 决定是否产出技能卡。
注意 `_templates/` 下的文件中，只有 maintenance_prompt 会被喂给模型；memory_pack_template 仅在首场顶替空 memory_pack，README 本身不喂给模型。

## 二、三条铁律

**铁律1 · 单一事实源。** 每份内容只有一个家。规则与数字只住 `_templates/maintenance_prompt.md`；备忘、数据流、锚点格式只住本 README；skills 顶部、memory_pack 顶部一律不贴任何备忘。要用就去原处复制，禁止二次落地。

**铁律2 · 存量逐字保留 + 行数核对。** 折叠产出 memory_pack 全文时，未涉及的节和条目必须逐字保留、不得改写。人工核对只做一个机械动作：数「长期记忆」节与「脊柱」节的行数，新行数必须 ≥ 旧行数；唯一例外是有条目被显式标 `[DEPRECATED]`。行数对不上即判定为静默丢失，打回重做。

**铁律3 · raw 文件名永不改名。** 文件名中的日期定义为**主题线起始日**，文件建立后永不修改，哪怕讨论跨数周。脊柱锚点的地基就是这个文件名，改名会让所有挂靠锚点静默断链。

## 三、锚点格式

脊柱节中引用 raw 的统一写法：

    raw/raw_<起始日YYYY-MM-DD>_<topic-slug>.md#turn<NNN>

示例：`raw/raw_2026-06-12_compression.md#turn003`

路径相对于所在项目文件夹根，topic-slug 用小写英文加下划线，三位轮次号补零。