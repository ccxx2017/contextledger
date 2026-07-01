# Turn 运行契约 [PROVISIONAL]

本文件补足 Phase 1-prep 的运行期约定：
- 主项目 checkpoint 判断
- reconcile retry 上限
- 项目级目录落盘约定
- `[L1] 本轮引入 / [L2] 存量问题` 的机械判定

## 1. 主项目 checkpoint

针对 `abu_modern` 当前状态：
- `graph/projects/abu_modern/graph_state.json` 的 `turn_counter = 3`
- `raw/projects/abu_modern/s001/` 下已有 `turn_001.md` 到 `turn_006.md`
- `graph/projects/abu_modern/run/` 已保存到 `graph_state.turn_003.json`

结论：
- Phase 1 首个正式 turn 应从 `turn_004` 开始

理由：
1. `turn_counter=3` 说明主图当前权威态只覆盖到第 3 轮
2. 直接从 `turn_007` 开始会跳过 `turn_004~006`，破坏 raw 到 graph 的线性提交序
3. 当前主图并非空图，因此不需要回到 cold-start replay；只需从已确认 checkpoint 顺延

## 2. reconcile retry 上限

- contract 常量：`MAX_RECONCILE_RETRIES = 3`

含义：
- 同一轮在 `reconcile_patch.py` 失败后，最多允许 3 次“回填结构化 error 后重试”
- 达上限仍失败，则不得 apply，必须转入 `quarantine/`

说明：
- 这里的 `3` 是运行契约常量，不再只依赖脚本默认值

## 3. 项目级目录约定

项目根：
- `graph/projects/<project_id>/`

正式运行期目录：
- `graph_state.json`：当前权威图
- `run/`：每轮应用后的图快照
- `patches/`：本项目正式 patch 落盘区
- `pending_merge/`：resolver 未敢自动合并的待审记录
- `reports/`：readiness、lint、assembly、dry-run、extractor 响应等报告
- `quarantine/`：失败 patch 与错误记录

建议命名：
- `patches/patch_004.json`
- `reports/reconcile_report.turn_004.json`
- `reports/lint_report.turn_004.json`
- `reports/lint_delta.turn_004.json`
- `pending_merge/pending_merge.turn_004.json`
- `reports/context_bundle.turn_004.json`
- `reports/assembly_report.turn_004.json`

## 4. [L1] / [L2] 机械判定

定义：
- `[L1] 本轮引入`：应用后 lint 中出现，但应用前 lint 不存在的问题
- `[L2] 存量问题`：应用前 lint 已存在，应用后仍存在的问题
- 持久基线：已被确认的历史存量问题，可额外落在 `lint_baseline.json` 中，作为跨轮稳定参照

参考实现脚本：
- `graph/scripts/diff_lint_reports.py`

输入：
- 应用前 `graph_state.json`
- 应用后 `graph_state.json`
- 可选：`lint_baseline.json`

输出：
- `introduced_errors`
- `preexisting_errors`
- `introduced_warnings`
- `preexisting_warnings`
- `baseline_matched_errors`
- `baseline_matched_warnings`

控制流：
- 若存在 `introduced_errors`，按 `[L1]` 处理：回滚并进入 retry / quarantine
- 若仅存在 `preexisting_errors`，按 `[L2]` 处理：不回滚本轮，但随移交报告显式标注

基线文件建议路径：
- `graph/projects/<project_id>/reports/lint_baseline.json`

## 5. scratch dry-run 纪律

dry-run 目标：
- 证明 `patch -> reconcile -> apply -> lint -> quarantine` 路径可运行

纪律：
- dry-run 不得覆盖主项目 `graph_state.json`
- 所有中间产物落在 `reports/dry_run/` 或临时 scratch 目录
- dry-run 可使用人工构造 patch 或已有样例 patch，不要求真实调用 Extractor
