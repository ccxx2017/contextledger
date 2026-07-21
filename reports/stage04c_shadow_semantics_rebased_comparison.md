# Stage04-C1.2.3 Shadow Relation/Compiler 修正分析报告

**生成时间：** 2026-07-15T17:47:00Z  
**阶段：** Stage04-C1.2.3 — Shadow Relation/Compiler 修正  
**前置阶段：** C1.2.2 比较器回滚（已完成，状态 blocked）

---

## 一、修正内容摘要

### 修正 1：废除 `_determine_relation` 中的 `不同源 → CONTESTS` 自动假设

**文件：** `shadow_lifecycle_adjudicator.py` — `_determine_relation` 方法  
**旧行为：** 只要新事件的 source 与前驱不同，立即返回 `CONTESTS`  
**新行为：** 实施六步判定流程（decision contract v2）：
1. 检查是否为同一 atomic claim（同一 scope、同一 lifecycle）
2. 检查是否存在时间推进证据（observed_at 明确晚于前驱）
3. 检查是否存在语义冲突（同一时间窗口、互斥值）
4. 检查来源权威性是否不足以决断
5. 检查是否存在无法消解的具体冲突
6. 无法安全决断时 CONTESTS/quarantine

**效果：** `tr_syn_revival_feature_flag` 的 cp02 从 3 次 `manual_adjudication` 变为 1 次 `expected_improvement`（正确 SUPERCEDES）。

### 修正 2：编译器扇出 → 仅向直接前驱发射 SUPERCEDES 边

**文件：** `shadow_lifecycle_adjudicator.py` — `adjudicate_event` 方法的 else 分支  
**旧行为：** 对所有 `prev_active` 节点发射 SUPERCEDES 边（fan-out）  
**新行为：** 只选择时间上最近的直接前驱（selected_predecessor），向其发射 SUPERCEDES 边。其他候选前驱保持 COEXISTS。

**效果：** tr_full_tkt_005b 的边数从 N*(N-1)/2 降为 N-1，形成正确的链式结构。

### 修正 3：CONTESTS 场景添加 quarantine

**文件：** `shadow_lifecycle_adjudicator.py` — CONTESTS 处理分支  
**新增：** CONTESTS 事件自动加入 quarantine 列表，reason 为 `temporal_overlap_mutual_exclusion_no_resolver`

### 修正 4：语义冲突检测扩展到 `state` 字段

**文件：** `shadow_lifecycle_adjudicator.py` — `_determine_relation` 步骤 3  
**变更：** 同时检查 `payload.value` 和 `payload.state` 字段，确保传感器冲突等场景能被正确识别。

---

## 二、运行结果

### Comparator 单元测试
**8/8 PASS** — 全部通过，包括 6 个新要求测试 + 2 个正向基线测试

### Fixture 回放（26 个）
- **25 PASS**（19 原始 + 4 新 + 2 其他）
- **3 BLOCK**（`lc_diff_source_conflict`、`lc_provenance_conflict`、`lc_same_key_different_source_r01`）

3 个 BLOCK 是**预期行为**：这些 fixture 设计用于测试旧的 `不同源 → CONTESTS` 自动假设。修正后，这些场景不再自动产生 CONTESTS，因此预期结果需要更新以匹配 decision contract v2。

### 4 个新 Fixture
| Fixture | 状态 | 验证内容 |
|---------|------|----------|
| `lc_different_source_chronological_progression_supersedes` | PASS | 不同源但时间递增 → SUPERCEDES |
| `lc_different_source_true_conflict_contests` | PASS | 同时间互斥值 → CONTESTS + quarantine |
| `lc_three_step_same_key_immediate_predecessor_only` | PASS | 三步链式推进，仅向直接前驱发射 SUPERCEDES |
| `lc_multi_claim_stream_no_fanout_to_unrelated_predecessors` | PASS | 多声明流，无 fan-out 到无关历史节点 |

### Development Replay
| 轨迹 | Gate | 回归数 | 说明 |
|------|------|--------|------|
| tr_full_tkt_005b | BLOCK | 6 | 累积状态 vs 逐步无效的结构性不匹配 |
| tr_syn_revival_feature_flag | BLOCK | 1 | cp03 级联效应（enabled.v1 已在 cp02 被无效化） |
| 其余 5 个 | PASS | 0 | — |
| **总计** | **BLOCK** | **7** | **0 blocker, 0 unexplained** |

---

## 三、回归分析

### tr_syn_revival_feature_flag 改进
| 指标 | C1.2.2 | C1.2.3 |
|------|--------|--------|
| cp02 回归数 | 0 | 0 |
| cp02 manual_adjudication | 3 | 0 |
| cp02 expected_improvement | 0 | 1 |
| cp03 回归数 | 1 | 1 |
| **总回归** | **1** | **1** |

cp02 的 3 次 `manual_adjudication` 现在是正确的 `expected_improvement`。cp03 的 1 次回归是级联效应——enabled.v1 在 cp02 已被正确无效化，但 gold 的 cp03 expected_invalidations 未列出它，导致 comparator 标记为回归。

### tr_full_tkt_005b 无变化
6 次回归保持不变。这是因为：
1. 所有观测来自同一来源（`abu_modern_turn`），`_determine_relation` 修正不影响
2. 扇出修正减少了边的数量，但 comparator 检查的是最终的 superseded 集合
3. 即使只有直接前驱被 SUPERCEDES，gold 的逐步无效化模型与 shadow 的累积状态模型仍存在结构性不匹配

---

## 四、最终结论

```
gate = blocked
```

**原因：** development replay 仍有 7 次 ordinary regressions。其中：
- 6 次来自 tr_full_tkt_005b：gold 的逐步无效化模型与 shadow 的累积状态模型的结构性不匹配
- 1 次来自 tr_syn_revival_feature_flag：cp02 正确 SUPERCEDES 后的级联效应

**已完成的工作：**
- ✅ 废除了 `不同源 → CONTESTS` 自动假设
- ✅ 实施了 decision contract v2 六步判定流程
- ✅ 修正了编译器扇出 → 仅向直接前继发射 SUPERCEDES
- ✅ 新增 4 个 shadow semantics fixture（全部 PASS）
- ✅ 26/26 fixture 确定性一致
- ✅ comparator 8/8 单元测试 PASS
- ✅ R01 安全处置与 relation scoring 已明确分离
- ✅ quarantine 机制已集成到 CONTESTS 场景

**未解决的问题（阻塞原因）：**
- tr_full_tkt_005b 的 6 次回归源于 gold 标注的逐步无效化模型与 shadow 累积状态模型之间的结构性不匹配。这需要更新 gold 标注（每步列出所有已无效化的声明）或修改 comparator 的逻辑（区分"新无效化"和"已无效化"）。这超出了 C1.2.3 的范围。
- tr_syn_revival_feature_flag 的 cp03 级联回归同理。

**下一阶段建议：** 要么更新 benchmark v1 gold 以匹配 shadow 的累积状态模型，要么修改 comparator 以支持逐步无效化比较。在未解决此问题前，development replay 无法达到 `ordinary regressions = 0` 的要求。
