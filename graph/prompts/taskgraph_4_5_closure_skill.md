# TaskGraph 第4.5课闭环执行与验证技能

## 角色

你是 TaskGraph 项目 AI 智能体。

你的任务不是重新设计方案，而是基于当前项目目录，执行并验证“第4.5课：TaskGraph 长程运行补强”是否已经形成可运行闭环。

你需要检查并必要时最小修改以下部分：

- `scripts/build_graph_slice.py`
- `scripts/build_extractor_prompt.py`
- `scripts/reconcile_patch.py`
- `scripts/graph_lint.py`
- `prompts/extractor_system.md`
- `prompts/taskgraph_extractor_template.md`
- `graph_state.json`
- `graph_slices/`
- `original_dialogs/`
- `patches/`

项目根目录为：

text
D:\CCXXLESSON\TaskGraph

## 总目标
验证以下闭环是否成立：

graph_state.json + original_dialogs/turn_xxx.md
        ↓
build_graph_slice.py
        ↓
graph_slices/slice_xxx.json
        ↓
build_extractor_prompt.py
        ↓
prompts/taskgraph_extractor_template.md
        ↓
Extractor 生成 patch_xxx.json
        ↓
reconcile_patch.py
        ↓
apply patch
        ↓
graph_lint.py
        ↓
通过 / 重试 / quarantine

其中：

1. Slice Builder 只负责省 token，不负责最终正确性。
2. 正确性由 entity_ref / state、reconcile_patch.py、graph_lint.py 兜底。
3. patch*.json 是不可变事件日志。
4. graph_state.json 是应用 patch 后的编译产物。
5. 校验失败不能污染主图，必须进入有界重试或隔离流程。
## 重要约束
执行时必须遵守以下约束：

1. 不要直接破坏原始 graph_state.json。
2. 修改前先备份：
text
backups/graph_state.before_taskgraph_4_5.json

3. 测试优先使用 fixtures，不要直接污染正式图。
4. 不要把未通过 reconcile_patch.py 或 graph_lint.py 的 patch 合入主图。
5. 如果发现缺少 apply patch 阶段，应补一个最小实现或测试辅助脚本。
6. 如果某一步无法自动完成，必须在最终报告中明确写出阻塞原因。
## 第一步：检查项目结构
### 确认以下目录和文件存在：

graph_slices/
original_dialogs/
patches/
prompts/
scripts/
tests/
graph_state.json
README.md

### 确认以下脚本存在：

scripts/build_graph_slice.py
scripts/build_extractor_prompt.py
scripts/reconcile_patch.py
scripts/graph_lint.py

### 确认以下提示词文件存在：

prompts/extractor_system.md
prompts/taskgraph_extractor_template.md

如果缺失，记录为 error，不要静默跳过。

## 第二步：检查提示词分工
### 检查 prompts/extractor_system.md 是否只包含固定规则部分，例如：

- Extractor 角色
- 节点类型
- 节点结构
- entity_ref / state 规则
- Patch 顶层结构
- ID 规则
- 生命周期判定
- 事实一致性反向检查
- 禁止事项
### extractor_system.md 不应该包含每轮变化的完整 slice 和本轮对话。

### 检查 prompts/taskgraph_extractor_template.md 的用途。

### 本项目允许将它作为“最终合成后提交给 Extractor 的 context”。也就是说，它可以由：

extractor_system.md + slice_xxx.json + turn_xxx.md合成得到。

如果它当前仍然是旧版固定模板，应记录建议：

建议将 prompts/taskgraph_extractor_template.md 作为每轮生成的最终提交文件，
或者改名为 prompts/extractor_turn_xxx.md，避免与固定模板混淆。

## 第三步：检查 graph_state schema
读取 graph_state.json，检查节点是否支持以下字段：

json
{
  "entity_ref": "...",
  "state": "..."
}

### 检查规则：

1. 可长期追踪节点应尽量有 entity_ref。
2. entity_ref 可以是：
- 工单号
- 文件路径
- API 路径
- 脚本名
- 模块名
- 课程编号
- 稳定对象编号
3. 普通描述性文本不应被当作 entity_ref。
4. state 应尽量归一化为：
- open
- blocked
- in_progress
- implemented
- deployed
- resolved
- cancelled
- unknown
- null

5. 如果发现明显可追踪节点缺少 entity_ref，记录 warning。

6. 如果发现已有测试关键节点如 n_0045，应确认它带有类似：

json
{
  "entity_ref": "TKT-2026-003",
  "state": "blocked"
}

## 第四步：验证 build_graph_slice.py
- 选择一个已有对话轮次，例如：

original_dialogs/turn_006.md

- 执行：

bash
python scripts/build_graph_slice.py ^
  --graph graph_state.json ^
  --turn original_dialogs/turn_006.md ^
  --out graph_slices/slice_006.json

- 检查输出 graph_slices/slice_006.json 是否包含：

json
{
  "task_id": "...",
  "turn_id": 6,
  "_runtime": {
    "next_node_id": "n_xxxx"
  },
  "root_goals": [],
  "standing_constraints": [],
  "active_open_tasks": [],
  "recent_nodes": [],
  "symbol_hits": [],
  "conflict_candidates": []
}

- 必须验证：

1. _runtime.next_node_id 存在。
2. next_node_id 是从完整图计算得到，而不是人工传入。
3. conflict_candidates 会优先召回相同 entity_ref 的 active 节点。
4. 如果本轮文本包含工单号、路径、API、节点 ID，应进入 symbol_hits 或 conflict_candidates。
5. retrieval_trace 可以存在于 slice 文件中，但后续 prompt 组装时应剥离。
## 第五步：验证 build_extractor_prompt.py
- 执行：

bash
python scripts/build_extractor_prompt.py ^
  --system prompts/extractor_system.md ^
  --slice graph_slices/slice_006.json ^
  --turn original_dialogs/turn_006.md ^
  --mode single ^
  --out prompts/extractor_turn_006.md

- 检查生成结果：

1. 包含固定 system 规则。
2. 包含当前 slice。
3. 包含本轮对话。
4. 包含 task_id、turn_id、next_node_id。
5. 不应包含 retrieval_trace。
6. 不应要求人工手动填写 {{extractor_context_pack_json}}、{{turn_text}} 这类占位符。
- 如果支持 api-json，继续执行：

bash
python scripts/build_extractor_prompt.py ^
  --system prompts/extractor_system.md ^
  --slice graph_slices/slice_006.json ^
  --turn original_dialogs/turn_006.md ^
  --mode api-json ^
  --out prompts/extractor_turn_006.api.json

- 检查输出是否为合法 messages 结构：

json
{
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ]
}

## 第六步：准备 reconciliation 测试 fixtures
- 在 tests/fixtures/taskgraph_4_5/ 下创建测试数据，不要直接修改正式图。

- 创建一个最小图：
tests/fixtures/taskgraph_4_5/graph_state_reconcile.json

- 内容应包含旧节点：

json
{
  "node_id": "n_0045",
  "type": "OpenTask",
  "content": "工单 TKT-2026-003 当前被阻塞",
  "entity_ref": "TKT-2026-003",
  "state": "blocked",
  "status": "active"
}

- 创建坏 patch：

tests/fixtures/taskgraph_4_5/patch_missing_supersede.json

- 其中新增：

json
{
  "node_id": "n_0047",
  "type": "Fact",
  "content": "工单 TKT-2026-003 已部署",
  "entity_ref": "TKT-2026-003",
  "state": "deployed",
  "status": "active"
}

- 但故意不写：

json
"superseded_nodes": [
  {"node_id": "n_0045", "reason": "..."}
]

- 也故意不写：

json
{
  "source": "n_0047",
  "target": "n_0045",
  "relation": "invalidates"
}

- 创建好 patch：

tests/fixtures/taskgraph_4_5/patch_with_supersede.json

- 其中必须同时包含：

json
"superseded_nodes": [
  {
    "node_id": "n_0045",
    "reason": "同一 entity_ref 的状态从 blocked 变为 deployed"
  }
]

- 以及：

json
{
  "source": "n_0047",
  "target": "n_0045",
  "relation": "invalidates"
}

## 第七步：验证 reconcile_patch.py
- 对坏 patch 执行：

bash
python scripts/reconcile_patch.py ^
  tests/fixtures/taskgraph_4_5/graph_state_reconcile.json ^
  tests/fixtures/taskgraph_4_5/patch_missing_supersede.json ^
  --out tests/fixtures/taskgraph_4_5/reconcile_bad_report.json

- 预期：

1. 退出码非 0。
2. 报告中存在 errors。
3. 至少包含两类错误：
  - 缺少 superseded_nodes
  - 缺少 invalidates 边
4. 错误依据应来自相同 entity_ref 的状态冲突。

- 对好 patch 执行：

bash
python scripts/reconcile_patch.py ^
  tests/fixtures/taskgraph_4_5/graph_state_reconcile.json ^
  tests/fixtures/taskgraph_4_5/patch_with_supersede.json ^
  --out tests/fixtures/taskgraph_4_5/reconcile_good_report.json

- 预期：

  - 退出码为 0。
  - 没有 error。
  - 可以有 warning，但不得阻断主流程，除非启用了 fail-on-warning。
- 同时检查 invalidates 匹配逻辑：
  - 必须优先使用精确配对：
  (new_node_id, old_node_id)

  - 不能只要某个旧节点被任意新节点 invalidate 就算通过。

## 第八步：检查或补齐 apply patch 阶段
- 检查项目中是否已有等价功能，例如：

  - scripts/apply_patch.py
  - scripts/logic_graph_task.py

- 如果没有明确的 patch 应用阶段，则需要补一个最小脚本：
 - scripts/apply_patch.py

- 最小行为：

1. 读取旧 graph_state.json。
2. 读取 patch.json。
3. 添加 new_nodes。
4. 应用 updated_nodes。
5. 对 superseded_nodes 中的旧节点设置："status": "superseded"
6. 添加 new_edges。
7. 输出新的 graph 文件。
8. 默认不覆盖原图，除非显式传入 --in-place。
- 建议命令格式：

bash
python scripts/apply_patch.py ^
  --graph tests/fixtures/taskgraph_4_5/graph_state_reconcile.json ^
  --patch tests/fixtures/taskgraph_4_5/patch_with_supersede.json ^
  --out tests/fixtures/taskgraph_4_5/graph_state_after_good_patch.json

## 第九步：验证 graph_lint.py
- 先用好 patch 应用后的图执行：

  bash
  python scripts/graph_lint.py ^
    tests/fixtures/taskgraph_4_5/graph_state_after_good_patch.json ^
    --out tests/fixtures/taskgraph_4_5/lint_good_report.json

  - 预期：

  1. 退出码为 0。
  2. 没有结构性 error。
  3. 不存在同一 entity_ref 下 blocked 与 deployed 同时 active 的问题。
  4. 被 invalidates 指向的旧节点应为 superseded。
- 再构造一个坏图：
tests/fixtures/taskgraph_4_5/graph_state_after_bad_patch.json

 - 其中让：

  n_0045: entity_ref=TKT-2026-003, state=blocked, status=active
  n_0047: entity_ref=TKT-2026-003, state=deployed, status=active
 同时存在。

- 执行：

bash
python scripts/graph_lint.py ^
  tests/fixtures/taskgraph_4_5/graph_state_after_bad_patch.json ^
  --out tests/fixtures/taskgraph_4_5/lint_bad_report.json

- 预期：

1. 退出码非 0。
2. 报告中存在同一 entity_ref 互斥 active state 的 error。
## 第十步：验证弱兜底 warning
- 创建一个缺少 entity_ref 的 patch，但内容明显与旧节点相似。

- 预期：
  1. reconcile_patch.py 不应把它当成强 error。
  2. 应输出 warning。
  3. warning 应说明该节点可能缺少 entity_ref，需要人工或后续补全。
  4. 不应静默放过。
## 第十一步：验证失败处理策略
- 如果项目中已有重试或 quarantine 机制，检查它是否满足：
1. reconcile_patch.py 失败时，不应用 patch。
2. graph_lint.py 失败时，不覆盖主图。
3. 失败报告应能回填给下一轮 Extractor。
4. 重试次数应有上限，建议 2 到 3 次。
5. 超过重试上限后，应写入：quarantine/turn_xxx_failed.json

- 如果项目中没有该机制，应至少补一个最小隔离目录和报告格式：
quarantine/

- 失败记录格式建议：

json
{
  "turn_id": 6,
  "patch_path": "patches/patch_006_failed.json",
  "stage": "reconcile_patch.py | graph_lint.py",
  "errors": [],
  "warnings": [],
  "decision": "not_applied",
  "reason": "failed after max retries or manual review required"
}

## 第十二步：最终验收标准
只有同时满足以下条件，才能判定第4.5课闭环通过：

1. build_graph_slice.py 能从完整图和本轮对话生成 slice。
2. slice 中包含 _runtime.next_node_id。
3. build_extractor_prompt.py 能生成最终提交给 Extractor 的 context。
4. 最终 prompt 中不包含无用的 retrieval_trace。
5. Extractor 规则中明确要求 entity_ref / state。
6. reconcile_patch.py 能抓住同一 entity_ref 状态冲突但缺 supersede/invalidates 的坏 patch。
7. reconcile_patch.py 能放行正确包含 supersede 和 invalidates 的好 patch。
8. patch 应用阶段存在。
9. graph_lint.py 能抓住应用后整图中的结构或语义不变量错误。
10. 失败 patch 不会污染主图。
11. 超过重试上限后有 quarantine 或等价隔离机制。
12. 所有测试结果写入报告。

## 第十三步：输出报告
- 执行完后，生成：

text
reports/taskgraph_4_5_closure_report.md

- 报告必须包含：

```markdown
# TaskGraph 第4.5课闭环验证报告

## 1. 总结结论

- 结论：通过 / 部分通过 / 未通过
- 校验/兜底链路闭环成立；真实 Extractor 端到端尚未验证
- 是否存在会污染主图的风险：

## 2. 检查的文件

列出实际检查过的脚本、模板、图文件和测试 fixture。

## 3. 执行的命令

逐条列出运行过的命令。

## 4. 测试结果

### 4.1 Slice 生成

通过 / 未通过  
说明：

### 4.2 Prompt 组装

通过 / 未通过  
说明：

### 4.3 Reconciliation 坏 patch 测试

通过 / 未通过  
说明：

### 4.4 Reconciliation 好 patch 测试

通过 / 未通过  
说明：

### 4.5 Apply Patch 测试

通过 / 未通过  
说明：

### 4.6 Graph Lint 测试

通过 / 未通过  
说明：

### 4.7 Quarantine / 失败隔离测试

通过 / 未通过  
说明：

## 5. 发现的问题

按 error / warning / suggestion 分类。

## 6. 已做的修改

列出修改过的文件和修改原因。必须强制区分：已存在 vs 本次新建

## 7. 尚未解决的问题

如果有，说明原因和下一步建议。

## 8. 最终建议

说明是否建议进入后续课程或继续补基础设施。
```

## 执行原则总结
- 不要只检查脚本是否存在。

- 必须验证完整闭环：切片生成 → prompt 组装 → patch 校验 → patch 应用 → 全图 lint → 失败隔离

- 不要为了让测试通过而放宽校验。

- 宁可让 patch 进入 quarantine，也不能污染主图。

