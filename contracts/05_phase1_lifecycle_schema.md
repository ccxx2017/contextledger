# Phase 1 Schema：Lifecycle / Revival 扩展（设计稿）

## 目标

- 让“同一条生命周期流（lifecycle flow）”中的多个节点能够被当作同一实体流来裁决与装配，从而支持 `tr_revival_round5x` 这类“审计→修复→验证→复验”的单流推进。
- 在不破坏现有 `entity_ref + status/state + invalidates/supersedes` 纪律的前提下，引入一个更稳定、更接近业务语义的裁决键，避免依赖纯粹的 `pending_merge` 归并来“凑出”生命周期单流。

## 非目标（本轮不做）

- 不在本轮把 `partial/conditional/valid_time` 这些 Phase 0.5 已知缺口一并纳入 schema 扩展。
- 不在本轮实现 `successor/provenance` 的版本化语义（会在本设计的“后续扩展点”里预留落点）。

## 背景问题（当前为何会卡）

- 现有机械核的失效裁决触发条件是“新旧节点 `entity_ref` 相同（且非 null）”。这在 `OpenTask/Decision/Fact` 的单实体流上成立，但在 `round5.*` 这类“同一生命周期却拆成多个 entity_ref”时失效。
- 结果是：生命周期推进不会自然产生 `invalidation/supersedes`，active-set 会把各阶段并列保留，必须依赖 resolver 将多个 entity_ref 强行归并成同一键，才能测到单流推进。

## 核心设计：新增 Lifecycle 裁决键

### 新字段（节点级）

在节点结构中新增一组可选字段（缺省为 `null`，保持完全兼容）：

- `lifecycle_ref: string | null`
  - 语义：该节点所属的“生命周期流”的稳定标识。
  - 示例：`TKT-2026-005B_round5`
- `lifecycle_stage: string | null`
  - 语义：该节点在生命周期流中的阶段标识，仅用于解释与调试，不参与硬裁决。
  - 示例：`audit` / `fix` / `verify` / `reverify` / `reconcile` / `report`
- `lifecycle_seq: number | null`
  - 语义：生命周期流内的顺序号（可由 turn 或 extractor 产生），用于在存在乱序观测时提供稳定排序锚点。
  - 规则：若为空，排序回退到 `created_turn`，再回退到节点 id 的稳定排序。

### 裁决键（Adjudication Key）

引入统一定义：

- `adjudication_key(node) = node.lifecycle_ref ?? node.entity_ref`

约束：

- 当 `adjudication_key(node)` 为 `null` 时，该节点不进入自动失效裁决（与现有 `entity_ref=null` 行为一致）。
- 当 `lifecycle_ref` 存在时，允许 `entity_ref` 在生命周期流内保持“阶段拆分”的粒度；裁决与装配以 `lifecycle_ref` 为主。

## 失效语义更新（机械核约束）

### 触发条件更新

现有触发条件：

- 新节点与某个 active 旧节点 `entity_ref` 相同（且非 null）

升级为：

- 新节点与某个 active 旧节点 `adjudication_key` 相同（且非 null）

这意味着：

- 同一 `lifecycle_ref` 下，即使 `entity_ref` 不同，也允许被视为同一“裁决流”。

### supersedes / invalidates 的纪律保持不变

保持 Phase 0.5 的硬约束不变，只把 “entity_ref 相同” 替换为 “adjudication_key 相同”：

- 若同一 `adjudication_key` 下新旧节点 `state` 发生互斥冲突，则 patch 必须同时声明：
  - 旧节点退出当前态（`status=superseded`）
  - 产生 `invalidates`（或 `supersedes`）边（以现有互斥矩阵判定）

## 装配语义更新（Assembler 读取纪律）

### 当前态成员资格

现有纪律保持不变：

- “当前什么成立”只看 `status=active`，不允许用 `state` 替代。

新增装配分组口径：

- 当前态集合按 `adjudication_key` 分桶（而不是只按 `entity_ref` 分桶）。
- 这使得 `round5.*` 的各阶段节点能够在同一桶内被自然地 supersede，从而只暴露单流的当前态。

## 对 benchmark 的直接落点（Phase 0.5 → Phase 1 的验收条件）

### tr_revival_round5x 的 schema 表达目标

- 所有 `round5.*` 阶段节点应设置同一 `lifecycle_ref = TKT-2026-005B_round5`
- 每个阶段节点的 `lifecycle_stage` 填入对应阶段名
- 生命周期推进的节点之间，应当在同一 `adjudication_key` 下形成可裁决的 supersession 链，从而：
  - `expected_invalidations` 能被命中（至少在 full replace 语义下）
  - active-set 不再并列保留审计/修复/验证各阶段

### 验收标准（以 Phase 0.5 指标为准）

- `tr_revival_round5x`：
  - invalidation：`4/4 true positive`
  - active-set：每步 `active_set_f1 = 1.0`
  - entity_resolution：`false_split_count = 0`
- 全局：
  - `must_include recall` 不低于 `D1=1.0`
  - `active-set Set-F1` 继续显著高于 `D2`

## 迁移/兼容策略（完全兼容）

- 旧数据无需迁移：缺 `lifecycle_ref` 时，系统行为与当前一致（`adjudication_key = entity_ref`）。
- 新数据逐步增量注入：
  - extractor 在识别到生命周期拆分模式（如 `*_audit/_fix/_verify/...`）时，写入 `lifecycle_ref` 与 `lifecycle_stage`
  - resolver 仍可保留，但不再是让生命周期单流成立的唯一手段

## 后续扩展点（为 successor/provenance 预留）

- 在 Phase 1 的后半段，引入 `successor/provenance` 语义时，可复用本设计的 `lifecycle_ref` 作为“版本流”的承载容器：
  - `lifecycle_ref` 负责“同一条流”
  - `successor` 边负责“流内的版本演进关系”
  - `lifecycle_stage` 可退化为 provenance 标签的一种实例

