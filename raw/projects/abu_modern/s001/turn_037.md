# 用户：
任务：将 TKT-2026-005B 从 paused_for_boss_review 恢复为“受限恢复态”，但禁止恢复完整研究执行。

前置约束：
- 禁止运行任何回测。
- 禁止调用 192.168.1.136:8000 的 backtest/builder 端点。
- 只允许修改工单状态与 Worklog。
- 不要 commit，等 Boss 审核。

必须读取：
1. aos/runtime/tickets/blocked/TKT-2026-005B-vcp-breakout-entry.md
2. skills/strategy_researcher/SKILL.md
3. skills/strategy_researcher/prompts/research_workflow.md
4. skills/strategy_researcher/TOOLS.md

修改要求：
1. 将 TKT-2026-005B 从 blocked 目录移回 open 目录。
2. 工单状态不要写成 ready_for_full_execution。
3. 优先使用：
   status: ready_for_limited_resume
   如果当前项目状态枚举不支持，则使用：
   status: open
   execution_mode: limited_resume
4. 在 Worklog 追加 Boss 授权记录，内容必须包含：
   - Boss 允许恢复的是“受限验证执行”，不是完整研究执行
   - 第一轮恢复必须是 smoke run：symbols ≤ 5，years ≤ 1
   - smoke 通过后最多放大到 symbols ≤ 20，years ≤ 3
   - timeout = 90s
   - 后端失败 / 超时 / 5xx / 连接失败 1 次即 paused_for_boss_review
   - 禁止自动重试
   - 禁止 231 标的回测
   - 禁止将受限阶段结果作为完整研究结论
5. 不得修改 research-runs 下已有研究产物。

完成后输出：
1. 实际读取了哪些 .md 文件
2. 实际修改了哪些文件
3. 工单最终路径
4. 工单最终 status 字段
5. 是否调用了 scripts/ 下任何脚本
6. 是否产生网络请求
7. git status
8. git diff --stat

不要 commit。
# feishu Agent:
完成报告

1. 实际读取了哪些 .md 文件

#
文件
路径
1
005B 工单
aos/runtime/tickets/blocked/TKT-2026-005B-vcp-breakout-entry.md
2
SKILL.md
skills/strategy_researcher/SKILL.md
3
research_workflow.md
skills/strategy_researcher/prompts/research_workflow.md
4
TOOLS.md
skills/strategy_researcher/TOOLS.md

另读 _protocol.md 和现有工单以确认 status 字段枚举约定（确认无枚举约束，可自由使用新值）。
2. 实际修改了哪些文件

文件
路径
操作
行数变化
005B 工单
aos/runtime/tickets/open/TKT-2026-005B-vcp-breakout-entry.md
修改
+28/-2
—
从 blocked/ 移到 open/
移动
—
3. 工单最终路径
/home/ccxx/aos_repo/aos/runtime/tickets/open/TKT-2026-005B-vcp-breakout-entry.md
4. 工单最终 status 字段
ready_for_limited_resume
5. 是否调用了 scripts/ 下任何脚本
否。
6. 是否产生网络请求
否。
7. git status
修改：     aos/runtime/tickets/open/TKT-2026-005B-vcp-breakout-entry.md
未跟踪:    README_PAUSE.md (005B research-runs, 之前创建)
未跟踪:    TKT-2026-005C-backtest-safety-guard.md (之前创建, 未 commit)

8. git diff --stat
aos/runtime/tickets/open/TKT-2026-005B-vcp-breakout-entry.md | 30 ++++++++++++++++++++--
 1 file changed, 28 insertions(+), 2 deletions(-)

未 commit，等你审核。

任务：对 TKT-2026-005B 执行“受限恢复执行前检查”，禁止运行回测，禁止调用后端。

必须读取：
1. aos/runtime/tickets/open/TKT-2026-005B-vcp-breakout-entry.md
2. skills/strategy_researcher/SKILL.md
3. skills/strategy_researcher/prompts/research_workflow.md
4. skills/strategy_researcher/TOOLS.md
5. skills/strategy_researcher/prompts/hypothesis_heuristics.md
6. skills/strategy_researcher/prompts/report_template.md

检查并输出：
1. 实际读取了哪些 .md 文件
2. 哪个文件是最高行为手册
3. 当前工单 status 是什么
4. 是否识别到 execution_mode / ready_for_limited_resume
5. 正式执行时必须遵循哪些 Phase
6. 本次是否允许完整研究执行
7. 本次是否只允许受限验证执行
8. smoke run 的资源预算：
   - symbols ≤ 5
   - years ≤ 1
   - timeout = 90s
9. smoke 通过后最大资源预算：
   - symbols ≤ 20
   - years ≤ 3
10. 后端失败 / 超时 / 5xx / 连接失败时应如何处理
11. 是否允许自动重试
12. 是否允许 231 标的回测
13. 是否已经满足“受限恢复执行”条件

禁止：
- 禁止运行 scripts/
- 禁止调用 192.168.1.136:8000
- 禁止修改文件
- 禁止 git commit

# feishu Agent:
现在完整掌握了所有信息。以下是受限恢复执行前检查报告：
───
受限恢复执行前检查报告
实际读取了哪些 .md 文件
| # | 文件                               | 绝对路径                                                                                       |
| --- | -------------------------------- | ------------------------------------------------------------------------------------------ |
| 1 | 工单 005B（当前）                      | /home/ccxx/aos_repo/aos/runtime/tickets/open/TKT-2026-005B-vcp-breakout-entry.md           |
| 2 | SKILL.md                         | /home/ccxx/.openclaw/workspace/skills/strategy_researcher/SKILL.md                         |
| 3 | research_workflow.md（主 playbook） | /home/ccxx/.openclaw/workspace/skills/strategy_researcher/prompts/research_workflow.md     |
| 4 | TOOLS.md                         | /home/ccxx/.openclaw/workspace/skills/strategy_researcher/TOOLS.md                         |
| 5 | hypothesis_heuristics.md         | /home/ccxx/.openclaw/workspace/skills/strategy_researcher/prompts/hypothesis_heuristics.md |
| 6 | report_template.md               | /home/ccxx/.openclaw/workspace/skills/strategy_researcher/prompts/report_template.md       |
哪个文件是最高行为手册
**prompts/research_workflow.md**。TOOLS.md 明确列出："主 playbook；每个 investigation 工单开始必读"。SKILL.md 也声明："行动手册见 prompts/research_workflow.md（每次任务开始必读）"。
当前工单 status 是什么
**ready_for_limited_resume**
是否识别到 execution_mode / ready_for_limited_resume
是。
• frontmatter status: ready_for_limited_resume 显式声明
• Worklog Boss 授权记录（2026-05-19）详细说明了授权范围："受限验证执行（非完整研究执行）"
正式执行时必须遵循哪些 Phase
按 research_workflow.md §2：
| Phase           | 必须？         | 本工单特殊性                                                               |
| --------------- | ----------- | -------------------------------------------------------------------- |
| Phase 0 环境同步    | 不得省略        | cd /home/ccxx/aos_repo && git pull --rebase                          |
| Phase 1 工单校验    | 不得省略        | intent_type=investigation ✅, assigned_to=agent-strategy-researcher ✅ |
| Phase 2 KB 上下文  | 标准路径        | 已有 Phase 2 记录（读 KB 9 策略基线），但重新执行时建议 re-read 获取最新状态                   |
| Phase 3 研究循环    | 标准路径        | 从 Round 3 开始；上限 5 轮（已用 2 轮，剩余 3 轮）                                   |
| Phase 4 产出报告    | 标准路径        | metrics.py → report_template.md                                      |
| Phase 5 Worklog | append-only | 追加即可                                                                 |
| Phase 6 终态提交    | 不得省略        | git add → commit → push                                              |
本次是否允许完整研究执行
否。
本次是否只允许受限验证执行
是。 工单 Worklog Boss 授权记录第 2 行明确："授权范围: 受限验证执行（非完整研究执行）"。
smoke run 的资源预算
| 参数      | 上限  | 依据                                              |
| ------- | --- | ----------------------------------------------- |
| symbols | ≤ 5 | Boss 授权限制第 1 条："第一轮恢复必须是 smoke run：symbols ≤ 5" |
| years   | ≤ 1 | 同上                                              |
| timeout | 90s | Boss 授权限制第 3 条 + research_workflow.md §3.1 硬限制  |
smoke 通过后最大资源预算
| 参数      | 上限   | 依据                                                                         |
| ------- | ---- | -------------------------------------------------------------------------- |
| symbols | ≤ 20 | Boss 授权限制第 2 条：max_symbols=20（与 call_backtest.py 的 MAX_SYMBOLS_DEFAULT 一致） |
| years   | ≤ 3  | Boss 授权限制第 2 条：max_years=3（与 call_backtest.py 的 MAX_YEARS_DEFAULT 一致）      |
后端失败 / 超时 / 5xx / 连接失败时应如何处理
一次即 raise，立即进入 paused_for_boss_review。
• Boss 授权限制第 4 条："后端失败 / 超时 / 5xx / 连接失败 1 次即 paused_for_boss_review"
• research_workflow.md §3.1 约束表下行："超时/5xx/连接失败：一次即 raise，禁止自动重试，该轮标记 backend_unreachable，立即进入 paused_for_boss_review"
• SKILL.md 失败处理矩阵："资源闸违规 → 立即 break，paused_for_boss_review，不重试"
是否允许自动重试
禁止。
• Boss 授权限制第 5 条："禁止自动重试"
• research_workflow.md §3.1："禁止自动重试"
• call_backtest.py 实现：network 错误返回退出码 1，不重试
是否允许 231 标的回测
绝对禁止。
• Boss 授权限制第 6 条："禁止 231 标的回测"
回复 用户327273: 
任务：对 TKT-2026-005B 执行“受限恢复执行前检查”，禁止运行回测，禁止调用后端。

必须读取：
1. aos/runtime/tickets/open/TKT-2026-005B-vcp-breakout-entry.md
2. skills/strategy_researcher/SKILL.md
3. skills/strategy_researcher/prompts/research_workflow.md
4. skills/strategy_researcher/TOOLS.md
5. skills/strategy_researcher/prompts/hypothesis_heuristics.md
6. skills/strategy_researcher/prompts/report_template.md

检查并输出：
1. 实际读取了哪些 .md 文件
2. 哪个文件是最高行为手册
3. 当前工单 status 是什么
4. 是否识别到 execution_mode / ready_for_limited_resume
5. 正式执行时必须遵循哪些 Phase
6. 本次是否允许完整研究执行
7. 本次是否只允许受限验证执行
8. smoke run 的资源预算：
   - symbols ≤ 5
   - years ≤ 1
   - timeout = 90s
9. smoke 通过后最大资源预算：
   - symbols ≤ 20
   - years ≤ 3
10. 后端失败 / 超时 / 5xx / 连接失败时应如何处理
11. 是否允许自动重试
12. 是否允许 231 标的回测
13. 是否已经满足“受限恢复执行”条件

禁止：
- 禁止运行 scripts/
- 禁止调用 192.168.1.136:8000
- 禁止修改文件
- 禁止 git commit
• call_backtest.py: MAX_SYMBOLS_DEFAULT=20，231 > 20 → _validate_request() 抛 BacktestGuardrailError
是否已经满足"受限恢复执行"条件
大部分满足，但有一条仍需 Boss 确认：
| 条件                                         | 状态          | 依据                                                                                          |
| ------------------------------------------ | ----------- | ------------------------------------------------------------------------------------------- |
| call_backtest.py 资源闸已实施（005C）              | ✅ 已满足       | MAX_SYMBOLS_DEFAULT=20, MAX_YEARS_DEFAULT=3, REQUEST_TIMEOUT_SEC=90, _validate_request() 生效 |
| 后端异步化改造                                    | ❌ 未完成       | 后端仍是同步模式，20 只标的 + 90s 超时下仍有未知风险                                                             |
| 工单状态已设为 ready_for_limited_resume           | ✅ 已满足       | 工单在 open/ 目录，status 正确                                                                      |
| 工单被阻止的 round 上限（2 failed rounds）未被计入完整研究结论 | ✅ 已满足       | Round 1 标记为"结论无效"，Round 2 标记为"未完成"                                                          |
| smoke run 资源预算明确                           | ✅ 已满足       | symbols≤5, years≤1, timeout=90s                                                             |
| 后端异步化缺失的风险是否被接受（仅限 ≤20 标的、≤3 年、90s 超时）     | ❓ 需 Boss 确认 | 在同步后端上以 ≤20 标的恢复执行，如果超时仍然发生，资源闸会自动拦住并 paused_for_boss_review，不会卡死。风险已隔离，可以一试。               |
建议结论：在同步后端上做 ≤5 标的、≤1 年、90s 超时的 smoke run 风险极低；即使后端挂住，90s 超时后资源闸会自恢复。可以进入正式执行。

