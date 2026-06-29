# abu_modern · phase05_replay

这是 `abu_modern` 的 `Phase 0.5` 失效回放基准沙箱。

目的：
- 在任何新管线代码之前，先构建一套与当前 schema/脚本实现脱钩的 gold 基准
- 用独立观测流暴露 `partial / conditional / revival / alias / provenance / valid-time` 的真实缺口
- 交付“哪里塌了”的地图，而不是“全部通过”的报告

目录约定：
- `trajectories/`：有序观测流，每条观测携带 `obs_id / observed_at / valid_from / valid_to / source / mentions / payload`
- `gold/`：逐步金标，包含 `expected_active_set / expected_invalidations / entity_clusters / must_include / valid_time_adjudication`
- `reports/`：评分结果与摘要
- `coverage_matrix.md`：8 类形态覆盖矩阵
- `gap_register.md`：现有 schema 与基线的失败地图

资产分层：
- 正式长期资产：
  - `trajectories/`：Phase 0.5 的样本库，后续 Phase 1 与回归测试继续复用
  - `gold/`：schema 无关金标，是后续实现必须持续对齐的评分基准
  - `coverage_matrix.md`：覆盖面记录，后续扩样本时继续维护
  - `gap_register.md`：从 Phase 0.5 过渡到 Phase 1 的问题地图
  - `reports/phase05_completion_lines.md`：Phase 1 的完成线依据
  - `reports/phase05_seal_report.md`：封板记录，保留“为什么这样定完成线”的依据
- 可重生成但建议保留的快照：
  - `reports/phase05_score_report.json`
  - `reports/phase05_score_summary.md`
  - 这两份可以通过评分脚本重跑生成，但建议保留为封板时点的对照快照
- 不建议删除：
  - 整个 `phase05_replay/` 目录都不是一次性临时目录，而是后续 Phase 1 的基准测试资产

相关脚本：
- `graph/scripts/seed_phase05_replay.py`：重建 Phase 0.5 基准数据
- `graph/scripts/score_phase05.py`：对跑基线、生成评分、封板报告与完成线文档

`reports/` 文件说明：
- `phase05_score_report.json`：机器可读的完整评分结果，包含分基线、分形态、分轨迹明细
- `phase05_score_summary.md`：人类可读的总览摘要，用于快速查看本轮评分结论
- `phase05_seal_report.md`：Phase 0.5 封板报告，记录封板时的核心结论与按形态 invalidation 拆分结果
- `phase05_completion_lines.md`：Phase 1 的完成线文档，按形态记录后续验收写法

纪律：
- gold 使用“事实上应该发生什么”的语言，不复用 `status / state / supersede / OpenTask` 词汇
- `partial / conditional / revival / valid-time` 预期会暴露缺口，不能为了通过率把它们改写成现有字段可表达的形状
- 乱序与迟到场景以文件内到达顺序为 transaction order，以 `observed_at` 为额外裁决键；若缺失则显式退回到达序
