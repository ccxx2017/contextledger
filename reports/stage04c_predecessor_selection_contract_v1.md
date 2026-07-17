# Stage04-C1.2.3: Predecessor Selection Contract v1

**生成时间：** 2026-07-15T16:45:00Z  
**适用范围：** shadow_lifecycle_adjudicator.py 的 `adjudicate_event` 中 SUPERCEDES 边的发射逻辑

---

## 一、问题

当前代码对同一 adjudication_key 下的所有 active 前驱都发射 SUPERCEDES 边（fan-out），导致：
- tr_full_tkt_005b 中 obs03 对 obs01 和 obs02 都发射 SUPERCEDES
- 但 gold 期望只有直接前驱 obs02 被 SUPERCEDES

---

## 二、Predecessor Selection 规则

### candidate_predecessors 定义

```
candidate_predecessors:
  - same adjudication_key
  - compatible scope（同一 dimension 或可归一化的 scope）
  - compatible atomic predicate（同一 atomic claim 或不同但兼容的 claim）
  - active or revivable historical state
  - temporally prior under observed/effective-time policy
```

### selected_predecessor 规则

```
selected_predecessor:
  - 唯一可辨识的直接前驱
  - 时间上最接近新事件的 active 节点
  - 如果存在多个时间相同的前驱 → 使用 lifecycle_seq 最高者
  - 如果仍然无法唯一确定 → 全部标记为 CONTESTS 并 quarantine
```

### 只向 selected_predecessor 发射 SUPERCEDES 边

**禁止**向 candidate_predecessors 中未被选中的节点发射 SUPERCEDES 边。

如果存在未被选中的候选前驱：
- 它们与新声明的关系应为 COEXISTS 或 UNRELATED
- 不应被标记为 superseded

---

## 三、边元数据记录

每条发出的边必须携带以下元数据：

```
edge_id: 唯一标识符
relation: SUPERCEDES / CONTESTS / COEXISTS / REVIVES
source_claim_id: 新声明的 claim_id
target_claim_id: 前驱声明的 claim_id
predecessor_selection_rule_id: "immediate_temporal_predecessor"
candidate_predecessor_ids: [所有候选前驱的 claim_id 列表]
selected_predecessor_id: 被选中的前驱 claim_id
selection_evidence: 选择理由（如 "observed_at: new=18:00 > target=09:00"）
```

---

## 四、多前驱场景处理

当存在多个候选前驱时（非单一链式场景）：

1. **唯一直接前驱** → 向其发射 SUPERCEDES，其他前驱保持 COEXISTS
2. **无唯一直接前驱**（多个时间相同或无法排序）→ 全部标记为 CONTESTS，放入 quarantine
3. **无候选前驱** → 创建新节点，无边
