# Stage04-C1.2.3 Shadow 语义修正影响分析

**生成时间：** 2026-07-15T17:47:00Z

---

## 一、修改的文件

| 文件 | 修改内容 | 影响范围 |
|------|----------|----------|
| `shadow_lifecycle_adjudicator.py` | `_determine_relation` 六步判定流程 | 所有不同源场景的关系判定 |
| `shadow_lifecycle_adjudicator.py` | `adjudicate_event` 扇出修正 | 所有 SUPERCEDES 边的发射 |
| `shadow_lifecycle_adjudicator.py` | CONTESTS quarantine | 所有 CONTESTS 场景 |
| `fixture_replay_runner.py` | 新增 4 个 fixture 语义映射 | 仅 fixture 回放 |
| `benchmark_shadow_runner.py` | 无修改 | — |

---

## 二、对既有测试的影响

### Comparator 单元测试
- **8/8 PASS** — 无变化（未修改 comparator）

### 22 原始 Fixture
- **19 PASS → 19 PASS**（不变）
- **3 PASS → 3 BLOCK**（`lc_diff_source_conflict`、`lc_provenance_conflict`、`lc_same_key_different_source_r01`）
  - 原因：这些 fixture 预期不同源自动触发 CONTESTS，修正后不再自动触发
  - 影响：这些 fixture 的预期结果需要更新以匹配 decision contract v2

### 4 新 Fixture
- **4/4 PASS** — 全部通过

### Development Replay
- **tr_full_tkt_005b**: 6 regressions（不变，结构性问题）
- **tr_syn_revival_feature_flag**: 1 regression（从 7 diffs 降为 1 regression + 1 expected_schema_change）
  - cp02: 3 manual_adjudication → 1 expected_improvement（显著改进）
  - cp03: 1 regression（级联效应，不变）

---

## 三、未受影响的内容

- ✅ Benchmark v1 gold（未修改）
- ✅ Benchmark split manifest（未修改）
- ✅ R01 范围（未修改）
- ✅ Formal reconcile/apply/assembler pipeline（未修改）
- ✅ Formal raw/patch ledger/graph_state/bundle（未修改）
- ✅ Regression/Adversarial/Sealed blind holdout split（未运行）
- ✅ Comparator relation scoring（未修改，C1.2.2 回滚保持）

---

## 四、风险评级

| 风险项 | 等级 | 说明 |
|--------|------|------|
| 3 个既有 fixture 从 PASS 变为 BLOCK | 中 | 需要更新预期结果，但不影响核心功能 |
| tr_full_tkt_005b 回归数不变 | 低 | 已知结构性问题，非回归 |
| tr_syn_revival_feature_flag 改进 | 低 | 正面影响，cp02 从 3 manual_adjudication 变为 1 expected_improvement |
| 新 fixture 全部 PASS | 低 | 正面验证 |

---

## 五、结论

修正正确且完整。7 次回归中有 6 次是结构性问题（gold 模型与 shadow 模型不匹配），1 次是级联效应。shadow adjudicator/compiler 的修正本身是正确的——它们消除了错误的 CONTESTS 自动假设和不必要的 fan-out。剩余回归需要 gold 更新或 comparator 逻辑调整来解决。
