# 下游装配消费契约 [PROVISIONAL]

本文件定义 Phase 1-prep 可执行的 `Assembler v1` 契约。
当前范围只覆盖 Graph-only 的正式最小装配闭环，不接入 Pack / Wiki。

## 1. 目标边界

- 输入：单个项目的 `graph_state.json`
- 输出：`ContextBundle` + `assembly_report`
- 权威源：只读 Graph；当前态成员资格只按 `status` 判定
- 不在本阶段承担的能力：
  - Pack / L3 软知识
  - Wiki / L4 深检索
  - valid-time-present 裁决增强
  - partial / conditional / revival / provenance 的能力提升

## 2. Phase 1 Assembler v1 输入

必需入参：
- `project_id`
- `turn_id`
- `graph_state.json` 路径
- `budget_profile`
- `max_nodes`

可选入参：
- `context_bundle` 输出路径
- `assembly_report` 输出路径

默认路径约定：
- `graph/projects/<project_id>/reports/context_bundle.<turn_id>.json`
- `graph/projects/<project_id>/reports/assembly_report.<turn_id>.json`

## 3. 当前态与筛选规则

- 当前态成员资格：`status=active`
- `status` 缺失时，Phase 1-prep 兼容旧图，按 `active` 处理
- `state` 不决定当前态成员资格；仅允许作为 pending open-task 的 gating 规则
- `OpenTask + state=open + 内容带待裁定信号` 的节点，可从装配结果中排除并记录到 `excluded_due_to_state`

## 4. priority 分层

允许值：
- `must_include`
- `should_include`
- `optional`
- `background`

装配顺序：
1. `must_include`
2. `should_include`
3. `optional`
4. `background`

规则：
- 预算不足时，绝不静默丢弃 `must_include`
- 若 active `must_include` 数量超过 `max_nodes`，Assembler 必须拒绝装配并返回退出码 `2`
- 被 `superseded` 的节点即使曾是 `must_include`，也必须退出当前态

## 5. ContextBundle v1 最小结构

`ContextBundle` 至少包含：
- `kind`
- `project_id`
- `turn_id`
- `source_graph`
- `authority`
- `assembly`
- `l1_baseline`
- `l2_task_state`
- `budget_policy`
- `provenance`

其中：
- `l1_baseline`：按 priority 分层后的节点正文
- `l2_task_state`：当前任务焦点、活跃节点数、已装配节点数
- `provenance`：若节点带 `source.raw_id / source.span`，则原样透传

## 6. assembly_report v1 最小结构

`assembly_report` 至少包含：
- `kind`
- `project_id`
- `turn_id`
- `result`
- `policy`
- `summary`
- `selected_node_ids`
- `selected_by_priority`
- `excluded_due_to_status`
- `excluded_due_to_state`
- `excluded_due_to_budget`

拒绝装配时还必须包含：
- `rejection.code`
- `rejection.message`
- `rejection.active_must_include_node_ids`

## 7. 实施脚本

Phase 1-prep 的参考实现脚本为：
- `graph/scripts/build_context_bundle.py`

该脚本必须：
- 移除 `phase0_manual` 路径硬编码
- 支持主项目 `graph/projects/<project_id>/graph_state.json`
- 支持按 `project_id / turn_id / budget` 生成正式产物
