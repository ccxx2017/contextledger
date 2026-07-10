# 用户：
是这样的，我的系统还是允许用户交互的形式，我不希望只有auto research的形式，因此，我们现在需要考虑是否新建一种接口，当进入的auto research时调用的该接口，而用户通过交互式进行构建时用的原来的接口，你看呢？
# GPT-5.5:
是，**应该新建一套 auto research 专用接口**，不要强行改掉现有交互式 builder。

推荐分成两条通道：

## 1. 保留现有交互式接口

用于人类通过飞书/对话构建策略：

```text
/strategy-builder/invoke
```

特点：

- 可以多轮追问
- 可以 `pending_user_input`
- 可以利用 session
- 适合人类边聊边改策略
- 继续服务 `quant_assistant`

这条不要破坏。

---

## 2. 新增 auto research 专用接口

用于 strategy-researcher 自动研究：

```text
POST /strategy-builder/compile-ir
```

或：

```text
POST /strategy-builder/auto-research/compile
```

特点必须是：

- 单次请求
- 无 session 依赖
- 不追问
- 不返回 `pending_user_input`
- 输入必须是完整 `strategy_ir`
- 输出只有：
  - 编译成功
  - 编译失败
  - 不支持
- 失败也必须是结构化 JSON

示例：

```json
{
  "strategy_ir": {...},
  "metadata": {
    "ticket_id": "TKT-2026-005B",
    "round": 3,
    "source": "strategy_researcher"
  }
}
```

返回：

```json
{
  "success": true,
  "strategy_id": "stg_xxx",
  "archive_created": true,
  "warnings": []
}
```

失败：

```json
{
  "success": false,
  "error": {
    "code": "IR_COMPILE_FAILED",
    "message": "...",
    "retryable": false,
    "field_errors": []
  }
}
```

---

## 关键原则

你不是要二选一，而是要**双接口分流**：

```text
人类交互式构建 → 旧 builder invoke
自动研究闭环 → 新 compile-ir / auto-research 接口
```

这样最好：

- 不牺牲人类交互体验；
- 不让自动 Agent 掉进多轮会话；
- 两条链路可分别验收；
- quant_assistant 和 strategy-researcher 职责也更清楚。

---

## 下一步建议

开新工单：

```text
TKT-2026-005D-auto-research-builder-api
```

目标不是重构旧 builder，而是新增 auto research API。

验收标准写死：

1. 旧 `/strategy-builder/invoke` 行为不变；
2. 新接口不允许 `pending_user_input`；
3. 新接口不依赖 session；
4. 输入完整 IR；
5. 返回结构化 JSON；
6. 成功后能生成 `strategy_id` 并落 KB；
7. 失败时不触发回测，不进入对话循环。

这个方向是对的。
