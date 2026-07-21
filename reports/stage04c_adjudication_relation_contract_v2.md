# Stage04-C1.2.3: Shadow Adjudication Relation Decision Contract v2

**生成时间：** 2026-07-15T16:45:00Z  
**替代版本：** 旧版 `_determine_relation` 中的 `different_source → CONTESTS` 默认规则  
**适用范围：** shadow_lifecycle_adjudicator.py 的 `_determine_relation` 方法

---

## 一、废弃规则

以下规则在 v2 中**不再作为默认行为**：

```
不同源 → CONTESTS（自动假设）
```

原代码（第 238-243 行）：
```python
if prev_active:
    prev_source = prev_active[0].get("source", "unknown")
    if new_source != prev_source:
        return "CONTESTS"
```

**问题：** 该规则将所有不同源的声明视为来源冲突，忽略了时间顺序、状态演化和证据充分性。release_note 和 incident_note 对同一 feature flag 的不同时间点的报道是正常的时间推进（SUPERCEDES），而非来源冲突（CONTESTS）。

---

## 二、新版六步判定流程

当新事件与现有 active 节点共享同一 `adjudication_key` 时，按以下顺序判定关系：

### 步骤 1：是否为同一 atomic claim（同一 scope、同一 lifecycle）

检查新声明和候选前驱声明是否指向同一 atomic claim（相同的 claim dimension + entity_ref + scope）。如果是同一 claim 的后续状态更新，进入步骤 2。

### 步骤 2：是否存在足够证据支持状态推进

检查新声明的 `observed_at` / `effective_at` 是否明确晚于前驱声明。如果新声明提供了新的证据（如更新的状态值、额外的执行结果），且时间上在前驱之后，则支持 SUPERCEDES。

### 步骤 3：是否存在语义冲突

检查新声明和前驱声明是否在**同一时间点**断言互斥的值。例如，两个声明都声称 feature 在 T09:00 处于 enabled 状态，但一个说 enabled、一个说 disabled。如果有时间重叠且值互斥，进入步骤 4。

### 步骤 4：来源权威性/可信度是否不足以决断

检查新来源的权威性是否低于或等于前驱来源，或者是否存在可信度争议（如匿名来源 vs 官方发布）。如果存在权威性质疑，进入步骤 5。

### 步骤 5：是否存在无法消解的具体冲突

只有在同时满足以下条件时才判定为 CONTESTS：
- 同一时间点（或时间窗口重叠）
- 互斥的值
- 无法通过时间顺序消解
- 来源权威性相当

### 步骤 6：无法安全决断时 CONTESTS / quarantine

如果以上步骤均无法得出结论（如缺少时间信息、声明模糊），则：
- 标记为 CONTESTS
- 同时放入 quarantine 列表
- 记录 conflict_marker

---

## 三、关系判定表

| 场景 | 关系 |
|------|------|
| 同一 atomic claim、同一 scope、有足够证据支持状态推进 | `SUPERCEDES`（首选） |
| 同一 atomic claim、同一 scope、数据矛盾但证据不够决断 | `CONTESTS` |
| 不同 atomic claim、同一 scope | `COEXISTS` / `UNRELATED` |
| 不同 entity / 不同 lifecycle | `COEXISTS` |
| 来源 alias 解析不确定 | `abstain/quarantine` |

---

## 四、tr_syn_revival_feature_flag 验证

在 `tr_syn_revival_feature_flag` 中：

- cp02: incident_note 报道 feature disabled，release_note 之前报道 enabled。时间上 T09:00 > T08:00，且状态从 enabled 变为 disabled 是合理的状态推进。→ **应判定为 SUPERCEDES**，而非 CONTESTS。

- cp03: release_note 报道 feature enabled.v2，时间 T13:00 > T09:00，状态从 disabled 变回 enabled。→ **应判定为 REVIVES**（ revival signal 检测优先）。

新版 decision contract 正确区分了"不同来源但时间推进"和"真正来源冲突"的边界。
