# abu_modern · phase0_manual · turn_001 执行报告

## 执行目标

本次执行按白皮书 `Phase 0` 的“手工代行”方式完成 `abu_modern` 的冷启动第 1 轮，验证以下事项：

- `raw -> normalized -> patch -> apply -> lint` 是否能在不覆盖主图的前提下跑通
- 手工 patch 是否能够生成一份结构自洽的 `graph_state.json`
- 是否可以基于首轮图状态手工拼出一份 `ContextBundle` 形状样例

## 输入来源

- Raw：`raw/projects/abu_modern/s001/turn_001.md`
- Norm：`normalized/projects/abu_modern/s001/turn_001.norm.md`
- Manifest：`normalized/projects/abu_modern/s001/turn_001.manifest.json`

## 产物

- 手工 patch：`graph/projects/abu_modern/phase0_manual/patches/patch_001.json`
- 生成图状态：`graph/projects/abu_modern/phase0_manual/graph_state.json`
- 图状态快照：`graph/projects/abu_modern/phase0_manual/run/graph_state.turn_001.json`
- Lint 报告：`graph/projects/abu_modern/phase0_manual/reports/lint_report.turn_001.json`
- legacy 手工 ContextBundle 样例：`graph/projects/abu_modern/phase0_manual/reports/context_bundle.turn_001.legacy_manual.json`
- 可重放 ContextBundle：`graph/projects/abu_modern/phase0_manual/reports/context_bundle.turn_001.json`
- 可重放装配报告：`graph/projects/abu_modern/phase0_manual/reports/assembly_report.turn_001.json`

## 执行结果

- 冷启动第 1 轮已成功落图
- `graph_lint.py` 返回 `ok=true`
- lint 结果：`0 error / 0 warning`
- 本轮图中共生成：
  - 9 个节点
  - 8 条边

## 本轮抽取出的核心节点

- `n_0001`：总目标，回归主线，AOS 反哺
- `n_0002`：阶段 0，维稳 `duty_reporter`
- `n_0003`：阶段 1，复活 `strategy_research_agent`
- `n_0004`：阶段 2，根据阶段 1 产物决定下一个 employee
- `n_0005`：阶段 3，后续再做指挥舱 MVP
- `n_0006`：`ROADMAP_v2.md` 文件产物
- `n_0007`：阶段 1 研究工单
- `n_0008`：`_frozen_ideas.md` 文件产物
- `n_0009`：决策 3 待确认，`strategy_research_agent.implementation_mode`

## 本次验证到的东西

1. 首轮冷启动可以只靠手工 patch 成功生成结构化图状态
2. 当前图脚本链路中的 `apply_patch.py` 和 `graph_lint.py` 可复用为手工期机械核
3. 只要节点都被边连接，冷启动图可以通过 lint，不会出现“非根孤立 active 节点”错误
4. 可以先用手工 `ContextBundle` 样例验证白皮书要求的装配形状，而不必等待正式 Assembler
5. 已为 `turn_002` 预置一个可被明确推翻的旧态节点 `n_0009`，后续可用它构造最小对抗测试

## 这次还没有验证到的东西

- 第 2～3 轮的真实冲突与 supersede / invalidates
- `entity_ref` 命名不一致导致的漏判问题
- `reconcile_patch.py` 的真实价值
- `must_include` 在预算压力下的行为
- 正式 Assembler 的机械实现

## 评审后补强

根据评审意见，本轮产物已额外完成以下补强：

1. 修复 `ContextBundle` 中的 content 改写问题，确保 bundle 内文本与 graph 节点逐字一致
2. 为所有入选 bundle 的节点补齐 provenance
3. 给节点增加 `priority` 字段，作为 `must_include / should_include / optional / background` 的图侧来源
4. 为 `turn_002` 选定专用冲突目标：`n_0009`
5. 新增前置规则文件：`graph/projects/abu_modern/phase0_manual/reports/turn_002_preconditions.md`
6. 记录术语映射债：`spec.state ≡ impl.status`
7. 明确优先级裁定：`supersede` 支配 `priority`，`must_include` 只在 `status = active` 的当前态集合上评估
8. 在 `turn_005` 封板时，已将 `turn_001` 的手工 bundle 样例归档为 legacy，并用当前最小 Assembler 重生成可重放的 canonical bundle / assembly report

## 下一步建议

1. 继续手工执行 `turn_002`
2. 用 `n_0009` 作为旧态 X，生成新态 Y = `AOS-native`
3. 在 patch 中同时写 `superseded_nodes` 与 `invalidates` 边
4. apply 后执行一次手工 assemble，验证 `(a)(b)(c)` 三条断言
5. 一旦冲突测试跑通，再决定是否继续扩成更正式的 `Phase 0.5` 种子基准
