# turn_004 执行报告

## 1. 本轮目标

本轮围绕 `n_0013` 的“待裁定”语义闭环，验证三件事：

1. 裁定前，`state=open` 的待定关系必须从 should 集合掉出，且原因记为 `excluded_due_to_state`
2. 裁定时，旧节点 `n_0013` 必须退出当前态，确认态新节点不得继续使用 `state=open`
3. 裁定后，在 `budget=4` 下验证 `must` 全保，且 `should` 按 `created_turn/node_id` 的新近优先规则回填

## 2. 产物清单

- 预装配报告：`graph/projects/abu_modern/phase0_manual/reports/assembly_report.turn_003_pre_adjudication_budget4.json`
- 预装配 bundle：`graph/projects/abu_modern/phase0_manual/reports/context_bundle.turn_003_pre_adjudication_budget4.json`
- normalized：`normalized/projects/abu_modern/s001/turn_004.norm.md`
- manifest：`normalized/projects/abu_modern/s001/turn_004.manifest.json`
- patch：`graph/projects/abu_modern/phase0_manual/patches/patch_004.json`
- graph snapshot：`graph/projects/abu_modern/phase0_manual/run/graph_state.turn_004.json`
- lint：`graph/projects/abu_modern/phase0_manual/reports/lint_report.turn_004.json`
- post bundle：`graph/projects/abu_modern/phase0_manual/reports/context_bundle.turn_004_budget4.json`
- post assembly：`graph/projects/abu_modern/phase0_manual/reports/assembly_report.turn_004_budget4.json`

## 3. 验收点一：裁定前装配

预装配报告中，`n_0013` 已不再落入 `should_include` 或 `excluded_due_to_budget`，而是被单独记录为 `excluded_due_to_state`：

```json
{
  "policy": {
    "state_participates_in_current_membership": true,
    "backfill_order": "created_turn desc, node_id asc"
  },
  "selected_by_priority": {
    "must_include": ["n_0001", "n_0003", "n_0010"],
    "should_include": ["n_0011"]
  },
  "excluded_due_to_state": [
    {
      "node_id": "n_0013",
      "type": "OpenTask",
      "state": "open",
      "reason": "state_open_pending_candidate"
    }
  ]
}
```

结论：
- `n_0013` 因 `state=open` 的 pending 候选语义被排除
- 它不再被误记为 `budget_exhausted`

## 4. 验收点二：裁定动作

`patch_004.json` 中的裁定动作如下：

```json
{
  "new_nodes": [
    {
      "node_id": "n_0014",
      "entity_ref": "strategy_research_agent.quant_assistant_relationship",
      "type": "Decision",
      "state": null,
      "status": "active"
    }
  ],
  "superseded_nodes": [
    {
      "node_id": "n_0013",
      "reason": "turn_004 已裁定 quant_assistant 与 strategy-researcher 为平行 Agent / 共享后端，旧的待定关系退出当前态。"
    }
  ],
  "new_edges": [
    {
      "source": "n_0014",
      "target": "n_0013",
      "relation": "invalidates"
    }
  ]
}
```

apply 后的图快照显示：

```json
{
  "n_0013": {
    "status": "superseded",
    "state": "open"
  },
  "n_0014": {
    "status": "active",
    "state": null,
    "entity_ref": "strategy_research_agent.quant_assistant_relationship"
  }
}
```

结论：
- 旧的待定节点 `n_0013` 已 supersede
- 确认态节点 `n_0014` 没有继续使用 `state=open`
- `n_0014` 与 `n_0013` 共享同一 `entity_ref`，完成同实体裁定替换

## 5. 验收点三：裁定后装配 + budget=4

裁定后装配报告如下：

```json
{
  "policy": {
    "state_participates_in_current_membership": true,
    "backfill_order": "created_turn desc, node_id asc",
    "max_nodes": 4
  },
  "selected_node_ids": ["n_0001", "n_0003", "n_0010", "n_0014"],
  "selected_by_priority": {
    "must_include": ["n_0001", "n_0003", "n_0010"],
    "should_include": ["n_0014"]
  },
  "excluded_due_to_status": [
    {"node_id": "n_0009", "status": "superseded"},
    {"node_id": "n_0013", "status": "superseded"}
  ]
}
```

post bundle 中的实际片段：

```json
{
  "l1_baseline": {
    "must_include": [
      {"node_id": "n_0001"},
      {"node_id": "n_0003"},
      {"node_id": "n_0010"}
    ],
    "should_include": [
      {
        "node_id": "n_0014",
        "entity_ref": "strategy_research_agent.quant_assistant_relationship"
      }
    ]
  }
}
```

结论：
- `must` 三节点全部保留
- 唯一回填的 `should` 是最新确认态 `n_0014`
- 之前的 `n_0011/n_0012/n_0002/n_0006/n_0007` 留在 `excluded_due_to_budget`
- `budget=4` 的 should 排序用例已通过真实装配验证

## 6. lint 同步结果

`lint_report.turn_004.json` 已与装配层保持同一口径：

```json
{
  "adjudication_policy": {
    "current_membership_field": "status",
    "state_participates_in_current_membership": true,
    "state_gate_field": "state",
    "pending_state_rule": "exclude state=open pending open-task candidates from current membership"
  },
  "status_observations": {
    "superseded_node_ids": ["n_0009", "n_0013"],
    "excluded_due_to_state_node_ids": []
  },
  "summary": {
    "errors": 0,
    "warnings": 0
  }
}
```

结论：
- `state_participates_in_current_membership` 已从 `false` 翻为 `true`
- `status` 仍是主裁定字段
- `state` 仅作为 pending gate 参与成员资格判定

## 7. 最终结论

- `turn_004` 已完成一次“待裁定 -> 确认态”的完整闭环
- `n_0013` 在裁定前被 `state=open` 正确挡出主要上下文
- `n_0014` 在裁定后以确认态进入 `budget=4` 的 should 回填集合
- 本轮同时还清了 `budget=4` 的 should 排序验证欠账
