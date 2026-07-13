# [COMPAT]
## GPT-5.6-Sol 对 ContextLedger 项目的全面评审与执行建议

**总体判断**：ContextLedger 已非构想阶段，而是一个完成机械闭环验证、正在攻坚语义正确性的工程项目。其核心价值在于帮助长程 Agent 维护"截至当前什么仍然成立"的可撤销、可裁定、可回放的当前世界状态，而非简单的记忆存储。项目已通过回滚 checkpoint、冻结版本、恢复 quarantine-only 重跑等操作建立了正确的工程纪律，这是比单轮指标提升更重要的成果。

---

### 一、三个最核心的结构性问题

**1. 瓶颈不在机械核，而在语义编译前端**

当前链路中 Apply、Replay、Lint、Quarantine、Assembler 等后半段已相对可控，真正的不确定性集中在 Extractor（是否提取正确）、Resolver（是否对齐同一对象）、Adjudicator（是否误判失效）三步。下一阶段应拆开前端语义链路，而非继续堆砌 Graph 类型或 Assembler 功能。

**2. entity_ref 职责过载**

entity_ref 同时承担实体身份、冲突分桶、失效匹配、状态聚合、检索锚点五重职责，是系统脆弱的根源。引入 `lifecycle_ref`、`lifecycle_stage`、`lifecycle_seq`、`adjudication_key` 的方向正确，但必须满足以下条件方可实施：

- 明确三者的身份不变量：`entity_ref` = 对象身份，`lifecycle_ref` = 对象的一条状态演化流，`adjudication_key` = 冲突裁定分桶键，三者不得互相隐式替代；
- `lifecycle_seq` **不能由 LLM 自由生成**，必须由机械层分配。LLM 仅提议语义（surface entity、状态变化类型、事件关系、显式时间/阶段描述），Resolver 决定 canonical entity 与 lifecycle 匹配，机械层最终决定 lifecycle_ref、sequence 编号、合法状态转移、adjudication_key、同桶排序及 active 集合。否则强保证仍建立在 LLM 命名一致性之上。

**3. provenance conflict 与 invalidation 必须彻底分离**

当前低 precision 的最大单项来源即 provenance conflict 被自动视为失效。以下情形不应触发失效：用户与工具结果冲突、不同来源给出不同判断、推测与实测冲突、不同环境结果不同、并列证据冲突、来源可信度不足。应将裁决结果分为 `SUPERCEDES`（明确替代）、`COEXISTS`（允许并存）、`CONTESTS`（冲突但不足以判定失效）三类，`CONTESTS` 不得直接修改 active 状态，应进入待裁定集合或由来源优先级规则处理。

---

### 二、生命周期 schema 实现前必须补齐的九项内容

1. **身份不变量**：明确 node 能否无 lifecycle_ref、一个 lifecycle_ref 是否只能属于一个 canonical entity、一个 entity 是否允许多个 active lifecycle 并存、alias 合并后 lifecycle_ref 如何迁移；
2. **sequence 分配规则**：区分 `observed_at`（系统收到时间，单调不可改）与 `effective_at`（业务生效时间，可迟到/缺失/不确定），形成轻量双时态模型；
3. **状态转移表**：为节点类型定义允许转移（如 proposed→active→superseded→revived），机械可执行者进入主图，存疑者进入 quarantine；
4. **full/partial/conditional/revival 正式语义**：Phase 1 优先采用"原子化声明"，不建设通用 JSON path 失效；partial 需明确作用域，conditional 需包含条件作用域，revival 建模为新事件恢复旧状态而非修改旧 patch；
5. **provenance conflict 分离**（如上）；
6. **Resolver 支持 abstain**：低置信度不得静默降级为新 entity_ref，必须可进入 quarantine；
7. **旧数据迁移规则**：`lifecycle_ref` 缺失时默认等于 `entity_ref` 只能作为版本化兼容规则，不是隐式 fallback，迁移前后分别保留 checkpoint；
8. **新增 lint 规则**：lifecycle_ref 指向不存在实体、跨 canonical entity、sequence 非法倒退、revival 无可恢复目标、partial/conditional 缺少作用域、provenance conflict 直接写成 full invalidation、legacy 与 lifecycle_v1 混裁等；
9. **replay fixture**：至少覆盖同实体多生命周期、alias 指向同/不同 lifecycle、late arrival、provenance conflict、partial、conditional、revival、false alias、sequence collision、legacy migration 等场景，比真实批量跑更早完成。

---

### 三、Extractor / Resolver / Adjudicator 职责重新划分

- **Extractor**：只提取声明——对象、状态、显式否定、显式替代、时间/环境/分支/来源、lifecycle 线索、证据跨度，不直接决定最终 active/superseded；
- **Resolver**：负责身份解析——输入表面引用和候选，输出 canonical entity、lifecycle 匹配、alias 记录、证据、置信度或 abstain；
- **Adjudicator**：判断语义关系——supersedes/refines/contests/coexists/revives/unrelated；
- **Mechanical Compiler**：根据 adjudication_key、状态转移规则、时序、作用域、来源规则确定最终 active 集合。

此拆分增加接口但显著改善可测试性，否则一次误判无法定位是提取、对齐、分类还是编译环节出错。

---

### 四、下一阶段最优执行顺序

**STEP 0：恢复"仓库当前事实"**——生成机器可读的 `current_state_manifest.json`，含 commit、schema/extractor/cleaner/resolver 版本、graph_state checksum、latest applied/quarantined turn、node/edge counts、active/superseded counts、quarantine reason 分布、lint baseline、benchmark 版本、当前指标，后续所有实验引用此 manifest。

**STEP 1：冻结 benchmark v1**——分为 development（调参）、regression（每次提交运行）、blind holdout（规则冻结后揭晓）、adversarial（alias/late event/provenance 诱饵），冻结 gold schema、baseline 实现、metric 脚本及 D1/D2 定义。

**STEP 2：完成 lifecycle schema RFC**——就九项问题形成明确决策表，回答谁分配 lifecycle_ref/seq、late event 如何处理、provenance conflict 能否触发失效、partial 最小表达、conditional 作用域存储、revival 编译方式、legacy 兼容、哪些必须 quarantine 后，再进入实现。

**STEP 3：实现最小 lifecycle 核心**——仅解决已被数据证明的问题（多生命周期、revival、provenance conflict 不再自动失效、到达/生效时间分离、alias 解析），暂不加入通用规则引擎、任意逻辑条件、通用 field-level DSL、跨项目知识合并、MemoryPack 生命周期同步。

**STEP 4：双轨 shadow replay**——新旧裁定链路同时运行，逐 checkpoint 比较 active set、invalidation、must_include、quarantine、assembler token 及下游输出差异，未过门槛前不替换主链。

**STEP 5：消融实验**——比较 entity_ref only、+resolver、+lifecycle、+lifecycle+provenance separation、完整方案，验证各层独立收益，防止设计过度膨胀。

**STEP 6：验证下游任务收益**——设计三类长程任务（需求反复修改、多轮实现与回滚、后台异步工具执行），比较 full-history、rolling summary、vector RAG、last-write-wins 与 ContextLedger，以任务成功率、废弃约束引用次数、错误动作数、must_include 遗漏率、token 消耗、延迟、人工干预次数为最终指标。仅提升 Graph Set-F1 而不减少下游错误动作，则产品价值未被证明。

---

### 五、指标体系调整

- **引入错误成本加权**：区分 Critical false invalidation、Critical must_include miss、Ordinary false invalidation、Missed invalidation、Benign duplication；设硬门槛——must_include recall 不低于 D1，关键约束 false invalidation 为零或全部进入 quarantine；
- **单独报告 Resolver 指标**：canonical entity accuracy、lifecycle resolution accuracy、alias merge precision/recall、abstain precision、因解析错误导致的误失效数量，alias merge precision 优先；
- **单独报告隔离质量**：quarantine rate、auto-recovery rate、manual-review rate、repeat-failure rate、reason distribution、silent-corruption count——隔离率可阶段性较高，但 silent corruption 必须趋近零。

---

### 六、Assembler 的三项硬要求

1. 强制约束不得与普通检索竞争 token——预算顺序为 `must_include reserved → current task state → immediate dependencies → recent tool outcomes → optional soft context`，超预算显式 fail 或降级；
2. 所有注入内容可解释——附带 `why_included`、`source_node`、`relevance_path`、`authority`、`status`、`token_cost`，便于区分错误来源；
3. 评测装配而非仅评测存储——增加 current-state retrieval recall、irrelevant-context ratio、stale-context leakage、must_include ordering、context token efficiency、downstream instruction adherence。

---

### 七、MemoryPack 与 OpenCode 的处理策略

- **MemoryPack：继续延期**——核心价值未验证、生命周期未稳定、Pack 引入额外陈旧窗口与一致性问题，待 TaskGraph+Assembler 证明下游收益且用户明确需要跨任务知识复利时再进入 Phase 2；
- **OpenCode：仅保留最窄集成**——仅覆盖主会话链路，使用稳定 wrapper 注入，保留宿主原始上下文与 CL 上下文的对照日志，先 shadow 再接管，暂不覆盖子 Agent，暂不扩展多宿主适配。

---

### 八、明确禁止的十项操作

1. 不实现 MemoryPack；2. 不扩展更多宿主；3. 不继续增加节点/边类型；4. 不让 LLM 直接决定最终状态；5. 不让 LLM 自由生成 sequence；6. 不在同一批轨迹上持续调参并宣称泛化；7. 不用单一 Set-F1 掩盖关键约束被错误失效；8. 不将 provenance conflict 直接等同 invalidation；9. 不用人工修 patch 提高通过率；10. 不在 schema 未稳定时优化全图 lint 性能。

---

### 九、Phase 1 封板标准

- **可复现性**：新 schema 下 patch replay 确定，graph_state 可稳定再生，migration 前后可审计，所有工具/prompt/contract 有版本，无人工 patch 进入主图；
- **语义正确性**：lifecycle fixture 全通过，revival 无回归，provenance conflict 不默认触发 full invalidation，late event 有明确处理规则，alias 错误合并可阻断或隔离，partial/conditional 不整体误杀旧节点；
- **安全性**：must_include recall 不低于 D1，关键约束 false invalidation 为零或全部 quarantine，silent corruption 为零，abstain 路径完整；
- **泛化性**：blind holdout 仍有提升，消融实验能说明独立收益，指标脚本和数据集已冻结；
- **下游价值**：至少在一种真实长程 Agent 任务中，比 full-history 或 RAG 更少引用失效信息，相同 token 下成功率更高，或以更低 token 达到相同成功率，must_include 遵循率不下降。

---

### 十、最高优先级动作

**冻结 benchmark v1，在不修改主链的前提下实现 lifecycle schema 的 shadow compiler，对全部历史轨迹进行双轨回放与误差归因。** 这一步可同时回答 lifecycle_ref 是否真正解决问题、指标提升是否可泛化、provenance/revival/late event 各自贡献、新 schema 是否破坏确定性、quarantine 是否下降、是否值得继续增加模型复杂度。在此之前，不扩大产品范围。

---

**最终结论**：批准 lifecycle 方向，但必须补齐身份、时序、来源、状态转移和迁移契约；让 LLM 负责提出声明，机械层负责分配身份与编译状态；冻结基准，用 shadow replay 和 blind holdout 验证；在真实下游收益被证明前，继续冻结 MemoryPack 和多宿主扩展。这是当前风险最低、信息增益最高的执行路径。
## Stage02 启动：git 前置完成，STEP 0 与 STEP 2 已落地，建议先冻结 benchmark 再进主链实现

用户指令要求按 GPT-5.6-Sol 建议实施，执行前先提交当前工作区、合并 main，再开新分支。项目AI已完成 git 前置动作：提交 main（commit 890219b，信息为 Finalize Phase 0.5 benchmark and Phase 1 schema design draft），并从最新 main 新开分支 `phase1-lifecycle-stage02`。随后优先落实 GPT-5.6-Sol 建议中的 STEP 0（当前状态清单）和 STEP 2（lifecycle schema RFC），未贸然进入真实实现。

已完成三项产物：① `current_state_manifest.json`——锁定分支/commit、schema 契约位置、graph_state.json 的 SHA256、turn_counter=84、node/edge 数、quarantine 分布、lint 基线、benchmark 口径与关键指标；② `current_graph_lint_report.json`——补跑并落盘当前 lint 基线；③ 完整版 lifecycle RFC（`05_phase1_lifecycle_schema.md`）——已明确 entity_ref/lifecycle_ref/adjudication_key 职责拆分、身份不变量、lifecycle_seq 不由 LLM 自由生成、observed_at/effective_at 双时态边界、SUPERCEDES/COEXISTS/CONTESTS/REVIVES/UNRELATED 五类裁决、provenance conflict 不得默认折叠为 full invalidation、resolver abstain、legacy 兼容/迁移规则、必增 lint 规则、必备 replay fixtures、benchmark 验收目标。

当前分支 `phase1-lifecycle-stage02` 上三份产物尚未提交。项目AI建议按 Stage02 文档顺序，先做 benchmark v1 冻结（划分 development/regression/blind holdout/adversarial），再补 lifecycle fixtures（revival、provenance conflict、late arrival、legacy migration）及 shadow replay 设计，完成后对比新旧裁决链差异，最后才进入 reconcile/apply/assembler 主链实现。
## Stage02实施确认与军师AI评审修正指令

用户确认按GPT-5.6-Sol建议进入Stage02实施，要求先提交当前工作区并合并main，再开新分支执行。项目AI已完成git前置动作（提交main，commit 890219b，新开分支`phase1-lifecycle-stage02`），优先落实STEP 0和STEP 2，产出三份产物：`current_state_manifest.json`（锁定分支/commit、graph_state.json的SHA256、turn_counter=84、node/edge数、quarantine分布、lint基线、benchmark口径）、`current_graph_lint_report.json`、完整版lifecycle RFC（`05_phase1_lifecycle_schema.md`，已明确entity_ref/lifecycle_ref/adjudication_key职责拆分、身份不变量、lifecycle_seq不由LLM生成、双时态边界、五类裁决语义、provenance conflict不得折叠为full invalidation、resolver abstain、legacy迁移规则、lint规则、replay fixtures、benchmark验收目标）。三份产物当前未提交，项目AI建议下一步先冻结benchmark v1并补lifecycle fixtures+shadow replay设计，再进主链实现。

军师AI评审认为方向正确、节奏稳健，尤其肯定未简化"加字段即完成"、已明确LLM不分配序号、provenance conflict分离、提出必要契约、暂不改主链。但指出当前回复主要是"完成事项叙述"而非可机械验收的交付，要求以下补强：

**一、先完成Stage02原子提交**——将三份产物以"Freeze Stage02 repository baseline and lifecycle RFC"提交，提交前报告`git status --short`、`git branch`、`git rev-parse HEAD`、`git log -1`、`git diff --check`，提交后报告新commit SHA、clean status、base main SHA及merge-base。

**二、manifest必须可再生且来源可溯**——`turn_counter`、node/edge数、quarantine分布须由当前`graph_state.json`实测得出，不得复述历史叙述快照；每个统计项附带来源字段（路径、SHA256、生成时间）；补充版本指纹：main_base_commit、stage_branch_head、working_tree_clean状态、Python/Node版本、extractor/cleaner/resolver的prompt/contract及文件hash、benchmark数据集与metric脚本hash、lint基线hash与路径、manifest生成脚本路径；quarantine条目总数、按reason分类数、未解决数；active/superseded/pending状态分布。manifest须能由脚本再生而非人工编辑维护。

**三、RFC需补充可执行决策表**——明确lifecycle_ref分配者（LLM提议→Resolver匹配→机械层生成ID）、lifecycle_seq仅机械层确定、observed_at单调不可改、effective_at可缺失/晚到及其排序规则、晚到事件只影响未来编译不重算旧patch、CONTESTS不使旧节点superseded、Phase 1 partial统一要求声明原子化、conditional缺condition时处理方式、revival以新事件表达不修改旧patch、abstain是否quarantine或创建provisional节点、legacy adjudication_key fallback版本化规则。同时增加"Phase 1 Non-goals"小节明确排除通用规则语言、field-level DSL、跨项目合并、自动解决所有来源冲突、MemoryPack同步、多宿主集成、全量性能优化。

**四、调整后续阶段为严格四步**——A：提交锁定Stage02（通过条件：三产物已提交、manifest可脚本再生、git diff为空、数字与实测一致）；B：冻结Benchmark v1（落盘development/regression/blind_holdout/adversarial四个split的case ID、数据hash、gold标注版本、D1/D2 baseline精确定义与实现版本、metric脚本hash、旧链路基线成绩、允许调参范围、benchmark版本号规则；lifecycle fixtures与blind holdout隔离，fixture为白盒机制测试，holdout为泛化评测）；C：先写fixtures和shadow replay规格（最小覆盖：同entity不同lifecycle不互杀、revival派生、provenance conflict只产生CONTESTS、late arrival双时态行为、legacy兼容迁移、alias错误时abstain/quarantine、sequence collision保守处理、replay后确定性再生；每个fixture含input event stream、expected patches/relations、expected graph state及active/superseded/pending set、expected quarantine、expected assembler must_include）；D：定义shadow replay可执行验收门槛（输出old_state_hash/shadow_state_hash、逐checkpoint状态差异、关系差异、must_include差异、quarantine差异、assembler差异、差异分类为expected_improvement/expected_schema_change/regression/unexplained，并事先明确哪些差异允许、哪些须人工裁定、哪些自动阻断切换、什么指标门槛可进入主链替换候选）。

**五、明确shadow不变量**——事件不可改写、历史patch不可改写、lifecycle升级不得人工编辑旧patch、schema迁移版本化可回放、shadow输出独立目录不污染主图、shadow失败须quarantine或终止不得"尽量生成"；确定性要求同一输入同一版本必须产生相同patch序列/graph state/context bundle/metrics，且需分开验证固定LLM输出时机械后端确定性以及真实LLM输出时前端语义波动；安全要求must_include recall不低于D1、critical constraints不得静默失效、CONTESTS不得坍缩为SUPERCEDES、resolver低置信度不得强行merge、新方案不增加silent corruption、任何降级可观测可归因。

**六、下一轮可实现的代码限于旁路**——benchmark校验脚本、fixture runner、shadow graph compiler、新旧状态diff工具、lifecycle schema validator、manifest再生脚本、shadow replay报告生成器；不得改写正式apply、不得将新adjudication_key接入正式reconcile、不得更改生产assembler默认注入、不得对已有patch做迁移式重写、不得用人工patch修复fixture。

**最终指令**：批准当前方向，但先不进入主链实现。项目AI须依次完成：①Stage02原子提交并报告完整git状态；②复核manifest数值来源并补充版本指纹；③进入Stage03仅做旁路产物，依次交付benchmark v1 freeze manifest、至少8类lifecycle fixture、shadow replay可执行规格（含diff schema、阻断门槛、报告样例）；④fixture与blind holdout完全隔离；⑤提交任何主链实现前先提交Stage03 readiness report，逐项确认RFC中各项语义已转换成可执行验收规则。当前判断可批准，但前提是将"已核对"转化为可再生manifest、带hash的冻结benchmark、可运行fixture、可归因shadow diff和预先写死的阻断门槛。
## Stage02收尾与Stage03旁路产物交付及军师AI验收评审

项目AI-KIMI2.7已按GPT-5.6-Terra评审意见完成执行：Stage02三份产物（`05_phase1_lifecycle_schema.md`、`current_state_manifest.json`、`current_graph_lint_report.json`）连同可再生的manifest生成脚本（`generate_state_manifest.py`）以原子提交方式落于分支`phase1-lifecycle-stage02`，HEAD为`683d205`，base main为`890219b`，工作树干净。manifest已包含graph_state实测路径与SHA256、生成时间、生成脚本及hash、runtime组件指纹、benchmark score/hash、quarantine分布、lint基线hash、git状态快照，所有数字源自当前`graph/projects/abu_modern/graph_state.json`实测。

Stage03旁路产物按Terra四阶段要求交付：Benchmark v1 freeze（development=7/regression=6/blind_holdout=2/adversarial=2，含freeze manifest及校验脚本）；8个lifecycle fixtures（two_lifecycles_no_kill、revival、provenance_conflict、late_arrival、legacy_migration、alias_abstain、sequence_collision、replay_determinism，含fixture_schema与校验脚本）；Shadow replay executable spec（含主spec、diff_report_schema及示例报告）；Stage03 readiness report。两个校验脚本均通过，未修改`reconcile_patch.py`、`apply_patch.py`或assembler主链。

军师AI-Terra总体判断：工程治理和旁路准备合格，可批准进入"shadow adjudication链的旁路实现阶段"，但尚未形成lifecycle机制正确性证据。认可点：Stage02提交纪律合格（可再生的manifest）、manifest升级方向正确（接近实验状态锚点）、"先shadow后替换"节奏正确。需警惕的问题：validator通过仅证明文件结构自洽，不等于fixture语义通过——需新增真正执行语义的runner（如`run_lifecycle_fixture_replay.py`）逐fixture输出checkpoint预期与实际状态对比，文件合法性校验与语义行为回放必须分层。"连续三次PASS"不能作为主链替换的主要证据，应拆分为确定性重跑、fixture语义、regression不回退、blind holdout达到预注册门槛、must_include安全红线不下降、critical false invalidation为零或全部隔离、diff无未解释blocker、旁路不污染主图等多重条件。Benchmark样本规模偏小（blind holdout仅2条）尚不能支撑强泛化结论，须完成split审计（完整轨迹不跨split、模板/alias不泄漏、机制类型分布、holdout在规则设计期间保持不可见）。

Shadow replay实现前须补齐的契约：shadow与正式主链物理隔离（shadow输出置于`shadow_replay/runs/<run_id>/`下，不写正式graph_state、不写正式patch ledger、不改raw、不fallback到正式链）；输入层分层验证（层1固定结构化声明验证机械确定性，层2真实Extractor/Resolver观察前端误差）；diff分类必须预注册而非事后解释，将must_include下降、critical false invalidation、CONTESTS坍缩为SUPERCEDES、低置信度强制merge均设为blocker。Stage03 readiness report须逐项确认RFC决策已转为机器可测试规则，并列出未决风险（owner/decision deadline/default-safe行为/blocker分类）。

Terra批准进入Stage04-A，任务明确定义为"实现无副作用、可确定性回放的shadow lifecycle adjudication kernel"——允许shadow输入适配器、resolver适配器、adjudication_key分桶、五类关系输出、双时态排序、shadow state compiler、fixture语义replay runner、run-scoped输出、diff runner、benchmark只读执行器、可再生报告；禁止修改正式reconcile/apply/assembler、改写已存在raw/patch/正式图、合并shadow回正式图、人工补patch使fixture通过、用blind holdout调参、让LLM生成最终lifecycle_ref/seq、以"后续再解释"接受未分类diff。最终指令：提交Stage04-A implementation contract明确隔离与禁止机制；实现fixture semantic replay runner实际执行shadow adjudication与compiler并逐checkpoint对比；benchmark运行前补充split审计；diff spec预先锁定五类差异分类规则；连续三次PASS仅作确定性复现检查；主链候选切换前须同时满足fixture语义通过、regression无安全回退、blind holdout达预注册门槛、must_include recall不低于D1、critical false invalidation为零或全部quarantine、无未解释blocker diff、shadow输出未污染正式主图；完成后提交Stage04-A report逐fixture/split/checkpoint报告输入hash、runtime fingerprint、state/bundle hash、diff分类和未决风险，不提交主链改动。
## Stage04-A完成确认与Stage04-B启动：shadow kernel机制验证通过，进入冻结基准评测阶段

项目AI已完成Stage04-A全部交付：交付Stage04-A implementation contract（明确shadow输入/输出目录、run ID、状态隔离、失败处理、runtime fingerprint、禁止写入正式主图机制）；实现shadow lifecycle adjudication kernel（含shadow adjudicator、shadow compiler、shadow bundle builder三份可执行脚本）；实现fixture semantic replay runner，实际执行shadow adjudication+compiler，逐checkpoint比对expected relation、active set、quarantine、must_include并生成diff report与gate decision；8个fixture（two_lifecycles_no_kill、revival、provenance_conflict、late_arrival、legacy_migration、alias_abstain、sequence_collision、replay_determinism）全部PASS，两次回放hash一致确认确定性；完成benchmark v1 split审计（确认无轨迹跨split、模板/alias泄漏分数可接受、各split机制类型分布已记录）；更新shadow diff spec，锁定blocker/regression/expected_schema_change/manual_adjudication/unexplained五类差异，明确must_include下降、critical false invalidation、CONTESTS→SUPERCEDES自动坍缩、低置信度强制alias merge均为blocker；交付Stage04-A report（逐fixture、逐split、逐checkpoint报告输入hash、runtime fingerprint、state/bundle hash、diff分类和未决风险）。Git状态：分支phase1-lifecycle-stage02，HEAD 943b3f7，base main 890219b，工作树干净，未修改reconcile_patch.py、apply_patch.py、build_context_bundle.py、assembler及正式graph_state.json等任何主链文件。

军师AI-Terra裁定认可Stage04-A完成，批准进入Stage04-B（Frozen Benchmark Shadow Evaluation），但明确此批准仅表示shadow kernel具备隔离运行、机制级fixture回放、基础确定性验证和差异分类能力，不表示lifecycle方案已在真实历史轨迹上证明收益，也不表示可进入正式主链替换。

本轮认可点：旁路边界被遵守（shadow输出位于run-scoped目录，主链文件未改动）；fixture runner已从文件校验升级为语义执行（开始验证REVIVES是否改变派生当前态、CONTESTS未被错误折叠、多lifecycle不互杀、late arrival符合规则、alias不确定性正确abstain/quarantine、state/bundle可重放再生）；diff分类已预先固定且安全红线明确；split审计为必要动作。但指出仍需补强：确认主链未改动的证据应通过`git diff --name-only`命令输出证明；"模板/alias泄漏分数可接受"须由预先写死的数值门槛和算法定义；8个fixture全部通过不等于真实语料正确性，只能定性为shadow kernel机制正确性与隔离性初步成立；"两次hash一致"只说明有限确定性，须明确hash覆盖范围并做干净checkout的独立性验证；Stage04-A报告中"逐split"表述存在歧义——若尚未运行完整benchmark shadow replay，则报告不得暗示已实际评测regression/holdout，应明确区分Fixture execution、Benchmark split audit、Development shadow replay、Regression shadow replay、Blind holdout shadow replay、Adversarial shadow replay各自的执行状态。

Stage04-B正确目标定义为：在不改变冻结benchmark、冻结diff分类、冻结安全红线和不污染正式主图的条件下，测量shadow lifecycle链相对旧链的真实收益、退化和不确定性。开始前须锁定evaluation manifest（benchmark version/split hash、case ID列表、gold annotation hash、metric脚本hash、旧链输出hash、shadow kernel commit SHA、runtime fingerprint、diff spec hash、gate rules版本、运行命令、随机种子/确定性模式、时间戳）；将"模板/alias泄漏可接受"转为可验证规则（同canonical entity/alias family/事件模板规范化指纹不得跨development与blind_holdout，泄漏发现后必须重新split并提升benchmark版本）；固定manual_adjudication裁定流程（不得直接计为shadow改进，未裁定时计入unresolved，blocker或unexplained不得手工降级为expected_schema_change除非先修改版本化规则并从头复跑）。Stage04-B执行顺序：①固定candidate后重跑8个fixture；②跑development（仅用于诊断，规则变化后提升版本并重新跑fixture/development）；③冻结最终candidate跑regression；④regression无blocker、无unexplained diff、must_include不低于D1且关键约束无false invalidation后执行一次sealed blind-holdout run；⑤执行adversarial安全评测。每次运行需逐case逐checkpoint输出input hash、runtime fingerprint、relation/state/bundle hash、旧新差异、diff分类、quarantine变化和gate decision。

主链候选切换硬门槛明确：shadow隔离且证据完备、fixture全通过且新增修复对应新fixture、diff无blocker且无unexplained且manual_adjudication已留存裁定、must_include recall不低于D1且不低于旧链、critical false invalidation为零或全部quarantine、regression无预注册安全指标回退且核心指标改善或至少不劣于旧链、blind holdout不低于预注册基线且不夸大泛化、adversarial无blocker且安全用例无回归、quarantine增量有归因不以大量quarantine换取表面precision提升、所有输入/代码/输出/报告/裁定均带hash和commit指纹。连续重复运行仅用于证明确定性，不能替代语义正确性、泛化性或主链切换证据。最终仅可提交Stage04-B evaluation report和主链候选切换申请包，不得提交主链替换实现。
# [/COMPAT]

