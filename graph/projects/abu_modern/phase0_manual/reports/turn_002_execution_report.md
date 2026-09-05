# turn_002 执行报告

## 1. 本轮目标

- 以 `abu_modern/s001/turn_002.md` 为输入，验证旧态 `n_0009` 能否被新态 Y 真实 supersede。
- 本轮沿用 `phase0_manual` 沙箱，不覆盖主图。
- 装配阶段采用紧预算策略，只保留 `status=active` 且 `priority=must_include` 的节点。

## 2. 产物清单

- normalized: `normalized/projects/abu_modern/s001/turn_002.norm.md`
- manifest: `normalized/projects/abu_modern/s001/turn_002.manifest.json`
- patch: `graph/projects/abu_modern/phase0_manual/patches/patch_002.json`
- graph snapshot: `graph/projects/abu_modern/phase0_manual/run/graph_state.turn_002.json`
- lint report: `graph/projects/abu_modern/phase0_manual/reports/lint_report.turn_002.json`
- context bundle: `graph/projects/abu_modern/phase0_manual/reports/context_bundle.turn_002.json`
- assembly report: `graph/projects/abu_modern/phase0_manual/reports/assembly_report.turn_002.json`
- budget=2 rejection report: `graph/projects/abu_modern/phase0_manual/reports/assembly_rejection_budget2_report.md`

## 3. supersede 承载方式

本轮按 preconditions 同时落地了两类承载：

```json
"superseded_nodes": [
  {
    "node_id": "n_0009",
    "reason": "turn_002 明确确认实现方式为 AOS-native，旧的待确认决策退出当前态。"
  }
],
"new_edges": [
  {
    "source": "n_0010",
    "target": "n_0009",
    "relation": "invalidates"
  }
]
```

结论：
- `superseded_nodes` 已实际出现在 `patch_002.json`
- `invalidates` 边已实际出现在 `patch_002.json`

## 4. 新节点 Y 与 entity_ref

新节点 Y 为 `n_0010`，其 `entity_ref` 与旧态 `n_0009` 保持一致：

```json
{
  "node_id": "n_0010",
  "type": "Decision",
  "content": "决策 3 已确认：阶段 1 的 Strategy Research Agent 采用 AOS-native 路线。",
  "entity_ref": "strategy_research_agent.implementation_mode",
  "state": null,
  "status": "active"
}
```

结论：
- Y 已携带 `entity_ref = strategy_research_agent.implementation_mode`
- 本轮确实对同一 `entity_ref` 做了新旧态切换，而不是新增一个无关决策

## 5. graph 与 lint 验证

### 5.1 status 翻转证据

图状态中的新旧节点如下：

```json
{
  "n_0009": {
    "status": "superseded",
    "_superseded_reason": "turn_002 明确确认实现方式为 AOS-native，旧的待确认决策退出当前态。"
  },
  "n_0010": {
    "status": "active",
    "entity_ref": "strategy_research_agent.implementation_mode"
  }
}
```

### 5.2 lint 报告证据

```json
{
  "summary": {
    "nodes": 10,
    "edges": 10,
    "active_nodes": 9,
    "superseded_nodes": 1,
    "errors": 0,
    "warnings": 0
  },
  "adjudication_policy": {
    "current_membership_field": "status",
    "state_participates_in_current_membership": false
  },
  "status_observations": {
    "superseded_node_ids": [
      "n_0009"
    ]
  }
}
```

结论：
- `status` 翻转已生效，linter 识别到 1 个 superseded 节点，且该节点为 `n_0009`
- lint 报告明确当前态裁定字段是 `status`
- lint 报告明确 `state` 不参与当前态成员资格判断

## 6. Assembler 机械验证

本轮已新增最小确定性 Assembler：`graph/scripts/build_context_bundle.py`

其装配规则为：

```text
status=active -> priority 顺序(must_include > should_include > optional > background) -> 在预算内按 created_turn/node_id 贪心装配
```

对应的装配报告如下：

```json
{
  "policy": {
    "current_membership_field": "status",
    "state_participates_in_current_membership": false,
    "budget_profile": "tight_budget_must_only",
    "max_nodes": 3,
    "overflow_rule": "never_drop_must_include"
  },
  "summary": {
    "active_nodes": 9,
    "superseded_nodes": 1,
    "active_must_include_nodes": 3,
    "selected_nodes": 3
  },
  "selected_node_ids": [
    "n_0001",
    "n_0003",
    "n_0010"
  ],
  "excluded_due_to_status": [
    {
      "node_id": "n_0009",
      "status": "superseded"
    }
  ]
}
```

结论：
- `context_bundle.turn_002.json` 现在是脚本机械生成，不再是手工装配样例
- `n_0009` 被排除出装配输入集的原因已机械记录为 `status=superseded`
- 预算为 `3`，而 active 的 `must_include` 节点也是 `3` 个，因此本轮不存在静默丢弃 must 的空间

## 7. 三条断言

### 断言 (a)：当前态含 Y

机械生成的 bundle 片段：

```json
"must_include": [
  {
    "node_id": "n_0001",
    "type": "UserGoal",
    "content": "回归主线，AOS反哺：让 AOS 的下一个 employee 直接服务于量化主线，而不是继续服务于 AOS 自己。"
  },
  {
    "node_id": "n_0003",
    "type": "OpenTask",
    "content": "阶段 1：复活 Strategy Research Agent，作为 AOS 的第一个领域 employee，目标是恢复量化主线并产出可信策略档案。"
  },
  {
    "node_id": "n_0010",
    "type": "Decision",
    "content": "决策 3 已确认：阶段 1 的 Strategy Research Agent 采用 AOS-native 路线。"
  }
]
```

结论：`PASS`

### 断言 (b)：bundle 全文搜不到旧态 `n_0009`

对 `context_bundle.turn_002.json` 搜索 `n_0009` 的结果：

```text
No matches found
```

bundle 的 `must_include` 仅包含：

```text
n_0001
n_0003
n_0010
```

装配报告同时给出排除原因：

```json
"excluded_due_to_status": [
  {
    "node_id": "n_0009",
    "status": "superseded"
  }
]
```

结论：`PASS`

### 断言 (c)：紧预算下稳定 must 节点仍在

本轮 bundle 由 Assembler 在 `max_nodes=3` 下机械生成。装配报告显示 active 的 must 节点数恰好为 `3`，且全部入选：

```json
{
  "budget_profile": "tight_budget_must_only",
  "max_nodes": 3,
  "active_must_include_nodes": 3,
  "selected_node_ids": [
    "n_0001",
    "n_0003",
    "n_0010"
  ]
}
```

结论：`PASS`

## 8. budget=2 拒绝用例

为验证 `must_include` 保护规则的拒绝分支，本轮额外执行了一个边界测试：

```json
{
  "max_nodes": 2,
  "active_must_include_nodes": 3,
  "result": "rejected",
  "selected_nodes": 0,
  "rejection_code": "MUST_INCLUDE_OVER_BUDGET"
}
```

对应产物见：
- `assembly_report.turn_002_budget2_reject.json`
- `assembly_rejection_budget2_report.md`

该用例证明：
- 当 `budget < active must_include` 时，Assembler 会拒绝装配
- 不会偷偷丢掉某个 must 节点后继续产出 bundle
- 失败路径已经真实执行，不再是未覆盖代码

## 9. 最终结论

- `turn_002` 已成功完成一次真实的 supersede 冲突测试
- `patch_002` 同时落地了 `superseded_nodes` 与 `invalidates`
- 新节点 Y 使用了与旧态相同的 `entity_ref`
- 三条断言 `(a)(b)(c)` 全部通过，且 `(b)(c)` 现在由机械装配结果支撑，而不是手写 bundle
- `budget=2` 的拒绝路径也已通过机械验证
- lint 报告同时给出：
  - `status` 是当前态裁定字段
  - `state` 不参与当前态裁定
  - `n_0009` 已被识别为 superseded
