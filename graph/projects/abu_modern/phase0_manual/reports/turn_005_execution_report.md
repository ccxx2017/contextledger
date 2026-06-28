# turn_005 执行报告

## 1. 本轮目标

本轮不再新增语义用例，只做三件封板动作：

1. 从 `turn_001 -> turn_004` 的 patch 链全链重放
2. 重生成所有 canonical `context_bundle.* / assembly_report.*`
3. 把 `turn_002~004` 的经验固化进 Phase 0 runbook

## 2. 本轮新增产物

- 封板脚本：`graph/scripts/replay_phase0_seal.py`
- 封板报告：`graph/projects/abu_modern/phase0_manual/reports/turn_005_seal_report.json`
- turn_005 总结：`graph/projects/abu_modern/phase0_manual/reports/turn_005_execution_report.md`
- Phase 0 runbook：`runbook/process_turn_phase0.md`

## 3. 全链重放结果

封板报告最终结果：

```json
{
  "ok": true,
  "graph_replay": [
    {"turn_id": "turn_001", "semantic_equal": true, "sha256_equal": true},
    {"turn_id": "turn_002", "semantic_equal": true, "sha256_equal": true},
    {"turn_id": "turn_003", "semantic_equal": true, "sha256_equal": true},
    {"turn_id": "turn_004", "semantic_equal": true, "sha256_equal": true, "matches_current_graph_state": true}
  ]
}
```

结论：

- `patch_001..004` 现在可以从 `graph/graph_state.seed.json` 全链重放
- `graph_state.turn_004.json` 可被确定性重建
- 当前 `graph_state.json` 与重放得到的 `turn_004` 终态一致

## 4. 本轮发现并修复的真实漂移

第一次运行封板脚本时，报告为 `ok=false`，原因是：

- `graph_state.turn_001.json` 是旧快照
- 它缺少 `n_0009` 与 priority 字段
- 而 `graph_state.turn_001.rerun.json` 与 patch 链 replay 结果一致

修复动作：

- 将 `run/graph_state.turn_001.json` 校正为与 `graph_state.turn_001.rerun.json` 相同的 canonical 版本
- 重新运行封板脚本

这说明：

- 本轮不是“直接宣告通过”，而是先发现了真实的 replay drift
- 漂移已被修复，并在第二次 seal 中收敛为 `ok=true`

## 5. bundle 可再生结果

封板报告中的 bundle 再生结果如下：

```json
{
  "turn_001": {"bundle_sha": true, "report_sha": true},
  "turn_002": {"bundle_sha": true, "report_sha": true},
  "turn_003": {"bundle_sha": true, "report_sha": true},
  "turn_003_pre_adjudication": {"bundle_sha": true, "report_sha": true},
  "turn_004": {"bundle_sha": true, "report_sha": true}
}
```

结论：

- 所有 canonical `context_bundle.*.json` 都可由对应图快照重新生成
- 所有对应 `assembly_report.*.json` 也都可重生成
- 当前封板采用的是“字节级一致”标准，不只是语义级一致

## 6. turn_001 canonical 化

`turn_001` 原始 bundle 曾是手工样例：

- 已归档为 `context_bundle.turn_001.legacy_manual.json`

当前 canonical 版本改为：

- `context_bundle.turn_001.json`
- `assembly_report.turn_001.json`

它们现在均由当前最小 Assembler 机械生成，并纳入 seal report 的再生验证。

## 7. runbook 回填

本轮已新增 `runbook/process_turn_phase0.md`，固化了以下经验：

- `status` 主裁定，`state` 仅作为 pending gate
- `supersede` 支配 `priority`
- `must_include` 只在当前态集合上评估
- `superseded_nodes` 必须是对象数组，不能写成字符串数组
- `excluded_due_to_state` 与 `excluded_due_to_budget` 必须可区分
- `budget == must_count`、`budget < must_count`、`budget = 4` 三类预算行为
- `turn_005` 的封板命令与通过条件

同时，`runbook/process_turn.md` 已加入指向 `process_turn_phase0.md` 的导航说明。

## 8. 最终结论

- Phase 0 已满足“机制成立 + 全程可复现 + 有 runbook 可重跑”
- 本轮按计划在第 5 轮封板，没有继续扩新用例
- 后续若再跑，是修 bug，不是继续加 Phase 0 用例
