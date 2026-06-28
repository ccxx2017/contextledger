# turn_004 候选用例：pending 语义裁定

## 当前观察

`turn_003` 中的 `n_0013` 目前存储为：

```json
{
  "node_id": "n_0013",
  "type": "OpenTask",
  "entity_ref": "strategy_research_agent.quant_assistant_relationship",
  "state": "open",
  "status": "active",
  "priority": "should_include"
}
```

## 暴露的问题

- `status=active` 只能表达“仍属于当前态集合”
- `state=open` 只能表达“这是一个未完成任务”
- 当前真正的缺口不是“少一个 tentative 字段”，而是装配层没有利用 `state=open` 去区分“待裁定”与“已拍板”

当前结论：

1. `n_0013` 继续用 `OpenTask + state=open + status=active` 承载
2. 暂不引入 `tentative` / `pending_decision` 一类新字段
3. 下一轮优先走“路线 A”：让装配层在 membership/优先级判定里利用 `state`

## 下一轮更有价值的测试

`turn_004` 应优先围绕 `n_0013` 设计：

- 输入一个最终裁定版本，例如：
  - 关系最终确认为 A
  - 或关系最终改判为 B
- 检查旧的“待定关系”如何退出当前态
- 验证最终裁定节点是否 supersede 当前的 `n_0013`
- 在最终裁定**之前**先跑一次装配，确认 `n_0013` 不应以待定身份进入主要上下文
- 在最终裁定**之后**再跑一次装配，确认确认态按规则进入上下文

## 设计裁定

- 采用路线 A：先复用 `state=open`，不新增字段
- 只有当后续出现“已拍板但 `state=open`”或“未拍板但 `state!=open`”这类反例时，才考虑路线 B
- 因此，`turn_004` 的重点不是改 schema，而是验证：
  - 装配层如何利用 `state=open` 降低待裁定节点的可见性
  - 最终裁定后该节点如何被 supersede 或转为确认态

## 当前结论

- `turn_003` 的真正新信息不是装配路径，而是 `n_0013` 揭示的“state 已有、但装配未用”的缺口
- 在正式推进 `turn_004` 前，方案已经收敛为路线 A：先利用现有 `state=open`，不做过度 schema 扩展
