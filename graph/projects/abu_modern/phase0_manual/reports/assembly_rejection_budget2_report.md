# budget=2 拒绝用例报告

## 1. 测试目的

- 验证最小确定性 Assembler 在 `active must_include` 数量超过装配预算时，会**拒绝装配**，而不是静默丢弃 must 节点。
- 本用例对应评审指出的未验证分支：`budget < active_must_include`。

## 2. 测试命令

```bash
python graph/scripts/build_context_bundle.py \
  --graph graph/projects/abu_modern/phase0_manual/graph_state.json \
  --project-id abu_modern \
  --turn-id turn_002_budget2_reject \
  --out graph/projects/abu_modern/phase0_manual/reports/context_bundle.turn_002_budget2.json \
  --report-out graph/projects/abu_modern/phase0_manual/reports/assembly_report.turn_002_budget2_reject.json \
  --max-nodes 2 \
  --budget-profile reject_if_must_exceeds_budget
```

## 3. 运行结果

- 进程退出码：`2`
- 结果：`rejected`
- 未生成 `context_bundle.turn_002_budget2.json`
- 已生成 rejection report：`assembly_report.turn_002_budget2_reject.json`

## 4. rejection report 证据

```json
{
  "result": "rejected",
  "policy": {
    "current_membership_field": "status",
    "state_participates_in_current_membership": false,
    "budget_profile": "reject_if_must_exceeds_budget",
    "max_nodes": 2,
    "overflow_rule": "never_drop_must_include"
  },
  "summary": {
    "active_must_include_nodes": 3,
    "selected_nodes": 0
  },
  "rejection": {
    "code": "MUST_INCLUDE_OVER_BUDGET",
    "active_must_include_node_ids": [
      "n_0001",
      "n_0003",
      "n_0010"
    ]
  }
}
```

## 5. 结论

- `budget=2 < active must_include=3` 时，Assembler 没有静默丢弃 must 节点
- 它按规则拒绝装配，并留下可复核的 rejection report
- 这条用例补上后，`must_include` 保护规则已覆盖：
  - `budget == must_count`：可装配，且 must 全保
  - `budget < must_count`：拒绝装配，不产出 bundle
