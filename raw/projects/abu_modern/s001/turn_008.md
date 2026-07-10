# 用户(执行了上面的1-9项)：
@Claude-Opus-4.7 我已经执行了上面的1-9项，至于补丁 A 里，SKILL.md 的 Phase 0 pull 失败处理问题暂时不用分，现在，现在是否还缺少strategy-researcher相关脚本文件呢
# Claude-Opus4.7:

## 还缺 3 个脚本，但现在不是写它们的时候

## 一、缺什么

按你之前贴的 quant_assistant 三脚本风格（urllib + JSON stdout + 标准 error 语义），strategy-researcher 最终需要 **3 个脚本**：

| # | 脚本 | 作用 | 对应后端 |
|---|------|------|---------|
| 1 | `call_builder.py` | 把 intent 转成策略 IR | `POST /strategy-builder/invoke` |
| 2 | `call_backtest.py` | 对 IR 跑回测拿 BacktestResult | `POST /backtests/execution-config` |
| 3 | `kb_query.py` | 读知识库（子命令：`index` / `list` / `read <id>` / `log`） | `GET /api/v1/knowledge/*` ×4 |

**注意不需要** `kb_write.py`——因为 TKT-2026-003 的决议是"写侧自动 hook 在 builder/backtest 成功路径里"，Agent 永远不直接写知识库。这也是为什么我之前把脚本数从 5 个砍到 3 个。

## 二、为什么现在不该写

脚本 #1 和 #2 可以照抄 quant_assistant 的结构立刻写完（后端 API 已存在）。但脚本 #3 的 4 个 GET 端点**此刻还不存在**——TKT-2026-003 完成后才会有。现在写 `kb_query.py` 等于对着 spec 编码、无法联调，而且一旦 TKT-2026-003 实施时字段微调（比如 `list_strategy_archives` 的每项多/少一个字段），脚本就得返工。

**更糟的问题**：三个脚本里有两个能立刻写、一个不能，会诱导你只写能写的那两个、留 `kb_query.py` 悬着——然后 Agent 无法真正启动，因为研究循环的第一步就是 `read_index()`。

## 三、建议动作：补立 TKT-2026-004

TKT-2026-003 的 frontmatter 已经写了 `blocks: [TKT-2026-004]`，那张工单就该是这个。建议你批准后我起草如下骨架（不展开全文，只列 meta 让你先拍）：

```yaml
id: TKT-2026-004
title: strategy-researcher 脚本实现（3 个 HTTP 封装）
status: open
priority: high
assigned_to: boss    # 初期你手动兜底
blocked_by: [TKT-2026-003]
blocks: []
tags: [agent, strategy-researcher, openclaw-skill]
```

交付物就是上面三个 .py，验收标准是：Ubuntu 端命令行能直接跑通 `python call_builder.py '{"intent":"..."}'` 并拿到合法 IR、`python kb_query.py list` 能拿到 `[]` 或档案数组。

## 四、当前阻塞链的状态图

```
TKT-2026-002 (Charter)          ✅ closed
        │
TKT-2026-003 (Backend API)      🔴 open ← 现在卡在这
        │
TKT-2026-004 (Scripts)          ⚪ 待建
        │
TKT-2026-005 (首个研究任务)     ⚪ 未来的第一张"业务工单"
```

## 最后一个决定

要我**现在起草 TKT-2026-004 的完整工单文件**吗？还是你打算先埋头把 TKT-2026-003 后端 API 敲出来、完工之后再一起处理 004？

——**"先起草 004" / "先做 003"**，回一个我就进下一步。

