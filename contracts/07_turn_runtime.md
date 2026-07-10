# Turn 运行契约 [PROVISIONAL]

本文件补足 Phase 1-prep 的运行期约定：
- 主项目 checkpoint 判断
- reconcile retry 上限
- 项目级目录落盘约定
- `[L1] 本轮引入 / [L2] 存量问题` 的机械判定
- 校准期 `human_edits` 记录与毕业条件
- 正式流水线的时序前置校验

## 1. 主项目 checkpoint

针对 `abu_modern` 当前状态：
- `graph/projects/abu_modern/graph_state.json` 的 `turn_counter = 3`
- `raw/projects/abu_modern/s001/` 下已有 `turn_001.md` 到 `turn_006.md`
- `graph/projects/abu_modern/run/` 已保存到 `graph_state.turn_003.json`

结论：
- Phase 1 首个正式 turn 应从 `turn_004` 开始

理由：
1. `turn_counter=3` 说明主图当前权威态只覆盖到第 3 轮
2. 直接从 `turn_007` 开始会跳过 `turn_004~006`，破坏 raw 到 graph 的线性提交序
3. 当前主图并非空图，因此不需要回到 cold-start replay；只需从已确认 checkpoint 顺延

## 2. reconcile retry 上限

- contract 常量：`MAX_RECONCILE_RETRIES = 3`

含义：
- 同一轮在 `reconcile_patch.py` 失败后，最多允许 3 次“回填结构化 error 后重试”
- 达上限仍失败，则不得 apply，必须转入 `quarantine/`

说明：
- 这里的 `3` 是运行契约常量，不再只依赖脚本默认值

## 3. 项目级目录约定

项目根：
- `graph/projects/<project_id>/`

正式运行期目录：
- `graph_state.json`：当前权威图
- `run/`：每轮应用后的图快照
- `patches/`：本项目正式 patch 落盘区
- `pending_merge/`：resolver 未敢自动合并的待审记录
- `reports/`：readiness、lint、assembly、dry-run、extractor 响应等报告
- `quarantine/`：失败 patch 与错误记录
- `reports/turn_004_execution_report.md`：本轮执行与人工裁定记录

建议命名：
- `patches/patch_004.json`
- `reports/reconcile_report.turn_004.json`
- `reports/lint_report.turn_004.json`
- `reports/lint_delta.turn_004.json`
- `pending_merge/pending_merge.turn_004.json`
- `reports/context_bundle.turn_004.json`
- `reports/assembly_report.turn_004.json`

## 4. [L1] / [L2] 机械判定

定义：
- `[L1] 本轮引入`：应用后 lint 中出现，但应用前 lint 不存在的问题
- `[L2] 存量问题`：应用前 lint 已存在，应用后仍存在的问题
- 持久基线：已被确认的历史存量问题，可额外落在 `lint_baseline.json` 中，作为跨轮稳定参照

参考实现脚本：
- `graph/scripts/diff_lint_reports.py`

输入：
- 应用前 `graph_state.json`
- 应用后 `graph_state.json`
- 可选：`lint_baseline.json`

输出：
- `introduced_errors`
- `preexisting_errors`
- `introduced_warnings`
- `preexisting_warnings`
- `baseline_matched_errors`
- `baseline_matched_warnings`
- `issue_code_histogram`：按违例 `code` 聚合后的计数直方图（用于识别“同类问题持续触发”的信号）

控制流：
- 若存在 `introduced_errors`，按 `[L1]` 处理：回滚并进入 retry / quarantine
- 若仅存在 `preexisting_errors`，按 `[L2]` 处理：不回滚本轮，但随移交报告显式标注

基线文件建议路径：
- `graph/projects/<project_id>/reports/lint_baseline.json`

补充约定：
- `lint_baseline.json` 中的 `remediation_status=tracked` 不是永久豁免
- 每个 tracked 项必须带：
  - `first_confirmed_turn`
  - `escalate_after_turns`
  - `escalate_on_or_after_turn`
  - `overdue_action`
- `diff_lint_reports.py` 在匹配 baseline 时，若当前轮次达到 `escalate_on_or_after_turn` 且仍为 `tracked`，必须将该项写入 `overdue_baseline_issues`
- `overdue_baseline_issues` 在当前阶段先作为治理告警，不自动阻塞提交；是否升级为硬阻塞，由后续治理轮再收紧

## 5. 正式流水线的时序前置校验

目标：
- 防止脚本因读取不存在文件而直接崩溃
- 防止脚本误读“轮次不匹配”或“同名旧快照”的 after-graph
- 防止 `apply_patch.py` 把 patch 套到错误上一态并持久化错误写入

当前规则：
- `apply_patch.py` 必须校验 `graph.turn_counter == patch.turn_id - 1`
- `apply_patch.py` 可传 `--expected-turn`，要求 `patch.turn_id == expected_turn`
- `diff_lint_reports.py` 必须传 `--expected-turn`
- `diff_lint_reports.py` 可传 `--after-newer-than <本轮 patch 或其他参考文件>`，要求 after-graph 修改时间晚于参考文件
- `graph_lint.py` 可传 `--expected-turn` 与 `--newer-than`
- `build_context_bundle.py` 内建校验 `graph.turn_counter == turn_id`，并可传 `--newer-than`

拒绝策略：
- 若 `apply_patch.py` 的输入图不是 patch 合法的上一态，脚本必须在写出前拒绝执行
- 若 `apply_patch.py` 的 patch 轮次与 `--expected-turn` 不一致，脚本必须在写出前拒绝执行
- 若 after-graph 文件不存在，脚本必须以明确报错退出，提示“请先生成本轮 graph_state 快照”
- 若 after-graph 的 `turn_counter` 与预期轮次不一致，脚本必须拒绝执行，避免误读旧轮次快照
- 若 after-graph 的修改时间不晚于参考文件，脚本必须拒绝执行，避免误读同名旧快照

推荐顺序：
1. `apply_patch.py --graph run/graph_state.turn_004.json --patch patches/patch_005.json --expected-turn turn_005 --out run/graph_state.turn_005.json`
2. `graph_lint.py run/graph_state.turn_005.json --expected-turn turn_005 --newer-than patches/patch_005.json`
3. `diff_lint_reports.py --before-graph run/graph_state.turn_004.json --after-graph run/graph_state.turn_005.json --expected-turn turn_005 --after-newer-than patches/patch_005.json`
4. `build_context_bundle.py --graph run/graph_state.turn_005.json --turn-id turn_005 --newer-than patches/patch_005.json`

说明：
- 以上规则能机械拦住三类错误：
  - 写入前上一态错误
  - 文件尚未生成
  - 轮次错误或旧快照被误读

## 6. 校准期 human_edits 记录

目的：
- 记录“本轮准入裁定时，人工到底改了什么”
- 该记录用于校准期回看，不用于宣称模型已学会

规则：
- 不新增三段式永久命名规范
- 原始模型输出的最高价值证据是 `extractor_raw_response.turn_004.txt`
- 每轮只在 `turn_xxx_execution_report.md` 中追加结构化字段 `human_edits`

建议结构：

```json
"human_edits": [
  {
    "node_id": "n_0033",
    "field": "status",
    "before": null,
    "after": "superseded",
    "reason": "resolved 语义需同步退出当前态"
  }
]
```

毕业条件：
- 若连续 5 轮真实 turn 的 `human_edits` 为空，或仅命中“已知且已被现有 lint/reconcile 明确拦截的错误类型”，且本轮未出现“新错误类型”，则停止要求记录 `human_edits`
- 到达毕业条件后，默认把安全网完全交给机械层

计数规则：
- `turn_004` 不计入“连续 5 轮干净轮次”中的 `1/5`
- 原因：`turn_004` 的 `human_edits` 非空，且其中至少包含“本轮才刚被机械层学会拦截”的新错误类型
- 因此 `turn_004` 在毕业计数器中记为“重置轮 / 第 0 轮”，后续连续干净轮次从 `turn_005` 才开始计

## 7. 观察期边界

当前已落地但仍属观察期的规则：
- `reconcile_patch.py` 新增的“终态 OpenTask 缺少 `status=superseded`”检查，只精确覆盖 `OpenTask(state -> resolved/cancelled)` 这一方向
- 该规则是由 `turn_004` 真实反例触发的定向补丁，不应表述为“所有 node type 的通用状态联动机制已完成”
- 反方向检查，即“节点已 `status=superseded` 但 `state` 未同步到合理终态”，目前尚未落地机械检查；出现真实反例后再决定是否泛化

## 8. scratch dry-run 纪律

dry-run 目标：
- 证明 `patch -> reconcile -> apply -> lint -> quarantine` 路径可运行

纪律：
- dry-run 不得覆盖主项目 `graph_state.json`
- 所有中间产物落在 `reports/dry_run/` 或临时 scratch 目录
- dry-run 可使用人工构造 patch 或已有样例 patch，不要求真实调用 Extractor

## 9. Phase 1 单写者线性化（禁止并行派工）

约束：
- Phase 1 运行期禁止并行派工与并行提交：同一轮 turn 只能有一个协调者产出单个 patch 并线性提交
- 该约束用于规避 valid-time 能力缺口被提前触发

说明：
- 若未来引入并行派工，必须先补齐 valid-time adjudication 的端到端契约与拦截机制，再解除该约束

## 10. 关闭候选检测（闸门召回）

目的：
- 召回“可能应被本轮内容回答/推进，但 patch 未显式 updated”的旧 `open` / `blocked` / `in_progress` 节点
- 该步骤不做最终裁决，只提供候选清单，作为闸门人工核对输入

参考脚本：
- `graph/scripts/detect_close_candidates.py`

## 11. pending_merge 消化机制（禁止静默搁置）

目标：
- `pending_merge/` 是“保守不合并”的安全网，但进入队列不等于被处理
- 每条 pending_merge 必须能机械追踪：为什么被挂起、阻塞在哪一轮、何时升级、最终消化成什么

最小要求（同构 baseline 过期机制）：
- 每条 pending_merge 必须在项目侧登记为一条可追踪条目（建议文件：`pending_merge/pending_merge_register.json`）
- 登记条目必须包含：
  - `requires_evidence`：指明要回哪段原文核查什么（例如“回 turn_005 原文核查路径迁移意图”）
  - `blocked_turn`：该条目首次阻塞的轮次
  - `escalate_after_turns` / `escalate_on_or_after_turn`：超期升级阈值
- 超期策略：
  - 若达到 `escalate_on_or_after_turn` 且仍未消化，必须升级为硬阻塞（退出本轮提交或阻止进入下一轮）

消化去向必须落盘：
- digest 成 `alias`：更新 `contracts/05_entity_naming.md` 的别名映射表，使 resolver 下次可自动规范化
- digest 成 `supersede`：在后续 turn 以图变更形式留下可查痕迹（旧节点退出当前态集合 + 新节点取代）
- digest 成 `coexist`：显式记录二者关系（不得仅“放任漂移”）

参考脚本：
- `graph/scripts/check_pending_merge_register.py`
