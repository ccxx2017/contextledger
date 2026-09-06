# validate_v2 · 独立验收集（评审第二轮 §四 修订版）

## 状态：未收集。**冻结时点后移**——pilot 通过之后才收集并冻结，此前不落任何轨迹

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
