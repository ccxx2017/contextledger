# ContextLedger 设计白皮书 (v2.0)

## 长程 Agent 任务的领域状态层与记忆基础设施

---

## 一、问题域、设计哲学与系统边界

### 1.1 核心矛盾

在 LLM 长程项目协作中，上下文窗口是有限资源，而任务知识持续膨胀。这一矛盾催生了两个同等致命的问题：

*   **信息过载**：上下文无限增长导致关键约束被稀释，模型在噪声中丢失焦点。
*   **事实失效不可追踪**：旧方案被新事实推翻后，若缺乏显式失效机制，过期约束将持续污染上下文，导致模型基于已不成立的前提做出错误推理。

传统的梯度压缩将这两个问题混为一谈，用“变短”代替“变准”，导致承重墙与脚手架被一视同仁地稀释，知识复利流失，且总量始终不收敛。

### 1.2 设计哲学：三个范式转移

| 旧范式 | 新范式 | 核心变化 |
| :--- | :--- | :--- |
| 按时间位置降采样 | **按闭环度与承重度分流** | 分辨率跟随价值，而非新近度 |
| 单一摘要流 | **硬状态与软知识双轨治理** | 结构化事实失效 + 叙事性经验沉淀 |
| 拼接式上下文注入 | **带预算的选择性装配** | 检索与正确性解耦，冲突通过切分消除 |

### 1.3 核心定位

ContextLedger 不是通用聊天记忆压缩器。它是面向**长程、有状态、约束会演化的 Agentic 任务**的**领域状态层 / Agent Memory Backbone**。

> **一句话定位**：让 Agent 在运行数月之后，依然精确知道什么已经不成立了。

### 1.4 系统级认识论边界（重要声明）

**ContextLedger 是一致性引擎，非真值引擎。**

系统的机械核（reconcile/apply/lint）能保证图内部不自相矛盾，但**无法保证图反映现实**。Extractor 可能抽错、`entity_ref` 可能配错、用户可能断言假前提。这一边界是领域无关的——在量化交易首战场景中，一个被错误 supersede 的因子决策掉的同样是真金白银。

明确此边界，不仅是为了诚实，更是为了保护产品定位：我们不承诺“绝对正确”，我们承诺“演化可追溯、失效可机械裁决”。

---
### 1.5 执行模型边界：单协调者线性提交假设（Phase 1）

ContextLedger 的写入管线（Extractor → Patch → reconcile → apply → lint）隐含串行假设：上一轮 apply 完成才有下一轮，"当前成立态"在提交之间无歧义。这一线性一致性在人机对话中由"轮次"免费提供，在后台自动执行 / 多 Agent 场景中则须由架构显式提供。

**Phase 1 执行模型假设**：存在单一协调者作为唯一写者，所有子 Agent 的动作与返回均经其观测序线性化后写入 ledger，TaskGraph 仅按该观测序更新。据此，状态写入的并发一致性得以解决，**不需要向量钟或分布式共识**。子 Agent 内部可物理并发，但在协调者的观测面前坍缩为一条有序序列。

**轮次的泛化**：一个 ledger step = 协调者每观测到一个事件（发出调度 / 收到返回 / 超时 / 取消 / 改派），而非"调度 + 完成"绑定为一对——二者在观测序中通常不相邻。

**仍未关闭的洞（重要）**：单写者只保证"谁来写"（一致性），不保证"事实何时成立"（valid-time）。并行派工会令协调者的**观测序**与事实的 **valid-time 序**脱钩：Agent A 于 10:00 查得 stock=0、10:05 返回，Agent B 于 10:03 查得 stock=10、10:04 返回，按"后观测覆盖先观测"将误判 stock=0——一致性未破，但信念错了。此非并发写之过，而是协调者并行读所致。

**Phase 1 最小修补**：子 Agent 返回结果应携带 `observed_at`；reconciler 在该字段存在时按 valid-time 裁决 `invalidates`，缺失时退回到达序。一个字段、一条规则即可挡住上述反例。完整 bitemporal 信念回补（迟到观测的历史回填）仍列为后续扩展，见 §3.1 预留字段位。

> 一句话边界：Phase 1 依赖单写者线性提交序解决并发一致性；但并行派工下观测序 ≠ valid-time 序，reconciler 在同一 `entity_ref`、同一状态维度内，以 `observed_at` 作为新鲜度裁决键：只有 `observed_at` 更新的观测才可推翻较旧 active state；迟到但 `observed_at` 更旧的观测只能作为历史证据记录，不得反向推翻较新的当前态。缺失 `observed_at` 时，才退回协调者到达序。
## 二、系统总体架构

### 2.1 四层不变量

系统的全部数据治理收敛于四个不变量。它们不是按“内容类型”切分，而是按**更新规则**切分——文件边界的唯一正当职责是分隔更新规律不同的内容。

| 不变量 | 更新规则 | 定位 | 回答的问题 |
| :--- | :--- | :--- | :--- |
| **`raw`** | 写一次，永不修改 | 唯一原始证据真源（source-of-record for observations） | "说过什么、原文是什么" |
| **`TaskGraph`** | 每轮追加 Patch，机械合并 | 当前裁定信念态（current adjudicated belief state） | "当前什么成立、什么被推翻" |
| **`MemoryPack`** | 周期性追加，不回改旧行 | 软知识容器 + 派生叙事视图 | "关于 X 积累了什么方法论与偏好" |
| **`Assembler` 输出** | 每轮临时生成，不落盘 | 查询时预算编译产物 | "本轮 LLM 需要看到什么" |

### 2.2 正文归属判据：死于离散事件 vs 渐进褪色

**铁律：同一条知识的正文只能在一处持有。**

早期归属口诀“凡能想象其有朝一日被推翻的，归 TaskGraph”存在致命缺陷：几乎所有有用的东西都能被想象推翻（方法论会过时、偏好会变），这会将 Pack 吸空。

**正确的归属判据应为：失效是“死于离散事件”还是“渐进褪色”？**

| 失效模式 | 特征 | 归属 | 处理机制 |
| :--- | :--- | :--- | :--- |
| **死于离散事件** | 失效存在一个可被指认、可挂 `invalidates` 边的时刻（如：决策被新决策 supersede，工单状态变更）。必须有明确 `entity_ref`，需要 `invalidates` 链，影响当前任务合法状态。 | **TaskGraph** | 机械失效，旧节点标记 `superseded` |
| **渐进褪色** | 失效没有那个“事件时刻”（如：方法论逐渐不再适用，用户口味变化，经验自然老化）。 | **MemoryPack** | 靠“不再相关”从 Assembler 检索中自然掉出 |

**抽取期即分对**：纪律/约束在 Extractor 抽取时直接生为 Graph 节点，经验/偏好直接生为 Pack 条目。**中间无“提升/迁移”通道**，杜绝双源漂移窗口。
* 误分类的修复通道（不破坏单一正文原则）：判据指向"它将来如何失效"，而这是未来属性，抽取期无法完全判断。一条被归为"渐进褪色"的方法论，可能在数十轮后被明确决策离散推翻；一条记入 Graph 的约束也可能从未发生"事件时刻"，只是慢慢无人提及却永久占用 must_include 预算。

* 为此引入适用性裁定事件：不迁移正文（Pack 条目仍留 Pack，Graph 不复制其正文），但允许 Graph 追加一个事件节点，声明"某 Pack 条目在某 scope 下被某决策禁用/降权/不再适用"。这既保持正文单一归属，又为抽取期误判留下机械可挂的修复路径。该事件经 dependency_refs 反向联动，使被裁定的软卡进入暂停/降权态。

### 2.3 物理目录结构

```text
contextledger/
├── raw/                  # SSOT：原始对话/资料，Append-only
├── normalized/           # 纯函数派生层 f(raw)，可安全删除重生成
├── graph/                # 事实与状态层（TaskGraph）
│   ├── scripts/          # reconcile, apply, lint, entity_resolver
│   └── projects/         # graph_state.json, patches/, slices/, pending_merge/
├── pack/                 # 叙事与软料层（MemoryPack）
│   ├── _templates/       # 折叠规则
│   └── projects/         # 每项目 memory_pack.md
├── assembler/            # 查询时装配（只读组件）
└── contracts/            # 跨模块契约（唯一真源）
```

---

## 三、TaskGraph：硬状态权威层

### 3.1 核心数据模型

TaskGraph 将任务上下文抽象为带状态的结构化图，核心机制是 **`entity_ref` + `invalidates`**，实现机械化的事实失效判定。

术语对齐（重要）：
- 规范层所说的“当前裁定态 / current adjudicated belief state”，在节点字段上由 `status` 承担。
- `status ∈ {active, superseded}`：决定节点是否仍属于当前态集合。
- `state ∈ {open, blocked, implemented, deployed, resolved, ...}`：描述实体在现实世界中的领域生命周期，不决定节点是否仍为当前成立态。
- 因此，文档中若出现“当前状态 / 当前什么成立”的表述，除非特别声明为领域状态枚举，否则均指 `status` 维度而非 `state` 字段。

*   **节点（Node）**：包含 `node_id`, `type`, `content`, `entity_ref`（稳定实体标识）, `state`（状态枚举）, `status`（`active`/`superseded`）。
*   **边（Edge）**：合法关系包括 `refines` | `depends_on` | `supports` | **`invalidates`** | `implements` 等。
*   **Patch**：每轮对话抽取的不可变事件日志，包含 `new_nodes`, `updated_nodes`, `superseded_nodes`, `new_edges`。
* 失效形态边界声明（重要）：当前裁定态由 `status=active/superseded` 二值承载，`invalidates` 为整体替换。这只能表达线性覆盖式演化（新决策整体取代旧决策）。以下形态 Phase 1 不支持，列为已知未覆盖边界：

形态|含义|当前状态
partial invalidation	|只推翻旧节点的部分子句	|未支持，schema 预留
conditional invalidation | 仅在某配置/时间窗/市场下失效 | 未支持，schema 预留
revival / rollback	| 被否方案后续重新启用，active set 非单调	| 未支持，schema 预留
bitemporal	| 区分 valid-time（事实何时成立）与 transaction-time（系统何时知道）	| 未支持，schema 预留
* 预留字段位：节点 schema 即刻加入 invalidation_type（枚举：full / partial / conditional / revival，Phase 1 仅允许 full）与 valid_time / tx_time 占位字段（Phase 1 不参与裁决）。预留字段位的目的是：当基准证明需要这些形态时，扩展不必重构已落盘数据。
* observed_at 与 valid_time 的关系：`observed_at` 是 Phase 1 的轻量新鲜度键，仅用于同一 `entity_ref`、同一状态维度下的当前态裁决排序；它不提供完整 bitemporal 历史回填能力。Phase 1 中 `valid_time` / `tx_time` 仍为预留字段，不作为完整双时间轴模型启用。reconciler 只保证：较新的 `observed_at` 可推翻较旧状态；迟到但更旧的观测不得反杀较新的 active state；缺失 `observed_at` 时退回协调者到达序。

### 3.2 写入管线：LLM 提议，机械层裁决

TaskGraph 的正确性建立在**三层防护**之上。LLM 仅负责“提议”（生成 Patch），确定性代码负责“裁决”。

```text
[用户对话] + [graph_state.json]
   │
   ▼
[Graph Slice Builder]     ← O(1) 切片，只省 Token 不保正确性
   │
   ▼
[Extractor Prompt]         ← System Rules(可缓存) + Slice + Turn Text
   │
   ▼
[LLM Extractor]           ← 生成 patch.json（不可变事件日志）
   │
   ▼
[Entity Resolver]         ← 【新增】实体归一化，维护 canonical id 与别名
   │                         核心纪律：合并保守（拿不准则不合并）
   ▼
[reconcile_patch.py]      ← 前置校验：entity_ref 强判定 + 文本弱兜底
   │                         失败 → 结构化 Error 回填重试(上限3次)
   │                         仍失败 → 隔离至 quarantine/
   ▼
[apply_patch.py]          ← 纯机械合并
   │
   ▼
[graph_lint.py]           ← 后置质检：全图不变量校验
   │
   ▼
[graph_state.json]        ← 编译态（禁止手改）
```

### 3.3 核心新增：Entity Resolution 层

全部机械裁决依赖 `entity_ref` 精确匹配，但 Extractor 跨轮命名不一致会直接拖垮 `invalidates` 机制。这是当前最大的工程缺口。

*   **职责**：维护 canonical id、别名注册表、合并/分裂记录及跨轮一致性检查。Resolver 每次裁决须输出：match_confidence、merge_reason、non_merge_reason、candidate_aliases。否则 merge-review 沦为事后人肉猜谜，且基准无法定位漏/错合并的归因。
*   **核心纪律：合并保守**。
    *   **漏匹配**（同一实体被叫成不同名）：本应触发的 invalidates 边永不触发，旧约束永久静默存活，成为藏在实体分裂里的僵尸（与"废案不死"同构，lint 同样无感）。其代价不是"多活几轮"，而是"无人召回则永不失效"——故必须配 merge-review 回路兜底。
    *   **错合并**（将两个不同实体错合并）：代价是给无关实体间凭空造出 `invalidates` 边，使仍成立的决策被错误 supersede，且图内完全自洽、lint 无法捕获。
    *   **结论**：默认策略（待基准校准，非公理）：拿不准则不合并。但须承认：漏匹配直接导致失效漏召（背叛"杀死活废案"的核心使命），错合并导致误杀有效决策（伤精确率），两者均为静默僵尸。"保守是否真优于激进"取决于两类错误的真实基率与 merge-review 实效，由 §9.3 Phase 0.5 失效回放基准（含 alias 陷阱、non-invalidation 诱饵）裁定，在跑过基准前不得作为公理。
    Merge-Review 回路（兜底机制）：resolver 对"疑似同一但未敢合并"的实体对落入 pending_merge/ 待审表，由后续轮次的新证据或周期性复核裁决归并。无此回路，"合并保守"只是把"错合并的显性污染"换成"漏合并的隐性僵尸"，净收益存疑。

### 3.4 失败隔离（Quarantine）

> **宁可漏记一轮，绝不污染主图。**

Reconcile/Lint 失败时，将结构化 Error 回填 Prompt 重试。超限仍失败，则拒绝合并，将 Patch 隔离至 `quarantine/` 目录。
quarantine patch 只有在修正后重新通过 reconcile/apply/lint，才能并入主图；不得人工直接改 graph_state 绕过。

---

## 四、MemoryPack：软知识沉淀层

### 4.1 核心定位

MemoryPack 是**软料提取器**。周期性从 raw + TaskGraph 快照中捞出图无法建模的软知识（方法论、偏好、技能、反模式、经验教训）。

*   **不持有 live state**：当前状态的权威源是 TaskGraph。
*   **不承担渲染职责**：喂给 LLM 的上下文由 Assembler 在 query-time 现编译。
*   **不独立判定事实失效**：仅渲染图增量为可读叙事，存放图装不进的软料。

### 4.2 数据结构与更新纪律

MemoryPack 采用 **Append-only + 追加式取代** 的更新纪律。

*   **条目形态**：包含 ID、content（长度不限）、scope、evidence_refs、scope_refs、dependency_refs、raw_refs、retrieval_affordance（可检索性元数据）、supersedes（轻指针）。引用字段语义统一见 §4.3 表，全文档以此四元组为准。
*   **更新铁律**：只追加，永不回改旧行。物理文件保持 Append-only（审计层），注入 LLM 上下文时（读面）过滤 `superseded` 条目。

### 4.3 与 TaskGraph 的引用接口与失效联动

软知识失效不再是系统漏洞，而是通过引用接口被自然解决：

| 引用类型 | 含义 | 被失效后的响应 |
| :--- | :--- | :--- |
| `evidence_refs` | 软卡从哪些图状态/事件中归纳而来 | 不一定废卡，标记“证据过期/需复核” |
| `scope_refs` | 软卡适用于哪些项目/任务/主题范围 | 降低召回优先级或限制适用范围 |
| `dependency_refs` | 软卡成立是否依赖某些当前状态 | **卡片暂停/降权**（依赖节点被 supersede，软卡自动失效） |
| `raw_refs` | 软卡与原始证据的关联 | 一般不发生失效（raw 为 SSOT） |

**结论**：依赖图事件的软知识失效，由 `dependency_refs` 联动解决；渐进褪色的软知识，靠 Assembler 检索时的相关性衰减自然掉出。**无需“软节点提升”概念，无需修改 Graph schema。**
可靠性标注：dependency_refs 由折叠期 LLM 判断附加，其准确率与 §4.4 Pack Lint 同属概率性而非机械性。漏附一个 ref，对应软卡在其依赖被 supersede 时不会自动暂停，变成静默陈旧软事实（与漏匹配同构）。本机制并非闭式解，可靠性受限于折叠膜（见 §8.2）。

### 4.4 Pack Lint：事实泄漏检测

*   **职责**：检测 Pack 条目中是否夹带了当前状态/决策/约束（硬事实）。
*   **性质**：判断“一句话是否为当前事实”属模糊的 LLM 判断，无法如 `graph_lint` 般机械裁决。因此 Pack Lint 仅作**启发式警告**，非硬门禁。
*   **处理**：若发现泄漏，要求拆分——硬事实归 Graph，软解释归 Pack，连接用 `graph_ref`。

---

## 五、Assembler：查询时装配层

### 5.1 核心定位
* 成熟度声明：本章详尽程度高于其依赖契约的成熟度（03_graph_schema 为 PROVISIONAL，04_assembly 为 PLACEHOLDER，Assembler 本体排于 Phase 3）。本章描述为目标形态而非已冻结契约；在 graph schema 经 Phase 0.5 基准稳定前，本章细节有返工风险，不应被其详尽度误读为高确定性。
* Assembler 是将 TaskGraph 与 MemoryPack 转化为**主 LLM 可直接使用的上下文包**的只读组件。它在 query-time 运行，**是唯一向 LLM 渲染事实的执行者**。

### 5.2 四层分层装配

| 层级 | 来源 | 触发方式 | 新鲜度 | 内容 |
| :--- | :--- | :--- | :--- | :--- |
| **L1 常驻基线** | Pack 概览 + Graph 核心约束 | 每轮 push | 高 | 硬约束、核心偏好、当前焦点 |
| **L2 任务状态** | TaskGraph 当前态 | query 驱动，图遍历 | 最高（每轮） | 相关子图节点 + 失效裁定后的当前状态 |
| **L3 软知识** | MemoryPack | 相关性检索 | 中（≤2轮滞后） | skills、方法论、反模式、偏好 |
| **L4 深检索** | Wiki / RAG | 仅前三层不足时触发 | 最静态 | 跨项目知识、历史深度论述 |

### 5.3 不可静默丢弃硬约束机制（核心新增）

**问题**：切片硬上限和装配预算解决的是“喂给 LLM 的那一口”，但 `standing_constraints` + `open_tasks` 在真正长程中仍可无界增长。一旦超装配预算，选择又变有损，落入“出口膜”风险。

**收敛问题定义**：装配器能否从无界 active 集中可靠选出有界且不漏关键约束的子集。

**机制**：
1.  **优先级分层**：Graph 节点标注装配优先级（`must_include` / `should_include` / `optional` / `background`）。
2.  **不可静默丢弃**：预算不够时，优先机械压缩表达、降软料预算、发警告或拒绝装配，**绝不可静默丢弃 `must_include` 约束**。
3. 上界锚定：仅 active 节点可进 must_include，被 supersede 即自动退出。此约束将 must_include 的规模锚定在"同时成立的关键约束数"，挂靠失效体系，而非无限累积。
4.  **核心评测**：头条评测项永远是**关键 active 约束的召回率**是否接近 100%，优先级分层仅为手段而非结论。
5. 诚实边界：当同时成立的 must_include 约束累积到超过装配预算时，"绝不可静默丢弃"+"必要时拒绝装配"合起来意味着——存在一个项目复杂度上限，越过它系统只能停摆或要求人类重新缩小任务范围。这不是缺陷，是诚实的边界。must_include 收敛的是"有损取舍"，不消灭复杂度本身。
### 5.3.1 两套分层的交互裁定
§5.2 的 L1–L4 按来源与新鲜度分层，§5.3 的 must/should/optional/background 按装配优先级分层，二者正交，须显式裁定其交叉单元，否则 Assembler 实现产生歧义。

裁定规则：

1. "每轮必进"（L1 语义）与 must_include（不可静默丢弃）是两个独立保证，不可互相推导。
2. Graph 来源的 active 关键约束：可进 must_include（受 §5.3 第 3 点上界锚定约束）。
3. Pack 来源的"核心偏好"：归入 L1 常驻基线，享有"每轮 push"，但不享有 must_include 的拒绝装配级保护——预算极端紧张时，Pack 核心偏好先于 Graph must_include 被压缩。
4. 即：must_include ⊆ Graph active 节点；L1 ⊇ must_include ∪ Pack 核心偏好。L1 是"默认每轮进"的并集，must_include 是其中"宁可拒绝装配也不丢"的硬核子集，二者非同一集合。
* 保证的成立条件（集成等级）：上述 must_include 不静默丢弃保证，仅在 ContextLedger 拥有"最终装配权"时成立——即宿主满足：(a) 所有 user / assistant / tool / agent-dispatch / return 事件均经由 `ingest` 进入本系统；(b) 每次调用下游 LLM 前必经 `assemble`，且其输出即为送入 LLM 的最终上下文；(c) 宿主原生记忆不得在 `assemble` 之后再静默注入权威状态。不满足上述条件的接入（如建议式旁路、纯拉取式 MCP）只能提供软知识供给，本系统不对其 must_include 与当前态正确性作机械保证。
### 5.4 冲突消除与产物分叉

*   **冲突消除**：通过切分消除（Graph 独占事实，Pack 独占软料），而非权威序兜底。
*   **产物分叉**：
    *   **喂下游 LLM**：Assembler 临时编译的 Context Pack，**不落盘**。
    *   **给人读/审计**：叙事快照。**降级为事后导出的 debug 视图**，不占用折叠预算，不作为核心制品。核心消费者仍是 LLM/Agent。

### 5.5 脊柱锚点的双重复用

脊柱（每阶段一行：做什么 → 为何转向 → 结果，带锚点）在折叠时为审计而建，在装配时复用为**检索索引**：

Assembler 用当前问题沿脊柱导航到对应图节点 ID 和 raw 段。引用完整性校验必须纳入 `graph_lint.py`。
阶段说明：脊柱索引依赖折叠管线产出，故为 Phase 3 增量。Phase 1 的 L2 检索走原生图遍历（沿 entity_ref 与边），不依赖脊柱，二者不构成依赖环。

---

## 六、契约体系与防漂移机制

### 6.1 核心契约（`contracts/` 目录）

| 契约 | 状态 | 内容 |
| :--- | :--- | :--- |
| `01_raw_anchors.md` | STABLE | Raw ID 格式规范；Span 必须翻译回 Raw 偏移 |
| `02_ownership.md` | STABLE | **知识正文归属权。判据：“死于离散事件 vs 渐进褪色”** |
| `03_graph_schema.md` | PROVISIONAL | 节点/边结构与失效语义定义；含 invalidation_type 与 bitemporal 字段位（Phase 1 仅启用 full 单调子集，余为预留） |
| `04_assembly.md` | PLACEHOLDER | 装配环节前置闸 |
| `05_normalized.md` | STABLE | Normalized 必须是 `f(raw)` 纯派生物 |

### 6.2 防漂移补丁汇总

| 风险 | 机制 | 作用层 |
| :--- | :--- | :--- |
| 双源事实漂移 | 单一正文原则 + “事件 vs 褪色”归属判据 + 抽取期即分对 | 跨模块 |
| 软知识失效漏判 | `dependency_refs` 联动 + 渐进褪色靠检索掉出 | Graph ↔ Pack 接口 |
| 关键约束被静默丢弃 | Assembler `must_include` 机制 + 召回率评测 | Assembler |
| 实体命名不一致 | Entity Resolver（合并保守） | Graph 写入管线 |
| Pack 夹带硬事实 | Pack Lint（启发式警告） | Pack 读面 |
| 装配优先级(criticality)无归属 | criticality 由 Extractor 抽取期标注，作为图节点属性纳入失效体系；被 supersede 即失效 | Graph schema ↔ Assembler |
| 并行派工下观测序≠valid-time序 | observed_at 作排序键 + 缺失退回到达序（Phase 1）；完整 bitemporal 列为扩展 | Graph 写入管线 |
graph_state.json 必须可由 patches/ 确定性重放生成，禁止成为新的事实源。
---

## 七、三条管线的节奏与协作

| 管线 | 频率 | 本质 | 原因 |
| :--- | :--- | :--- | :--- |
| **写入管线**（Graph） | 每轮 | 逐轮事件流，抓“刚发生了什么状态变化” | 失效是离散事件，攒轮会导致 `invalidates` 链断裂 |
| **折叠管线**（Pack） | 每 N 轮 | 周期性意义提炼，抓“这一段攒下来什么值得留” | 模式识别需足够材料，单轮看不出 |
| **装配管线**（Assembler） | 每轮按需 | Query-time 预算编译 | LLM 每轮都需要上下文，时效性要求最高 |

**交接纪律**：折叠时读图必须读 TaskGraph **快照**并尊重，绝不自己重新推断当前态。

* 澄清：每轮捕获 ≠ 每轮全量物化。"失效是离散事件、攒轮会断 invalidates 链"只证明事件须在发生时附近被捕获（每轮廉价 append 事件日志），不等于"每轮全套 reconcile/apply/全图 O(N) lint 须全量物化"。后者是一个成本/正确性赌注：赌摊销后每轮归并代价低于惰性重导出代价。

* 对多数轮次不会被以冲突方式回查的长程任务，可将昂贵归并与不变量校验惰性化或批处理（每 N 轮或 query-time 触发）。这为折叠器提供了比"捞软料"更硬的定位候选：惰性归并的批处理单元。

* 但须诚实标注权衡：惰性化引入"已 append 未归并事件"与"图态"之间的一致性窗口，而 §5 装配恰是最需要图最新之处。本白皮书 Phase 1 暂取每轮全量物化以消除该窗口；惰性化作为性能演进选项，须在基准证明每轮物化代价确为瓶颈后再启用。

---

## 八、可观测性与调试

### 8.1 Task Context Debug Report

调试对象是管线中间产物，而非模型内心推理。生成静态报告包含：Conversation 原文、Patches 序列、Graph 演化时间线、Context Pack 构建 Trace、Supersession 链条。

### 8.2 端到端可靠性模型

> 端到端可靠性 ≤ 最弱那层膜，且实际低于任何单层膜。 三层膜串联且失败近似独立时，端到端可靠性是各层之积而非取最小值：若三层各为 0.9
0.9，端到端约为 0.729，而非 0.9。最弱膜是天花板，不是实际值。因此评测须用端到端 Set-F1（Phase 0.5 基准的 checkpoint 机制）直接测量，而非分层测后取 min。

*   **入口膜（Extractor + Entity Resolver）**：`entity_ref` 跨轮稳定性、实体归一化准确率。
*   **折叠膜（Pack 上线后）**：dependency_refs / scope_refs 附加的准确率。漏附即软卡失效漏判，产生静默陈旧软事实。Pack 未上线（Phase 1）时此膜不存在。
归属误判（应入 Graph 的硬约束被错记为 Pack 软料，或反之）亦属此膜的失败形态，其兜底为上述"适用性裁定事件"回路——current merge-review 仅覆盖实体漏匹配，不覆盖归属误判，二者需分别设回路。
*   **出口膜（Assembler）**：关键 active 约束的召回率。

评测重点应从"打磨引擎"转向"管好三层膜"。三层膜共享同一失败形态——静默的僵尸：该触发的失效没触发，且图内自洽、lint 无感。系统对显性污染（错合并、静默丢约束）防护良好，对隐性遗漏的防护则依赖 merge-review 回路与折叠膜质检。

---

## 九、产品战略与演进路径

### 9.1 适用领域优先级

| 领域 | 契合度 | 切入点 |
| :--- | :--- | :--- |
| **量化交易项目开发** | 最高 | 决策频繁推翻、因子演化强。首战领域 |
| **律师业务** | 高 | 独特价值在于“可审计的决策演化轨迹” |
| **医疗诊断** | 技术最契合，产品最危险 | 留待成熟 |

### 9.2 产品形态：SDK / Agent Memory Backbone

不与智能体平台竞争“通用浅层记忆”。做“领域状态层 SDK”，服务自行搭建长程 Agent 的开发者。
据此区分三种集成等级，并明确各自可承诺的保证：

| 集成形态 | 是否持有最终装配权 | 可机械保证当前态与 must_include | 定位 |
|---|---|---|---|
| Hard integration（接管 ingest + assemble） | 是 | 是 | 主产品形态 |
| Soft integration / MCP（建议式供给） | 否 | 否（仅软知识） | 辅助接入 |
| Offline replay / audit | 不涉及在线 | 仅事后验证 | 评估与调试 |

对外集成契约因此收敛为两道钩子：`ingest(event)`（保证 raw 事件流完整线性进入，由 §1.5 的单协调者作为唯一写者提交）与 `assemble(goal) -> ContextBundle`（由本系统产出并拥有最终上下文）。ContextLedger 不是智能体，也不假设自建智能体；它假设宿主编排循环中存在一个协调者来充当其单一写者。文档中出现的参考循环仅为基准回放与接入示例的测试夹具，不属于产品本体。

### 9.3 阶段演进路线图与最小闭环

**Phase 0（当前）：手工代行与形状验证**
*   **边界**：手工产出的“喂下游上下文”必须长成 Assembler 的形状。**注意：Phase 0 验证的是“形状”，而非核心命题本身。**
*   **纪律**：不在 Pack 中手写事实正文、手判失效。

**Phase 0.5：失效回放基准（先于一切管线代码的硬门禁）**

* 产物：手工标注 15–20 条失效回放轨迹，覆盖矩阵须填满以下形态：full invalidation、partial invalidation（只推翻子句）、conditional invalidation（时间窗/配置依赖）、revival（决策回滚后重新启用）、alias 陷阱（同实体异名）、provenance 冲突、non-invalidation 诱饵（看似失效实则不失效）、乱序到达 + 迟到观测（valid-time 与 transaction-time 分离：检验观测序与事实成立序脱钩下的失效裁决是否按 observed_at 正确裁定）
* 硬指标：invalidation precision / recall、active-set Set-F1、must_include recall、entity-resolution false-merge / false-split rate、valid-time 裁决正确率（观测序与 valid-time 序冲突时，携带 observed_at 是否正确改判、缺失是否正确退回到达序）这些指标自 Phase 1 起成为所有后续阶段的合并门禁。

* 此基准一次回答三个问题：相较 Flat RAG 的必要性增益、缺陷补到何处算够（完成线）、"合并保守优于激进"是否成立（见 §3.3 经验问题）。
* 副作用即正作用：标注 partial / conditional / revival 轨迹时，会强制暴露 §3.1 二值单调 schema 无法表达这些形态——在写代码前揭示地基缺口。标注乱序 / 迟到观测轨迹会强制暴露 §1.5 的 valid≈tx 假设在并行派工下崩掉——在写任何后台适配代码前揭示该假设边界。
**Phase 1：最小闭环与单一命题验证（当前首要里程碑）**
*   **最小闭环**：`raw` → Extractor → **Entity Resolve** → patch → reconcile/apply/lint → `graph_state` → Assembler L1/L2 输出。**Pack 暂缓。**
*   **单一验证命题**：当旧约束被新约束推翻时，**supersession 链是否稳定保留，且最终上下文只暴露当前成立态、不泄露废案**。
*   **此命题跑通前，Pack 折叠、叙事快照等均属装饰。**
* 此命题的"达成/未达成"由 Phase 0.5 基准的 Set-F1 与 must_include recall 门禁裁定，不接受主观判断。
**Phase 2：Pack 接入与软知识沉淀**
*   在 Graph 机械核验证过关后，启用折叠管线。
*   验证 `dependency_refs` 联动与检索褪出机制。

**Phase 3：Assembler 完整形态与 Wiki 自然生长**
*   装配器四层完整上线，`must_include` 机制生效。
*   脊柱锚点复用为检索索引，Wiki 概念页按需派生。

---

## 附录 A：核心术语表

| 术语 | 定义 |
| :--- | :--- |
| SSOT | source-of-record，唯一原始证据真源，指 raw。记录"谁在何时说过什么/工具返回什么"，其内容本身可能错误、过期或互相矛盾 |
| belief state | TaskGraph 持有的当前裁定信念态，是对证据的一致性裁决产物，非真值 |
| **entity_ref** | 稳定实体标识，用于机械精确匹配同一实体 |
| **invalidates** | 边关系，表示源节点使目标节点不再成立 |
| **superseded** | 节点状态，表示该节点已被新信息取代 |
| **死于离散事件** | 归属判据：失效有明确时刻，可挂 `invalidates` 边，归 Graph |
| **渐进褪色** | 归属判据：失效无明确时刻，靠检索掉出，归 Pack |
| **合并保守** | Entity Resolver 纪律：拿不准则不合并，防错合并重于防漏匹配 |
| **must_include** | Assembler 优先级：绝不可静默丢弃的硬约束 |

## 附录 B：设计决策记录摘要 (v2.0 更新)

| 决策 | 结论 | 关键理由 |
| :--- | :--- | :--- |
| 归属口诀 | **改为“死于离散事件 vs 渐进褪色”** | 旧口诀“能否被推翻”会将 Pack 吸空 |
| 软节点提升 | **彻底删除** | 抽取期即分对，中间无迁移通道，杜绝双源漂移窗口 |
| Entity Resolution | **新增，且必须“合并保守”** | 默认保守，阈值由基准校准 |
| Assembler 丢弃约束 | **设 must_include，不可静默丢弃** | 解决 active 集无界增长下的收敛问题，保召回率 |
| 叙事快照 | **降级为 debug 视图** | 核心消费者是 LLM，不占用折叠预算 |
| 认识论边界 | **上升为系统级声明** | 一致性引擎，非真值引擎，领域无关 |
| Phase 0 验证目标 | **验证“形状”，非核心命题** | 避免“命题已被验证”的错觉 |
| 合并保守的兜底 | 新增 merge-review 回路 | 漏匹配会产生"永久静默存活"的僵尸，需周期复核归并 |
| dependency_refs 联动 | 标注为概率性，非闭式解 | 折叠膜与 Pack Lint 同属 LLM 判断，受 §8.2 折叠膜约束 |
| 可靠性模型膜数 | 由两层改为三层（入口/折叠/出口） | Pack 上线引入折叠膜，最弱膜原则需覆盖它 |

---

*本白皮书 v2.0 综合了 Claude-Opus-4.8 与 GPT-5.5 的深度评审意见，修复了归属判据过粗、软知识失效过度工程、Entity Resolution 缺失等核心内伤，明确了系统认识论边界与最小闭环里程碑。*
