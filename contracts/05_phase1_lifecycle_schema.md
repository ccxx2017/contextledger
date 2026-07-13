# Phase 1 RFC：Lifecycle / Revival Schema v1

## 文档状态

- 状态：`RFC Draft`
- 阶段：`Phase 1 / Stage02`
- 兼容策略：`完全兼容旧图读取`
- 当前实现状态：`未进入真实系统实现，仅完成 RFC`

## 1. 问题定义

Phase 0.5 已证明两件事：

1. 机械核在 `full invalidation` 上是成立的；
2. `tr_revival_round5x` 这类“审计 -> 修复 -> 验证 -> 复验”的单流推进，目前只能靠 resolver / pending_merge 勉强补出来，schema 本身没有一等表达。

当前根因不是“系统不会替换旧状态”，而是：

- 同一条生命周期流被拆成多个 `entity_ref`；
- 机械核的失效触发条件又只看 `entity_ref`；
- 因而 revival / lifecycle progression 无法自然进入裁决链。

本 RFC 的目标是把“同一对象的一条状态演化流”从 `entity_ref` 中拆出来，形成稳定的生命周期裁决键。

## 2. 设计目标

- 让 `tr_revival_round5x` 这类单流推进场景得到一等表达；
- 保持现有 `status/state/invalidates/supersedes` 纪律不被破坏；
- 保持旧图、旧 patch、旧 benchmark 的读取兼容；
- 不让 LLM 直接决定最终身份、顺序或当前态；
- 为后续 `successor/provenance` 扩展预留位置，但本 RFC 不实现它。

## 3. 非目标

本 RFC 不在本轮解决：

- 通用 `partial invalidation` 路径级表达；
- 通用 `conditional invalidation` 逻辑引擎；
- `valid_time` 的完整双时态编译；
- `successor/provenance` 的版本图；
- 跨项目知识合并；
- MemoryPack / 多宿主同步。

## 4. 核心抽象

### 4.1 三个键的职责拆分

```text
entity_ref       = 对象身份
lifecycle_ref    = 对象的一条状态演化流
adjudication_key = 冲突裁定分桶键
```

定义：

```text
adjudication_key(node) = node.lifecycle_ref ?? node.entity_ref
```

约束：

- `entity_ref` 继续表示“这是什么对象”；
- `lifecycle_ref` 表示“这是该对象的哪一条生命史 / 执行流 / 轮次流”；
- `adjudication_key` 只负责“它应与谁发生机械裁决”；
- 三者不得隐式互相替代。

### 4.2 新增字段

在节点上新增 5 个可选字段，默认 `null`：

- `lifecycle_ref: string | null`
- `lifecycle_stage: string | null`
- `lifecycle_seq: integer | null`
- `observed_at: string | null`
- `effective_at: string | null`

字段语义：

- `lifecycle_ref`：生命周期流稳定标识，例如 `TKT-2026-005B_round5`
- `lifecycle_stage`：阶段标签，只用于解释与 lint，不直接驱动当前态
- `lifecycle_seq`：同一生命周期流内的稳定顺序号，由机械层分配
- `observed_at`：系统收到该事件的时刻，必须单调、不可回写
- `effective_at`：业务上生效的时间，可为空、可晚到、可不确定

## 5. 身份不变量

必须满足以下不变量：

1. 节点可以没有 `lifecycle_ref`
2. 一个 `lifecycle_ref` 只能归属于一个 canonical entity
3. 一个 `entity_ref` 可以拥有多条 `lifecycle_ref`
4. `lifecycle_ref` 一旦分配，不得在原节点上原地修改
5. alias merge 时，迁移的是“canonical entity 归属”，不是重写旧节点的 `lifecycle_ref`
6. `lifecycle_ref` 不要求跨项目全局唯一，但要求项目内稳定唯一

如果违反以上不变量，必须进入 `quarantine`，不得静默写入主图。

## 6. 责任边界

### 6.1 LLM 允许做的事

- 提取 surface entity
- 提取可能的 lifecycle 线索
- 提取阶段语义
- 提取显式时间 / 环境 / 来源
- 提出候选关系：`supersedes / contests / coexists / revives`

### 6.2 Resolver 允许做的事

- 决定 canonical entity
- 给出 `lifecycle_ref` 候选匹配
- 给出 alias / lifecycle match 证据
- 输出 `abstain`

### 6.3 机械层必须做的事

- 分配最终 `lifecycle_ref`
- 分配 / 校验 `lifecycle_seq`
- 计算 `adjudication_key`
- 判定合法状态转移
- 处理 observed/effective 时序
- 决定当前 active 集合

原则：

> LLM 提议语义，机械层分配身份并执行状态转移。

## 7. Sequence 与双时态

### 7.1 顺序规则

`lifecycle_seq` 不是 LLM 自由生成的字段。

分配规则：

1. 同一 `lifecycle_ref` 下按 `observed_at` 排序
2. 若 `observed_at` 缺失，则按 `created_turn`
3. 若仍冲突，则按节点 id 稳定排序
4. `effective_at` 不改变既有 `lifecycle_seq`，只影响后续时序裁决解释

### 7.2 late arrival 处理

- `observed_at` 决定账本写入顺序，必须稳定
- `effective_at` 决定业务上“声称何时生效”
- 晚到事件不得原地回写旧 patch
- 晚到事件是否改变当前态，由 compiler 在读取时根据规则解释

本 RFC 第一版只要求字段存在与规则明确，不要求完整 `valid_time` 求值。

## 8. 裁决关系类型

Phase 1 将新旧声明之间的关系扩展为：

```text
SUPERCEDES
COEXISTS
CONTESTS
REVIVES
UNRELATED
```

语义：

- `SUPERCEDES`：明确替代，可进入 `invalidates/supersedes`
- `COEXISTS`：作用域不同或允许并存，不改当前态
- `CONTESTS`：存在冲突，但不足以判谁失效，不改当前态
- `REVIVES`：在同一生命周期流中恢复先前状态
- `UNRELATED`：不同流，不参与裁决

关键约束：

> provenance conflict 不得再被默认折叠成 full invalidation。

## 9. 状态转移规则

本 RFC 不扩张大量状态枚举，而是采用“节点事实状态 + 关系边 + compiler 派生当前态”的方式。

允许的高层转移：

```text
proposed -> active
active -> superseded
suspended -> active
active -> contested
active -> revived
```

映射原则：

- `status` 仍然只允许 `active/superseded`
- `revival` 不通过回写旧节点 `status=active` 实现
- revival 由新事件 + `REVIVES` 关系驱动，由 compiler 派生“当前恢复态”

## 10. 失效裁决规则更新

现有触发条件：

- 新旧节点 `entity_ref` 相同（且非 null）

升级为：

- 新旧节点 `adjudication_key` 相同（且非 null）

保持以下纪律不变：

- 若机械核判定为替代或矛盾，patch 必须显式声明对应边与旧节点退出当前态
- 任何“只改 state 不改 status”的写法仍属违约

## 11. 对 partial / conditional / revival 的最小语义

### 11.1 Full

新声明完整替代旧声明，走现有 `invalidates/supersedes`

### 11.2 Partial

Phase 1 不做通用 path 级失效系统。采用：

- 优先把声明原子化
- 无法原子化时进入 `quarantine`

### 11.3 Conditional

必须显式携带条件作用域，例如环境、分支、市场、日期窗。

若缺失条件作用域：

- 不得执行硬失效
- 进入 `CONTESTS` 或 `quarantine`

### 11.4 Revival

- revival 是“新事件恢复先前状态”
- 不允许把旧 patch 原地改回 `active`
- 必须通过新节点 + `REVIVES` 关系表达
- compiler 根据生命周期流派生“当前恢复态”

## 12. Resolver 的 abstain 机制

Resolver 必须允许：

```json
{
  "resolution": "abstain",
  "reason": "ambiguous_lifecycle"
}
```

规则：

- false merge 比 missed merge 更危险
- false invalidation 比 missed invalidation 更危险
- 低置信度 lifecycle 解析不得静默生成新 canonical 结论
- 必须走 `quarantine` 或待裁定路径

## 13. 兼容 / 迁移策略

完全兼容旧图读取：

```text
schema_version < lifecycle_v1:
    adjudication_key = entity_ref

schema_version >= lifecycle_v1:
    adjudication_key = lifecycle_ref if present else entity_ref
```

迁移原则：

- 不要求一次性全图迁移
- 新字段缺失时按 legacy 规则读取
- 迁移前后必须保留 checkpoint
- benchmark / replay 先做 shadow 对比，再替换主链

## 14. 必须新增的 lint 规则

至少新增以下 lint：

1. `lifecycle_ref` 指向多个 canonical entity
2. 同一 `lifecycle_ref` 下 `lifecycle_seq` 重复或倒退
3. `REVIVES` 找不到合法目标
4. `partial` 缺少原子化或作用域
5. `conditional` 缺少 condition
6. provenance conflict 被直接写成 full invalidation
7. `adjudication_key` 在无授权情况下变化
8. legacy 节点与 lifecycle_v1 节点发生模糊混裁

## 15. 必须具备的 replay fixtures

Phase 1 实现前，至少补齐以下 fixture：

1. 同实体，不同 lifecycle
2. alias 指向同 lifecycle
3. alias 指向不同 lifecycle
4. late arrival
5. provenance conflict
6. partial
7. conditional
8. revival
9. false alias temptation
10. sequence collision
11. legacy migration

## 16. 对 benchmark 的直接验收目标

### 16.1 revival

`tr_revival_round5x` 目标：

- `invalidation true_positive = 4/4`
- 每步 `active_set_f1 = 1.0`
- `false_split_count = 0`

### 16.2 红线

- `must_include recall >= D1`
- 关键约束 `false invalidation = 0`，否则必须被隔离
- `silent corruption = 0`

### 16.3 provenance

`tr_prov_run54b` 在 Phase 1 不要求完全解决，但必须做到：

- provenance conflict 不再默认被写成 full invalidation
- `alias merge` 与 `version succession` 不再混用

## 17. 实现顺序建议

按 Stage02 的节奏，下一步顺序应为：

1. 先冻结 current state manifest
2. 再冻结 benchmark / holdout / baseline 定义
3. 先做 lifecycle fixtures
4. 再做 shadow replay
5. replay 通过后才进真实链路实现

## 18. 当前结论

本 RFC 当前给出的不是“马上上代码”，而是：

- 明确 `entity_ref / lifecycle_ref / adjudication_key` 的职责拆分
- 明确 lifecycle_v1 的兼容规则
- 明确 revival / provenance conflict 的最小语义
- 明确哪些情况必须 quarantine

只有这些被钉死后，Phase 1 的真实实现才值得开始。
