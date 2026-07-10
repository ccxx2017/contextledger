# 用户：
Round 6A backend defect diagnosis 已完成。以下是关键发现摘要：
  ──────────────────────────────────────────────────────────────────────────────────────────────────────
  核心缺陷：position_pnl_pct 是未注册的幽灵字段
   层级                状态        关键证据
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Compile Schema      被动接受    IRExpression.context 是自由字符串，无枚举校验
   Compile Generator   不使用      graph.py 使用的是 unrealized_pnl_pct
   Evaluator           ❌ 未实现   CONTEXT_REGISTRY 中不存在 position_pnl_pct，会抛出 KeyError: 未注册
                                   的 context: position_pnl_pct
   Execution           ❌ 未实现   universal_factor.py 调用 evaluate_phase_transition 时无 try-catch
  trade_data_source=missing 的来源
  backtest_api.py:519-523：当 _extract_trades(run_id) 和 _extract_backend_trades(backend_result) 都返回
  空列表时，设置为 "missing"。根本原因是 零交易（trades.csv 只有表头）。
  BUY triggered_count=0 的根因
  backtest_api.py:471-489：triggered_count 从 orders_df 统计 side == "BUY" 的数量。orders_df 为空 → tota
  l_buy = 0 → triggered_count = 0。
  position_pnl_pct 的单位陷阱
  IR 中使用的是 -7（百分比绝对值），但系统内部 unrealized_pnl_pct 使用小数制（-0.07）。即使改名将 contex
  t 映射到 unrealized_pnl_pct，值 -7 也永远不会被满足（-0.07 <= -7 为 False）。
  ir_8001383b352d 已备份隔离
  3 个 active cache 目录已从 data/runs/backtest/ move 到隔离区：
  • run-8f20f146-20250101-20250912-820b8995
  • run-8f20f146-20250101-20251230-820b8995
  • run-8f20f146-20250912-20251230-820b8995
  备份路径：data/backups/round6a_cache_pollution_20260531_ir8001383b352d/
  交付物
   文件                                                说明
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   quant_intelligence/tests/test_strategy_ir_positio   7 个 synthetic evaluator tests，全部通过
   n_pnl_pct_defect.py
   temporary_for_test/BDO组织推进/temp/patch_draft_p   三层修复方案草案（Evaluator 兼容 / Compile 校验
   osition_pnl_pct.md                                  / graph.py 兜底）
   temporary_for_test/BDO组织推进/temp/Round6A_backe   完整诊断报告
   nd_defect_diagnosis.md
  明确声明
  • ✅ 未运行回测
  • ✅ 未创建新 run
  • ✅ 未修改策略实验语义
  • ✅ 未修改 accepted baseline
  • ✅ ir_8001383b352d 的 active cache 已备份隔离

# GPT5.5:
这次可以定性了：**Round 6A 不是策略实验失败，而是后端 IR / evaluator 能力缺陷。**

当前不要再让 Feishu Agent 尝试任何替代方案。

---

## 当前正式结论

```text
Round 6A: aborted / blocked
原因: position_pnl_pct 是未注册 context 字段，compile 层放行，但 evaluator/execution 层不支持
性质: backend defect，不是策略结果
baseline: run-54b-20250101-20251230-d37c696d 继续保持 accepted
```

项目 AI 的诊断可以验收为：

```text
Round 6A backend defect diagnosis: PASSED
```

但不能验收为：

```text
Round 6A passed
```

---

## 新增 forbidden run 清单

除了之前三个 quarantined run，以下三个也必须加入禁用清单：

```text
run-8f20f146-20250101-20250912-820b8995
run-8f20f146-20250101-20251230-820b8995
run-8f20f146-20250912-20251230-820b8995
```

当前 forbidden / not comparable runs 应为：

```text
run-749b90e9-20250101-20250110-fcac2c66
run-749b90e9-20250101-20251230-820b8995
run-e92b485b-20250101-20251230-820b8995
run-8f20f146-20250101-20250912-820b8995
run-8f20f146-20250101-20251230-820b8995
run-8f20f146-20250912-20251230-820b8995
```

这些都不能用于 baseline 比较、绩效判断或 Round 6A 结论。

---

## 下一步应该做什么

建议现在进入一个**后端修复工单**，不是继续 Round 6A。

核心修复目标不是“换一种止损写法”，而是让系统明确做到：

1. compile 层不能再静默接受未知 context；
2. `position_pnl_pct` 要么被明确拒绝，要么被明确映射为 canonical 字段；
3. canonical 字段应是系统已有的：

```text
unrealized_pnl_pct
```

4. 单位必须统一，不能让 `-7` 和 `-0.07` 混用。

---

## 推荐修复原则

我建议采用这个口径：

```text
Round 6A 的真实语义是 -7% 未实现收益止损。
系统内部 canonical 表达应为：
unrealized_pnl_pct <= -0.07
```

不要继续使用：

```text
position_pnl_pct <= -7
```

因为现在已经证明：

- `position_pnl_pct` 没注册；
- `-7` 单位也不对；
- 即使只改字段名，`-7` 也会导致永远不触发。

---

## 可发给项目 AI 的下一步指令

```text
批准进入 backend defect repair planning / patch implementation。

目标：
修复 Round 6A 暴露出的 IR context 字段不一致问题，但不得运行真实回测，不得创建新 run，不得进入 Round 6A。

Accepted baseline 严禁触碰：
run-54b-20250101-20251230-d37c696d

Forbidden runs 严禁使用为正式证据：
- run-749b90e9-20250101-20250110-fcac2c66
- run-749b90e9-20250101-20251230-820b8995
- run-e92b485b-20250101-20251230-820b8995
- run-8f20f146-20250101-20250912-820b8995
- run-8f20f146-20250101-20251230-820b8995
- run-8f20f146-20250912-20251230-820b8995

修复范围：
1. 为 IRExpression.context 增加合法 context 校验。
2. 明确支持 canonical context:
   unrealized_pnl_pct
3. 对 position_pnl_pct 做以下二选一处理，并说明理由：
   A. 编译期拒绝 position_pnl_pct，提示使用 unrealized_pnl_pct；
   B. 编译期将 position_pnl_pct 显式 alias 到 unrealized_pnl_pct，并记录 normalization。
4. 统一百分比单位：
   - 内部使用小数制：-0.07 表示 -7%
   - 如果输入为 -7，必须编译期拒绝或显式规范化，不能静默通过。
5. universal_factor.py 对 transition evaluator 的 KeyError 增加清晰错误报告，不允许悄悄产生 0 trades。
6. 添加单元测试：
   - unknown context 必须失败
   - unrealized_pnl_pct <= -0.07 可被 evaluator 正确识别
   - position_pnl_pct 的处理行为符合设计
   - holding_days + unrealized_pnl_pct 两个 transition 可以共存
   - -7 与 -0.07 的单位行为有明确测试
   - evaluator 抛错不会被误包装成正常 0-trade 结果

允许：
- 修改后端源码
- 写单元测试
- 运行单元测试 / synthetic evaluator tests
- 更新诊断文档和修复说明

禁止：
- 不得运行真实回测
- 不得创建新 run
- 不得修改策略实验结论
- 不得进入 Round 6A
- 不得进入 Round 6B
- 不得测试其他 stop_loss_pct
- 不得修改 accepted baseline

交付物：
1. patch diff 摘要
2. 新增/修改测试清单
3. 测试运行结果
4. context registry 最终支持字段列表
5. position_pnl_pct 最终处理策略
6. 百分比单位规则
7. 明确声明未运行回测、未创建新 run、未修改 baseline
```

---

## 对 Feishu Agent 的指令

```text
停止 Round 6A。
不得继续重试。
不得尝试 close vs entry_price * 0.93。
不得尝试 risk_management 参数。
不得测试其他 stop_loss_pct。
不得进入 Round 6B。
等待后端修复完成并通过单元测试后，再由我显式批准是否重新执行一次 clean Round 6A。
```

---

## 当前状态一句话

**现在不是继续跑策略的时候，而是先修后端：把 `position_pnl_pct` 这个幽灵字段和 `-7` 单位陷阱彻底消掉。**

