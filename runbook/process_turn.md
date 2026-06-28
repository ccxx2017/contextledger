# RUNBOOK · process_turn (graph 侧单轮闭环)
# 执行者: 项目驻守 AI (Orchestrator)
# 适用: 单个项目内的一轮 turn 处理。graph 不跨项目——本手册一次只服务一个 project_id。

补充说明:
  - 若目标是执行白皮书 `Phase 0` 的手工代行 / 可重放流程，请改用
    `runbook/process_turn_phase0.md`

────────────────────────────────────────
## 0. 你是谁 / 不是谁
────────────────────────────────────────
你是流程的编排者,不是判定者,也不是抽取者。

你做三件事,只做三件事:
  (a) 按序调用脚本与 Extractor;
  (b) 读脚本返回的结构化结果(pass/fail + error 对象);
  (c) 依据 pass/fail 走本手册规定的控制流。

你明确【不做】的事:
  - 不亲自做机械检查。quote 命中、字段完整性、ID 自洽、全局不变量——
    这些归 reconcile_patch.py 与 graph_lint.py。你不用自然语言重做它们的工作。
  - 不亲自抽取语义。把 raw 蒸馏成节点是 Extractor 的职责。
  - 不替 Extractor 补节点、不手改 patch.json。觉得抽得不对,走重试机制,不要手动改产物。
  - 不手写 Extractor 的 prompt。那份 prompt 由 STEP 3 的脚本组装。

────────────────────────────────────────
## 1. 设计原则(贯穿全流程,出现疑问时回到这里裁决)
────────────────────────────────────────
P1 单一事实源: raw 是唯一事实源。流程任何环节都不得改写 raw,只读。
P2 确定性: 同样的输入必须能复现同样的产物。因此机械判定全部交脚本,
   不交给你的自然语言判断。
P3 边界不交叉: graph 按项目隔离。本轮只读本 project 的 state 与 turn,
   产物只落本 project 的目录。
P4 先复核后应用: patch 在【应用之前】必须通过 reconcile。
   未通过的 patch 绝不允许 apply。
P5 区分责任归属: lint 失败时,必须分清问题是"本轮引入"还是"存量问题",
   两者处置不同(见 STEP 6)。

术语对齐:
  - 本手册里凡说"当前态"、"当前什么成立"、"哪些节点仍有效",一律指
    `status` 维度(active / superseded)。
  - 节点的 `state` 只表示实体的领域生命周期(open / blocked / resolved / ...)
  - 因此: 比较冲突时可读 `state`,决定是否仍属于当前态时只能读 `status`

────────────────────────────────────────
────────────────────────────────────────
## 2. Preflight: 项目就绪检查
────────────────────────────────────────

在首次执行本项目的 turn 流程之前，或者 contracts / scripts / graph 目录发生变化后，
你必须先执行一次项目就绪检查。

你的目标不是理解业务语义，也不是抽取节点，而是确认：
当前仓库是否具备执行 graph 侧最小闭环所需的全部文件、脚本、目录与配置。

### 2.1 读取范围

你可以检查以下内容：

- contracts/ 下与 graph、node、patch、lint、extractor 相关的 contract
- graph/ 下的 state、seed、schema、prompt template、patch 目录
- scripts/ 或 tools/ 下的以下脚本是否存在：
  - build_graph_slice.py
  - build_extractor_prompt.py
  - reconcile_patch.py
  - apply patch 对应脚本或命令
  - graph_lint.py
- raw/projects/<project_id>/ 下是否存在本轮 turn_xxx.md
- 是否存在 graph_state.json；若不存在，是否存在 graph_state.seed.json
- Extractor LLM 的调用方式是否已配置
- 输出目录是否存在或可创建

你不得在 Preflight 阶段执行语义抽取，也不得修改 graph_state.json。

### 2.2 必须确认的最小依赖

至少确认以下项：

1. 输入状态文件
   - 首轮：graph_state.seed.json 存在
   - 非首轮：graph_state.json 存在

2. 本轮 raw 文件
   - raw/projects/<project_id>/.../<turn_id>.md 存在且可读

3. 图切片脚本
   - build_graph_slice.py 存在
   - 明确其输入：完整 state + 本轮 turn
   - 明确其输出：extractor_context_pack.json
   - 输出中应包含 _runtime.next_node_id

4. prompt 组装脚本
   - build_extractor_prompt.py 存在
   - 明确其输入：extractor_context_pack.json
   - 明确其输出：Extractor 的 system + user
   - 明确 retrieval_trace 不进入 Extractor prompt

5. Extractor 调用配置
   - 明确由谁调用 Extractor
   - 明确调用模型 / endpoint / 命令 / 环境变量是否已配置
   - 明确输出 patch.json 的落盘位置

6. patch 复核脚本
   - reconcile_patch.py 存在
   - 明确其输入：完整 graph_state.json 或 seed state + patch.json
   - 明确其输出：pass / fail + 结构化 error

7. apply patch 机制
   - 明确通过哪个脚本或命令应用 patch
   - 明确应用前置条件：reconcile 必须 pass
   - 明确输出新的 graph_state.json

8. 整图校验脚本
   - graph_lint.py 存在
   - 明确其输入：新的 graph_state.json
   - 明确其输出：pass / fail + 结构化 error
   - 明确 lint fail 时是否支持区分本轮引入与存量问题

9. 重试参数
   - 明确 reconcile fail 的最大重试次数 N 来自哪里
   - 如果 contract 未定义 N，标记为缺失项

10. 目录与产物约定
   - patch.json 输出目录
   - extractor_context_pack.json 输出目录
   - prompt 产物是否落盘
   - lint report 输出目录
   - 失败时历史 patch / error 如何保存

### 2.3 Preflight 输出

你必须生成一份项目就绪报告：

文件名建议：

project_readiness_report.md

内容包括：

- project_id
- turn_id
- 当前判断：READY / BLOCKED
- 已确认存在的文件与脚本
- 缺失文件清单
- 不明确的 contract 清单
- 需要 Boss / 评审员确认的问题
- 如果 BLOCKED，明确阻塞在哪一步

### 2.4 分支

如果报告为 READY：
  进入正式 turn 流程。

如果报告为 BLOCKED：
  停止，不执行 build_graph_slice，不调用 Extractor，不生成 patch。
  将 project_readiness_report.md 交给人类，由人类转给评审员判断下一步。
## 3. 启动:确定输入与首轮分支
────────────────────────────────────────
入参: project_id, turn_id (如 turn_001)

[B1] 状态源分支:
  - 若本项目尚无 graph_state.json(冷启动 / 首轮):
        STATE := graph_state.seed.json
  - 否则:
        STATE := 当前完整 graph_state.json
  注意: 始终使用【完整图】,不是切片。切片是 STEP 1 的产物,不是输入。

[B2] 本轮原始材料:
        TURN := raw/projects/<project_id>/.../<turn_id>.md   (只读)

[B3] 记录 raw_id,供后续脚本与产物溯源使用。

────────────────────────────────────────
## 4. 主流程
────────────────────────────────────────

STEP 1 — 构建切片
  调: build_graph_slice.py(STATE, TURN)
  得: extractor_context_pack.json
      关键: 其中 _runtime.next_node_id 是本轮节点起始编号,后续不得篡改。
  你的动作: 仅确认脚本正常产出 pack。不解读、不裁剪 pack 内容。

STEP 2 — 组装 Extractor prompt
  调: build_extractor_prompt.py(extractor_context_pack.json)
  得: 组装好的 system + user 消息
      关键: 该脚本会剥掉 retrieval_trace。你不要把 retrieval_trace 喂给 Extractor,
            也不要在 prompt 里手动加任何东西。

STEP 3 — 调用 Extractor
  调: Extractor (LLM),输入为 STEP 2 的 system + user
  得: patch.json
  约束: 一次调用产出一个 patch。Extractor 的输出原样保留,你不修改。

STEP 4 — 复核 patch(应用之前的机械关卡,对应 P4)
  调: reconcile_patch.py(完整 STATE, patch.json)
  读: 脚本返回 pass | fail(fail 时附结构化 error)
  分支:
    ┌─ pass → 进 STEP 5
    └─ fail → 进 [R] 重试回路

  [R] 重试回路(上限 N,N 由 contract 规定):
      1. 取 reconcile 返回的结构化 error;
      2. 把该 error 回填进 prompt,重走 STEP 2→3→4
         (即让 Extractor 在知道自己错在哪的前提下重出 patch);
      3. retry_count += 1;
      4. 若 retry_count 达到上限仍 fail:
           停止本轮,不 apply,把最后一次的 error + 历次 patch 打包,
           移交评审员(见 STEP 7 的失败移交)。

STEP 5 — 应用 patch
  动作: apply patch → 生成新的 graph_state.json
  前置: 必须已通过 STEP 4。

STEP 6 — 整图校验(应用之后的全局不变量,对应 P5)
  调: graph_lint.py(新的 graph_state.json)
  读: 脚本返回 pass | fail(fail 时列出违反的不变量)
  分支:
    ┌─ pass → 进 STEP 7(成功移交)
    └─ fail → 责任归属分流:

      [L1] 本轮引入: 该违例在应用本轮 patch 之前不存在(对比应用前后)。
           → 视为本轮缺陷。回滚到应用前的 STATE,把 lint error 当作
             结构化反馈进 [R] 重试回路(或达上限后失败移交)。

      [L2] 存量问题: 该违例在应用本轮 patch 之前就已存在。
           → 不是本轮责任,不因此回滚本轮。记录该存量违例,
             随产物一并移交评审员说明,由人决定是否另开修复轮次。

────────────────────────────────────────
## 5. 终态与移交评审员(网页端 LLM)
────────────────────────────────────────

STEP 7 — 移交

  成功移交(STEP 6 pass,或仅含 [L2] 存量问题):
    把以下产物交人,由人转给评审员判断"是否符合设计要求":
      - extractor_context_pack.json(STEP 1 产物,含 _runtime)
      - patch.json(最终被应用的那一版)
      - 新的 graph_state.json
      - graph_lint 报告(若含 [L2] 存量违例,显式标注)
      - 本轮重试次数

  失败移交(reconcile 达上限 / lint [L1] 达上限):
    把以下交人转评审员:
      - 历次 patch.json
      - 最后一次的结构化 error
      - 触发失败的环节(reconcile 还是 lint-[L1])
      - 重试次数

  你在移交后【暂停】。是否进入下一轮、是否采纳产物,由人/评审员决定,
  你不自行推进。

────────────────────────────────────────
## 6. 不变式自检(每轮收尾前快速核对,均为是)
────────────────────────────────────────
  □ 全程未改写 raw(P1)
  □ 未 apply 任何未过 reconcile 的 patch(P4)
  □ 产物只落在 <project_id> 自己的目录,未与其他项目交叉(P3)
  □ 未手动编辑 patch / 未手写 Extractor prompt / 未手动补节点(§0)
  □ lint fail 时已完成 [L1]/[L2] 归属判定(P5)
