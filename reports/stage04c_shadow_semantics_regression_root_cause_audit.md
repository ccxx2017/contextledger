# Stage04-C: 7 次普通回归根因审计报告

**生成时间：** 2026-07-15T16:44:00Z  
**审计范围：** tr_full_tkt_005b（6次回归）+ tr_syn_revival_feature_flag（1次回归）  
**对比照版本：** Comparator v2 post-rollback（C1.2.2）  
**Shadow 组件版本：** shadow_lifecycle_adjudicator.py + shadow_compiler.py（未修改）

---

## 一、tr_full_tkt_005b — 6 次回归（编译器扇出缺陷）

### 回归 #1：cp_after_obs03 — tr_full_tkt_005b.obs01.active

| 字段 | 值 |
|------|------|
| case_id | tr_full_tkt_005b |
| checkpoint_id | cp_after_obs03 |
| raw observations | obs03 引入 tr_full_tkt_005b.obs03.active（ticket_state=open） |
| gold relation/state | COEXISTS — obs01.active 不在 gold 的 expected_invalidations 中 |
| shadow relation/state | SUPERCEDES — shadow 中 obs03.active → obs01.active 存在边，obs01.active 状态为 superseded |
| claim decomposition | 单个原子声明：TKT-2026-005B 的 ticket_state=open |
| entity_ref | TKT-2026-005B（跨所有 obs 一致） |
| lifecycle_ref | 同生命周期（隐含于相同 dimension/entity） |
| adjudication_key | {entity:TKT-2026-005B, dimension:ticket_state} |
| source/channel/provenance | abu_modern_turn / turn_0115（所有 obs 同源） |
| observed_at | obs03: 2026-01-03T18:00:00Z |
| effective_at | 2026-01-03T18:00:00Z |
| candidate predecessor set | {obs01.active, obs02.active}（两者均在 obs03 前处于 active 状态） |
| selected predecessor | **obs02.active**（直接前驱，时间最近） |
| actual emitted edges | obs03.active → obs01.active（SUPERCEDES）, obs03.active → obs02.active（SUPERCEDES） |
| expected emitted edges | obs03.active → obs02.active（SUPERCEDES）仅一条 |
| actual invalidation set | {obs01.active, obs02.active} |
| gold invalidation set | {obs02.active} |
| active-set impact | obs01.active 被错误标记为 superseded |
| must_include/bundle impact | must_include=obs03.active，不受影响 |
| **root-cause layer** | **compiler_edge_emission** |
| **minimal repair target** | shadow_compiler 的边发射逻辑：只向直接前驱发射 SUPERCEDES 边 |

### 回归 #2：cp_after_obs04 — tr_full_tkt_005b.obs01.active

| 字段 | 值 |
|------|------|
| checkpoint_id | cp_after_obs04 |
| raw observations | obs04 引入 tr_full_tkt_005b.obs04.active |
| gold relation/state | COEXISTS — obs01.active 不在 gold expected_invalidations 中 |
| shadow relation/state | SUPERCEDES — obs04.active → obs01.active |
| candidate predecessor set | {obs01.active, obs02.active, obs03.active} |
| selected predecessor | obs03.active（直接前驱） |
| actual emitted edges | obs04.active → obs01.active, obs04.active → obs02.active, obs04.active → obs03.active |
| expected emitted edges | obs04.active → obs03.active |
| root-cause layer | **compiler_edge_emission**（与 #1 同源） |

### 回归 #3：cp_after_obs04 — tr_full_tkt_005b.obs02.active

| 字段 | 值 |
|------|------|
| checkpoint_id | cp_after_obs04 |
| gold relation/state | COEXISTS — obs02.active 不在 gold expected_invalidations 中 |
| shadow relation/state | SUPERCEDES — obs04.active → obs02.active |
| candidate predecessor set | {obs01.active, obs02.active, obs03.active} |
| selected predecessor | obs03.active |
| actual emitted edges | obs04.active → obs02.active（多余边） |
| expected emitted edges | 不应存在 obs04 → obs02 的边 |
| root-cause layer | **compiler_edge_emission** |

### 回归 #4：cp_after_obs05 — tr_full_tkt_005b.obs01.active

| 字段 | 值 |
|------|------|
| checkpoint_id | cp_after_obs05 |
| gold relation/state | COEXISTS |
| shadow relation/state | SUPERCEDES — obs05.active → obs01.active |
| candidate predecessor set | {obs01.active, obs02.active, obs03.active, obs04.active} |
| selected predecessor | obs04.active |
| actual emitted edges | obs05.active → obs01.active, obs05.active → obs02.active, obs05.active → obs03.active, obs05.active → obs04.active |
| expected emitted edges | obs05.active → obs04.active |
| root-cause layer | **compiler_edge_emission** |

### 回归 #5：cp_after_obs05 — tr_full_tkt_005b.obs03.active

| 字段 | 值 |
|------|------|
| checkpoint_id | cp_after_obs05 |
| gold relation/state | COEXISTS |
| shadow relation/state | SUPERCEDES — obs05.active → obs03.active |
| candidate predecessor set | {obs01.active, obs02.active, obs03.active, obs04.active} |
| selected predecessor | obs04.active |
| actual emitted edges | obs05.active → obs03.active（多余边） |
| expected emitted edges | 不应存在 obs05 → obs03 的边 |
| root-cause layer | **compiler_edge_emission** |

### 回归 #6：cp_after_obs05 — tr_full_tkt_005b.obs02.active

| 字段 | 值 |
|------|------|
| checkpoint_id | cp_after_obs05 |
| gold relation/state | COEXISTS |
| shadow relation/state | SUPERCEDES — obs05.active → obs02.active |
| candidate predecessor set | {obs01.active, obs02.active, obs03.active, obs04.active} |
| selected predecessor | obs04.active |
| actual emitted edges | obs05.active → obs02.active（多余边） |
| expected emitted edges | 不应存在 obs05 → obs02 的边 |
| root-cause layer | **compiler_edge_emission** |

---

## 二、tr_syn_revival_feature_flag — 1 次回归（级联效应）

### 回归 #7：cp_after_tr07_obs03 — tr07.feature.enabled.v1

| 字段 | 值 |
|------|------|
| case_id | tr_syn_revival_feature_flag |
| checkpoint_id | cp_after_tr07_obs03 |
| raw observations | obs03 引入 tr07.feature.enabled.v2（来源 release_note） |
| gold relation/state | COEXISTS — enabled.v1 不在 gold expected_invalidations 中（gold 期望在 cp02 已被无效化） |
| shadow relation/state | SUPERCEDES — shadow 中 enabled.v2 → enabled.v1 存在 SUPERCEDES 边 |
| claim decomposition | 同一 atomic claim（feature flag 启用状态）的不同版本 |
| entity_ref | Alpha feature |
| lifecycle_ref | 同一生命周期 |
| adjudication_key | {entity:Alpha feature, dimension:feature_flag_state} |
| source/channel/provenance | release_note（与 cp02 的 incident_note 不同源） |
| observed_at | 2026-01-02T13:00:00Z |
| effective_at | 2026-01-02T13:00:00Z |
| candidate predecessor set | {enabled.v1}（cp02 时 enabled.v1 因 CONTESTS 保持 active） |
| selected predecessor | enabled.v1（唯一的 active 前驱） |
| actual emitted edges | enabled.v2 → enabled.v1（SUPERCEDES） |
| expected emitted edges | 不应存在此边（gold 期望 enabled.v1 已在 cp02 被无效化） |
| actual invalidation set | {enabled.v1} |
| gold invalidation set | {}（cp03 的 gold 不包含 enabled.v1） |
| active-set impact | enabled.v1 在 cp03 被标记为 superseded |
| must_include/bundle impact | must_include=enabled.v2，不受影响 |
| **root-cause layer** | **adjudication_relation + predecessor_selection** |
| **minimal repair target** | shadow adjudicator 的 CONTESTS 自动假设（不同源→CONTESTS）导致 cp02 未正确无效化 enabled.v1，进而导致 cp03 产生级联回归 |

---

## 三、根因总结

### tr_full_tkt_005b（6 次回归）

**统一根因：compiler_edge_emission**

Shadow adjudicator 的 `_determine_relation` 返回 `SUPERCEDES`（同源，正确）。但在 `adjudicate_event` 的 else 分支（第 156-163 行）：

```python
for prev in prev_active:
    if prev.get("lifecycle_ref") == lifecycle_ref:
        patch["superseded_nodes"].append(prev["node_id"])
        patch["new_edges"].append({"source": node_id, "target": prev["node_id"], "relation": "supersedes"})
```

这段代码遍历**所有** `prev_active` 节点，向每一个发射 SUPERCEDES 边。这就是 fan-out 缺陷。

**正确的行为应该是：** 只选择**时间上最近的直接前驱**（selected_predecessor），向其发射 SUPERCEDES 边。其他候选前驱应保持 COEXISTS 或 UNRELATED 关系。

### tr_syn_revival_feature_flag（1 次回归）

**根因链：**

1. **第一层：adjudication_relation** — `_determine_relation` 中 `new_source != prev_source → CONTESTS` 是过度匹配。release_note 和 incident_note 对同一生命周期上的同一声明的不同时间点的报道，应判定为 SUPERCEDES（时间推进），而非 CONTESTS（来源冲突）。

2. **第二层：predecessor_selection** — 因为 cp02 产生了 CONTESTS 而非 SUPERCEDES，enabled.v1 没有被无效化，保持在 active 状态。到 cp03 时，enabled.v2 看到 enabled.v1 仍然是 active，于是对其发射 SUPERCEDES 边。这是 cp02 错误的级联结果。

3. **第三层：compiler_edge_emission** — 如果 cp02 正确产生 SUPERCEDES，enabled.v1 会被正确无效化，cp03 就不会有 enabled.v1 作为 candidate predecessor，从而不会产生这条回归边。

### 根因分类分布

| 回归编号 | root-cause layer |
|---------|-----------------|
| #1 | compiler_edge_emission |
| #2 | compiler_edge_emission |
| #3 | compiler_edge_emission |
| #4 | compiler_edge_emission |
| #5 | compiler_edge_emission |
| #6 | compiler_edge_emission |
| #7 | adjudication_relation（根源）+ predecessor_selection（级联） |

**所有 7 次回归均可追溯至 shadow adjudicator/compiler 的两个可修复缺陷：**
1. `_determine_relation` 的 CONTESTS 自动假设（不同源即 CONTESTS）
2. `adjudicate_event` 的 fan-out 边发射逻辑（对所有 prev_active 发射 SUPERCEDES）

**不使用 "cascading effect" 作为根因类别。** 级联是结果描述，不是根因分类。
