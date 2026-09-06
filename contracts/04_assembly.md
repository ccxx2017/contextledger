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

## 7. action-readiness 行动就绪度声明（GPT-6 评审工作包 C）

> 关键区分（评审 §二.3）：**主图未被错误写入** ≠ **主图足够完整、可以支撑当前行动**。
> quarantine 成功只证明前者。Assembler 必须显式声明后者，禁止在存在未裁定事件时
> 悄悄返回"正常当前态"。

### 7.1 readiness manifest

每次装配除 `context_bundle` 与 `assembly_report` 外，必须产出
`assembler_manifest.json`（`kind: assembler_manifest.v1`），至少包含：

| 字段 | 语义 |
|---|---|
| `state_revision` | `f"{committed_turn:04d}:{graph_state_sha256[:12]}"`，行动前核验的唯一版本凭据 |
| `readiness` | `ready` / `degraded` / `blocked` 三态（封闭枚举） |
| `reason_codes` | 触发降级/阻塞的原因代码（封闭词表，见 7.2） |
| `unresolved_event_ids` | 已知未裁定事件的标识（quarantine 登记簿中 unreviewed 条目等） |
| `integrity_risks` | 结构化的完整性风险说明（自由文本 + 关联 reason_code） |

三态语义：
- `ready`：无未裁定事件、预算无溢出、装配输入与权威图一致
- `degraded`：存在非阻断风险（如 lint warning、quarantine 有已裁定条目），当前态可用但须知情
- `blocked`：存在不得基于当前态行动的情形（must_include 溢出、未裁定隔离条目、
  绕过闸门发布等），宿主不得消费该装配结果

### 7.2 reason_codes 封闭词表（初版）

- `MUST_INCLUDE_OVER_BUDGET`：active must_include 超预算，装配被拒绝（已实现，§4）
- `QUARANTINE_NONEMPTY`：quarantine 登记簿存在 `unreviewed` 条目（未裁定隔离写入）
- `LINT_WARNING_PRESENT`：当前图存在未登记的 lint warning
- `STATE_REVISION_STALE`：行动前核验发现 state_revision 已过期
- `PREMISE_VIOLATED`：行动前提核验失败（见 7.4）
- `PENDING_MERGE_OVERDUE`：pending_merge 登记簿存在超期未消化条目
- `PUBLISHED_WITH_BYPASS`：本轮经 `--unsafe-rebuild-mode` 绕过闸门发布

### 7.3 宿主消费规则

- 宿主（或任何行动方）在基于装配结果行动前，必须读取 `assembler_manifest.json`
- `readiness: blocked` → 禁止行动
- `readiness: degraded` → 允许行动，但 reason_codes 必须随行动上下文透传
- `state_revision` 是行动前提的一部分（见 7.4）

### 7.4 行动前版本/前提核验接口

宿主在关键动作执行前，通过只读接口核验装配前提是否仍然成立：

- 脚本：`graph/scripts/verify_preaction.py`
- 输入：`--project-id`、`--state-revision`（行动时依据的版本）、`--must-include` 清单、可选 `--premise k=v`
- 判定：当前权威图的 state_revision 与所依据版本一致，且前提仍成立 → 退出码 `0`
- 任一不成立 → 退出码 `2`，stdout 输出 `{"reason_codes": [...], "detail": ...}`
- 退出码 `2` 时宿主必须重新装配、重新决策，不得沿用旧依据执行

> 该接口只回答"依据是否过期"，不保证模型理解、遵守或执行正确（评审 §二.4）。

## 8. 实施脚本

Phase 1-prep 的参考实现脚本为：
- `graph/scripts/build_context_bundle.py`

该脚本必须：
- 移除 `phase0_manual` 路径硬编码
- 支持主项目 `graph/projects/<project_id>/graph_state.json`
- 支持按 `project_id / turn_id / budget` 生成正式产物
