# turn_002 冲突测试前置规则

本文件用于响应 `temp/白皮书执行反馈phase0.md` 的评审意见，给 `phase0_manual` 的 `turn_002` 对抗测试补足最小规则。

## 1. 当前态裁定规范

- `status` 是当前态裁定的唯一权威字段
- 允许值仅为：
  - `active`
  - `superseded`
- `state` 不再参与“当前态是否成立”的判断
- `state` 仅保留为领域生命周期字段；在本次 `Decision` 冲突测试中可为 `null`

说明：
- 之所以采用 `status` 而非 `state`，是因为当前机械核 `apply_patch.py` 与 `graph_lint.py` 已将 `status` 作为图生命周期字段
- 本规则把“哪个字段决定当前态”钉死，避免 `state=open` 与 `status=active` 的语义歧义继续扩散到断言层
- 白皮书术语与实现字段的临时映射为：`spec.state ≡ impl.status`
- 这是一笔已记录的规范债：后续要么统一白皮书与实现命名，要么持续维护该映射，不允许无声漂移
- 在 `phase0_manual` 中，任何“当前态集合”的计算都只允许读取 `status`，不得读取 `state`

## 2. supersede / invalidates 的承载方式

`turn_002` 若产生“新决策 Y 推翻旧决策 X”，必须同时写两类信息：

1. `superseded_nodes`
   - 将旧节点 `X.node_id` 写入 `superseded_nodes`
   - Apply 后旧节点的 `status` 必须变为 `superseded`

2. `new_edges`
   - 追加一条 `invalidates` 边
   - 形式：`{ "source": "新节点Y", "target": "旧节点X", "relation": "invalidates" }`

选择理由：
- `superseded_nodes` 负责写入后的当前态翻转
- `invalidates` 边负责保留审计链与显式失效关系
- 两者同时存在，才能同时服务断言与审计

## 3. turn_002 目标冲突节点

- 旧态 X：`n_0009`
- 旧态内容：`决策 3 待确认：阶段 1 的 Strategy Research Agent 实现方式尚未确定，候选为 AOS-native 或 quant-native。`
- 稳定 `entity_ref`：`strategy_research_agent.implementation_mode`
- 节点类型：`Decision`

预期新态 Y：
- `阶段 1 的 Strategy Research Agent 采用 AOS-native 路线`
- `entity_ref` 必须仍为 `strategy_research_agent.implementation_mode`

## 4. must_include 的图侧来源

- `must_include` 不再由 bundle 手工拍脑袋指定
- 统一从节点属性 `priority` 派生
- 当前约定：
  - `must_include`
  - `should_include`
  - `optional`
  - `background`

优先级裁定：
- `must_include` 只在**当前态集合**上评估
- 当前态集合定义为：`status = active`
- 若某节点被 `supersede`，即 `status` 翻转为 `superseded`，则该节点**立即退出** `must_include` 候选集
- 也就是说：`supersede` 支配 `priority`

`turn_002` 的断言 (c) 将直接验证：
- 所有 `priority = must_include` 且 `status = active` 的节点，都必须进入 bundle

## 5. turn_002 三条断言

在 `turn_002` apply 后，对 `entity_ref = strategy_research_agent.implementation_mode` 执行一次最小确定性 assemble，并检查：

1. 断言 (a)
   - bundle 中必须包含新态 Y

2. 断言 (b)
   - bundle 中不得包含旧态 X
   - 旧态 X 只允许出现在 graph 审计链中，不得出现在当前态输出中

3. 断言 (c)
   - 所有 `priority = must_include` 且 `status = active` 的节点必须进入 bundle
   - 即使预算很紧，也不得静默丢弃
   - 该断言优先使用**未被 supersede 的稳定 must 节点**验证，如 `n_0001`、`n_0003`
   - 不使用被 supersede 的 `n_0009` 作为断言 (c) 的测试对象，避免与断言 (b) 构造性冲突

## 6. turn_002 交付验收

`turn_002` 完成后，报告中必须显式给出以下证据，而不只是 `pass/fail`：

1. supersede 的实际承载方式
   - `patch_002.json` 中必须同时出现：
     - `superseded_nodes`
     - `invalidates` 边

2. 新节点 Y 的稳定实体标识
   - 新节点 Y 必须携带 `entity_ref = strategy_research_agent.implementation_mode`

3. 三条断言的 bundle 证据
   - 断言 (a)：贴出机械生成 bundle 中包含 Y 的片段
   - 断言 (b)：贴出机械生成 bundle 中不再出现 `n_0009` 的证据
   - 断言 (c)：贴出紧预算下稳定 must 节点仍保留在机械生成 bundle 中的片段

4. 装配链条必须可追溯
   - `context_bundle.turn_002.json` 必须是 Assembler 对 `graph_state` 的函数输出
   - 不接受手写 bundle 作为 `(a)(b)(c)` 的测试证据
