# validate_v2 · 独立验收集（评审第二轮 §四 修订版）

## 状态：已收集并冻结（2026-09-07，v2.0，6 案例）

冻结依据：P1/P2 pilot 通过（实验装置被证明真实工作）后，按收集规范从
`raw/projects/abu_modern/s001` 的 64 个**未开采轮次**中选定 6 段真实轨迹，
逐条编写观测与 gold，`validate_v2_manifest.json`（逐文件 sha256）落盘即冻结。

| 案例 | 形态 | 来源 |
|---|---|---|
| tr_vv2_01_runid_confusion | provenance_conflict + 共存负样本 | turn_066 |
| tr_vv2_02_cachepollution_reject | full invalidation + 负样本 decoy | turn_077 |
| tr_vv2_03_abort_handover | 中止 + 责任移交 + 冲突维持负样本 | turn_081 |
| tr_vv2_04_rootcause_update | 根因更新（informational invalidation） | turn_077→082 |
| tr_vv2_05_version_history_negative | 纯负样本（历史引用不失效） | turn_003 |
| tr_vv2_06_compaction_pressure | 记忆压力（压缩稿 source-of-record）+ 负样本 | 压缩稿 |

结构验证已通过（哈希/引用/来源隔离）；**集合未被消耗**——评分运行留待正式成对运行阶段。
已知局限见 manifest 的 known_limitations（改派/恢复独立轨迹段缺失，由 vv2_01/vv2_03 部分覆盖；
n=6 且集中于 Round 5/6 弧段，结果不外推）。

## 顺序纪律（评审 §四核心修正）

```
版本与接缝证明 → 独立 pilot → 修正实验装置 → 冻结 validate_v2 → 正式成对运行
```

**validate_v2 不用于调试**插件、评分器、宿主适配——这些在独立冒烟案例与
pilot 开发轨迹上完成（见 `reports/review_round2/pilot_design.md`）。

## 用途与定位

6–8 条真实轨迹 = **第一轮小规模价值验证**，不包装成广泛可靠性证明。
seal 的 blind_holdout（2 条）继续封存。

## 构成要求（收集前确认）

1. **来源**：未参与任何 v1/v2/v3 规则调参、未参与 pilot 的真实会话；
   不得从既有轨迹改名/改实体/改数值派生（模板泄漏检测同 v1_freeze）。
2. **按整条轨迹划分**，不做事件级随机拆分。
3. **判据先于数据**：gold 规则沿用 phase05_v3 schema；修订 gold 须先在
   development 验证再重标本集，禁止看完结果改 gold。
4. **一次性使用**：仅在正式成对运行阶段跑一次；跑完即转为历史结果。
5. **覆盖要求**（6–8 条中至少包含）：
   - 取消、改派、晚到、恢复各 ≥1（对应评审首场景四事件）；
   - **不应失效的负样本** ≥1（非失效 decoy）；
   - **关键事件未裁定/进入 quarantine 的案例** ≥1（验证隔离与 readiness 路径）；
   - **能激活新 lifecycle 路径的案例** ≥1（patch 真实携带 lifecycle 字段，
     主链 adjudicator 路径实际触发——补上 B 线缺的真实证据链）。
6. **冻结动作**：collect 完成后生成 `validate_v2_manifest.json`
   （逐文件 sha256，格式同 v1_freeze）+ 计分规则快照；冻结后
   实现/gold/配置不得修改，任何修改开启新实验版本并保留失败结果（评审 §六.6）。

## 运行方式（冻结后）

```bash
python graph/scripts/score_phase05.py --project-dir graph/projects/abu_modern/benchmark/validate_v2
```

结果与 v1_freeze baselines 对照，双分母（submitted_only / all_inputs）并报；
行动收益指标按 `reports/review_round2/pilot_design.md` 主报告模板出具，
Graph 指标为诊断附件。
