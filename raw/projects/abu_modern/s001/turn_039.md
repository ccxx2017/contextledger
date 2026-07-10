# 用户：
附件(temporary_for_test\BDO组织推进\修正数字员工的实施进行中.md)是我当前的项目实施情况，后面究竟该怎么做？请你给出你的方案

# GPT5.5:
## 结论

后面**不要继续让 strategy-researcher 执行研究**。  
当前真正卡点不是研究策略，而是 **builder / backtest 工具契约不合格**：

1. **Builder 仍是交互式会话组件**，不适合数字员工自动研究闭环。
2. **Backtest 接口会 500**，且错误对象不可 JSON 序列化，说明后端错误契约不稳定。
3. 同步回测虽然加了脚本护栏，但后端仍没有真正的异步、取消、隔离机制。
4. 当前 Ticket B 的 smoke run 已经失败，不能继续扩大执行。

所以路线应改为：

> **暂停研究 → 修工具契约 → 做技术 smoke → 再恢复受限研究 → 最后做后端异步化。**

---

# 我的方案

## 阶段 0：立即冻结当前 Ticket B

目标：不要再污染现场。

要求：

- `TKT-2026-005B` 保持 `paused_for_boss_review`
- strategy-researcher 不再调用：
  - builder
  - backtest
  - kb_query
  - scripts 下任何脚本
- 保留已有 trace、worklog、失败响应
- commit + push 当前暂停状态

这一轮不能被视为研究结论，只能视为 **工具链失败证据**。

---

## 阶段 1：开新工单修工具契约

建议新开：

```text
TKT-2026-005D-builder-backtest-contract-repair
```

实施主体不是 strategy-researcher，而是：

```text
Project AI / Claude Code / 后端开发者
```

### 1.1 修 backtest 500 问题

必须先修这个：

当前错误：

```text
TypeError: ValueError is not JSON serializable
```

说明后端异常响应没有统一封装。

验收标准：

- 后端任何异常都返回结构化 JSON
- 不允许 FastAPI 直接尝试序列化 Python exception 对象
- 返回格式类似：

```json
{
  "success": false,
  "error": {
    "code": "BACKTEST_INTERNAL_ERROR",
    "message": "...",
    "request_id": "...",
    "retryable": false
  }
}
```

- 同类错误不能再出现 HTTP 500 + 非 JSON 序列化异常
- 加一个最小测试覆盖：故意抛 `ValueError`，接口仍返回合法 JSON

---

### 1.2 把 Builder 改成非交互式契约

这是更大的问题。

现在 builder 会出现：

```text
pending_user_input
session corrupted
多轮未收敛
```

这说明它是“聊天式构建器”，不是“Agent 可调用工具”。

strategy-researcher 需要的是这种接口：

```text
输入：完整 strategy_ir JSON
输出：成功 / 编译错误 / 不支持原因
禁止：继续追问、pending_user_input、多轮聊天
```

建议新增或改造一个端点，例如：

```text
POST /strategy-builder/compile-ir
```

或者：

```text
POST /strategy-builder/invoke
mode=strict_ir
```

契约：

```json
{
  "success": true,
  "strategy_id": "stg_xxx",
  "compiler_status": "compiled",
  "warnings": []
}
```

失败时：

```json
{
  "success": false,
  "error": {
    "code": "IR_COMPILE_FAILED",
    "message": "...",
    "field_errors": []
  }
}
```

硬规则：

- 不允许 `pending_user_input`
- 不允许 session 依赖
- 不允许自动多轮对话
- 不允许 builder 自己决定继续问问题
- Agent 只提交完整 IR，builder 只负责编译和落档

否则 strategy-researcher 会一直被 builder 拖进对话泥潭。

---

### 1.3 暂时关闭 auto_backtest

在修复期建议：

```text
builder 只负责生成 strategy_id / archive
backtest 由 call_backtest.py 显式调用
```

原因：

- 便于定位错误来源
- 避免 builder 内部自动触发回测造成隐藏卡死
- 让 trace 更清楚

等稳定后再考虑恢复 auto_backtest。

---

## 阶段 2：做纯技术 smoke，不做研究

新开：

```text
TKT-2026-005E-technical-e2e-smoke
```

目的不是研究 VCP，而是验证链路：

```text
IR → builder strict compile → strategy_id → backtest → KB 读取 → trace 落盘
```

要求：

- 使用手写最小 IR
- 1 到 5 个标的
- 3 个月到 1 年窗口
- 不让 LLM 生成假设
- 不让 strategy-researcher 自主研究
- 只测工具链是否闭环

验收标准：

1. builder 返回 `strategy_id`
2. 无 `pending_user_input`
3. backtest 返回合法 JSON
4. 不出现 HTTP 500
5. KB 中能读到新策略档案
6. backtest 结果能追加进档案
7. 后端无卡死进程
8. call_backtest.py 护栏仍然生效

只有这个通过，才能恢复 Ticket B。

---

## 阶段 3：恢复 Ticket B，但仍是受限研究

恢复条件：

- 005D 通过
- 005E 技术 smoke 通过
- 后端不再 500
- builder 已有 strict/non-interactive 模式

然后才让 strategy-researcher 恢复：

```text
TKT-2026-005B limited_resume
```

恢复规则：

- 从 Round 3 继续
- 先 5 标的、1 年
- 通过后最多 20 标的、3 年
- 仍然禁止 231 标的大回测
- 后端 5xx / 超时 / 连接失败一次即暂停
- builder 出现 `pending_user_input` 即暂停
- 不允许 Agent 自己解释为“这次不算失败”

---

## 阶段 4：并行推进后端异步化，但不要抢在契约修复前

后端异步化仍然必要，但顺序应该是：

```text
先修契约，再做异步化
```

否则会把一个坏的同步接口，变成一个坏的异步接口。

后端异步化目标：

- `POST /jobs`
- `GET /jobs/{run_id}`
- `POST /jobs/{run_id}/cancel`
- worker 隔离
- 单 caller 并发限制
- 超时强杀子进程
- queue stats
- Agent 端轮询与取消

但这是下一阶段，不是当前第一优先级。

---

# 推荐工单顺序

```text
005B：保持 paused_for_boss_review
005D：修 builder/backtest 工具契约
005E：纯技术端到端 smoke
005B：受限恢复研究
006：正式 strategy-researcher v1 研究能力迭代
后续：后端异步化与多 agent 机制改造
```

---

# 当前最重要的判断

你现在不要再纠结 VCP 策略本身。  
当前系统还没到“研究策略好坏”的阶段。

真正要解决的是：

> strategy-researcher 能否稳定调用一组非交互式、可超时、可失败、可追踪的研究工具。

如果这个不解决，后面每个研究工单都会重复卡死、误判、无限对话、错误重试。

我的建议：**马上开 005D，先修 builder/backtest 契约。**

