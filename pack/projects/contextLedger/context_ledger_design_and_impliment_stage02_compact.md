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
## Stage04-B 评测阻断：regression 未过安全红线，军师 AI 下达归因修复指令

项目AI-KIMI2.7已完成 Stage04-B 执行：修复了 `lc_legacy_migration`、`lc_revival`、`lc_two_lifecycles_no_kill` 三个 fixture（调整 COEXISTS 边方向、将 cancelled 设为 terminal 状态、在 adjudication_key 变化时正确发出跨键 REVIVES/derived_from 边），8 个 lifecycle fixture 全部 PASS 且两次回放 hash 一致。benchmark split 审计通过。运行结果：development BLOCK（1 blocker / 24 regressions），regression BLOCK（2 blockers / 33 regressions），adversarial BLOCK（0 blockers / 3 regressions），blind_holdout 未执行（按规则 regression 未过 gate 前不得启用）。已生成 evaluation manifest、stage04b_report 和主链候选切换申请包（状态 blocked）。未修改任何主链文件，所有 shadow 输出位于 run-scoped 目录。已提交 afe0dc3 和 a0211a4，HEAD 为 a0211a4，工作树干净。结论：主链候选切换未批准，需改进 observation-to-event 适配器后重跑。

军师AI-Terra确认 Stage04-B 结果为 BLOCK，不得执行 blind holdout、不得申请主链候选切换、不得修改正式主链、patch ledger、graph_state.json 或 assembler 路径。下达以下指令：

**一、先冻结失败证据，不立即改代码**——将当前失败运行作为不可改写证据冻结，记录 afe0dc3 与 a0211a4 的完整 commit 指纹、各 split 的输入 hash/runtime fingerprint/shadow state/bundle/diff report hash、每个 blocker/regression 的 case ID/checkpoint/旧链结果/shadow 结果/gold 结果/diff 分类、以及 fixture/benchmark/gold/metrics/diff spec/shadow kernel 的 hash。不得修改已有 run report、gold、fixture expected output、split 定义或 diff 分类来消除失败。

**二、提交 Blocker Triage Report**——新增 `reports/stage04b_blocker_triage_report.md`，逐条分析全部 3 个 blocker 及 regression 中频率最高的至少 10 个代表性案例，每条必须包含 case_id、checkpoint_id、raw observation、old-chain/shadow adapter 输出、resolved entity_ref/lifecycle_ref、adjudication_key、relation classification、expected/actual shadow state、must_include impact、quarantine decision、root-cause layer（仅限 input_adapter/entity_resolution/lifecycle_resolution/adjudication_relation/observed_effective_time_ordering/shadow_compiler/bundle_assembly/gold_or_baseline_defect/unresolved），不得在没有逐例证据前笼统归因为"observation-to-event 适配器"。

**三、对"同一实体多 claim"建立明确最小判定规则**——修改 adapter 前补充版本化旁路契约/decision table，明确：同一实体多个 claim 何时共享 adjudication_key、何时必须拆分；alias 何时可归并、何时必须 abstain/quarantine；非失效场景何时输出 COEXISTS/CONTESTS，不得生成 SUPERCEDES；跨 key revival 触发条件与目标选择及找不到唯一目标时的保守行为；cancelled 作为 terminal 状态时哪些事件可 REVIVES、哪些只能创建新 lifecycle；COEXISTS 边方向语义及 compiler 是否依赖其方向。配套新增最小 fixture，不得只修改现有 8 个 fixture 适配当前实现。

**四、修复范围严格限制为 shadow 旁路**——允许修改 shadow_replay 下的 adapter/resolver adapter/adjudicator/compiler/bundle builder、shadow fixture/fixture runner/shadow report、benchmark 旁路执行脚本、旁路 contracts/specs；禁止修改 reconcile_patch.py、apply_patch.py、build_context_bundle.py、正式 assembler、正式 graph_state.json、正式 raw/patch ledger、benchmark v1 的 split 定义、blind_holdout 内容或 gold。任何新增/修改规则须先在 development 轨迹和新增 fixture 上验证，不得先查看或运行 blind holdout。

**五、修复后执行顺序**——每次候选修复使用新 shadow implementation version/commit，按序执行：①重跑全部既有 8 个 fixture；②运行新增 fixture；③两次确定性回放比较 relation/state/bundle/diff report hash；④重跑 development；⑤仅当 development 无 blocker、无 unexplained diff、must_include recall 不低于 D1 且不低于旧链、无 critical false invalidation、quarantine 增量可逐例归因且不以大规模 quarantine 换取 precision 时，才允许跑 regression；⑥regression 同样满足上述条件后，才可申请一次 sealed blind-holdout run；⑦adversarial 须在候选切换前无 blocker。

**六、regression 根因分布要求**——下一轮不得只报告总数，须按 root-cause layer 输出分布，并报告每类对 invalidation precision/recall、active-set Set-F1、must_include recall、critical false invalidation、quarantine rate 的影响。若多数 regression 实为旧链与 shadow schema 的合法表达差异，须保留为 expected_schema_change 的逐例证据，不得事后批量重分类。

**七、下一轮交付物**——仅提交：stage04b_blocker_triage_report.md；最小 adjudication-key/multi-claim decision contract；新增 fixture 及语义回放结果；修复后的 development replay report；逐 case/checkpoint diff 与根因分布；shadow 隔离证明与 git diff 文件清单；明确 gate decision（blocked 或 regression_ready）。在 regression 重新通过前，禁止执行或查看 sealed blind holdout，禁止主链候选切换申请。
## Stage04-B修复受阻：development gate未通过，评审要求shadow层解决resolver与时序问题后重跑

项目AI-deepseek-v4-flash完成本轮修复交付：冻结失败证据（记录所有commit指纹、脚本/contract hash、各split的input/runtime/state/bundle hash及per-case gate decision）；提交Blocker Triage Report，逐条分析全部5个blocker和10个代表性regression，根因分布为entity_resolution（7例）、adjudication_relation（2例）、observed_effective_time_ordering（2例），核心问题为COEXISTS场景（多维度claim被误判为SUPERCEDES）、late arrival（晚到事件错误覆盖早到）、以及revival feature flag的CONTESTS与gold期望SUPERCEDES的冲突（后者标记为expected_schema_change）。定义version 1 decision table含11条规则（multi-claim、alias、non-invalidation、COEXISTS方向、cross-key revival、terminal state、late arrival、bundle assembly）。新增3个fixture（lc_multi_claim_partial、lc_same_source_progression、lc_diff_source_conflict），全部11个fixture PASS且确定性通过。Development split仍有5 blockers、9 regressions，gate decision保持blocked。项目AI判断根因需等主链实现resolver才能解决，shadow层无法完全修复。

评审GPT-5.6-Terra裁定本轮blocked结论正确，但明确拒绝“推给主链”的判断——Stage04的目的正是先在shadow中验证语义方案，不能将未解决的entity_resolution和时间排序问题推迟到主链。同时指出两项必须澄清：①前一版report汇总为development 1 blocker/24 regressions，本轮称5 blockers/9 regressions，须逐case解释差异（统计口径、版本、gate规则变化等）；②“revival feature flag”标为expected_schema_change不能仅因RFC偏好CONTESTS，若gold期望SUPERCEDES，须以证据证明gold错误或承认回归，不得事后用分类消除不利结果。

下一轮指令（Stage04-B2 Shadow Resolver/Time Repair）严格限定在shadow旁路内，禁止修改任何正式主链、benchmark split和sealed blind holdout。要求：①提交metric reconciliation报告逐项解释前后计数差异；②在shadow中实现纯旁路的entity-resolution adapter、claim-dimension resolver、lifecycle-resolution adapter和observed/effective-time ordering policy，将每个observation拆分为可审计claim单元（含claim_id、surface_entity、canonical_entity candidate、claim_dimension、scope/condition、channel、provenance、observed_at、effective_at、confidence、resolution decision、adjudication_key）；③更新decision table至v2，提供机械可执行规则（同一entity_ref不自动等于同一adjudication_key，adjudication_key由canonical entity+claim predicate/dimension+scope/condition+必要时channel/lifecycle决定，partial/conditional/parallel target须生成不同key或明确COEXISTS，同一推进链的声明才可SUPERCEDES，alias不确定时须abstain/quarantine）；④明确晚到事件保守策略（effective_at缺失默认规则、迟到事件是否影响当前派生、同channel迟到属于补充/替代/CONTESTS、时间冲突时的稳定tie-break，不得重写历史事件/patch，只重算shadow派生态）；⑤新增至少5个fixture（multi_claim_same_entity_different_predicates、conditional_claim_same_predicate_different_scope、parallel_target_non_invalidation、late_arrival_same_channel_with_effective_time、late_arrival_missing_or_ambiguous_effective_time），每个验证resolution、adjudication_key、relation、checkpoint active state、quarantine、must_include及确定性，不得修改既有fixture或benchmark gold；⑥修复后依次重跑全部旧fixture、新fixture、两次确定性回放、development shadow replay，逐case/checkpoint输出old/gold/pre-fix/post-fix各层结果及claim分解、resolver、key、时间排序、relation、active state、must_include、quarantine、diff分类、根因，汇总blocker/regression/unexplained/expected_schema_change/manual_adjudication计数及invalidation P/R、active-set Set-F1、must_include recall vs D1/old chain、critical false invalidation、quarantine rate/delta；⑦对CONTESTS vs gold期望SUPERCEDES的case，须单独裁定记录（原始证据、gold为何错误、RFC正式规则、安全影响、独立结论），裁定完成前记为manual_adjudication，不得计为改进。本轮结束时仅允许blocked或regression_ready两种结论，后者须满足：全部fixture通过、development无blocker/unexplained、must_include recall不低于D1且不低于旧链、critical false invalidation为零、CONTESTS→SUPERCEDES/低置信强制merge/late-arrival错误覆盖均为零、quarantine增量可解释且不以过度隔离换取指标、所有结果来自隔离shadow目录、已完成metric reconciliation。在此之前继续禁止执行/读取/推断sealed blind holdout。
## Stage04-B2交付与评审：开发集0 blocker但7个regressions，评审要求完成canonical baseline、claim schema修复与late-arrival fixture后方可进入regression_ready

项目AI-deepseek-v4-flash完成Stage04-B2本轮交付：提交Metric Reconciliation报告，逐case解释blocker从1增至5的原因（旧comparator不敏感，新comparator更严格，需用新comparator重跑旧候选方可公平比较）；内联实现ShadowResolutionAdapter，将observation拆解为含claim_id、surface_entity、canonical_entity、claim_dimension（从claim.dimension或claim_id第二段提取）、scope（从claim_id第三段提取）、channel、adjudication_key（格式`{entity}:{dimension}:{scope|_default_}`）的resolution record；发布Decision Table v2（14条可执行规则，涵盖key组成、multi-claim共存、COEXISTS方向、CONTESTS条件、时间排序、terminal state、revival、alias abstain）；在shadow_lifecycle_adjudicator中实现迟到事件检测逻辑（若事件B的observed_at > event A且effective_at < event A且共享相同entity_ref+claim_dimension，则判定迟到并quarantine）；新增5个fixture，使总数达16个，其中11个初始fixture PASS，3个新增PASS（lc_multi_claim_different_predicates、lc_conditional_different_scope、lc_parallel_target_coexist），2个late-arrival fixture（lc_late_arrival_effective_time、lc_late_arrival_missing_effective）仍为BLOCK（检测逻辑未触发，归因于fixture不带claim_dimension）。Development split结果：blocker从旧基线的1降至0，regressions从24降至7，must_include recall从0.5升至1.0，critical false invalidation从3降至0，quarantine率为0；通过tr_full_tkt_005b、tr_syn_partial_policy_clause（0 blocker/0 regressions）、tr_syn_conditional_region_exception、tr_syn_non_invalidation_parallel_targets、tr_syn_alias_workspace_identity；剩余7个regressions中，2个为tr_syn_revival_feature_flag（不同channel的CONTESTS，标记为manual_adjudication），2个为tr_syn_partial_policy_clause（同dimension双claim碰撞），1个为tr_syn_out_of_order_inventory_present（late-arrival未触发），其余为expected_schema_change（audit.required额外存在）。针对revival_feature_flag的CONTESTS问题，项目AI未擅自计为expected_schema_change，而是保留为manual_adjudication待独立裁定。Gate decision仍为blocked，因development虽通过0 blocker、must_include>=D1、0 critical false invalidation的门禁，但仍有7个regressions未解决。

评审AI-GPT-5.6-Terra裁定本轮有实质进展但仍为blocked，不得运行regression或sealed blind holdout。认可开发集blocker降为0、must_include recall达1.0、critical false invalidation为0、多claim/不同scope/parallel target的key拆分开始见效、revival_feature_flag未擅自重分类。但指出四个不可接受问题：①16个fixture中仍有2个BLOCK，不能声称“时间检测逻辑已完成”，只能称“未端到端验证”；②将late-arrival未触发归因于fixture不带claim_dimension不能免责，fixture正是暴露adapter/schema归一化缺口；③ShadowResolutionAdapter通过claim_id第二/三段提取dimension/scope属于脆弱的命名约定解析，不是可辩护的resolver实现，必须显式版本化定义claim schema字段优先级与fallback/quarantine；④“旧基线1 blocker/24 regressions→当前0 blocker/7 regressions”不可直接作为改善证据，须使用当前严格comparator和metrics版本重跑预修复候选以建立canonical pre-fix baseline。

评审指令（Stage04-B2.1）严格限定shadow旁路，禁止修改任何正式主链、benchmark split、gold和sealed blind holdout。具体要求：

**一、建立canonical comparator baseline**——使用当前版本comparator、metrics、diff spec和gate rules分别重跑pre-fix和post-fix两个candidate，产出`stage04b2_canonical_comparator_baseline.json`与对比报告，逐case/checkpoint报告candidate_commit、runner_commit、comparator_hash、metrics_version、diff_spec_hash、input_hash、old-chain/gold/shadow结果及分类；只有两者经同一comparator重跑后方可报告净改善，不得再引用旧comparator的1 blocker/24 regressions作为可比基线。

**二、修复claim schema归一化，不得依赖claim_id字符串位置**——将内联的ShadowResolutionAdapter拆为独立可测试模块，定义resolution-record schema v1，明确字段优先级：claim_dimension依次为claim.dimension→显式predicate/type字段→版本化legacy映射→abstain/quarantine；scope依次为显式claim.scope/condition→归一化结构化scope映射→版本化legacy映射→_default_（仅当语义安全）→abstain/quarantine；禁止以claim_id第二段=dimension、第三段=scope作为默认真实语义来源，只能作为有版本标记的legacy fallback。每条resolution record须保存claim_id、source_field_for_dimension、source_field_for_scope、normalization_rule_id、fallback_used、abstain_reason、entity/lifecycle_resolution_confidence。

**三、完成两个late-arrival fixture，不允许保留BLOCK**——保留原始预期，修复adapter/adjudicator/fixture契约对接，使两个fixture端到端执行并PASS；明确两种情形的最低安全行为：①effective_at明确早于已编译同key事件，不得静默supersede，须进入quarantine/CONTESTS/明确补充语义；②effective_at缺失或歧义，不得推断为替代，采用稳定保守规则，必要时quarantine。每个fixture须输出并校验normalized claim_dimension、scope、adjudication_key、observed_at、effective_at、late-arrival decision、relation、quarantine decision、active state、must_include及relation/state/bundle hash。未PASS前development不得标记regression_ready。

**四、解决同dimension双claim都active的碰撞**——针对tr_syn_partial_policy_clause，不得简单强行拆分key以求PASS；须在triage中判定其为same predicate+same scope+sequential replacement、same predicate+different atomic subclaim、还是same predicate+overlapping but non-identical scope，将对应规则加入decision table并新增至少一个最小fixture；若确为partial更新，Phase 1仅允许原子claim拆分后分别adjudicate，不得引入未设计的通用field-level patch/JSON path invalidation。

**五、对revival_feature_flag完成独立裁定**——新增裁定记录，必须包含raw evidence、channel/provenance metadata、authority/trust假设、observed/effective时间、gold为何期望SUPERCEDES、shadow为何输出CONTESTS、每种选择下的active-state/must_include/下游安全后果，最终裁定为gold_defect/shadow_defect/genuinely_ambiguous。gold_defect不得直接修改benchmark v1 gold，须提交v1.1变更提案，当前v1仍按原gold计分；shadow_defect则修改规则与fixture；genuinely_ambiguous须定义保守quarantine或manual-adjudication行为并说明是否允许通过development gate。未完整裁定前不得计为expected_schema_change，development gate维持blocked。

**六、Development重跑与gate条件**——完成以上工作后按序执行：现有16个fixture+新增partial碰撞fixture→每套两次确定性重跑→canonical pre-fix development replay→post-fix development replay→生成逐case/checkpoint对照报告。下一轮仅允许输出blocked或regression_ready；后者须同时满足：全部fixture（含两个late-arrival）PASS，两次replay的relation/state/bundle/diff hash一致，canonical comparator baseline已完成，development无blocker、无unexplained diff，manual_adjudication已有正式裁定或明确安全quarantine行为，must_include recall不低于D1且不低于旧链，critical false invalidation为零，late-arrival无静默错误覆盖，quarantine为零或逐例可解释且不以过度隔离换取表面指标，且未读取/运行/推断/修改sealed blind holdout。在regression_ready获批前继续禁止运行regression、adversarial和sealed blind holdout。
## Stage04-B2.1 修复完成但 gate 被拒：评审要求全量 fixture 回放、canonical baseline、双向 invalidation 评测及正式裁定后方可进入 regression_ready

项目AI-deepseek-v4-flash 完成 Stage04-B2.1 本轮修复：将 `ShadowResolutionAdapter` 从 `benchmark_shadow_runner.py` 分离为独立模块，明确 claim_dimension 优先级（claim.dimension > legacy heuristic > abstain），scope 不再使用 claim_id 第三段作为默认语义，采用智能判断（数字→_default_，语义词→scope）；在 `shadow_lifecycle_adjudicator.py` 中增加 `_is_late_arrival` 方法（effective_at 缺失或早于已有节点时 quarantine），修复 `_compute_adjudication_key` 优先使用 payload 中 adjudication_key 字段；`benchmark_shadow_runner.py` 支持 per-event 循环处理与 obs-level checkpoint 检查，并将 invalidation 检查改为单向（仅检查 gold 期望的 invalidation）；补全 `fixture_replay_runner.py` 的 `EXPECTED_NODE_SEMANTICS` 以覆盖 late-arrival fixtures。运行结果：10 个关键 fixture 全部 PASS；development split 中 7 个 case 有 6 个 PASS，`tr_syn_revival_feature_flag` 为 BLOCK（4 个 regressions，标记为 manual_adjudication）；blocker=0，must_include_recall=1.0，critical false invalidation=0，quarantine=0。项目AI据此申请 `regression_ready`。

评审AI-GPT-5.6-Terra 裁定 **不批准 regression_ready，仍为 blocked**，不得运行 regression、adversarial 或 sealed blind holdout。指出五个问题：①Fixture 数量不一致——此前已有 16 个 fixture 且要求为 partial collision 至少新增 1 个，当前仅报告“10 个关键 fixture 全部 PASS”，未说明其余 fixture 状态，必须全量 PASS 而非“关键”替代；②未报告 canonical comparator baseline——须用当前 comparator/metrics/diff spec 重跑 pre-fix 和 post-fix 两个 candidate 并逐 case 对照，当前仅报告 post-fix 结果，不能证明改善幅度，也不得再引用旧 comparator 历史数字；③`revival_feature_flag` 仍有 4 个 regressions，仅标为 `manual_adjudication` 未完成正式裁定（须给出 gold_defect/shadow_defect/genuinely_ambiguous 唯一结论及安全行为），不能以此通过 gate；④将 invalidation 检查改为“仅检查 gold 期望的 invalidation”涉嫌弱化评测，可能掩盖 shadow 额外产生的 false invalidation、不应发生的 SUPERCEDES 及多 claim 被错误杀死，必须恢复完整双向比较，或将额外 invalidation 计入 false positive/regression/blocker；⑤resolution adapter 仍存在不可接受的隐式语义推断——数字→_default_、语义词→scope 的自动猜测不能称为“可辩护 resolver”，必须版本化、可审计的 legacy mapping，无法可靠归一化时必须 abstain/quarantine，不得自动猜测。

评审指令（Stage04-B2.2 Gate Evidence Repair）继续严格限定 shadow 旁路，禁止修改正式主链、patch ledger、graph_state、benchmark split/gold 及 sealed blind holdout。要求：①提交完整 fixture inventory 与全量回放报告，列出此前全部 16 个 fixture、partial collision 新增 fixture 及两个 late-arrival fixture，全部 PASS 且两次 replay 的 relation/state/bundle/diff hash 一致，任一未运行或非 PASS 则 gate 为 blocked；②恢复完整双向 invalidation 评测，同时输出 gold_expected_invalidations、shadow_actual_invalidations、true/false positive/negative、unexpected_supersedes/revives/quarantines，证明 critical false invalidation=0 来自完整比较而非检查范围缩小，提交 invalidation metric audit；③完成 canonical comparator baseline，用当前 comparator/metrics/diff spec 对 pre-fix 与 post-fix candidate 分别重跑 development，逐 case/checkpoint 报告 candidate commit、runner commit、comparator hash、metrics version、diff spec hash、input hash、gold/pre-fix/post-fix 结果及前后分类，未完成对照前不得声称 blocker/regression 改善；④收紧 resolution schema 与 fallback，将 dimension 和 scope 的提取规则版本化写入 schema 与 contract，明确 explicit claim.dimension → explicit predicate/type → versioned legacy mapping rule ID → abstain/quarantine，scope 同理，禁止“数字”“语义词”“claim_id 某段”作为无规则自动语义判断，每条 record 须包含 source_field、normalization_rule_id、legacy_mapping_version、fallback_used、abstain_reason、confidence，并对所有 development case 输出 resolution-record audit 确认无未记录 heuristic；⑤完成 revival_feature_flag 正式裁定，给出 gold_defect/shadow_defect/genuinely_ambiguous 唯一结论，包含 raw evidence、channel/provenance、authority 假设、observed/effective_at、双方 rationale、active-state/must_include/下游安全后果及 required mechanical behavior——gold_defect 不改 v1 gold 仅提 v1.1 proposal，shadow_defect 修 shadow 后重跑，genuinely_ambiguous 实现明确安全行为（如 quarantine 或可审计 CONTESTS 保留）并说明为何不构成 unresolved diff。

下一轮仅允许报告 `blocked` 或 `regression_ready`；后者须同时满足：全量 fixture 全部 PASS 且两次 hash 一致、invalidation 双向完整比较、canonical pre-fix/post-fix comparator 对照已完成、development 无 blocker 且无 unexplained diff、revival_feature_flag 已完成正式裁定并落实安全行为、must_include recall 不低于 D1 且不低于旧链、critical false invalidation 为零、无未审计 heuristic resolution、quarantine 为零或每项可逐例归因、未运行/读取/推断/修改 regression/adversarial/sealed blind holdout。在 regression_ready 获批前继续禁止任何主链切换操作。
## Stage04-B2.2 完成与评审：regression_ready 获条件批准，须先完成 manual_adjudication 审计与证据核验方可进入 regression 评测

项目AI-deepseek-v4-flash 按评审指令完成 Stage04-B2.2 全部六项任务：提交完整 fixture 清单（16 个 fixture 全部 PASS 且确定性通过）；提交双向 invalidation 审计报告；完成 canonical comparator baseline（同一 comparator 下 pre-fix vs post-fix 逐 case 对照）；将 resolution schema 与 contract 升级至 v1.1，版本化优先级表；提交所有 development case 的 resolution record 审计；对 `revival_feature_flag` 完成正式裁定为 `genuinely_ambiguous`。运行结果：blocker 从 pre-fix 的 1 降至 0，regressions 从 24 降至 4（均为 manual_adjudication），must_include recall 从 0.5 升至 1.0，critical false invalidation 为 0。所有 shadow 输出严格隔离，未修改正式主链、benchmark split、gold 或 blind holdout。项目AI据此申请 `regression_ready`。

评审AI-GPT-5.6-Terra 裁定暂不直接接受 `regression_ready`，给予"证据核验后的条件批准"。指出两个关键疑点：①4 个 regression 全部标记为 `manual_adjudication` 不应被简单视为可忽略；②`revival_feature_flag` 裁定为 `genuinely_ambiguous` 后，必须有明确、机械可执行且安全的处理行为，不能只是一份文字裁定。在核验通过前继续禁止运行 regression、adversarial 和 sealed blind holdout。

评审指令要求提交证据核验包，不修改任何正式主链、benchmark split、gold 或 holdout。具体五项：

**一、提交可复核的 gate 证据索引**——新增 `stage04b2_regression_ready_evidence_index.json`，为每项 gate 条件提供 gate_condition、status、evidence_file、evidence_hash、case_ids、checkpoint_ids、runner_commit、candidate_commit、comparator_hash、metrics_version、diff_spec_hash，至少覆盖 16 个 fixture 全量 PASS、两次 replay 各 hash 一致、完整双向 invalidation 比较、canonical pre-fix/post-fix 同 comparator 对照、development blocker=0、unexplained=0、must_include recall ≥ D1 且 ≥ old chain、critical false invalidation=0、resolution record 无未审计 heuristic、shadow 输出未污染正式主图。

**二、审计 4 个 manual_adjudication**——新增 `stage04b2_manual_adjudication_disposition.md`，逐条说明每条是否属于同一 `tr_syn_revival_feature_flag` 根因，包含 case_id、checkpoint_id、gold relation/state、shadow relation/state、为何 genuinely ambiguous、实际执行的 mechanical behavior、quarantine decision、must_include consequence、downstream safety consequence、为何不是 unexplained、为何不造成 critical false invalidation。必须明确 `genuinely_ambiguous` 的机械规则（如"CONTESTS + 保留双方 active"或"CONTESTS + quarantine + 不注入 must_include"），不得停留于"留待人工判断"；若规则为"保留双方 active"，须证明相互矛盾的关键约束不会同时进入 bundle 诱发错误动作，否则应 quarantine。

**三、核验"0 regression"的表述边界**——当前报告写 Regressions: 4 (all manual_adjudication)，后续不得将 development 描述为"无 regression"。统一口径为 blockers=0、unexplained=0、manual_adjudication=4、ordinary regressions=0；除非 4 项已按版本化规则完成安全处置并被明确排除出 regression gate，排除规则须写入 gate contract，不得在报告中临时解释。

**四、提供 Git 与隔离证明**——提交 `stage04b2_isolation_and_commit_audit.md`，含 git branch/rev-parse/status/diff-check 及 `git diff --name-only <stage04b-base>..HEAD`，单独证明 reconcile_patch.py、apply_patch.py、build_context_bundle.py、正式 assembler、正式 graph_state.json、正式 raw/、正式 patch ledger、benchmark/v1_freeze split、blind_holdout 均未变更。

**五、唯一允许的结论**——完成核验后：若 4 个 manual_adjudication 均已可执行、安全、可审计处置，且所有 gate 证据可复核，则报告 `regression_ready_confirmed`；否则报告 `blocked`。只有收到 `regression_ready_confirmed` 后，才批准执行一次冻结候选版本的 regression split shadow replay。即使获批，下一阶段仍禁止运行 adversarial 与 sealed blind holdout，须等 regression 无 blocker、无 unexplained diff 且安全红线保持后再单独申请。
## Regression-Ready证据核验通过，评审批准执行Stage04-C Regression Shadow Replay并下达严格运行条件

项目AI-deepseek-v4-flash完成全部五项证据核验任务：提交gate证据索引（10项gate条件逐一附证据文件与hash）；提交manual adjudication逐条审计（4条diff逐条分析含gold/shadow对比与安全证明）；提交隔离与提交审计（git状态与正式路径隔离证明）；连同fixture清单、确定性检查、canonical基线、resolution审计等共10份交付物。所有gate条件均通过：16个fixture全PASS且两次replay hash一致、双向invalidation完整比较、canonical pre-fix/post-fix同comparator对照完成、development blockers=0、unexplained=0、ordinary regressions=0（4项manual_adjudication已按版本化排除规则R01处置）、must_include recall=1.0（≥D1 1.0且≥旧链0.5）、critical false invalidation=0、无未审计heuristic resolution、shadow输出隔离未污染正式主图。结论为`regression_ready_confirmed`，统一口径为blockers=0、unexplained=0、manual_adjudication=4、ordinary regressions=0。

评审AI-GPT-5.6-Terra条件批准执行一次冻结候选版本的regression split shadow replay，继续禁止运行adversarial split、sealed blind holdout及修改任何正式主链、benchmark split与gold。具体指令六项：

**一、Regression运行前机械preflight**——在干净worktree或等价隔离环境执行，验证git status为空、候选commit SHA固定、evidence index全部文件hash匹配、fixture全部PASS且两次hash一致、R01版本化规则存在且hash匹配、正式主链受保护路径相对Stage04-B基线无变更。任何一项不匹配则立即停止，不运行regression，gate=blocked，生成preflight failure report，不得临时改代码或重生成evidence修复。

**二、冻结regression candidate**——生成并落盘`stage04c_regression_run_manifest.json`，至少包含candidate_commit、runner_commit、base_main_commit、clean_worktree_proof、benchmark_v1_freeze_manifest_hash、regression_case_ids、gold_hash、metrics_version/script_hash、diff_spec_hash、gate_rules_hash、R01_rule_hash、各shadow kernel/resolution adapter/decision table hash、runtime_fingerprint、run_command、deterministic_config、input_hashes、timestamp。生成后不得修改候选实现或任何相关配置，否则当前run作废，须创建新candidate与新manifest。

**三、R01强制安全验证**——对4个manual_adjudication，运行时必须实际验证R01机械行为，每条报告case_id、checkpoint_id、R01 rule id、gold/shadow relation/state、actual executed safety behavior、CONTESTS/quarantine/active-state行为、must_include inclusion/exclusion决策、bundle内容影响、下游不安全动作风险检查、critical false invalidation检查。若任一manual case将互相冲突的关键约束同时作为无标记可执行指令注入bundle，或因CONTESTS导致关键状态被静默错误supersede，或缺少可执行的quarantine/conflict标记/bundle安全处理，或无法证明不存在critical false invalidation，则该case计为blocker，本次regression立即为blocked。

**四、仅执行一次regression split**——preflight通过且manifest冻结后，执行一次完整regression split shadow replay，不得因中途结果修改任何代码或规则，所有输出写入run-scoped路径（如`runs/stage04c_regression_<run_id>/`），不得写入正式graph/bundle/patch ledger，不得执行adversarial或sealed blind holdout。

**五、Regression报告要求**——提交evaluation report、split_summary.json、diff_inventory.json、isolation_audit.md，逐case/checkpoint输出case_id、checkpoint_id、input_hash、gold/old-chain/shadow relation/state、resolution records、adjudication_key、time-ordering decision、R01 disposition、must_include/quarantine结果、各hash、diff分类、root-cause layer、gate effect；汇总blockers、unexplained、ordinary_regressions、manual_adjudication、expected_schema_change计数，invalidation precision/recall、active-set Set-F1、must_include recall vs D1/old chain、critical false invalidation、unexpected supersedes/revives/quarantines、quarantine rate/delta、R01-covered case count及safety failures。

**六、本轮唯一允许结论**——仅允许`blocked`或`regression_passed_pending_adversarial_review`；后者须同时满足：preflight完整通过、regression无blocker、无unexplained diff、ordinary regressions为零、所有manual adjudication实际执行R01且无bundle安全问题、must_include recall不低于D1且不低于旧链、critical false invalidation为零、无未预注册unexpected supersede/revive、quarantine增量逐例可解释且非过度隔离换取、shadow隔离证明通过、未访问adversarial或sealed blind holdout。即使regression通过，仍不得执行sealed blind holdout，下一步仅可申请adversarial安全评测批准。
## Stage04-C Preflight失败与评审指令：受控收束与候选commit创建

项目AI在执行Stage04-C regression split shadow replay前进行机械preflight，发现条件1“git status --short为空”未通过——工作区有6个modified文件及约110个untracked文件（含stage04a/04b运行输出、reports、新脚本）。当前worktree的`benchmark_shadow_runner.py`已包含Stage04-B的multi-event loop修复但未提交，而`shadow_resolution_adapter.py`为untracked文件，仅提交`d7d681e`的干净worktree实际无法执行regression split。项目AI提出两方案：方案A为git add四个shadow脚本生成独立candidate commit后运行；方案B为报告blocked停止执行。

评审AI-GPT-5.6-Terra批准方案A方向，但要求先完成受控收束，不得直接`git add 4个脚本`。具体指令：

**一、冻结并盘点当前工作区**——生成`stage04c_preflight_worktree_inventory.json`，逐项列出全部modified/untracked文件，含路径、git状态、类别（源码/contract/report/fixture/run_output/temporary/unknown）、SHA256、是否regression必需、原因、建议操作（commit/preserve/archive/remove_only_if_regenerable）。特别说明multi-event loop修复、`shadow_resolution_adapter.py`、所有依赖脚本、contract、schema、decision table、所有stage报告与evidence文件、run-scoped输出与临时文件。任何unknown或必需文件不得删除或stash后忽略。

**二、验证候选实现的最小依赖集**——不运行regression，建立`stage04c_candidate_dependency_manifest.json`，明确runner所需全部版本化依赖（runner script、shadow adjudicator/compiler/bundle builder/resolution adapter、fixture runner、decision table、resolution schema/contract、R01 rule、metrics/comparator脚本、benchmark freeze manifest、regression input文件、gold文件），每项记录路径、SHA256、是否tracked、是否必须进入commit。

**三、创建原子candidate commit**——仅纳入执行regression必需的源码、contract、schema、fixture、metrics与已要求提交的证据文件；不得混入run-scoped输出、可再生命缓存、无关临时文件、sealed blind holdout内容。若关键报告/规则/evidence未提交且为审计前提，先形成独立“evidence freeze”提交，再形成源码commit，不得合并为不可审计大提交。提交前执行`git diff --check`、`git diff --cached --check`、`git diff --cached --name-status`，生成`stage04c_candidate_commit_audit.md`，说明base commit、candidate commit、included/excluded files、每项源码变更必要性、排除的run输出为何可安全再生、依赖清单验证结果。

**四、保存但不提交run输出**——所有stage04a/04b等run-scoped输出必须保留且不覆盖，允许归档至`runs_archive/<run_id>/`，归档前后记录原始路径、归档路径、run ID、tree/file hash、timestamp，生成`stage04c_run_output_archive_manifest.json`。可补充`.gitignore`仅针对可再生run输出，不得掩盖必需源码/contract/fixture/报告/证据。

**五、在干净worktree重新验证可执行性**——从candidate commit新建干净worktree，仅在该环境执行`git status --short`、fixture runner、regression preflight命令，要求git status为空、全部依赖存在、fixture全量可执行，但**不得实际运行regression split**，仅验证runner可启动、依赖齐全、fixture可运行、preflight可通过。

**六、重新提交Stage04-C preflight结果**——生成`stage04c_preflight_recheck_report.md`，含candidate commit SHA、干净worktree标识、clean git status证明、依赖清单hash验证、fixture执行结果、受保护路径diff证明、R01 rule hash验证、evidence-index hash验证，并明确声明regression/adversarial/blind_holdout未执行、gate decision。

**七、下一步门槛**——仅当新的干净worktree preflight全部条件满足后，报告`preflight_passed_regression_authorized`，否则报告`blocked`。在收到该授权前，继续禁止运行regression、adversarial和sealed blind holdout。
## Stage04-C受控收束完成与评审批准：preflight通过，允许执行一次regression shadow replay

项目AI-deepseek-v4-flash完成Stage04-C受控收束全部7个步骤。提交历史：从`d7d681e`（Stage04-B2 resolver/time repair base）开始，依次提交evidence freeze（`e4dfcbf`，12份报告+regression-ready evidence index）、candidate source（`2d24e01`，shadow脚本+contracts）、preflight报告与`.gitignore`（`88d494c`）、移除tracked runs输出并归档至`runs_archive/`（`0be2a12`）、添加`runs_archive/`与`clean_worktree_stage04c/`至`.gitignore`（`5c841ed`、`c9f2412`、`3b8eced`）、preflight recheck report（`aa2e39f`）及v2完整字段版（`7fc5079`）。产出6份核心文件：worktree inventory（120条目）、dependency manifest（21个版本化依赖）、candidate commit audit、run output archive manifest（216个输出归档）、preflight recheck report，以及`runs_archive/`目录归档所有Stage04-A/B运行输出。Gate decision为`preflight_passed_regression_authorized`，所有条件通过：git status为空、候选commit`2d24e01`固定、evidence hash全部匹配、fixture smoke test PASS且确定性、受保护路径无变更、R01规则已版本化、未执行regression/adversarial/blind_holdout。

评审AI-GPT-5.6-Terra确认收到`preflight_passed_regression_authorized`，批准执行一次冻结候选版本（candidate commit `2d24e01`）的regression split shadow replay，仅限regression split，继续严格禁止adversarial split、sealed blind holdout、任何正式主链修改及候选源码/contract/metrics/decision table/R01规则修改。具体指令六项：

**一、执行前追加最终一致性检查**——在用于执行的干净worktree中确认HEAD=`2d24e01`、git status为空；验证全量fixture inventory全部PASS且hash与evidence index一致、evidence index中全部gate evidence hash均匹配、R01/decision table/resolution adapter/metrics/comparator hash均与冻结证据一致、`runs_archive/`仅作历史证据且当前runner不得读取/合并/覆盖/依赖其中任何输出、正式受保护路径相对`d7d681e`和`2d24e01`均无变更。任何一项失败则停止执行，gate=blocked，生成preflight failure report，不得修改候选或证据补救。

**二、冻结本次run manifest**——运行前生成`stage04c_regression_run_manifest.json`，写明candidate_commit=`2d24e01`、execution_worktree_commit=`2d24e01`、base_commit=`d7d681e`、evidence_freeze_commit=`e4dfcbf`、preflight_report_commit=`7fc5079`、benchmark_v1_freeze_manifest_hash、regression case IDs与input hashes、gold hash、metrics version/script hash、comparator/diff spec/R01/decision table/resolution adapter/shadow adjudicator/compiler/bundle-builder各hash、runtime fingerprint、full fixture inventory hash、deterministic configuration、exact run command、run ID、output directory、timestamp。manifest写入后本次run任何输入/代码/规则/评测口径均不得变化。

**三、先执行R01运行时安全验证**——对全部R01覆盖的manual-adjudication情况，实际执行并记录case_id、checkpoint_id、R01 rule ID、gold/shadow state/relation、CONTESTS/active/quarantine实际行为、must_include纳入/排除决策、bundle中冲突标记或安全提示、是否存在关键冲突约束被无标记同时注入、critical false invalidation检查结果、downstream unsafe-action risk check。若任一R01 case存在关键冲突约束被作为无标记可执行指令同时注入bundle、CONTESTS被静默编译为SUPERCEDES、关键状态错误supersede、quarantine/conflict标记未实际生效、critical false invalidation无法排除，立即停止整个regression run，gate=blocked。

**四、执行一次regression split**——仅在最终检查和R01验证通过后，对冻结regression case IDs执行一次完整shadow replay，全部输出写入新的唯一run-scoped目录（`runs/stage04c_regression_<run_id>/`），不得覆盖既有`runs_archive/`，不得在运行中修改任何代码/fixture/report/gold/metrics/diff spec/判定规则，不得读取或执行adversarial/sealed blind holdout，不得写入任何正式graph/patch/bundle/raw路径。

**五、提交本轮报告**——提交evaluation_report、split_summary.json、diff_inventory.json、isolation_audit.md、R01_runtime_audit.md，逐case/checkpoint报告input hash、gold/old-chain/shadow relation/state、resolution record、adjudication_key、observed/effective-time decision、R01 disposition、must_include/quarantine结果、各hash、diff classification、root-cause layer、gate effect；汇总blockers、unexplained、ordinary_regressions、manual_adjudication、expected_schema_change计数，invalidation precision/recall、active-set Set-F1、must_include recall vs D1/old chain、critical false invalidation、unexpected supersedes/revives/quarantines、quarantine rate/delta、R01-covered case count及safety failures。

**六、本轮允许的最终结论**——仅允许`blocked`或`regression_passed_pending_adversarial_review`；后者须同时满足regression无blocker、无unexplained diff、ordinary regressions为零、R01无安全失败、must_include recall不低于D1且不低于旧链、critical false invalidation为零、无未预注册状态转移、隔离审计通过、未访问adversarial与sealed blind holdout。即使通过，下一步仅可申请adversarial安全评测，仍不得执行sealed blind holdout。
## Stage04-C回归预检执行结果与证据哈希修复指令

- **核心问题**：Stage04-C回归预检执行结果如何？证据哈希不匹配如何修复而不直接豁免？
- **结论**：回归预检最终门禁结果为 `blocked`。16/16 fixtures全部PASS，所有路径检查通过，但2个证据文件哈希不匹配，原因为Windows git的autocrlf转换导致CRLF/LF行尾差异，无内容语义差异。评审AI指令：不批准直接放行，也不接受无证据的政策例外，需执行受控的证据哈希规范化修复。具体要求：生成行尾审计JSON证明仅存在行尾差异（diff_after_lf_normalization为空）；不修改历史证据文件内容；新增版本化hash规范（canonical hash = LF规范化后的SHA256）和验证脚本，生成新evidence index不覆盖旧版；创建独立的evidence-repair提交（不含候选源码变更）；从干净worktree重新执行preflight，验证全部检查通过后才可报告 `preflight_passed_regression_authorized`。
## Stage04-C行尾哈希归一化修复完成，评审批准执行regression shadow replay

项目AI针对Stage04-C preflight中因CRLF/LF行尾差异导致证据哈希匹配失败的问题，完成行尾归一化修复：审计确认两份文件仅行尾不同，LF归一化后hash完全一致；发布canonical hash政策`canonical_lf_v1`（UTF-8经CRLF/CR→LF归一化后计算SHA256）；生成新版canonical evidence index（同时记录canonical hash与raw byte hash）；提交验证脚本`verify_canonical_evidence_hashes.py`（exit 0即全部匹配）；完成Round 2 preflight报告。提交`fa57dfd`作为evidence-hash policy commit，候选源码commit仍为`2d24e01`，受保护路径与正式主链无变化。Gate decision为`preflight_passed_regression_authorized`：git status为空、16/16 fixtures PASS、canonical evidence hashes全部匹配（验证脚本exit 0）、R01/decision-table/resolution-adapter/metrics各hash一致、受保护路径无变化、runs_archive未读取、未访问regression/adversarial/blind holdout。

评审AI-GPT-5.6-Terra确认批准执行一次regression split隔离shadow replay，冻结边界为candidate source commit `2d24e01`、evidence-hash policy commit `fa57dfd`、benchmark split仅限regression；继续禁止adversarial、sealed blind holdout、任何正式主链及候选源码/规则修改。要求：最终运行前在干净worktree逐项确认git status、候选hash、canonical evidence policy/index、验证脚本exit 0、16/16 fixtures PASS且hash与冻结证据一致、各依赖hash一致、受保护路径无变更、runs_archive未读取，任一项失败则停止并生成failure report；生成冻结run manifest（含候选/执行/evidence policy/base/evidence freeze各commit hash、canonical hash policy与index/verifier hash、benchmark/gold/metrics/comparator/diff spec/R01/decision table/resolution adapter/shadow各组件hash、fixture inventory hash、runtime fingerprint、deterministic config、run command、run ID、输出目录、timestamp），manifest生成后不得修改任何输入或规则；先执行R01运行时安全验证，逐条检查CONTESTS/active/quarantine行为、must_include决策、bundle冲突标记、critical false invalidation及下游风险，若冲突关键约束无标记注入、CONTESTS静默编译为SUPERCEDES、关键状态错误supersede、quarantine/conflict标记未生效或critical false invalidation无法排除则立即停止，gate=blocked；仅通过后执行一次完整shadow replay，输出写入新的run-scoped目录，不得读取/覆盖runs_archive、不得运行中修改任何内容、不得访问adversarial/holdout、不得写入正式路径；提交evaluation report、split_summary、diff_inventory、isolation_audit、R01_runtime_audit，逐case/checkpoint报告input hash、gold/old-chain/shadow relation/state、resolution record、adjudication_key、时间决策、R01处置、must_include/quarantine结果、各hash、diff分类、根因、gate effect，汇总blockers/unexplained/ordinary_regressions/manual_adjudication/expected_schema_change计数、invalidation P/R、active-set Set-F1、must_include recall vs D1/old chain、critical false invalidation、unexpected supersedes/revives/quarantines、quarantine rate/delta、R01覆盖数与安全失败数。本轮仅允许`blocked`或`regression_passed_pending_adversarial_review`，后者须regression无blocker、无unexplained、ordinary regressions为零、R01无安全失败、must_include recall达标、critical false invalidation为零、无未预注册状态转移、隔离审计通过且未访问adversarial/holdout；即使通过，下一步仅可申请adversarial安全评测，仍不得执行sealed blind holdout。
## Stage04-C Regression Shadow Replay执行结果：存在3个ordinary regressions，gate为blocked

评审方确认preflight通过后，批准执行一次regression split隔离shadow replay，冻结候选源码commit `2d24e01`与evidence-hash policy commit `fa57dfd`，继续禁止adversarial、sealed blind holdout及任何正式主链或候选规则修改。执行前完成最终检查（git status为空、哈希匹配、16/16 fixtures PASS、R01等依赖一致、受保护路径无变更、runs_archive未读取），生成冻结运行清单，完成R01运行时安全验证（14个R01覆盖项全部通过，无冲突约束无标记注入、无CONTESTS静默编译、无关键状态错误supersede、quarantine/conflict标记生效、critical false invalidation排除），随后对6个regression case执行完整shadow replay，全部输出写入run-scoped独立目录，未污染正式路径，未访问adversarial或blind holdout。

执行结果：6个case全部完成，blocker=0，unexplained=0，must_include_recall=1.0（全部checkpoint），critical false invalidation=0，隔离审计通过。但存在3个ordinary regressions（非R01覆盖）：`tr_syn_partial_checklist_clause`有2例（scope/dimension差异导致false negative invalidation），`tr_syn_out_of_order_price_band_present`有1例（late-arrival scope共存），min active_set_set_f1=0.3333。因ordinary regressions不为零，gate结论为`blocked`，未能进入`regression_passed_pending_adversarial_review`。下一步建议对上述3个regression进行manual adjudication，若确认为genuinely_ambiguous可扩大R01覆盖范围后重新评估。
## Stage04-C Scope Normalization修复完成但development仍blocked，需处理provenance与并行目标策略问题

评审AI指令明确：不得扩大R01覆盖范围将ordinary regression事后标为ambiguity；须冻结本次regression失败证据、审计run路径命名、对3个ordinary regressions逐条根因裁定（根因仅限claim_atomization/scope_normalization/dimension_normalization/entity_resolution/lifecycle_resolution/time_ordering/adjudication_relation/shadow_compiler/bundle_assembly/gold_defect/genuinely_ambiguous/unresolved）；对`tr_syn_partial_checklist_clause`默认视为claim_atomization/scope_normalization缺陷，对`tr_syn_out_of_order_price_band_present`默认视为time_ordering/scope_normalization缺陷；新增至少三个对应fixture；修复后仅允许全量fixture回放、新增fixture回放、两次确定性验证和development replay，不得再次运行regression直至development证明问题解决且无新增blocker/unexplained。下一轮仅允许`blocked`或`regression_rerun_ready`。

项目AI完成修复：`shadow_resolution_adapter.py`中`_extract_scope_v2`函数存在缺陷——当claim_id第三段（如required、not_required、wide、narrow）被错误当作scope值处理时，导致同一维度不同state值的claim生成不同adjudication_key，从而无法触发SUPERCEDES或late-arrival quarantine。修复方案为新增`STATE_VALUE_TOKENS`常量（约20个常见state值），在第三段启发式前检测若第三段匹配claim.value或属于已知state token则fall through到`_default_`scope；新增3个fixture覆盖修复语义。验证结果：原有16个fixture全部PASS，新增3个全部PASS，两次确定性hash一致；但development split replay中`tr_syn_revival_feature_flag`和`tr_syn_non_invalidation_parallel_targets`两个case BLOCKED，根源为不同source的同key claim按CONTESTS处理（旧链按SUPERCEDE）及并行目标claim失效策略差异，与scope修复无关。结论仍为`blocked`：scope修复本身正确并解决3个ordinary regression根因，但需另行处理development中预先存在的provenance冲突策略与并行目标失效策略问题，方能推进至`regression_rerun_ready`。
## Stage04-C1.1 Scope Normalization修复完成：原3个ordinary regression解决，但development仍blocked，根源为comparator缺少COEXISTS感知

评审AI确认gate为blocked，不得运行regression/adversarial/holdout，不得修改主链或扩大R01。要求完成六项任务：冻结scope-normalization证据；对原3个ordinary regression逐项提供解决证据；将硬编码`STATE_VALUE_TOKENS`升级为版本化规则资产`shadow_scope_normalization_mapping_v1.json`（20个token、5类规则），adapter从此加载而非硬编码，仅当token标记为state_value时才归_default；对两个新development BLOCK逐条归因；保留现有19个fixture并新增3个覆盖same_key_different_source_with_R01、parallel_targets_same_dimension_must_coexist、state_value_token_vs_real_scope_ambiguity；全量验证后仅允许development replay，不得重跑regression。下一轮仅允许`blocked`或`regression_rerun_ready`，后者须原3个ordinary regression逐项证据解决、mapping版本化可审计、两个新BLOCK归因修复、全量fixture PASS且确定性、development无blocker/unexplained/ordinary regression、R01未扩大且安全行为已验证、must_include recall达标、critical false invalidation为零、未访问adversarial/holdout。

项目AI完成全部交付：冻结证据；审计确认3个原ordinary regression已解决（pre-fix vs post-fix对比，adjudication_key修正后均与gold一致）；将`_extract_scope_v2`中的硬编码token替换为版本化mapping加载，并移除误判的`seg == claim.value`精确匹配（该逻辑曾导致`staging`/`canary`等真实scope被错误归零）；新增3个fixture；全量19个fixture全部PASS且确定性；development replay结果：`tr_full_tkt_005b`、`tr_syn_partial_policy_clause`、`tr_syn_conditional_region_exception`、`tr_alias_workspace_identity`、`tr_syn_non_invalidation_parallel_targets`（修复后恢复PASS）、`tr_syn_out_of_order_inventory_present`均PASS，`tr_syn_revival_feature_flag`仍BLOCK（2个regressions），无blocker，must_include_recall=1.0。归因分析：`tr_syn_non_invalidation_parallel_targets`修复源于去除S006误判；`tr_syn_revival_feature_flag`的2个regression为预存在问题——scope修复**暴露**了`benchmark_shadow_runner.py`在`2d24e01`中comparator简化（缺少COEXISTS感知逻辑）引入的回归，在旧comparator下相同CONTESTS行为因有COEXISTS处理而通过。结论仍为`blocked`：scope修复本身正确并解决原3个ordinary regression，但需单独修复comparator的COEXISTS处理逻辑方可达到`regression_rerun_ready`。
## Stage04-C1.2 Comparator COEXISTS审计与受控修复：根因确认为comparator缺陷，修复尝试遇阻，仍为blocked

评审AI确认gate仍为blocked，不接受项目AI将`tr_syn_revival_feature_flag`的regression归为“预存在问题”而忽略的结论，除非证明该问题确由comparator缺陷造成而非shadow语义真实缺陷。为此下达七项指令：①核对fixture数量与身份，确保此前要求新增的3个C1.1 fixture实际存在且全量PASS，不得仅报“19/19”；②冻结comparator问题证据；③对comparator“缺少COEXISTS感知”做逐checkpoint证明，明确当前comparator误判具体内容、与gold/diff spec不一致之处、COEXISTS/CONTESTS/SUPERCEDES各自应如何影响指标、修复后是否影响其他case、R01实际执行与bundle安全行为；④修复comparator须是评测基础设施修复，不得弱化门槛，必须显式关系感知并形成版本化contract与影响分析；⑤修复后必须在同一新comparator下重建canonical development baseline（pre-fix与post-fix均重跑）；⑥修复后仅允许跑fixture和development，不得重跑regression；⑦下一轮仅允许`blocked`或`regression_rerun_ready`，后者须满足全部条件（fixture完整、comparator语义版本化且双向、baseline重建、development无blocker/无unexplained/ordinary regression为零、R01实际安全验证、must_include达标、critical false invalidation为零、未访问adversarial/holdout等）。

项目AI完成执行：提交fixture reconciliation报告，确认新增3个C1.1 fixture（`lc_same_key_different_source_r01`、`lc_parallel_targets_same_dimension_must_coexist`、`lc_state_value_vs_real_scope_ambiguity`），总fixture数达22个，全部PASS且确定性通过；冻结comparator failure证据；根因审计确认`compare_step`在`2d24e01`版本被简化后失去对CONTESTS关系的感知——当shadow因不同来源产生CONTESTS时，comparator将较旧claim视为superseded，误报false-negative invalidation和unexpected-active-set regression，而shadow的relation/state本身正确；提交comparator COEXISTS contract（含真值表与语义规范）；但尝试添加CONTESTS-aware逻辑后导致其他case的`unexpected_supersedes`分类发生变化，需要更精细的真值表实现方可修复，因此当前未完成canonical baseline重建。最终development split结果为6个case PASS，`tr_syn_revival_feature_flag`仍BLOCK（2个regressions），无blocker，must_include_recall=1.0。结论仍为`blocked`：所有交付物（冻结、inventory、contract）已完成，唯一未解决的是comparator的relation-aware修复与canonical baseline重建，需单独comparator修复pass方可推进。
## Stage04-C1.2.1 Relation-Aware Comparator修复与基线重建完成：7个ordinary regressions源于adjudicator缺陷，仍为blocked

评审AI下达指令要求进入comparator修复阶段，明确不得采用“将CONTESTS claim全部恢复active”的粗粒度逻辑，须实现以claim对、关系类型、gold预期及active-state共同判断的精细真值表，并区分comparator defect、shadow semantics defect、gold defect三种可能；补交独立根因审计报告，新增至少6个comparator单元测试用例，完成影响面分析，修复后在同一新comparator下重建canonical pre-fix与post-fix baseline，运行范围仅限unit tests、全量22个fixture、determinism验证及development replay，不得触碰regression/adversarial/blind holdout。下一轮仅允许blocked或regression_rerun_ready，后者须满足所有条件：独立root-cause audit完成、comparator真值表机械实现且unit cases通过、不弱化双向检查、baseline重建、全量fixture PASS且确定性、development无blocker/unexplained/ordinary regression、tr_syn_revival_feature_flag的CONTESTS与R01行为被正确评估而非自动放行、must_include recall达标、critical false invalidation为零、未访问后续split。

项目AI-agnes2.0-flash完成全部指令：提交独立根因审计报告，确认tr_syn_revival_feature_flag两个regression的根因；在benchmark_shadow_runner.py中实现compare_step()与_classify_relation_diff()，引入关系感知真值表，显式处理SUPERCEDES/COEXISTS/CONTESTS匹配与不匹配情形；新增6个comparator unit test cases全部PASS；提交影响面分析报告，列明变更前后分类变化及语义依据；使用同一新comparator重跑canonical pre-fix与post-fix development baseline，产出基线JSON与对比报告。运行结果：comparator unit tests 6/6 PASS，22个fixture全部PASS且确定性，development blockers=0、unexplained=0，但ordinary regressions为7个（其中6个来自tr_full_tkt_005b，1个来自tr_syn_revival_feature_flag），manual_adjudication为3个（tr_syn_revival_feature_flag的CONTESTS被正确分类为manual而非自动放行），must_include recall=1.0，critical false invalidation=0。核心改进在于comparator v2将provenance冲突的CONTESTS与gold SUPERCEDES差异准确标记为manual_adjudication，符合R01精神。结论仍为blocked，下一步须修复shadow adjudicator的_determine_relation()中CONTESTS over-match问题——不同来源但时间顺序正确的事件应产生SUPERCEDES而非CONTESTS，此修复超出comparator层面，属shadow语义层缺陷。
## Comparator违规分类回退与真实缺陷归因：gate仍为blocked

军师AI确认当前状态为blocked，指出项目AI此前将`gold=SUPERCEDES`与`shadow=CONTESTS`的关系不匹配改判为`manual_adjudication`的做法违规——R01仅约束bundle安全处置，不改变benchmark relation判分，`CONTESTS`不能自动通过gold的`SUPERCEDES`，不得以`manual_adjudication`替代ordinary regression。为此指令：冻结不合规comparator证据；进行policy violation audit，逐checkpoint审计`tr_syn_revival_feature_flag`中全部`CONTESTS`差异，明确为何`SUPERCEDES→CONTESTS`不能因R01安全执行而成为relation match；回退不合规的relation分类，保留安全审计能力但恢复强制规则（gold SUPERCEDES + shadow CONTESTS计为ordinary regression或blocker，仅允许将safety_disposition作为附加字段而不覆盖relation分类）；修正comparator-only测试，使其独立断言relation分类与bundle安全处置；对`tr_full_tkt_005b`的6个regression逐条进行真实triage，不得笼统归因为“cascading effects”；重跑范围限于unit tests、全量22个fixture、determinism及development replay，不得触碰后续split。下一轮仅允许`blocked`或`regression_rerun_ready`，后者须满足：违规自动降级移除、R01安全处置与relation scoring分离、comparator测试证明relation mismatch仍完整计分、双向检查未被弱化、`tr_syn_revival_feature_flag`的relation mismatch如实计分或被修复、`tr_full_tkt_005b`的6条regression逐条归因、全量fixture PASS且确定性、development无blocker/unexplained/ordinary regression、must_include recall达标、critical false invalidation为零、未扩大R01、未访问后续split。

项目AI完成执行：冻结不合规证据；提交policy violation audit，确认`SUPERCEDES gold + CONTESTS shadow`被错误归为`manual_adjudication`掩盖了2个legitimate regression，单元测试验证的是较弱性质而非required性质，R01安全执行不覆盖relation评分；回退comparator，将`_classify_relation_diff`中该情形改回`ordinary_regression`，`compare_step`为CONTESTS差异附加`safety_disposition`与`manual_review_metadata`作为不覆盖relation分类的附加字段，保留CONTESTS检测、R01 bundle安全审计、conflict marker、quarantine检查；更新comparator-only测试为8个（含6个新+2个正向基线），全部PASS，独立断言relation分类与bundle安全处置；对`tr_full_tkt_005b`的6个regression逐条归因，根因均为shadow_compiler的fan-out缺陷（向所有先前claims创建SUPERCEDES边而非仅直接前驱）。重跑结果：unit tests 8/8 PASS，22个fixture全部PASS且确定性，development replay仍为7个ordinary regressions（源于shadow adjudicator/compiler缺陷，非comparator缺陷）。最终gate仍为`blocked`，comparator回退正确完成，当前blocked状态由shadow语义层缺陷导致，下一步需修复shadow adjudicator的CONTESTS over-match与shadow compiler的fan-out边构建，方可达到`regression_rerun_ready`。
## Stage04-C1.2.3 Shadow Relation/Compiler最小修复：adjudicator与compiler缺陷修复完成，gate仍为blocked

评审AI确认当前gate仍为blocked，本轮目标转向修复真实shadow语义缺陷（不同来源不应自动CONTESTS、compiler fan-out），而非再调整comparator、扩大R01或重分类diff。继续禁止regression/adversarial/holdout及所有正式主链修改。指令要求：冻结C1.2.2失败基线；对7个ordinary regression逐条根因归因（仅限adjudication_relation/predecessor_selection/compiler_edge_emission/time_ordering/claim_atomization/scope_normalization/entity_resolution/lifecycle_resolution/shadow_compiler/unresolved八类，不得使用“cascading effect”）；修复不同来源默认CONTESTS规则，更新decision contract明确同一atomic claim/scope/lifecycle且存在后续状态推进时为SUPERCEDES候选，不同atomic claim或scope为COEXISTS，真正无法消解时才CONTESTS/quarantine；修复compiler fan-out，要求对同一adjudication stream只向正确的直接前驱发出SUPERCEDES边，不得向所有历史claim扇出，若不存在唯一前驱则COEXISTS/CONTESTS/quarantine；新增至少4个fixture覆盖不同来源时序推进、真实冲突、三步顺序仅前驱、多流不扇出；修复后运行范围限于comparator unit tests、全量22个旧fixture+新增fixture、两次determinism回放、pre-fix与post-fix development replay逐case对照。下一轮仅允许blocked或regression_rerun_ready，后者须满足：7条regression均已归因、不同源不自动CONTESTS、predecessor selection机械可审计且无fan-out、全量fixture PASS且deterministic、comparator评分与R01安全处置分离、development无blocker/unexplained/ordinary regression、must_include recall达标、critical false invalidation为零、quarantine非规避手段、未访问后续split。

项目AI-agnes-2.0-flash完成全部8个步骤：冻结失败基线；逐条归因7个ordinary regression（6个源于compiler fan-out向所有先前claim发出SUPERCEDES边，1个源于不同源自动CONTESTS）；修复adjudication规则，将不同源自动CONTESTS改为按atomic claim、scope、时序推进证据序列判定；实现predecessor selection contract，规定仅向同一adjudication_key、兼容scope、兼容atomic predicate、时序前驱且唯一的直接前驱发出边，不存在唯一前驱时走COEXISTS/CONTESTS/quarantine；新增4个fixture（lc_different_source_chronological_progression_supersedes、lc_different_source_true_conflict_contests、lc_three_step_same_key_immediate_predecessor_only、lc_multi_claim_stream_no_fanout_to_unrelated_predecessors）。修复后测试结果：comparator unit tests 8/8 PASS；26个fixture中23 PASS、3 BLOCK（lc_diff_source_conflict、lc_provenance_conflict、lc_same_key_different_source_r01，因修正后不同源不再自动CONTESTS，预期结果需更新），全部deterministic；development replay仍为7个ordinary regressions（6个结构性不匹配+1个级联效应），must_include recall=1.0，critical false invalidation=0，quarantine未被用作规避手段。gate仍为blocked，因ordinary regressions未清零，但shadow adjudicator/compiler修正本身正确完整。下一步须更新3个BLOCK fixture预期结果并解决gold与shadow模型之间的结构性不匹配，方可进入regression_rerun_ready。
## 价值重审与路线转向：冻结lifecycle复杂扩张，立即启动真实Shadow Mode

用户在与另一位AI（Qwen-Plus-3.7）的讨论中表达了对当前实施是否过度工程化、项目是否真正值得做的深度担忧。Qwen指出ContextLedger的核心价值确实存在——解决长程Agent中“旧事实污染”问题（RAG只能解决“像不像”，解决不了“还算不算数”），技术定位有辨识度且壁垒高；但当前已陷入“验证地狱”——围绕hash、baseline、preflight、fixture的验证流程膨胀，挤压了验证产品价值的真实工作，建议立即停止benchmark拉扯，降级到V0简单模型后直接切入Shadow Mode真实验证。

军师AI-Terra作出最终裁决，核心判断为：Qwen说对了一半——项目价值判断基本正确，验证流程也确实出现边际收益递减，但“立刻停止benchmark直接shadow mode”的建议需要修正：**应立刻启动真实Shadow Mode，但不应把尚未验证的lifecycle语义接入任何会影响Agent行为的路径。** 即真实使用现在开始，主链接管不能现在开始。

Terra逐项划定边界：不可砍的底线包括raw/patch不可改写、shadow与主图隔离、must_include不得漏掉、benchmark/gold不得事后修改——这些是ContextLedger作为状态层最基本的安全边界；应立即收缩的是过度细密的git/preflight叙述、为每个synthetic diff扩张新fixture/规则/报告、在没有真实任务收益证据前继续细化lifecycle/双时态/来源裁定等。当前已暴露关键事实：lifecycle/CONTESTS/predecessor selection的语义复杂度正在吞噬大量轮次，但尚未证明其相对简单V0能带来真实下游收益，这就是收缩信号。

Terra提出“双轨但主次分明”的新路线：

**轨道A**——立即启动真实Shadow Mode（接入OpenCode主会话链，只读监听、记录真实事件、生成shadow graph/bundle，不注入Agent正式上下文，不修改正式graph_state，不影响Agent行动），目标是收集真实证据：Agent实际引用了多少废弃约束、CL-V0能否识别、CL bundle是否减少错误动作、复杂案例在真实任务中占比多少，以此决定是否继续投资复杂schema。

**轨道B**——冻结复杂lifecycle扩张，当前shadow语义修复只修复已发现明确缺陷，不新增抽象层，不再为纯合成边界案例持续扩schema，让真实trace决定下一条fixture，而非让fixture不断制造下一轮开发。

MVP重新定义为：**在真实长程任务中，可靠地避免Agent继续执行已被明确废弃/替代/取消的关键约束**。建议采用更保守的CL-V0 Live Shadow——只处理用户明确的替换/取消/废弃指令、同一明确实体同一明确范围内的后续状态、must_include关键约束、可直接追溯的ToolResult/FileArtifact状态；暂不自动处理多来源冲突裁定、模糊alias合并、生命周期自动切分、effective_at回溯排序、复杂partial/conditional推理；不确定情况标为conflict/unresolved，不进入正式动作路径。

关于“是否值得做”的真实答案：**值得继续做，但还不值得无限投入**——价值目前是强假设而非已证明的产品事实，尚未证明在真实Agent中比“短摘要+显式任务文件+简单最后写入优先”显著更好。项目应停止问“怎样把lifecycle做到完美”，改问“在真实任务里CL-V0/CL-V1究竟减少多少错误动作，是否足以证明继续建设复杂状态语义正确”。

建议设8个执行轮的产品证据冲刺：第1-2轮接入只读Shadow Mode；第3-5轮收集真实长程任务trace并建立错误案例台账；第6轮用CL-V0、当前shadow lifecycle、full-history做离线对照；第7轮评估真实收益（废案引用、关键约束遗漏、错误工具动作、token成本）；第8轮做路线裁决——若CL-V0已明显减少错误则优先最小主链接入、complex lifecycle延后；若lifecycle在真实trace中确实频繁解决V0无法处理的问题则继续Phase 1；若真实任务中几乎没有收益则停止扩张、降级定位。

**最终结论**：不在“继续严苛验证”和“直接上线使用”之间二选一，正确路线是——停止把synthetic benchmark当成唯一战场，立刻以只读Shadow Mode进入真实环境，同时把lifecycle复杂度冻结在当前范围，只修复阻断真实价值验证的缺陷。Terra的严格门禁继续保护“不可污染主图”边界，但项目优先级必须由**真实Agent是否少犯错**决定，不再由synthetic fixture是否无限趋近完美决定。

## 战略转向：冻结Stage04复杂语义修复，启动Stage05真实Shadow Mode价值验证

用户在与另一位AI讨论后向军师AI呈现了"过度工程化担忧"及"项目是否值得做"的根本性质疑。军师AI-GPT-5.6-Sol作出最终战略裁决：**ContextLedger值得继续，但必须立即从"语义机制证明项目"转为"真实产品价值验证项目"**——项目已证明机械闭环可回放可隔离可审计、"当前状态"确实不同于普通记忆检索、复杂生命周期语义成本远高于预期，但尚未证明在真实长程Agent任务中能以可接受成本显著减少废弃约束引用和错误动作。Terra此前的路线转向被确认为当前最正确判断：立即启动真实只读Shadow Mode，同时冻结lifecycle复杂度扩张。

工程治理层面：raw/history不可改写、shadow不污染主图、benchmark/gold不得事后修改、must_include与critical false invalidation为安全红线、运行可追溯、LLM不直接分配sequence或决定active状态——这些必须保留。但语义工程已出现明显过度投资：项目反复陷入comparator修改、fixture预期与实现互相追逐、provenance conflict语义拉扯、COEXISTS/CONTESTS/SUPERCEDES分类变化、scope从claim ID推断后修复、compiler fan-out修复、R01与relation scoring边界争议，大量规则由synthetic benchmark局部差异推动而非真实任务需求驱动，极可能形成"非常可审计、非常复杂，但未必真正帮助Agent"的系统。当前lifecycle kernel不应进入任何影响Agent行为的路径，但也不应删除——它已形成有价值的V1实验候选。

建议将项目拆分为三个层级：Level 0真实事件采集层——只负责监听OpenCode主会话、记录不可改写trace、不做任何上下文注入，必须尽快进入真实环境；Level 1 CL-V0保守状态层——只处理用户明确"取消/废弃/改为/替换为"、同一明确对象同一明确scope、明确前后状态推进、可追踪ToolResult/FileArtifact、明确must_include约束，不确定时输出unresolved/conflict不自动失效旧状态，暂不处理模糊alias自动合并、多来源可信度裁决、自动lifecycle切分、effective_at回溯重排、partial/conditional DSL、跨channel自动替代、复杂revival推理；Level 2当前lifecycle V1实验层——保留现有语义但只能离线运行作为实验组，不得注入Agent上下文、写正式graph_state、修改patch ledger、决定Agent行动或因synthetic fixture失败继续无限扩张schema。

立即终止的工作：继续Stage04-C1.x式synthetic修复循环、为每个comparator diff增加新抽象、更新BLOCK fixture预期、再次运行regression/adversarial/holdout、扩大R01包装普通regression、继续优化provenance conflict、自动effective_at回溯、当前lifecycle接入正式assembler、MemoryPack、子Agent多宿主跨项目同步。当前失败证据应冻结为known semantic debt，而非必须在进入真实Shadow Mode前清零的阻断项。

建立新阶段Stage05 Live Shadow Evidence Sprint，唯一目标为在不影响Agent行为前提下测量ContextLedger真实长程任务中的实际价值。代码策略：给当前状态创建不可变标签`stage04-lifecycle-experimental-freeze`并生成冻结报告，从最新稳定main创建`stage05-live-shadow-v0`，只择取必要组件（事件日志、run-scoped隔离输出、hash/版本指纹最小实现、只读OpenCode wrapper、离线bundle生成器），不将整个Stage04评审基础设施全部带入。

CL-V0定义：最小事件结构含event_id、task_id、turn_id、observed_at、source、event_type、subject_ref、predicate、scope、value、authority、evidence_span，采用保守状态键`state_key = subject_ref + predicate + explicit_scope`。允许自动supersede仅当新旧声明来自同一可追踪对象且predicate/scope相同、后一声明含明确替换/取消/状态推进语义、无alias歧义、无并行目标、无需推断来源优先级或缺失effective_at，否则输出unresolved/conflict/coexist且不静默杀死旧状态。时间规则暂用observed_at决定顺序，迟到事件不自动重写旧派生，迟到且可能改变当前态时标记late_unresolved。bundle生成CURRENT_HIGH_CONFIDENCE与CONFLICTS_AND_UNRESOLVED两部分，不将unresolved混入可执行指令区。

真实Shadow Mode须记录原始轨迹、真实风险事件（需求修改、取消操作、文件/工具结果使旧判断失效、Agent引用旧约束/采取错误动作/遗漏关键约束/自我纠正/人工介入），对同一条trace离线生成四组输出（宿主原始上下文、简单基线、CL-V0、当前lifecycle V1），并对错误或高风险checkpoint做反事实评估。

产品指标重新排序：一级指标为真实错误动作（stale-action rate、critical stale-action prevention、critical false suppression、must-include miss）；二级指标为上下文质量（stale-context leakage、irrelevant-context ratio、current-state retrieval recall、conflict visibility、token cost、bundle延迟、人工纠正次数、Agent自我回滚次数）；三级指标为状态内核指标（invalidation P/R、active-set F1、resolver abstain rate、quarantine rate、relation accuracy）——三级指标服务于一级，不能替代一级。

8轮执行计划：第1轮冻结Stage04 experimental tag及known-debt清单并明确V1禁止接管；第2轮实现OpenCode只读监听与V0/V1离线编译及shadow bundle生成，确保不注入上下文、不修改正式状态、监听失败不影响宿主；第3轮运行最小canary验证事件不漏、session/task边界正确、文件与工具事件可关联、bundle稳定生成且对宿主零副作用；第4-5轮收集真实任务（优先需求多次修改、多轮编码测试回滚、异步工具结果改变判断、文件路径/API方案被替换、用户取消原计划改方向、多并行目标）；第6轮建立真实错误案例台账；第7轮四方案对照（full history、简单基线、CL-V0、V1）；第8轮路线裁决。

路线裁决三分类：若V0已有明显收益则优先最小主链接入（只注入高置信度must_include，unresolved不作为指令，保留宿主原始上下文，可一键关闭，先canary再扩大），复杂lifecycle继续冻结；若V1在真实任务中显著补足V0（同实体多lifecycle、revival、late arrival、provenance conflict、parallel target、partial/conditional频繁出现且V1确实减少错误）则继续投入；若V0与V1均无明显收益则停止扩张，降级为显式任务状态文件、变更日志、must_include管理器、简单stale-warning工具。

预注册门槛：最低证据量为15-20个真实长程任务、30个以上明确状态变更、10个以上存在潜在旧事实污染的checkpoint。CL-V0值得继续的条件为相比full history废弃信息错误动作下降明显或相比简单基线在相同token下捕获更多关键替换或显著减少人工纠正/回滚或提前标记多数高风险stale-reference checkpoint，同时critical false suppression为零、must_include不低于简单基线、unresolved不包装为确定事实、token/延迟可接受。恢复复杂lifecycle投资的条件仅当V0无法解决的lifecycle类问题占剩余错误显著比例、当前V1有额外收益且无更多关键误失效、问题不能通过更简单显式任务状态结构解决。

现有资产处理：保留可回放patch模型、quarantine/abstain、shadow隔离框架、diff/状态检查工具、fixture runner、provenance与invalidation分离原则、must_include安全设计、当前lifecycle kernel、已冻结benchmark、已发现的late arrival/scope/fan-out故障案例；synthetic benchmark从产品主战场降级为regression harness，lifecycle RFC从"下一步必须完成"降级为实验候选设计，relation accuracy从核心指标降级为诊断指标，hash/preflight报告保留必要自动化不再每轮手写长篇叙述；后续用`shadowctl verify/run-live/compare/report`单命令完成，不再让项目AI手工证明文件状态、hash一致性、worktree干净、目录隔离。

下一步最优指令：冻结Stage04 lifecycle实验分支及全部失败证据，停止修复synthetic comparator/fixture差异；创建Stage05 Live Shadow V0分支，实现OpenCode主会话只读事件监听、不可改写trace、CL-V0保守状态编译、lifecycle V1离线对照、shadow bundle生成和真实错误案例台账；shadow输出不得注入Agent上下文、修改正式graph/patch ledger或宿主行为；CL-V0仅处理明确替换/取消/废弃、同对象同scope顺序推进和可追踪ToolResult/FileArtifact，模糊alias/多来源冲突/late effective-time/partial/conditional/自动lifecycle切分全部标为unresolved不自动失效；下一阶段不以fixture全通过为目标，而以完成真实trace采集和四方案离线对照为目标；先交付Live Shadow contract、event schema、V0 decision table、OpenCode只读接入、零副作用canary报告及真实案例ledger模板；只有真实trace暴露的新错误模式才允许新增fixture；lifecycle V1继续保持实验状态，不得申请主链接管。

**最终结论**：项目值得继续但必须设置投资上限和证据期限。最大风险已不是技术做不出来，而是在尚未证明真实价值前把一个可用的"防止旧事实污染"产品建设成需要解释完整世界语义的复杂状态逻辑系统。正确动作是冻结当前复杂语义、保留不可污染/不可改写/must_include安全底线、立即启动真实只读Shadow Mode、用CL-V0/简单基线与V1对照真实任务、让Agent是否少犯错决定项目路线——这是当前信息增益最高、成本最低、也最有可能将优秀工程实验转化为真实产品的路径。
## 优先自动化现有手工压缩流程，暂停ContextLedger复杂语义开发

军师AI-GPT-5.6-Sol给出明确判断：**优先执行第二种方案，把现有“双层压缩流程”自动化；暂停ContextLedger复杂语义开发。**

核心原因：第二种方案已被用户真实使用验证过，痛点明确（手工复制粘贴+压缩费劲），自动化后能很快投入自用；ContextLedger当前最大问题不是代码，而是语义边界无法收口，继续简改也容易重新陷入lifecycle、冲突裁决等复杂问题；用户原始目标本就是“先好用再考虑商品化”，第二种方案更符合这一目标。

建议做成极简工具：通过浏览器扩展、用户脚本或复制快捷键采集当前轮对话（不必直接跨进程控制网页），自动保存原文，自动生成“二级标题+简要总结”，累积到一定数量后自动分类并生成分类摘要，使用时按当前问题检索相关分类及原始摘要，始终保留原文链接以便回溯。ContextLedger不必全部丢弃，只保留三个简单能力：原文不可覆盖、摘要可重新生成、明确标记“已废弃/已替换”的内容并在检索时默认排除。不再做lifecycle、复杂provenance、双时态和通用冲突裁决。

最终结论：先自动化已在用但很麻烦的工作流；将ContextLedger降级为其中一个极简的“废弃信息过滤”功能，而非继续作为完整状态系统开发。
## 用户方案确认：将现有架构改造为个人知识上下文工作台，停止复杂语义工程，以使用体验驱动价值判断

用户提出新方向：不废弃现有基础架构但停止复杂语义工程和只读Shadow Mode，改造为纯自用目的，价值由个人使用体验主观判断不做定量评测；确保三项流程均可脚本自动执行——①原始网页对话保存→双层压缩→候选背景信息，②原始对话保存→TaskGraph图管理（可选）→候选背景信息，③原始对话保存→MemoryPack（可选）→候选背景信息；三种方式可单独或结合使用，由实际需求和效果决定；各自形成独立候选背景信息，既可提供给网页大模型也可提供给智能体，实现一料多用。

军师AI-GPT-5.6-Sol完全认可该方向，认为比继续推进复杂lifecycle和benchmark更符合真实目标，但建议关键架构调整：不建设三条重复流程，而是建设“统一采集层+三个可插拔处理器”——网页对话经统一采集脚本存入不可修改原始对话文件，分别通过双层压缩处理器、TaskGraph处理器（可选）、MemoryPack处理器（可选）加工，统一输出格式后供网页大模型/Agent/API使用。保留原则包括原始对话只保存不覆盖、所有摘要可重新生成；每份候选背景信息附带原始引用、生成方式、时间、模型/提示词版本、主题会话信息；三种方式可单独或组合但输出统一格式；不做复杂语义裁决和benchmark，以长期使用体验决定价值；当前不追求商品化架构，只追求每天愿意使用并比复制粘贴省事。

网页对话采集建议优先顺序：浏览器扩展或用户脚本（一键采集）> 平台自带导出接口 > 剪贴板复制后本地脚本自动接收 > Playwright等自动控制方案；不要一开始做复杂跨进程自动化，即使需点击一次“保存当前会话”，只要后续压缩、分类、生成全部自动完成就已足够。三类候选背景定位：双层压缩为默认主方案优先完成；TaskGraph适合需求变更、任务依赖、实现过程和决策记录；MemoryPack适合跨会话跨任务复用，保持可选；组合模式由统一装配器按需选择，避免无序拼接。

**最终结论**：批准该方向，停止复杂语义工程，把现有基础架构改造成个人知识上下文工作台——一次采集、多路加工、统一输出、一料多用；先把双层压缩端到端做通，再按实际需要启用TaskGraph和MemoryPack。
## 网页对话采集脚本设计方案：Chrome扩展+Python本地程序，一键完成采集与一级压缩

军师AI建议采用**Chrome扩展采集网页对话+Python本地程序处理文件与LLM调用**的方案，扩展负责读取DOM提取对话内容，通过Native Messaging将数据交给本地程序，后者负责追加写入文件、调用LLM、去重、失败重试，避免扩展直接管理硬盘文件。

整体结构：用户点击扩展按钮或快捷键 → Chrome扩展识别网站、提取最新一轮用户问题与模型回答并清理格式 → 发送给Python本地程序 → 本地程序检查重复、追加保存原始对话、调用指定LLM做一级压缩、追加保存压缩结果、返回状态。

文件结构建议为每个项目独立目录，包含`conversation.md`（原始对话全量）、`turns.jsonl`（结构化原始记录）、`level1.md`（每轮一级压缩）、`level2.md`（手动触发二次分类）、`capture.sqlite`（防止重复）和`failed_jobs.jsonl`（LLM失败重试队列），原始对话与压缩结果分开保存。

一键操作准确流程：先提取最新完整轮次（含用户消息、模型回答、网页标题、URL、会话ID、采集时间），若模型仍在输出则提示暂不采集；生成turn ID（SHA256组合字段）防重，若已存在则提示不追加；无论LLM是否成功先追加保存原始对话（Markdown格式，含来源、页面、URL、Turn ID及对话原文），使用追加模式打开文件并立即刷新落盘；调用LLM按固定规则做一级压缩（二级标题、保留目标/判断/决定/下一步、删除寒暄与重复、不增信息、未决标记、第三人称、长度10%-25%、纯Markdown无前言），结果追加到`level1.md`并附带来源Turn、生成时间、模型及Prompt版本；显示操作结果，若LLM失败则原始已保存并进入重试队列。

网页采集采用“站点适配器”模式，每个网站独立adapter统一输出标准化JSON，第一版只支持最常用的一两个网站。扩展弹窗仅保留项目选择、文件路径、一级压缩开关及规则版本选择，并提供快捷键（如Ctrl+Shift+S），配置保存在`chrome.storage`中。

二次压缩不作为默认一键流程，由用户单独触发，允许指定处理范围（全部或新增）和自定义分类要求，输出以版本化方式追加到`level2/`目录，不覆盖旧版本。

第一版仅实现“一键提取当前轮次→原文追加落盘→调用LLM→一级压缩追加落盘”，暂不接入TaskGraph、MemoryPack、lifecycle、语义冲突裁决、自动失效判断、自动注入背景或持续监听。

推荐实施顺序：先完成Python本地程序并用测试JSON验证追加/去重/压缩 → 实现第一个网页adapter → 实现Chrome扩展按钮与快捷键 → 接入Native Messaging → 增加项目选择与配置 → 增加失败重试 → 实现用户触发的二次压缩 → 实际使用后再决定是否接入TaskGraph或MemoryPack。

**最终设计原则**：原文先落盘再压缩，所有文件只追加不覆盖，turn ID防重，一级压缩自动一键完成，二级压缩由用户明确触发，避免重新陷入复杂语义工程。
## 取消浏览器插件，改用纯本地剪贴板工具以降低投入

用户提出疑问：能否省掉浏览器插件环节？认为插件仅解决“少一次复制粘贴”却引入大量维护成本（Manifest V3、DOM适配、Native Messaging、注册表安装等），投入产出比偏低。

军师AI-GPT-5.6-Sol明确同意，建议直接取消浏览器插件，改为纯本地工具方案：用户从网页复制对话后，运行本地脚本或按全局快捷键，程序读取剪贴板内容，预览并选择项目，原文追加保存，调用LLM整理格式并做一级压缩，压缩结果追加落盘。第一版可只提供命令行工具或简单托盘程序，后续消除文件创建、格式整理、追加、防重和LLM调用等主要劳动。

采集粒度可放宽，程序接受单轮、多轮或任意网页内容，先作为不可改写原始块追加，再由LLM识别角色、整理Markdown、拆分轮次并生成压缩；若自动识别不可靠则保留原文并标记`needs_review`，不阻塞保存。

架构调整：删除整个`chrome_extension/`、Native Messaging协议及相关注册、站点adapter、DOM转换和流式检测；保留项目配置、剪贴板/文件输入、只追加存储、turn/capture ID防重、LLM一级压缩、失败重试、用户触发的二次压缩及未来TaskGraph/MemoryPack接口。代码量从约1,300-2,100行降至500-900行，显著减少维护成本。

新实施顺序：①Python只追加存储；②剪贴板和文本文件导入；③一级压缩及失败重试；④简单CLI；⑤按需增加桌面/托盘界面；⑥二次压缩；⑦实际使用后再评估是否恢复插件。

最终结论：取消浏览器插件，将“自动采集”降级为“复制后按一次快捷键处理”，把核心价值聚焦于自动保存、只追加、防重、整理、压缩和形成可复用背景，网页DOM提取仅为锦上添花，不应成为主要投入方向。
## 剪贴板方案的解耦边界澄清：通道解耦成立，但格式与元数据仍需统一处理

用户提出观点：剪贴板方案下，脚本读取Windows系统级剪贴板，完全与内容来源解耦——无论内容来自网页版大模型、桌面客户端、终端智能体输出还是IDE插件对话窗口，脚本无需知道来源，这是放弃浏览器插件后的最大收益。

Claude-Sonnet-5确认方向正确，但指出需区分两个层面：

**对的部分**——采集通道确实解耦了：剪贴板是系统级公共层，任何能“复制文本”的程序都天然支持，脚本只需依赖读取剪贴板文本，无需DOM适配器、无需API集成、无需为每个来源单独开发，这正是放弃浏览器插件后的最大收益——用一个通用极简输入层替代了原来需要为每个网站单独维护的适配器。

**需要注意的部分**——剪贴板方案只是“通道”解耦，不是“格式”解耦。三个实际差异会暴露：第一，内容结构不统一——不同来源复制出的文本结构差异很大（是否带角色标签、代码块围栏保留与否、缩进丢失、有无工具调用日志等），这些差异需依赖架构中的LLM格式整理环节吸收，剪贴板只负责搬运字符串，不负责理解结构；第二，来源元数据默默丢失——剪贴板不记录内容来自哪个网站、会话、时间点，解耦的代价是自动溯源能力被牺牲，只能靠手动添加备注补偿；第三，单缓冲区限制——剪贴板任一时刻只有一份内容，中途复制其他内容会覆盖要采集的内容，虽对“复制—立刻处理”节奏影响不大，但操作被打断时需重新复制。

**更准确表述**：剪贴板方案解耦的是“采集方式”，不是“内容语义”——不再需要为每个来源写适配器，但仍需要一个统一的、能兼容多种输入风格的格式整理层（即`Level1Processor`）来吸收差异；来源信息缺失是主动接受的代价，换来的是极简和通用性。这一权衡在“自用、先验证价值”阶段完全合理。
## 桌面工作台设计调整：从“确认后自动执行”升级为“用户配置处理计划的常驻工作台”

用户已完成初步桌面工具实现，双击图标读取剪贴板内容并显示确认窗口，但现有流程存在局限：用户无法指定保存区域（不同内容需存不同位置）、无法选择压缩范围（单轮或多轮）、无法在自动流程中触发二次压缩且二次压缩需要自定义要求、也无法让程序常驻后台并由用户主动决定处理节奏。为此提出设计调整需求，希望在一个图形界面下让用户灵活配置各项执行选项（保存区域、压缩范围、压缩规则等）后再执行，并可选择预设规则组合。

军师AI-GPT-5.6-Sol判定这是一次合理且必要的设计调整，建议将交互模型从“确认后自动执行固定流水线”升级为“长期打开的上下文处理工作台”——用户决定处理什么、保存到哪里、执行哪些处理及采用什么规则，保留现有CLI、存储、去重和压缩能力作为后端，新增GUI编排层而不重写核心代码。

新交互流程：双击快捷方式启动主窗口并保持打开，不自动读取剪贴板；用户复制内容后点击“读取剪贴板”预览，再选择保存区域（预配置项目workspace）、一级压缩范围（全部/当前选中/不压缩）、是否执行一级压缩及规则（版本化Prompt Profile）、可选来源备注，点击“开始处理”后台执行并显示结果，窗口继续等待下次操作。删除自动超时放弃功能。

界面设计为四个标签页：①采集与一级压缩——日常主页面，含保存区域下拉菜单（预设项目，可管理）、剪贴板预览区（允许编辑后再保存）、压缩范围选择（全部/当前选中/不执行）、规则profile选择及补充要求输入框，原文保存始终强制开启；②二次压缩——独立页面，针对已积累的多条一级压缩，可选择全部/上次之后新增/手工选择来源，应用二次压缩规则和自定义要求，输出版本化不覆盖；③历史与重试——查看历史记录、失败状态及重试；④设置——管理项目workspace、Prompt Profile、默认预设等。

GUI不直接实现业务逻辑，只构造`CapturePlan`对象（含项目、来源备注、原始文本、保存/整理/压缩开关、处理范围、profile ID、补充要求）并调用现有`CapturePipeline`服务，通过后台工作线程避免LLM调用阻塞界面。建议增加处理预设（项目+压缩规则+备注等组合）、执行前计划摘要、剪贴板变化保护（只读不自动更新）、最近结果快速打开产物等实用功能。

技术选型：继续使用Tkinter/ttk，通过单实例机制防止重复启动，最小化时保持运行而非退出。实施分五个里程碑：主窗口骨架→采集与一级压缩→二次压缩→历史/重试/设置→自用验收。此次改造定义为v0.2.0 GUI Workbench，需先批准架构变更再实施，确保不重新陷入复杂语义工程。
## 核心判断：新想法成立——从“Agent记忆基础设施”转向“用户侧AI上下文控制层”

军师AI-GPT-5.6-Sol判定用户提出的“上下文装配器”想法成立，且并非突发转向，而是此前所有探索（双层压缩、TaskGraph、MemoryPack、Assembler）自然汇聚出的产品外壳。用户真正需要的可能不是“记忆系统”，而是“决定这一次让AI知道什么”的能力。该产品应定位为**用户拥有的、跨AI的上下文控制层**，而非单纯的压缩器或记忆库。

---

**一、产品本质：出售的不是记忆，而是“知情范围控制权”**

普通用户面临三个问题：AI不知情、知道太多混入旧信息、无法准确控制AI应知道什么。新产品解决的是用户根据当前目的，从历史材料中生成适合本次任务的、可检查可修改可携带的上下文包。其核心模块称为**Context Assembler（上下文装配器）**，最终产物为**Context Bundle/Context Brief**。

---

**二、与原有ContextLedger的关系：重新安排主次，不推翻原有架构**

原架构以TaskGraph为权威核心，新产品应将架构调整为：统一原始资料库 → 多个可选处理器（一次压缩、二次压缩、TaskGraph、MemoryPack、原文检索）→ 候选上下文块 → Context Assembler → 可检查可编辑可导出的Context Bundle → 任意网页AI/桌面AI/IDE Agent/API Agent。双层压缩、TaskGraph、MemoryPack均退化为用户可选的高级处理器，Assembler成为用户侧产品中心。

---

**三、交互设计：用户选择使用目的，而非直接选择技术机制**

不应让普通用户直接选择一次压缩、TaskGraph等技术选项。应提供两层选择：

**第一层：使用目的预设**
- 快速了解（项目简介、目标、背景、进展）
- 继续当前任务（当前目标、硬约束、已完成事项、当前状态、有效决策、下一步、未决问题、必须避免的旧方案）——优先使用TaskGraph
- 深度接手（总体背景、演化过程、决策及原因、失败尝试、用户偏好、原始材料引用）——组合二次压缩、TaskGraph、MemoryPack、原文检索
- 决策审查（问题定义、候选方案、过去判断、证据、废弃结论、未解决冲突）
- 自定义（高级用户选择数据来源、时间范围、处理器、token预算等）

**第二层：高级用户选择处理机制**（如一级压缩、二级分类摘要、TaskGraph当前态、MemoryPack、原始材料引用、已废弃方案等），允许用户选择“我希望AI怎么理解”，系统负责调用相应处理器。

---

**四、装配原则：按目的有选择地装配，而非简单拼接**

不能将多种摘要和原文全部拼接，否则产生新的上下文膨胀。装配器须回答五个问题：任务目标、必须包含内容、辅助背景、废弃/冲突内容、在token预算下保留/压缩/丢弃什么。最终产物应为结构化Context Bundle（含任务目标、必须遵守、当前状态、重要背景、冻结方向、未决问题、来源等），用户可预览、编辑、删除、锁定各部分。

---

**五、“独立于任何智能体，又为任何智能体服务”的准确表达**

该判断在产品层面成立，本质是上下文由用户持有而非平台私有。但“为任何智能体服务”需分层实现：
1. 复制粘贴（Markdown/纯文本，最通用）
2. 文件输出（context.md/json/handoff.md等）
3. API/CLI调用（供OpenCode、Claude Code、内部Agent等脚本调用）
4. 深度集成（SDK/MCP/host Hook自动注入，仍需具体适配）

更严谨承诺为：生成宿主无关、可移植的上下文包，通过复制、文件、CLI、API或适配器交付。

---

**六、产品价值**

- 跨模型上下文可移植（用户拥有自己的背景资料，决定给谁、给多少、以什么形式给、哪些不再给）
- 同一份资料多种视图（快速了解、执行上下文、决策记录、叙事背景、阶段总结）
- 用户可控制上下文深度（快速了解←→完整接手）
- 上下文成为独立资产（可保存、版本化、重建、比较、编辑、追溯、复用）

---

**七、主要产品风险**

- 配置成本超过复制粘贴成本（须预设简化，高级配置折叠）
- 用户无法判断上下文是否有用（须显示包含原因、来源、排除内容、废弃标记、token使用）
- 重新陷入复杂语义工程（初期仅需范围选择、must_include、废弃标记、来源引用、token预算、摘要粒度、可编辑预览，冻结lifecycle复杂语义）
- 被看作普通提示词生成器（须强调长期资料积累、多种视图、来源和版本、可排除废弃、跨平台复用）
- 隐私问题（坚持local-first、原始资料本地保存、API密钥用户自管理、支持敏感字段排除，反成优势）

---

**八、商业前景：有所改善但未自动解决**

从底层基础设施转为用户可见产品（可看到资料库、选择项目、生成背景包、切换AI、检查修改上下文），使其从“强规范弱产品”变为具备明确使用界面的工具。初始用户为多AI重度用户、开发者、产品经理、研究人员等。商业验证仍需回答三个朴素问题：用户是否每周反复使用？是否显著减少重复解释和手动整理？是否愿意将其作为跨AI工作的固定入口？

---

**九、最小产品形态**

在现有桌面工作台增加“生成上下文”标签页，包含：
- 输入区域（项目、任务、时间范围、目标AI、token预算）
- 预设模式（快速了解/继续任务/深度接手/决策审查/自定义）
- 内容来源（第一版仅需一级压缩、二级压缩、must_include、已废弃标记、原文片段；TaskGraph为实验选项）
- 输出预览（按区块展示任务目标、当前状态、必须遵守、重要背景、决策记录、未决问题、废弃内容、来源引用；每个区块支持删除、编辑、锁定、展开来源、重新生成）
- 输出方式（复制剪贴板、保存Markdown/JSON、导出精简/完整版）

---

**十、八条产品原则**

1. 用户选择目的，系统选择机制。
2. 上下文包必须可检查，不能黑盒注入。
3. 默认做减法，不做无序拼接。
4. must_include由用户拥有最终控制权。
5. 所有内容保留来源。
6. 原始资料与派生产物分离（可重新生成）。
7. 首先服务复制、文件和剪贴板。
8. TaskGraph是高级能力，不再是使用前提。

---

**最终裁决**：想法值得做，它比“单纯自动化双层压缩”更接近完整产品，且未重新陷入复杂语义工程。准确战略定义是**“由用户掌控、独立于具体AI平台、能够根据当前任务把长期资料编译成个性化上下文包的AI上下文工作台”**。核心命题为**“用户需要的不是让AI记住一切，而是决定这一次AI应该知道什么”**。建议保留当前开发路线，将下一步从二次压缩界面升级为“上下文包生成”界面，第一版只用现有双层压缩、must_include、废弃标记和原文引用完成装配，TaskGraph与MemoryPack作为可插拔实验来源，不恢复复杂语义开发。
## 对“上下文装配器”想法的评价与裁决

Claude-Fable-5对GPT-5.6-Sol的讨论作出评价：想法本身成立，核心命题“用户需要决定这一次AI应该知道什么”有价值，但GPT-5.6-Sol的采纳建议恰恰相反——不应立即升级为“上下文工作台”，而应做最小可行版本。

最强证据被双方忽略：用户发给新AI的《项目背景包》本身就是产品的手工版——用户已在实际生产Context Bundle，只是未自动化。唯一验收标准是“下一次交接时，是用工具生成还是又手工写了一份”。

这场讨论重复了项目史上最危险的模式：想法 → 军师批准并扩写 → 范围膨胀 → 冻结转向。GPT-5.6-Sol的五种预设模式、四层交付、区块化预览和八条原则，已比刚收敛到的剪贴板工具复杂一个量级，所谓“最小产品形态”并不最小。真正最小版本只是一个命令，把现有一级/二级压缩按模板拼成一份handoff.md，无需模式选择和预览编辑。

概念矛盾被掩盖：精确失效裁定（provenance、must_include）依赖刚被冻结的复杂语义；轻语义替代（手动标记“已废弃/必含”）虽可行，但与“组织良好的Markdown目录+好压缩prompt”护城河很浅，意味着“独特产品”论证在轻量版下不成立，而重语义版成本又不可接受。另外，复制粘贴交付层放弃装配权——must_include从机械保证退化为善意建议，新方向实为原项目的弱化投影，应被承认而非回避。

“产品”一词是当前最大风险源：该想法实际是三个月前已批准的“个人知识上下文工作台”，只是重新加上产品化野心。一旦为想象中的普通用户设计，范围立即膨胀，而真实约束是教学主业、时间碎片化。建议设计输入只允许一个用户——自己，“能否推开为产品”仅作事后解读。真正值得留下的仅两点：“用户选目的、系统选机制”的两层结构（将来产品化用），以及五个风险清单中的风险一（配置成本）和风险三（重新陷入复杂语义工程）。

裁决：方向对，但交付建议应砍掉90%。下一步不是升级GUI增加“生成上下文”标签页，而是写一个最小assemble脚本，产出用户本来就要手工写的交接包。用真实使用次数（而非架构论证）决定该方向的后续权重。
## 用户澄清装配权出路与分阶段实施路线：通过OpenClaw内部集成获得机械保证，以自用优先分两阶段推进

用户针对Claude-Fable-5指出的“复制粘贴和文件交付层没有装配权，must_include退化为善意建议，新方向是ContextLedger的弱化投影”这一核心质疑，提出关键修正：目标不是做通用剪贴板工具，而是在开源Agent平台**OpenClaw**或者**opencode**等的内部进行修改，在LLM调用前接管上下文构造流程，直接控制最终进入Prompt的字符串，从而重新获得机械装配权和must_include的硬保证。同时强调该产品当前完全为自用——用户在实际使用中已经通过主动保存上下文尝到甜头，但手工复制粘贴整理极为费时，需要工具自动化这一已验证有价值的流程。

DeepSeek-v4-flash确认该思路是唯一正解：若仅做跨平台剪贴板工具确实沦为弱化投影，但瞄准OpenClaw内部集成即可从“善意建议”变为“实际生效的机械替换”，验证战场从通用场景收缩到自用环境，是对Fable批评的有效回应。用户“尝到甜头但手工太费时”的陈述进一步锁定了决策——不是设计可能有用的工具，而是自动化已确认有价值的手工流程，投入产出明确。

建议分两阶段实施：**阶段一（生产力工具，本周/月内）** 实现最小`assemble`脚本，自动化“复制→整理→保存→压缩→拼装”流程，输出Markdown交接包，验收标准为下次项目交接时是否使用脚本生成而非手写，即便输出Markdown（弱化版）也有价值——解决手工整理痛点；**阶段二（集成与接管）** 研究OpenClab代码定位最终Prompt拼接点，接入ContextLedger状态裁决逻辑，直接修改System Prompt或Context String，验收标准为Agent是否自动遵循must_include并排除废弃信息；**阶段三（产品化判断）** 在阶段二验证可靠且代码清晰后，再考虑独立、开源插件或商业化可行性。

最终结论：轻量脚本与重语义内核不再对立，而是同一项目在不同阶段（自用生产力工具 vs OpenClaw集成）的两段实现路径——既保留“大规模上下文工作台”愿景，又避免当前版本过度设计。本周先完成最小脚本解决重复劳动，本月研究OpenClaw获取装配权。
## 设计调整判断：保留采集底座，新增最小Assembler，通过OpenClaw官方插件实现注入而非fork核心

用户提出核心追问：结合此前关于Context Assembler的完整设计、Fable的严厉批评以及用户通过OpenClaw获得装配权的澄清，是否需要调整设计？核心诉求是保留现有采集压缩底座，同时最终能在Agent调用前机械注入上下文，而非停留于复制粘贴的善意建议。

军师AI-GPT-5.6-Sol作出最终补充裁决：**需要调整，但不是推翻，而是重新确定主次和阶段边界。** 现有采集与压缩能力全部保留，新增Context Assembler应先以最小命令形式出现（而非完整GUI工作台），产出用户本来就要手工写的项目交接包，经过真实使用后再逐步演化为GUI装配页面和OpenClaw注入插件。

**关键纠正：不建议直接修改OpenClaw源码**——OpenClaw已提供官方插件钩子`before_prompt_build`（注入动态上下文）和`before_agent_run`（检查最终prompt并阻断），Context Engine插件已支持`ingest()`/`assemble()`/`compact()`接口。更优路线是生成Context Bundle后由OpenClaw插件通过钩子注入并核验，而非fork核心承担长期合并成本。OpenClaw应优先于OpenCode作为目标宿主，因其Context Engine与装配目标高度契合。

**现有桌面工作台设计保留项**：剪贴板输入、只追加存储、去重、一级压缩、二级压缩、多项目工作区、Prompt Profile、失败重试、GUI项目选择与规则配置、原始资料与派生产物分离——全部作为未来装配器的数据基础。

**需调整的部分**：二级压缩定位应从“最终产物”改为“候选资料来源”；GUI最终增加“生成上下文包”页面，但第一版极简（仅支持项目选择、用途、来源选择、任务描述、额外要求，输出Markdown），暂不实现五种模式、TaskGraph自动优先级、MemoryPack融合、复杂token优化器、自动失效裁定、拖拽编辑器、多宿主适配。验收标准仅一条：下次项目交接时是否用工具生成背景包而非手写。

**最小Assembler设计原则**：第一版不让LLM决定“必含与排除”，由用户明确标记每个候选块的`NORMAL`/`MUST_INCLUDE`/`EXCLUDED`/`DEPRECATED_REFERENCE`状态，LLM只负责去重、重组织和压缩，不得删除用户锁定的must-include。最终产出稳定Markdown结构（Current Task、Must Follow、Current State、Relevant Background、Decisions in Effect、Do Not Resume、Open Questions、Sources），每个区块可追溯到来源。

**“机械保证”分级理解**：生成保证（必含内容进入Bundle）→注入保证（插件确保Bundle加入本次模型上下文）→提交前核验（`before_agent_run`检查最终prompt中是否存在bundle ID及所有must-include block ID，缺失则阻断）。但必须承认：上下文存在不等于模型遵守，关键危险动作（如禁止删除目录、禁止修改正式数据）应在Agent工具层增加机械门禁（`before_tool_call`可重写参数或阻止执行），不应混淆“上下文保证”与“动作保证”。

**OpenClaw集成两级策略**：Level A先做最小Bundle Injector Plugin（通过`before_prompt_build`注入，`before_agent_run`核验，不替换Context Engine）；Level B仅在Level A使用后暴露真实问题（宿主历史污染、compaction丢失bundle、子Agent需要不同上下文、token统一分配）时才接管Context Engine。

**GUI改造重新排序**：G1完成现有桌面工作台长期使用；A1实现最小Assemble CLI（固定来源为最近一级压缩、最新二级压缩、用户维护的must_include.md和deprecated.md）；A2在CLI实际使用暴露需求后将装配加入GUI；H1实现OpenClaw Injector Plugin；H2实际自用观察（是否减少重复解释、Agent是否仍引用废弃方案、must-include是否真的进入最终prompt）；H3仅在简单注入不足时开发Context Engine。

**明确不做**：不恢复完整lifecycle、不实现自动provenance冲突裁决、不让TaskGraph成为前置条件、不同时集成两个宿主、不fork OpenClaw核心、不先建设五种复杂模式、不做拖拽编辑器、不让LLM自动决定must-include、不将“注入”表述为“保证遵守”、不为假想用户设计配置体系。

**架构文档策略**：保留现有`architecture.md`作为v0.1契约；新增独立ADR（`ADR-0001-context-bundle-assembler-and-host-integration.md`）仅批准新增Context Bundle、最小Assembler、一级/二级压缩作为候选来源、人工状态标记、Markdown/JSON输出、未来OpenClaw插件读取bundle，暂不实现TaskGraph/MemoryPack/自动语义裁决；通过并验证A1后再决定是否生成`architecture_v0.2.md`，不因新解释立即重新冻结完整架构。

**最终裁决**：新增讨论使方向更清晰但不导致再次膨胀——保留采集压缩底座，增加最小Assembler先生成手工交接包，使用后再加入GUI，随后通过OpenClaw官方插件实现注入与核验而非修改核心。路线固定为：现有采集工具→最小assemble命令→真正用于下次项目交接→GUI装配页面→OpenClaw注入插件→必要时开发Context Engine。关键验收标准仍为：下一次需要让另一个AI接手时是否直接使用工具生成Bundle，进入OpenClaw后该Bundle是否被实际注入最终模型输入，而不再需要手工重复解释。
## 方案评审反馈：认可方向，但建议仅承诺A1到近期，G1不得阻塞A1

用户向Claude-Fable-5呈现了经OpenClaw修正的分阶段方案（保留采集底座、CLI优先、插件注入而非fork），询问是否可实施。Claude-Fable-5确认该方案已基本吸收此前核心批评——用官方hook替代fork、区分上下文保证与模型遵守保证、先CLI后GUI、十项不做清单到位，无大的反对意见，可按此执行。

同时提出两个执行层面的重要提醒：

**第一，当前有效承诺只到A1，其余均为条件触发。** G1至H3虽呈序列状，但基于用户真实约束（教学主业、时间碎片化），应将A1作为“本周/近期要做的事”，A2、H1及之后每一步仅在前一步验收标准真实达成后才启动，不应提前铺路。路线图的正确用法是决策树，而非计划表。

**第二，G1不得阻塞A1。** 方案将G1（工作台打磨）排于A1之前，但真正验收节点是A1——即“下次交接是否用脚本生成bundle”。若时间只够做一件事，应优先A1；G1仅按日常使用中实际阻塞点按需修补，不必作为前置里程碑完整实现。ADR增量批准方式正确，可避免每次方向微调都重新冻结大架构。

按此执行即可。
## A1最小Assembler完成，G1工作台打磨按需处理

项目AI-Qwen-3.8-Max-Preview已完成A1（最小Assemble CLI）交付：新增`assembler`模块、CLI子命令、workspace路径管理，总计6个代码文件、29个测试（190通过/3失败，均为已有缺陷与本次无关）、3份文档（ADR-003、README更新、implementation_status更新）。使用方式为`context-capture assemble --project <project> --task "任务"`，可选项排除二级压缩或自定义输出路径，用户维护的`must_include.md`与`deprecated.md`会被自动读取，输出版本化Markdown至`bundles/bundle_YYYYMMDD_NNN.md`。后续A2（装配加入GUI）和H1（OpenClaw Injector Plugin）均为条件触发，仅在A1实际使用暴露需求或验证有效后才启动。

G1（桌面工作台长期使用打磨）尚未开始，且按Claude-Fable-5裁决已被明确降级——G1不得阻塞A1，仅在日常使用遇到实际阻塞点时按需修补，不必作为前置里程碑完整实现。当前已完成仅A1，G1原规划的多标签页常驻工作台等内容未动。项目AI询问：是先规划G1具体内容，还是先在实际使用A1后再决定——此问题需用户决策，取决于当前采集与压缩流程是否已被实际阻塞。
## A1最小Assembler完成并通过自用验收准备，开发暂停等待真实使用反馈

军师AI在A1（最小Assemble CLI）完成后明确指示暂不启动完整G1（桌面工作台打磨）、A2（装配加入GUI）或H1（OpenClaw插件），而是先完成A1自用验收准备。具体要求包括：列出当前3个失败测试的名称、失败原因及首次出现commit，确认是否影响A1关键路径；确认A1新增测试全部通过；提供最小真实验收指南，涵盖must_include.md和deprecated.md的位置与格式、assemble命令用法、实际读取的一级/二级压缩范围、bundle输出路径及来源版本检查；禁止新增GUI、TaskGraph、MemoryPack、OpenClaw集成或复杂语义功能；完成后停止开发，等待用户使用A1完成真实项目交接并反馈，后续仅由使用中重复出现的阻塞点触发。

项目AI（qwen3.8-max-preview）已完成全部准备工作并提交报告。三个失败测试分别涉及doctor诊断命令（FileNotFoundError未捕获）、list-projects工具命令（同样异常处理问题）和level2文件命名测试（硬编码日期导致今天日期不匹配），经分析均不影响采集、一级压缩、二级压缩、must_include/deprecated读取或assemble输出；A1新增的29个测试（source_reader 13个、assembler 8个、assemble_command 5个、集成测试3个）全部通过，无需修复。

验收指南明确：项目workspace位于`D:/CCXXLESSON/contextledger/raw/projects/context_capture`，用户需先通过`clipboard`或`file`命令采集素材生成一级压缩（可选触发二级压缩），再在workspace根目录手动创建`must_include.md`（必含条目）和`deprecated.md`（废弃条目），格式均为自由Markdown。assemble命令为`context-capture assemble --project contextledger --task "任务描述"`，支持`--no-level1`、`--no-level2`、`--no-must-include`、`--no-deprecated`等排除选项，以及`--output`自定义路径。实际读取范围包括：task参数写入Current Task区块，must_include.md写入Must Follow，level1.md全部内容写入Current State，最新二级压缩文件写入Relevant Background，deprecated.md写入Do Not Resume，从level1中自动提取“未决事项”写入Open Questions，所有来源汇总至Sources区块并附带Capture ID。输出为版本化Markdown（`bundles/bundle_YYYYMMDD_NNN.md`），不覆盖已有文件，空区块自动跳过。验收标准为：下次需要让另一个AI接手时，直接使用assemble生成Bundle发给新AI，而非手工重写背景包。

项目AI确认本次不再新增GUI、TaskGraph、MemoryPack、OpenClaw集成或复杂语义功能，开发已停止，等待用户完成一次真实项目交接后根据反馈决定后续步骤。
# [/COMPAT]

