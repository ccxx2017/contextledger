# TaskGraph 第4.5课闭环验证报告

## 1. 总结结论

- **结论：部分通过**
- 校验/兜底链路（切片生成 → prompt 组装 → patch 校验 → patch 应用 → 全图 lint → 失败隔离）闭环成立；真实 Extractor 端到端尚未验证。
- 是否存在会污染主图的风险：**否**。本次验证全部使用 `tests/fixtures/` 中的隔离数据，并在运行前对 `graph_state.json` 做了备份 `backups/graph_state.before_taskgraph_4_5.json`。

## 2. 检查的文件

### 脚本（已存在）
- `scripts/build_graph_slice.py`
- `scripts/build_extractor_prompt.py`
- `scripts/reconcile_patch.py`
- `scripts/graph_lint.py`
- `scripts/logic_graph_task.py`（存在，但 schema 与当前第4.5课不完全一致）

### 提示词文件（已存在）
- `prompts/extractor_system.md`
- `prompts/taskgraph_extractor_template.md`

### 图文件与对话（已存在）
- `graph_state.json`
- `original_dialogs/turn_006.md`

### 本次新建的 fixture 与产物
- `tests/fixtures/taskgraph_4_5/graph_state_reconcile.json`
- `tests/fixtures/taskgraph_4_5/patch_missing_supersede.json`
- `tests/fixtures/taskgraph_4_5/patch_with_supersede.json`
- `tests/fixtures/taskgraph_4_5/patch_weak_no_entity_ref.json`
- `tests/fixtures/taskgraph_4_5/graph_state_after_good_patch.json`
- `tests/fixtures/taskgraph_4_5/graph_state_after_bad_patch.json`
- `tests/fixtures/taskgraph_4_5/reconcile_bad_report.json`
- `tests/fixtures/taskgraph_4_5/reconcile_good_report.json`
- `tests/fixtures/taskgraph_4_5/reconcile_weak_report.json`
- `tests/fixtures/taskgraph_4_5/lint_good_report.json`
- `tests/fixtures/taskgraph_4_5/lint_bad_report.json`
- `graph_slices/slice_006.json`
- `prompts/extractor_turn_006.md`
- `prompts/extractor_turn_006.api.json`

### 本次新建的脚本与机制
- `scripts/apply_patch.py`（新建，最小 patch 应用脚本）
- `scripts/quarantine_patch.py`（新建，最小隔离辅助脚本）
- `quarantine/example_turn_006_failed.json`（隔离记录格式示例）
- `quarantine/turn_006_failed.json`（测试时由 quarantine_patch.py 生成）

## 3. 执行的命令

```powershell
# 备份原图
Copy-Item graph_state.json backups/graph_state.before_taskgraph_4_5.json

# 4.1 Slice 生成
python scripts/build_graph_slice.py `
  --graph graph_state.json `
  --turn original_dialogs/turn_006.md `
  --out graph_slices/slice_006.json

# 4.2 Prompt 组装（single 模式）
python scripts/build_extractor_prompt.py `
  --system prompts/extractor_system.md `
  --slice graph_slices/slice_006.json `
  --turn original_dialogs/turn_006.md `
  --mode single `
  --out prompts/extractor_turn_006.md

# 4.2 Prompt 组装（api-json 模式）
python scripts/build_extractor_prompt.py `
  --system prompts/extractor_system.md `
  --slice graph_slices/slice_006.json `
  --turn original_dialogs/turn_006.md `
  --mode api-json `
  --out prompts/extractor_turn_006.api.json

# 4.3 Reconciliation 坏 patch 测试
python scripts/reconcile_patch.py `
  tests/fixtures/taskgraph_4_5/graph_state_reconcile.json `
  tests/fixtures/taskgraph_4_5/patch_missing_supersede.json `
  --out tests/fixtures/taskgraph_4_5/reconcile_bad_report.json
# 退出码: 1

# 4.4 Reconciliation 好 patch 测试
python scripts/reconcile_patch.py `
  tests/fixtures/taskgraph_4_5/graph_state_reconcile.json `
  tests/fixtures/taskgraph_4_5/patch_with_supersede.json `
  --out tests/fixtures/taskgraph_4_5/reconcile_good_report.json
# 退出码: 0

# 4.5 Apply Patch 测试
python scripts/apply_patch.py `
  --graph tests/fixtures/taskgraph_4_5/graph_state_reconcile.json `
  --patch tests/fixtures/taskgraph_4_5/patch_with_supersede.json `
  --out tests/fixtures/taskgraph_4_5/graph_state_after_good_patch.json

# 4.6 Graph Lint 好图测试
python scripts/graph_lint.py `
  tests/fixtures/taskgraph_4_5/graph_state_after_good_patch.json `
  --out tests/fixtures/taskgraph_4_5/lint_good_report.json
# 退出码: 0

# 4.6 Graph Lint 坏图测试（同一 entity_ref 互斥 active state）
python scripts/graph_lint.py `
  tests/fixtures/taskgraph_4_5/graph_state_after_bad_patch.json `
  --out tests/fixtures/taskgraph_4_5/lint_bad_report.json
# 退出码: 1

# 4.7 弱兜底 warning 测试
python scripts/reconcile_patch.py `
  tests/fixtures/taskgraph_4_5/graph_state_reconcile.json `
  tests/fixtures/taskgraph_4_5/patch_weak_no_entity_ref.json `
  --out tests/fixtures/taskgraph_4_5/reconcile_weak_report.json
# 退出码: 0， warnings: 1

# 4.8 Quarantine 机制测试
python scripts/quarantine_patch.py `
  --turn 6 `
  --patch tests/fixtures/taskgraph_4_5/patch_missing_supersede.json `
  --report tests/fixtures/taskgraph_4_5/reconcile_bad_report.json `
  --stage reconcile
# 退出码: 0
```

## 4. 测试结果

### 4.1 Slice 生成

**通过**

说明：
- `graph_slices/slice_006.json` 成功生成。
- 包含 `_runtime.next_node_id: "n_0034"`，且该值由完整图自动计算得出，非人工传入。
- `conflict_candidates` 按预期召回了与 turn_006 文本存在符号命中或文本重叠的 active 节点（如 n_0026、n_0032、n_0033、n_0015 等）。
- `symbol_hits` 中包含了 turn_006 中提到的 API 路径、文件路径、模块名等符号。
- `retrieval_trace` 存在于 slice 文件中，供诊断使用。

### 4.2 Prompt 组装

**通过**

说明：
- `extractor_turn_006.md`（single 模式）和 `extractor_turn_006.api.json`（api-json 模式）均成功生成。
- 输出包含固定 `system` 规则、当前 `slice`、本轮 `turn_text`、`task_id`、`turn_id`、`next_node_id`。
- `retrieval_trace` 已被 `build_extractor_prompt.py` 的 `split_runtime_from_pack()` 剥离，未进入最终模型上下文。
- 最终 prompt 中不包含 `{{extractor_context_pack_json}}`、`{{turn_text}}` 等占位符。
- api-json 模式输出为合法 messages 结构：`{"messages": [{"role": "system", ...}, {"role": "user", ...}]}`。

### 4.3 Reconciliation 坏 patch 测试

**通过**

说明：
- 对故意缺少 `superseded_nodes` 和 `invalidates` 边的 patch 执行 reconcile。
- 退出码为 **1**。
- 报告中存在 **2 条 error**：
  - `STATE_CONFLICT_MISSING_SUPERSEDE`
  - `STATE_CONFLICT_MISSING_INVALIDATES`
- 错误依据为同一 `entity_ref=TKT-2026-003` 下 `blocked` → `deployed` 的状态冲突。

### 4.4 Reconciliation 好 patch 测试

**通过**

说明：
- 对正确包含 `superseded_nodes` 和 `invalidates` 边的 patch 执行 reconcile。
- 退出码为 **0**。
- `report.ok == true`，无 error。
- `resolved_conflicts` 中正确记录了冲突解决配对 `(n_0047, n_0045)`。

### 4.5 Apply Patch 测试

**通过**

说明：
- 新创建的 `scripts/apply_patch.py` 成功将好 patch 应用到测试图上。
- 输出文件 `graph_state_after_good_patch.json` 中：
  - `n_0047` 被新增。
  - `n_0045` 的 `status` 被设置为 `"superseded"`。
  - `invalidates` 边被加入 `edges`。
- 原图未被覆盖，符合默认安全行为。

### 4.6 Graph Lint 测试

**通过**

说明：
- 对好 patch 应用后的图执行 lint，退出码 **0**，无 error、无 warning。
- 被 `invalidates` 指向的旧节点 `n_0045` 状态为 `superseded`，通过校验。
- 对故意构造的坏图（`n_0045` 和 `n_0047` 同时为 `active`，且均指向 `entity_ref=TKT-2026-003`，state 分别为 `blocked` 和 `deployed`）执行 lint：
  - 退出码 **1**。
  - 捕获 `CONFLICTING_ACTIVE_STATES_FOR_ENTITY_REF` 错误，符合预期。
  - 同时捕获两条 `ACTIVE_ISOLATED_NODE`（fixture 中未给测试节点加边，属于 fixture 设计，不影响核心验证结论）。

### 4.7 Quarantine / 失败隔离测试

**部分通过**

说明：
- 项目中原本无自动重试或隔离机制。
- 本次新建了 `quarantine/` 目录、`scripts/quarantine_patch.py` 最小辅助脚本，以及示例记录格式。
- 测试验证：当 reconcile 失败时，`quarantine_patch.py` 能将失败 patch 和报告移入 `quarantine/`，并生成标准格式的失败记录。
- **尚未解决的问题**：目前需要外部调用者（如 shell 脚本或 CI pipeline）在 reconcile / lint 失败后显式调用 `quarantine_patch.py`。项目内尚无自动重试上限（2~3 次）和自动回退的闭环控制器。

## 5. 发现的问题

### error
- **无阻塞性 error**。所有脚本均按预期工作。

### warning
1. **`graph_state.json` 历史节点缺失 `entity_ref` 和 `state`**
   - 当前正式图中全部 33 个节点均未设置 `entity_ref` 和 `state`（字段值为 `null` 或不存在）。
   - 这导致 `build_graph_slice.py` 的 `conflict_candidates` 只能依赖文本匹配和符号命中，无法发挥 `entity_ref` 精确配对的强判定优势。
   - 建议：对历史节点进行一轮人工或半自动标注，至少给涉及工单、文件、API、模块的节点补上 `entity_ref` 和 `state`。

2. **`prompts/taskgraph_extractor_template.md` 当前为占位符 `[待合成]`**
   - 实际每轮产物由 `build_extractor_prompt.py` 输出到 `prompts/extractor_turn_xxx.md`。
   - 该文件名可能与"固定模板"产生混淆。
   - 建议：明确 `taskgraph_extractor_template.md` 的定位——是作为 build 的目标文件名（保留），还是改名为 `extractor_turn_xxx.md` 的生成说明。当前不影响功能，但需文档对齐。

### suggestion
1. **`scripts/logic_graph_task.py` 的 schema 未对齐第4.5课字段**
   - 其内部 `Node` dataclass 缺少 `entity_ref` 和 `state` 字段。
   - 如果后续继续使用 `logic_graph_task.py` 作为主图 apply 入口，需要将其 schema 与 `apply_patch.py` 对齐，或统一使用 `apply_patch.py`。
2. **补全自动控制器**
   - 当前 reconcile → apply → lint → quarantine 的串联需要外部脚本（如 shell / Python controller）驱动。
   - 建议后续课程补充一个 `scripts/pipeline_turn.py`，自动执行：
     1. `build_graph_slice.py`
     2. `build_extractor_prompt.py`
     3. （外部 LLM Extractor）
     4. `reconcile_patch.py` → 失败则重试 / quarantine
     5. `apply_patch.py`
     6. `graph_lint.py` → 失败则回滚 / quarantine

## 6. 已做的修改

| 文件 | 状态 | 说明 |
|------|------|------|
| `backups/graph_state.before_taskgraph_4_5.json` | **本次新建** | 正式图备份 |
| `tests/fixtures/taskgraph_4_5/*` | **本次新建** | 测试 fixture 与报告（共 12 个文件） |
| `graph_slices/slice_006.json` | **本次新建** | 由 build_graph_slice.py 生成 |
| `prompts/extractor_turn_006.md` | **本次新建** | 由 build_extractor_prompt.py 生成（single 模式） |
| `prompts/extractor_turn_006.api.json` | **本次新建** | 由 build_extractor_prompt.py 生成（api-json 模式） |
| `scripts/apply_patch.py` | **本次新建** | 最小 patch 应用脚本，支持 `--in-place` 和 `--out` |
| `scripts/quarantine_patch.py` | **本次新建** | 最小隔离辅助脚本，支持 `--turn --patch --report --stage` |
| `quarantine/example_turn_006_failed.json` | **本次新建** | 隔离记录格式示例 |
| `quarantine/turn_006_failed.json` | **本次新建** | quarantine_patch.py 测试生成 |

## 7. 尚未解决的问题

1. **历史数据 `entity_ref` / `state` 补全**
   - 原因：33 个历史节点全部缺失这两个字段，无法在当前真实图上验证 `entity_ref` 精确配对的完整效果。
   - 下一步：运行一次人工标注脚本或半自动标注，将已有节点的工单号、文件路径、API 路径提取为 `entity_ref`，并推断 `state`。

2. **端到端 Extractor 尚未验证**
   - 原因：本次验证仅覆盖机械链路（slice → prompt → reconcile → apply → lint），真实 LLM Extractor 生成 patch 的准确率未测。
   - 下一步：使用 `prompts/extractor_turn_006.api.json` 调用实际 LLM，观察其输出是否满足 extractor_system.md 的约束，并通过 reconcile。

3. **自动 pipeline 控制器缺失**
   - 原因：当前各脚本独立，需要外部串联。
   - 下一步：补充 `scripts/pipeline_turn.py` 或等价的 shell 脚本，实现自动重试上限、失败隔离、不污染主图。

## 8. 最终建议

- **建议先补历史数据标注**，再继续后续课程。因为 `entity_ref` 和 `state` 是第4.5课的核心 schema 扩展，如果历史节点全部缺失，长期运行中 `reconcile_patch.py` 的强判定等于失效，只能依赖弱兜底 warning，风险较高。
- 在补全历史数据后，**建议跑一次真实端到端验证**：用 `build_extractor_prompt.py` 生成的 api-json prompt 调用 LLM，拿到 patch 后走完整链路，确认 Extractor 能正确输出 `superseded_nodes` + `invalidates`。
- 如果端到端验证通过，且自动 pipeline 控制器补齐，第4.5课可视为**完全通过**。
