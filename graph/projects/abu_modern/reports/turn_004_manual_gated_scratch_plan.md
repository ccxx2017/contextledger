# turn_004 Manual-Gated Scratch Plan

目标：
- 第一次真实执行 extractor 链路
- 不自动落主图
- 在 scratch / 可回滚态上先跑一遍 `turn_004`
- 设置两个强制人工检视点：
  - `patch.json` 生成后停
  - `reconcile_report` 生成后停

## 输入

- `project_id=abu_modern`
- `turn_id=turn_004`
- `graph_state=graph/projects/abu_modern/graph_state.json`
- `turn=raw/projects/abu_modern/s001/turn_004.md`
- `baseline=graph/projects/abu_modern/reports/lint_baseline.json`

## scratch 目录

建议使用：
- `graph/projects/abu_modern/reports/scratch_turn_004/`

中间产物建议：
- `slice_004.json`
- `extractor_prompt.turn_004.json`
- `extractor_raw_response.turn_004.txt`
- `patch_004.raw.json`
- `patch_004.resolved.json`
- `entity_resolution.turn_004.json`
- `pending_merge.turn_004.json`
- `reconcile_report.turn_004.json`
- `graph_state.after_turn_004.json`
- `lint_report.turn_004.json`
- `lint_delta.turn_004.json`
- `context_bundle.turn_004.json`
- `assembly_report.turn_004.json`

## 手工闸门流程

1. 构建 slice
   - `build_graph_slice.py`
   - 只检查脚本成功产出，不改内容

2. 组装 prompt 并调用 Extractor
   - `invoke_extractor.py`
   - 输出 `patch_004.raw.json`

3. 人工检视点 A：检查 patch
   - 检查新增节点数量是否异常
   - 检查 `entity_ref`、`state`、`invalidates`、`superseded_nodes` 是否明显失真
   - 若不接受：停止，不进入 resolver / reconcile

4. 运行 resolver
   - `entity_resolver.py`
   - 输出 `patch_004.resolved.json` 与 `pending_merge.turn_004.json`

5. 运行 reconcile
   - `reconcile_patch.py`
   - 输出 `reconcile_report.turn_004.json`

6. 人工检视点 B：检查 reconcile 报告
   - 若 `errors > 0`：停止，不 apply，必要时 quarantine
   - 若 `warnings` 涉及关键实体误合并风险：停止，先人工判断
   - 若确认可接受：再进入 apply

7. 在 scratch 图上 apply
   - `apply_patch.py`
   - 输出 `graph_state.after_turn_004.json`
   - 禁止覆盖主项目 `graph_state.json`

8. lint + diff
   - `graph_lint.py`
   - `diff_lint_reports.py --baseline graph/projects/abu_modern/reports/lint_baseline.json`
   - 确认是否出现新的 `[L1]`

9. assemble
   - `build_context_bundle.py`
   - 只在 scratch 图上生成 bundle / report

10. 最终人工确认
   - 若 patch / reconcile / lint_delta / bundle 都接受
   - 再决定是否用同一版 patch 正式提交到主图

## 禁止事项

- 禁止把上述 1→10 串成无人值守自动 pipe 直接落主图
- 禁止在第一次真实 extractor 运行时跳过 A / B 两个人工检视点
