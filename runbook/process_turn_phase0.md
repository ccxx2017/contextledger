# RUNBOOK · process_turn_phase0 (白皮书 Phase 0 手工代行 / 可重放版)
# 执行者: 项目驻守 AI (Phase 0 Orchestrator)
# 适用: 白皮书 Phase 0。目标是验证机制成立、产物可重放、路径可复现，不追求自动 Extractor/Assembler 完整实现。

────────────────────────────────────────
## 0. 目标与边界
────────────────────────────────────────

你在 Phase 0 做三件事：

1. 以手工代行方式，把 raw turn 固化为 normalized / manifest / patch
2. 调机械核脚本完成 apply / lint / assembly
3. 把可重放产物与验收结论落盘，供评审员复核

你在 Phase 0 不做的事：

- 不声称已验证白皮书 Phase 0.5 / Phase 1 指标
- 不引入正式 Extractor / Resolver / Pack
- 不手工伪造 apply、lint、assembly 的结果

本手册服务的是：

- `Phase 0` 的机制验证
- turn 链的可确定性重放
- bundle 的可机械再生

────────────────────────────────────────
## 1. 术语对齐
────────────────────────────────────────

- `status` 是当前态主裁定字段，只允许取 `active / superseded`
- `state` 是领域生命周期字段，如 `open / blocked / resolved / implemented`
- `state` 不得承担 `active / superseded` 语义
- 在当前 Phase 0 canonical 口径下：
  - 当前态集合以 `status=active` 为主
  - 允许 `state` 作为 pending gate 参与成员资格判定
  - 当前唯一已落地的 pending gate 为：
    - `type=OpenTask`
    - `status=active`
    - `state=open`
    - 内容含“待定 / 待裁定 / 仍需最终裁定 / 当前推荐”等信号

术语裁定：

- `supersede` 支配 `priority`
- `must_include` 只在当前态集合上评估
- 被 supersede 的节点必须退出 `must_include` 候选集

────────────────────────────────────────
## 2. 目录约定
────────────────────────────────────────

以 `abu_modern` 为例：

- raw：`raw/projects/abu_modern/s001/turn_00X.md`
- normalized：`normalized/projects/abu_modern/s001/turn_00X.norm.md`
- manifest：`normalized/projects/abu_modern/s001/turn_00X.manifest.json`
- patch：`graph/projects/abu_modern/phase0_manual/patches/patch_00X.json`
- 当前图：`graph/projects/abu_modern/phase0_manual/graph_state.json`
- turn 快照：`graph/projects/abu_modern/phase0_manual/run/graph_state.turn_00X.json`
- lint：`graph/projects/abu_modern/phase0_manual/reports/lint_report.turn_00X.json`
- bundle：`graph/projects/abu_modern/phase0_manual/reports/context_bundle.*.json`
- assembly：`graph/projects/abu_modern/phase0_manual/reports/assembly_report.*.json`
- 阶段报告：`graph/projects/abu_modern/phase0_manual/reports/*.md`

────────────────────────────────────────
## 3. 产物纪律
────────────────────────────────────────

### 3.1 normalized / manifest

- 只做降噪，不做失效判断
- `manifest.span_map` 必须保留 raw 的字符偏移
- summary 允许概括，但 patch 中的 `content` 必须可回溯到 raw / graph 节点

### 3.2 patch

- patch 允许手工编写，但必须符合脚本输入格式
- `superseded_nodes` 必须是对象数组，不是字符串数组

正确示例：

```json
{
  "superseded_nodes": [
    {
      "node_id": "n_0013",
      "reason": "旧的待定关系退出当前态。"
    }
  ]
}
```

错误示例：

```json
{
  "superseded_nodes": ["n_0013"]
}
```

- 如需表达裁定替换，建议同时写：
  - `superseded_nodes`
  - `invalidates` 边
- 若是确认态替换 pending 候选，新节点的 `state` 不得继续为 `open`

### 3.3 bundle / assembly

- `context_bundle` 必须由 `graph/scripts/build_context_bundle.py` 生成
- 不接受手写 bundle 作为 `(a)(b)(c)` 或封板证据
- `excluded_due_to_state` 与 `excluded_due_to_budget` 必须可区分
- 不允许把 pending 排除信号淹没到 `excluded_due_to_budget`

────────────────────────────────────────
## 4. 单轮流程
────────────────────────────────────────

### STEP 1：准备 normalized / manifest

- 读取 raw turn
- 写出 `turn_00X.norm.md`
- 写出 `turn_00X.manifest.json`

### STEP 2：编写 patch

- 用 normalized / manifest 提炼本轮新增、更新、supersede
- 写出 `patch_00X.json`
- 若本轮是裁定轮：
  - 新旧节点必须共用同一 `entity_ref`
  - 旧节点经 `superseded_nodes` 退出当前态
  - 新节点若为确认态，不得继续 `state=open`

### STEP 3：apply

运行：

```bash
python graph/scripts/apply_patch.py --graph graph/projects/<project_id>/phase0_manual/graph_state.json --patch graph/projects/<project_id>/phase0_manual/patches/patch_00X.json --in-place --snapshot-dir graph/projects/<project_id>/phase0_manual/run
```

### STEP 4：lint

运行：

```bash
python graph/scripts/graph_lint.py graph/projects/<project_id>/phase0_manual/graph_state.json --out graph/projects/<project_id>/phase0_manual/reports/lint_report.turn_00X.json
```

验收要点：

- `ok=true`
- `errors=0`
- `state_participates_in_current_membership` 与当前 canonical 规则一致

### STEP 5：assembly

运行：

```bash
python graph/scripts/build_context_bundle.py --graph graph/projects/<project_id>/phase0_manual/graph_state.json --project-id <project_id> --turn-id turn_00X --out graph/projects/<project_id>/phase0_manual/reports/context_bundle.turn_00X.json --report-out graph/projects/<project_id>/phase0_manual/reports/assembly_report.turn_00X.json --max-nodes <N> --budget-profile <PROFILE>
```

### STEP 6：报告

- 写一份 `turn_00X_execution_report.md`
- 必须贴出关键 JSON 片段，不只报 pass / fail

────────────────────────────────────────
## 5. 已验证的 Phase 0 模式
────────────────────────────────────────

### 5.1 supersede 模式

已在 `turn_002` 验证：

- 旧态节点被 supersede
- 新态节点保留同一 `entity_ref`
- bundle 中出现新态、排除旧态

### 5.2 pending gate 模式

已在 `turn_004` 前置装配验证：

- `status=active` 不是唯一条件
- `state=open` 的 pending open-task candidate 会被记入 `excluded_due_to_state`
- 不得再把它归入 `excluded_due_to_budget`

### 5.3 budget 规则

已验证两侧边界：

- `budget == must_count`：`must` 全保
- `budget < must_count`：直接拒绝，不生成 bundle
- `budget = 4`：`must` 全保后，`should` 按 `created_turn desc, node_id asc` 回填

────────────────────────────────────────
## 6. turn_005 封板标准
────────────────────────────────────────

Phase 0 封板要满足三件事：

1. 全链重放
   - `patch_001..004` 从 seed 可确定性重放
   - `graph_state.turn_004.json` 可被字节级重建

2. bundle 可再生
   - canonical `context_bundle.*.json` 与 `assembly_report.*.json` 可由对应图快照重生成
   - 允许 legacy 手工样例归档，但 canonical 文件必须机械生成

3. runbook 可重跑
   - 规则、命令、约束、异常点必须写入本手册

────────────────────────────────────────
## 7. 封板命令
────────────────────────────────────────

运行：

```bash
python graph/scripts/replay_phase0_seal.py --project-id abu_modern
```

产物：

- `graph/projects/abu_modern/phase0_manual/reports/turn_005_seal_report.json`

封板通过条件：

- `ok = true`
- `graph_replay[*].semantic_equal = true`
- `graph_replay[*].sha256_equal = true`
- `bundle_replay[*].bundle.sha256_equal = true`
- `bundle_replay[*].assembly_report.sha256_equal = true`

────────────────────────────────────────
## 8. 备注
────────────────────────────────────────

- `context_bundle.turn_001.legacy_manual.json` 只保留为历史样例，不再作为 canonical 证据
- canonical `context_bundle.turn_001.json` / `assembly_report.turn_001.json` 由 turn_005 封板时重生成
- 若未来重放失败或 bundle 再生漂移，应视为 bug，进入修复轮；这不属于继续扩用例
