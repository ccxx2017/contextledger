# 用户：
以下是Feishu Ageng和项目AI就上述任务执行多轮次后的结果，请你定夺：
[QUOTE]
# Feishu Agent:
TKT-2026-005B Round 5.3A — 黑盒审计结论

1. 是否存在 fixed initial capital sizing？
✅ 是。 max_position_pct: null、sizing: null，但实际行为是所有下单基于 initial capital 1,000,000 的 ~20% = 200k/笔计算固定 shares。参数表确认无动态 sizing 配置。
2. 是否存在 cash < 0？
✅ 是。 从 2025-05-09 起 implied cash 即部分为负，06/24 起持续为负且急剧恶化：
2025-06-24: implied cash = -184,968
2025-06-26: implied cash = -1,565,185
2025-12-31: implied cash = -1,385,218系统在 cash 为负的情况下持续买入，没有任何 cash constraint。
3. 是否存在 market_value > equity？
✅ 是。 从 2025-05-09 起时有发生，06/24 起严重恶化：
2025-06-24: 788k / 603k = 1.31x
2025-06-26: 1,576k / 11k = 141.65x（持仓 157 万，权益只剩 1.1 万）
2025-12-31: 1,576k / 190k = 8.26x
4. 是否存在同一 symbol 未平仓重复开仓（pyramiding）？
✅ 是。 600036.SH：06/24 开仓 4200 股（持股期间已有旧仓 4400 未平）→ 06/25 +4200 → 06/26 +4200 → 06/27 +4200。4 个交易日内同一标的连续加仓 4 次，累计从 4400 → 21,200 股。601318.SH 同理。这是标准的 pyramid 叠加。
5. 买入订单是否疑似错误降低 equity？
✅ 是，但不完全是。 买入订单本身（cash ↓ + position ↑）不会直接降低 equity（只扣减 fees+slippage）。但这里的问题是：
买入时的 cash ↓ 是通过券商的隐含融资（margin）实现的。最终买单导致 cash 变为 -1.57M，但 equity 在 MktVal 的 mark-to-market 变动中同步损益。
当 equity 只有 11k 时再下单买 200k 的股票，这个订单执行后虽然 cash -200k、position +200k，账面 equity 不变，但此时 MktVal/Equity 比值就从 141 倍跳到 160 倍——此后哪怕 0.5% 的股价下跌也能清空 equity。
6. final_equity 是否能由交易流水闭合？
❌ 不能闭合。 gap = -689,451。

initial_equity:                   1,000,000
+ sum(net realized PnL, 50 trades):  -119,747
= expected equity (no other effects): 880,253
actual final equity:                   190,803
gap:                                  -689,451



缺口主要来自 intra-trade mark-to-market 的杠杆放大效应，体现在日频 NAV 变动中。
7. 当前结果是否允许进入 Round 6？
❌ 不允许。 当前回测引擎的 position sizing 逻辑通过黑盒审计确认存在以下结构性问题，所有指标（Sharpe, MDD, Total Return）均因固定仓位 × 无 cash constraint 的杠杆放大而失真，不能用于评估策略有效性：

问题
确认
严重度
Fixed initial capital sizing
✅
致命
无 max_exposure 限制
✅
致命
无 cash constraint
✅
致命
允许同一 symbol 叠加开仓
✅
严重
trade PnL 不闭合
✅
严重
无止损（stop_loss_pct: null）
✅
设计缺陷
无最大回撤保护（max_drawdown_pct: null）
✅
设计缺陷
证据包文件

文件
内容
evidence_r5_nav.csv (7.6k)
261 天 NAV/equity 序列
evidence_r5_daily_returns.csv (11.5k)
260 天 daily returns
evidence_r5_trades.csv (6.3k)
50 笔交易完整流水
/tmp/r5_summary.json
run 概要
/tmp/r5_params.json
参数配置（含空白的 position/risk/costs 字段）
/tmp/r5_positions_daily.json (70.6k)
166 天 × 466 条持仓明细
/tmp/r5_positions_daily_range.json (100.7k)
持仓区间详情
# 项目AI-GPT5.5:
Round 5.3B 已按“只修回测引擎、不改策略逻辑”的范围完成排查与修复。
本轮确认的主因不是 NAV 自身计算坏掉，而是引擎适配层存在 4 个账户口径问题：期末权益取值错误、未成交 raw order 混入统计、仓位 sizing 仍锚定初始资金、默认允许同一标的未平仓重复加仓。
关键修复已落在 executor_facade.py、custom_positions.py、abupy_caller.py。
建议必须让 Feishu Agent 重新通过后端 API 跑一次 Round 5 baseline 验证，因为这次修改影响了成交过滤、仓位 sizing 和 final equity 口径。
源码定位

order_value 口径：实际成交金额本质上是 buy_cnt * buy_price，buy_cnt 在 abupy_caller.py 的 patched_fit_buy_order() 中由 position.fit_position() 算出，再按市场最小交易单位取整。
shares 计算：position.fit_position() 返回原始数量 bc，随后在 patched_fit_buy_order() 中按 A 股 100 股、港股 lot、期货最小手数等规则落成 buy_cnt。
capital_base 原行为：patched_fit_buy_order() 仍把 factor_object.capital.read_cash 传进 position 构造；而 abupy 的 read_cash 实际是初始资金，不是当前现金。这正是“权益很低仍按 100 万的 20% 下单”的根因之一。
available_cash 读取：原始 abupy sizing 不依赖当前可用现金；本轮在 custom_positions.py 改为从 capital.capital_pd["cash_blance"] 读取当前现金，并结合 capital_blance 读取当前权益。
现金不足行为：原生执行阶段是“拒单”而不是自动缩单；本轮 sizing 先做 min(current_equity * ratio, available_cash)，因此默认不会再生成超现金规模的有效买入数量，available_cash<=0 时直接返回 0.0。
cash < 0：本轮默认禁止。动态 sizing 用 max(cash, 0.0)，原生 buy_stock() 也不会在现金不足时继续成交；本轮没有开启 margin mode。
同一 symbol 重复开仓：原生允许累计 keep_cnt；本轮在 abupy_caller.py 的 patched_buy_stock() 增加默认 guard，allow_pyramid=False 时若已有未平仓仓位则直接拒绝再次开仓。
equity 计算：账户真实权益应来自 capital_pd["capital_blance"]，或 cash_blance + *_worth。本轮在 executor_facade.py 的 _resolve_final_equity() 中明确优先按这个口径取值。
NAV 计算：本轮排查结论与审计现象一致，NAV 序列自身闭合，报告层口径仍是 equity / initial_equity，不是这次异常的主 bug。
realized_pnl / unrealized_pnl：本轮未改策略交易收益算法，主问题不在 PnL 公式本身，而在“未成交订单混入统计”和“final_equity 取成现金”导致 trade PnL 无法解释组合权益。
fees / slippage 重复扣除：本轮未发现明确的“双扣”证据；当前异常更符合口径错位，而不是手续费重复计提。
找到的 Bug

Bug 1：final_capital / final_equity 取值错误
位置：executor_facade.py 与 executor_facade.py
类型：账户权益口径 bug / 报表汇总 bug
现象：可能把期末现金当成期末权益，直接解释出 190,803，丢掉持仓市值部分。
Bug 2：未成交 raw orders 混入交易统计
位置：abupy_caller.py 与 executor_facade.py
类型：成交状态映射 bug / 数据污染 bug
现象：orders_pd 在执行前已生成，若不按 action_pd.deal 回筛，拒单/未成交卖出会污染 trades、PnL、最终持仓解释。
Bug 3：仓位 sizing 使用初始资金而不是当前账户状态
位置：custom_positions.py
类型：仓位管理 bug / 风控约束缺失
现象：账户权益下降后，后续订单仍按接近初始资金比例下单。
Bug 4：默认允许同一 symbol 未平仓重复开仓
位置：abupy_caller.py 与 executor_facade.py
类型：默认交易约束缺失
现象：同一标的可在未平仓状态下反复追加，放大总暴露和 symbol 暴露。
修改内容

在 executor_facade.py 接入 _filter_executed_orders()，只保留真实成交买单，并把未成交卖出回写成 keep，避免虚假平仓进入统计。
在 executor_facade.py 改为通过 _resolve_final_equity() 汇总真实组合权益，不再优先读现金。
在 executor_facade.py 把默认全局仓位类切到动态版本，并注入 allow_pyramid=False、max_total_exposure=1.0。
在 custom_positions.py 新增动态账户状态读取逻辑，按 current_equity 与 available_cash 联合 sizing：
target_notional = min(current_equity * ratio, available_cash)
available_cash <= 0 时拒绝下单
在 abupy_caller.py 给 action_pd 注入 order_idx，使 deal 状态可与 orders_pd 一一对齐。
在 abupy_caller.py 增加默认禁止 repeated entry 的 guard。
新增单元测试

新增/扩展测试文件：
test_backtest_accounting_guards.py
test_executor_facade.py
覆盖点：
测试 A：连续固定价格买入下，final equity 优先按组合权益解释，避免把本金错误记成损失。
测试 B：默认 allow_pyramid=False，并检查默认仓位配置含 max_total_exposure=1.0。
测试 C：现金不足/可用现金为 0 时拒绝继续买入。
测试 D：final_equity 优先使用 capital_blance，并验证未成交单不会污染账户闭合。
具体新增断言包括：
test_resolve_final_equity_prefers_portfolio_equity_over_cash
test_filter_executed_orders_drops_rejected_buy_orders
test_filter_executed_orders_converts_unfilled_sell_to_keep
test_fixed_percent_position_uses_current_cash_instead_of_initial_cash
test_fixed_percent_position_rejects_when_available_cash_is_zero
test_configure_position_management_sets_dynamic_equity_guards
test_configure_capital_guards_disables_pyramid_by_default
单元测试结果

.\.venv\Scripts\python.exe -m pytest backend/tests/abupy_adapter/execution/test_backtest_accounting_guards.py -q
5 passed in 0.24s
.\.venv\Scripts\python.exe -m pytest backend/tests/abupy_adapter/test_executor_facade.py -q
7 passed in 0.38s
.\.venv\Scripts\python.exe -m pytest backend/tests/abupy_adapter/test_strategy_real_execution.py -q
4 passed, 4 skipped in 0.27s
最近改动文件的 VS Code 诊断结果：
executor_facade.py、custom_positions.py、abupy_caller.py、test_backtest_accounting_guards.py、test_executor_facade.py 均无新增诊断错误。
是否需要重新跑 Baseline

需要。
原因：这次修改直接影响 3 个审计敏感口径：
成交订单集合
账户资金/权益 sizing
final_equity 汇总方式
建议 Feishu Agent 重新通过后端 API 跑 Round 5 baseline，并重点复核以下输出：
timeseries.csv 中每日 equity == cash + market_value
trades.csv 不再包含未成交单
final_equity 能被 realized_pnl + unrealized_pnl - fees - slippage + cash_adjustments 解释
2025-06-24 至 2025-06-27 不再出现默认 repeated entry
低 equity 状态下，不再按初始 1,000,000 的固定比例继续下单
补充判断

本轮没有改策略因子、信号、universe、train_split，也没有用“调策略表现”的方式掩盖引擎问题。
当前最可能解释你给出的 -674,445 gap 的主因，是“期末权益被取成现金”叠加“未成交订单污染统计”，而不是 NAV 本身断裂。

