# 用户：
请根据工单 TKT-2026-005B-vcp-breakout-entry.md 做正式执行前检查。
不要调用 scripts。
请自行判断并读取正式执行前必须加载的 skill、workflow、prompt 文件。
最后列出：
1. 你实际读取了哪些 .md 文件；
2. 哪个文件是最高行为手册；
3. 正式执行时必须遵循哪些 Phase；
4. 是否已经满足正式执行条件。

# feishu agent:
正式执行前检查报告

1. 实际读取了哪些 .md 文件

#
文件
路径
原因
1
工单
aos/runtime/tickets/blocked/TKT-2026-005B-vcp-breakout-entry.md
必须读取以确认任务内容、约束、研究目标、Worklog 历史
2
SKILL.md
skills/strategy_researcher/SKILL.md
身份绑定 + 读写边界 + 失败处理矩阵 + 资源闸约束声明
3
research_workflow.md（主 playbook）
skills/strategy_researcher/prompts/research_workflow.md
每个 investigation 工单开始必读
4
TOOLS.md
skills/strategy_researcher/TOOLS.md
脚本契约、命令行参数、后端地址、错误码
5
hypothesis_heuristics.md
skills/strategy_researcher/prompts/hypothesis_heuristics.md
§3.1 每轮提出假设前必读
6
report_template.md
skills/strategy_researcher/prompts/report_template.md
Phase 4 交付写作规范

（另外读取了 research-runs/TKT-2026-005B/ 下的现存产出文件用于校验状态。）
2. 最高行为手册
prompts/research_workflow.md（TOOLS.md 明确声明："主 playbook；每个 investigation 工单开始必读"）。

SKILL.md 也指定："本 SKILL.md 不再内嵌流程伪代码……行动手册见 prompts/research_workflow.md"。
3. 正式执行时必须遵循的 Phase
按 research_workflow.md §2，标准路径 Phase 0 / 1 / 6 不得省略：

Phase
内容
对本工单的特殊性
Phase 0
cd /home/ccxx/aos_repo && git pull --rebase
环境同步
Phase 1
检查 intent_type == investigation ✅、assigned_to == agent-strategy-researcher ✅
已验明
Phase 2
读 KB（archives → log → index）
已有 Phase 2 记录，但仍应 re-read 以获最新基线
Phase 3
研究循环（上限 5 轮），每轮：提出假设→builder→保存→分析
工单已有 Round 1（0 trades）和失败的 Round 2，恢复时从 Round 3 开始
Phase 4
产出报告（metrics.py → report_template）
需等研究完成
Phase 5
工单 Worklog append
append-only
Phase 6
git add → commit → push
终态提交

此外，2026-05-19 工单终止记录中写的恢复条件决定了正式执行时的额外约束：
资源闸（§3）：调用 call_backtest.py 前必须先检查 §3.1 的 3 项限值
§3.3 大 universe 准入流程：universe > 5 只标的时，必须先 smoke 验证
Builder 轮次限制（§3.2）：禁止 ≥3 轮 builder 对话，新 builder session（不是原 corrupted 的 session）
4. 是否已经满足正式执行条件
不满足。 以下三条阻断条件中，只有部分已解决：

阻断条件
状态
说明
① TKT-2026-005C 脚本侧硬限制
✅ 已实施
call_backtest.py 已加上 MAX_SYMBOLS_DEFAULT=20、MAX_YEARS_DEFAULT=3、REQUEST_TIMEOUT_SEC=90、_validate_request()、AOS_BOSS_OVERRIDE 授权机制
② 后端异步化改造
❌ 未完成
192.168.1.136:8000 的 backtest endpoint 仍然是同步的。231 标的回测仍然会阻塞请求线程。虽然有脚本侧 20 标的限值先拦住大 universe，但 20 只标的的回测在同步模式下仍有超时风险
③ 工单状态
❌ 已暂停
005B 工单当前 status: paused_for_boss_review，置于 blocked/ 目录。按 research_workflow.md §3.6，暂停恢复需要 Boss 显式确认
结论：即使第①条件已就位，第②条件（后端异步化）和工单状态本身（paused）仍阻止正式执行。需要 Boss 先做两个决定：
是否接受在同步后端上仅用 ≤20 标的、≤3 年、90s 超时的受限模式恢复 005B 研究？
是否显式将 005B 从 blocked 移回 open 并更新 status 为 ready_for_resume？

