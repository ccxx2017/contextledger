# Monorepo 工程化与目录契约
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

## contextledger 目录结构反馈与修正

**整体评价**：结构骨架对路，raw嵌套已解、normalized按需生成、contracts五份到位。但存在**一个会埋雷的定位错误**和两个待补的洞。

---

### 主要问题

#### 1. `normalized/projects/abu_modern/raw_2026-06-12_compression.md` 放错层（最急）

该文件同时踩三条线：  
- 它是“首场折叠冷启动”的一次压缩稿，177KB 远大于 `raw/projects/abu_modern/` 六个 turn 的总和，**不可能从这些 turn 降噪而来**。  
- normalized 契约要求 `f(raw)` 且可删除重生成，但此文件**没有 raw 源，无法再生**，属于不可再生的来源记录。  
- 放在“可安全删除的派生层”是危险的——一旦有人清空 normalized 重跑，该文件永久丢失。

**修正**：移回 `raw/projects/abu_modern/`（或对应的正确项目），文件头加一行“本文件为一次压缩稿，原稿未存，按 source-of-record 对待”，名称去掉 `compression` 歧义。  
**前置确认**：该文件主题是否确实属于 abu_modern？若属于 taskgraph，则归属需调整。

#### 2. `pack/` 缺少 `projects/`，memory_pack 无家可归

`pack/` 目前只有全局资产（`_templates`、`skills.md`、`README`、`MAINTENANCE_LOOP`），缺 `pack/projects/X/`。按目标态，每个项目的 `memory_pack.md` 应落在 `pack/projects/X/memory_pack.md`。不用预建空壳，但第一次折叠时落点必须是 `pack/projects/X/`，不可混入 raw 或 normalized。

#### 3. `contracts/05_nomalized.md` 几乎空壳且文件名拼错

文件仅 99 字节，装不下三条核心契约（`normalized=f(raw)`、不得注入判断、必须带可重放 manifest 及 span 翻译回 raw 偏移）。  
**修正**：改名为 `05_normalized.md`，补写完整契约；同时确认 `01_raw_anchors.md` 是否已含“经 normalized 抽取时 span 必须翻译回 raw 偏移”条款，缺则补上。

---

### 补充说明

- **`raw/projects/taskgraph` 和 `memory_governance` 不必删**：它们存放设计两个系统时的原始对话日志，是合法 raw 证据。之前“删自指条目”针对的是 `pack/projects/` 下的模块自指，raw 层不受影响。
- **`temp/`**：确认已在 `.gitignore` 中且无正式产物滞留。若有未归位的真源，需拎出。

---

### 动作清单（确认归属后执行）

1. 核对 177KB 文件的主题归属 → 移入 `raw/projects/<正确项目>/`，加头部定性声明，从 normalized 删除。
2. 补写 `05_normalized.md`（改名+补全三条契约+span 翻译条款）。
3. 核验 `01_raw_anchors.md` 是否包含 span 翻译回 raw 偏移的条款，缺则补。
4. 记录 memory_pack 落点规则：`pack/projects/X/memory_pack.md`，待第一次折叠时按需创建。
5. 确认 `temp/` 已 gitignore 且无真源滞留。

## 契约检查与设计对话归档建议

**用户问题**：将contracts所有文件附上，并询问`temp/`中存放的本项目设计对话是否应移至根目录下新建有意义名称的文件夹。

**Claude-Opus-4.8 核心建议：不要新建根目录，而是将它变为一个“被服务的项目”**

设计这套系统的对话本身，正是一段长程、有状态、约束不断演化的对话。它不应逃逸在raw/normalized/graph/pack纪律之外，而应是**第一个dogfood项目**：

```
raw/projects/contextledger/<session>/turn_NNN.md
```

与abu_modern、minecraft_agent完全平级，走相同管线。好处有三：
1. **不破契约**：新开`temp/`或`design_notes/`等于在四层之外再造一个“家”，违反“每份内容只有一个家”的铁律。
2. **自举验证**：这些设计对话中充满真实冲突（compact改名、raw嵌套、177KB归属），是验证`invalidates`语义最理想的零成本测试集。
3. **呼应设计基调**：手动期的产物将来是交给数字员工的SOP，让系统管理自己的诞生史，正是理念最干净的落地。

**建议动作**：把`temp/`中的内容归入`raw/projects/contextledger/`，原来`raw/projects/taskgraph`和`memory_governance`作为前身对话保留，不删。

---

**契约文件检查结果**

| 文件 | 状态 |
|---|---|
| `01_raw_anchors.md` | ✅ span翻译回raw偏移已补上 |
| `02_ownership.md` | ✅ 扎实完整 |
| `03_graph_schema.md` | ⚠️ PROVISIONAL，占位合理 |
| `04_assembly.md` | ⚠️ PLACEHOLDER，占位合理 |
| `05_nomalized.md` | ❌ 几乎空白（仅99字节），且文件名拼错 |

**必须修正的契约问题**：
1. `contracts/README.md` 表格漏列05，需补上一行。
2. 文件名 `05_nomalized.md` 拼错 → 改为 `05_normalized.md`。
3. `01_raw_anchors.md` 末尾“经 **nomalized** 抽取”同样拼错。
4. `05` 内容需补全为完整的normalized派生契约（定义、三条铁律、manifest存放规则）。

**一句话**：设计对话别开新根目录，归入 `raw/projects/contextledger/` 作dogfood项目，同时修掉README漏列05、两处 `nomalized` 拼错、05契约几乎空白这三个洞。
## graph 文件夹结构修正

用户纠正：graph 不是跨项目的全局图，而是每个项目各自独立的图，项目之间不会交叉。因此 graph 里确实需要 `projects/`，但需区分哪些归项目、哪些留根共享。

**分界原则**：是否绑定某一张具体图。

- **进 `graph/projects/<project>/`（每项目一份）**：`graph_state.json`（图真源）、`graph_slices/`、`reports/`、`quarantine/`、`patches/`、`run/`（若记录运行态）
- **留根下（全局共享，与具体图无关）**：`scripts/`、`tests/`、`prompts/`（模板）、`graph_state.seed.json`（新图初始化模子）、`env`、`.gitignore`、`README.md`

**预期布局**：
```
graph/
  scripts/  tests/  prompts/          # 全局机件
  graph_state.seed.json               # 新图模子
  README.md  .gitignore  env
  projects/
    abu_modern/
      graph_state.json                # 该图真源
      graph_slices/ reports/ quarantine/ patches/
    open_skywing_lab/
      graph_state.json
      ...
```

**纪律**：按需生成，不预建空壳（与 normalized 一致）。根下旧的 `graph_state.json` 需归位到对应项目，勿留作“假全局图”。`raw_id = <project>/<session>/<turn>` 前缀保留，作用改为**溯源锚点**（指向 raw 源），而非图内分区。