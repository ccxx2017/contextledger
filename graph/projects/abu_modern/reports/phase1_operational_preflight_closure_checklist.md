# Phase 1 Operational Preflight Closure Checklist

## 基本结论

- project_id: `abu_modern`
- 当前判断: `Phase 1-prep 已完成，Operational Preflight 由“缺少运行设施”收敛为“设施已齐，等待按 turn_004 正式进入主流程”`
- 本次工作范围:
  - 关闭 Operational Preflight 缺口
  - 不扩展 `Phase 0.5` 基准
  - 不实现 valid-time-present / partial / conditional / revival / provenance 的能力提升

## 1. 主项目 checkpoint

- 结论: 首个正式 turn 应从 `turn_004` 开始
- 状态: `CLOSED`
- 理由:
  - 当前主图 `turn_counter=3`
  - `run/graph_state.turn_003.json` 已存在
  - `raw` 已有 `turn_004` 到 `turn_006`，若从 `turn_007` 开始会跳过未入账 raw
  - 当前不是 cold-start，不需要回到 replay 模式
- 证据:
  - `graph/projects/abu_modern/graph_state.json`
  - `contracts/07_turn_runtime.md`

## 2. Extractor 调用 contract

- 状态: `CLOSED`
- 已落地:
  - 新增 contract：`contracts/06_extractor_runtime.md`
  - 新增脚本：`graph/scripts/invoke_extractor.py`
  - 新增 env 示例：`graph/env.example`
- 已明确:
  - 模型：`deepseek-v4-flash`
  - endpoint：默认 `https://api.deepseek.com/v1/chat/completions`
  - env：`EXTRACTOR_API_KEY / EXTRACTOR_BASE_URL / EXTRACTOR_MODEL / EXTRACTOR_TIMEOUT_SECONDS`
  - 默认 patch 落盘：`graph/projects/<project_id>/patches/patch_XXX.json`
  - prompt / 原始响应落盘：`graph/projects/<project_id>/reports/`
- 备注:
  - 真实 key 已经写入 `env`

## 3. reconcile retry N

- 状态: `CLOSED`
- 约定: `MAX_RECONCILE_RETRIES = 3`
- 证据:
  - `contracts/07_turn_runtime.md`
  - `graph/scripts/quarantine_patch.py --max-retries 3`

## 4. 主项目目录约定

- 状态: `CLOSED`
- 已落地:
  - `graph/projects/abu_modern/patches/README.md`
  - `graph/projects/abu_modern/pending_merge/README.md`
  - `graph/projects/abu_modern/reports/README.md`
- 约定目录:
  - `patches/`
  - `pending_merge/`
  - `reports/`
  - `quarantine/`
  - `run/`
- 说明:
  - `patches/` 与 `pending_merge/` 已在主项目下正式建立

## 5. Entity Resolver 最小接口与 pending_merge

- 状态: `CLOSED`
- 已落地:
  - contract 扩展：`contracts/05_entity_naming.md`
  - 脚本：`graph/scripts/entity_resolver.py`
- 最小输出字段已覆盖:
  - `match_confidence`
  - `merge_reason`
  - `non_merge_reason`
  - `candidate_aliases`
- dry-run 证据:
  - `graph/projects/abu_modern/reports/dry_run/phase1_prep/entity_resolution_good.report.json`
  - `graph/projects/abu_modern/reports/dry_run/phase1_prep/pending_merge.turn_004.json`

## 6. 正式 Assembler v1

- 状态: `CLOSED`
- 已落地:
  - `contracts/04_assembly.md` 从 placeholder 升级为可执行契约
  - `graph/scripts/build_context_bundle.py` 移除 `phase0_manual` 路径硬编码
  - 支持按 `project_id / turn_id / budget` 生成主项目产物
- 主项目验证结果:
  - 已生成 `graph/projects/abu_modern/reports/context_bundle.turn_004.json`
  - 已生成 `graph/projects/abu_modern/reports/assembly_report.turn_004.json`
- 当前水位:
  - active `must_include=1`
  - `max_nodes=12` 下成功装配，无静默丢弃 `must_include`

## 7. 主图 priority 迁移

- 状态: `CLOSED`
- 已落地:
  - 脚本：`graph/scripts/migrate_priorities.py`
  - 备份：`graph/projects/abu_modern/reports/graph_state.pre_priority_migration.json`
  - 报告：`graph/projects/abu_modern/reports/priority_migration_report.json`
- 执行结果:
  - 主图 40 个节点全部补齐 `priority`
  - 主图现已可支撑 `must_include / should_include / optional / background`

## 8. 前后态 diff / lint

- 状态: `CLOSED`
- 已落地:
  - 脚本：`graph/scripts/diff_lint_reports.py`
  - contract：`contracts/07_turn_runtime.md`
- dry-run 证据:
  - `graph/projects/abu_modern/reports/dry_run/phase1_prep/lint_delta.turn_004.json`
- 结果:
  - `introduced_errors = 0`
  - `preexisting_errors = 2`
  - `introduced_warnings = 0`
  - `preexisting_warnings = 2`
- 结论:
  - `[L1]/[L2]` 已可机械判定

## 9. contracts/README.md 漂移修正

- 状态: `CLOSED`
- 已修正:
  - 删除对不存在的 `05_normalized.md / 06_entity_naming.md` 的错误索引
  - 补入当前真实文件与新增 contract
- 证据:
  - `contracts/README.md`

## 10. scratch dry-run

- 状态: `CLOSED`
- 成功路径证据:
  - good patch: `graph/projects/abu_modern/reports/dry_run/patch_good.turn_004.json`
  - reconcile report: `graph/projects/abu_modern/reports/dry_run/phase1_prep/reconcile_good.report.json`
  - applied graph: `graph/projects/abu_modern/reports/dry_run/phase1_prep/graph_state.after_good.json`
  - lint report: `graph/projects/abu_modern/reports/dry_run/phase1_prep/lint_good.report.json`
  - lint delta: `graph/projects/abu_modern/reports/dry_run/phase1_prep/lint_delta.turn_004.json`
- 失败隔离路径证据:
  - bad patch: `graph/projects/abu_modern/reports/dry_run/patch_bad.turn_004.json`
  - reconcile fail: `graph/projects/abu_modern/reports/dry_run/phase1_prep/reconcile_bad.report.json`
  - quarantine record: `graph/projects/abu_modern/reports/dry_run/phase1_prep/quarantine/turn_004_failed.json`
- 结论:
  - `patch -> reconcile -> apply -> lint -> quarantine` 路径已在不污染主图的前提下验证可运行

## 存量问题声明

- 以下问题在 dry-run 前已存在，本次通过前后态 diff 被识别为 `[L2]`，不属于本次 prep 新引入:
  - `n_0006`：`RESOLVED_OPEN_TASK_STILL_ACTIVE`
  - `n_0008`：`RESOLVED_OPEN_TASK_STILL_ACTIVE`
  - `n_0011`：缺少 `entity_ref` 的 warning
  - `n_0018`：缺少 `entity_ref` 的 warning

## 下一步建议

- 按 `turn_004` 进入首个正式 Phase 1 turn
- 正式顺序建议:
  - `build_graph_slice.py`
  - `invoke_extractor.py`
  - `entity_resolver.py`
  - `reconcile_patch.py`
  - `apply_patch.py`
  - `graph_lint.py`
  - `diff_lint_reports.py`
  - `build_context_bundle.py`
