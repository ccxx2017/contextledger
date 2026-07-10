# 用户：
附件是根目录下的TOOLS.md
# Claude Opus4.7:
*Thinking...*

>  I need to provide them with the exact TOOLS.md file content formatted for the skill directory at `~/.openclaw/workspace/skills/quant_assistant/TOOLS.md`, and remind them that the root TOOLS.md should be replaced with the routing layer I outlined earlier.
> 
> The file is already well-structured as skill-private with the appropriate header and context notes, so I'll keep it essentially as-is with just a single clarifying line about its location and activation scope. Then I'll move on to the next step of replacing the root file.

好。你附件里的根 `TOOLS.md` 内容**本身就是按 skill 私有文件的格式写的**（开头自己就写了"这份文件只放当前环境特定的信息，配合 SKILL.md 使用"），所以不需要重写，只需要在最顶部加一行定位说明，其余一字不动。

## 步骤 1：新建 `~/.openclaw/workspace/skills/quant_assistant/TOOLS.md`

直接粘贴以下全文：

```markdown
# TOOLS.md

## quant_assistant 本地环境信息

> 本文件位置：`skills/quant_assistant/TOOLS.md`
> 作用域：**仅在 `quant_assistant` 技能被激活时生效**。
> 非本技能会话不应读取或引用本文件中的后端地址、脚本路径、命令模板与错误码。

这份文件只放当前环境特定的信息，配合 `SKILL.md` 使用。

## 技能目录

Ubuntu 侧实际技能目录：

```bash
~/.openclaw/workspace/skills/quant_assistant
```

脚本目录：

```bash
~/.openclaw/workspace/skills/quant_assistant/scripts
```

## 后端地址

Windows 端量化平台后端地址：

```bash
http://192.168.1.136:8000/api/v1
```

建议通过环境变量配置：

```bash
export QI_BACKEND_URL="http://192.168.1.136:8000/api/v1"
export QI_STRATEGY_BUILDER_LLM_MODE="real"
```

## 鉴权信息

订单执行脚本依赖以下环境变量之一：
- `QI_AGENT_AUTH_KEY`
- `OPENCLAW_AGENT_AUTH_KEY`
- `AGENT_ACCESS_KEY`

示例：

```bash
export QI_AGENT_AUTH_KEY="<你的 X-Agent-Auth 密钥>"
```

## 脚本与用途对照

- `scripts/query.py`
  - 只读查询：实例、账户、持仓、订单、回测结果、行情、dashboard、health、risk
  - 重要：不负责"提交回测"，只能查询已有 run_id 的结果/报告
- `scripts/strategy_builder.py`
  - 策略构建与多轮续聊（需要时可直出strategy_ir/execution_config）
- `scripts/strategy_deploy.py`
  - 策略部署：候选参数拉取、自动补齐、预检、发布
- `scripts/order_execute.py`
  - 高风险交易执行

## 推荐调用前缀

```bash
cd ~/.openclaw/workspace/skills/quant_assistant
```

## 常用命令模板

### 查询实例

```bash
python3 scripts/query.py instances
```

### 策略构建

```bash
python3 scripts/strategy_builder.py \
  --message "我主要做趋势。前面有趋势，经过一轮调整，结构紧凑，然后在放量突破时进去。" \
  --session-id "sb_real_case_001"
```

### 策略部署

```bash
python3 scripts/strategy_deploy.py \
  --strategy-id "50242a5c263e4ec8951515c677d4b768" \
  --strategy-name "AI部署验证-额度修复" \
  --environment SIMULATION \
  --run-mode REPLAY \
  --run-id "run-50242a5c-20240319-20260319-7b9f0f1e" \
  --account-id "84c3b56f-e80f-40fd-b2cb-9a9566c01781" \
  --initial-cash 200000
```

### 订单执行

```bash
python3 scripts/order_execute.py \
  --account-id "paper-acc-001" \
  --symbol "000001.SZ" \
  --side BUY \
  --qty 100 \
  --order-type MKT \
  --confirm
```

## 使用规则

- 每次查询都应实时执行脚本，不要复述旧结果
- 用户提到实例名称但没有 ID 时，先查 `query.py instances`
- 用户要"做策略/改策略"时，不要停留在闲聊，优先进入 `strategy_builder.py`
- 用户要"回测"时：必须走 `strategy_builder.py --auto-backtest` 或直接调用 `/backtests/execution-config`，不要猜测不存在的接口（如 /backtest/run、/backtest/submit、/strategy/backtest 等）
- 用户要"部署到模拟盘/实盘"时，优先进入 `strategy_deploy.py`，但仅限用户明确提出"部署/实盘/模拟盘/自动运行"
- 用户要"买入/卖出/下单"时，必须先确认，再调用 `order_execute.py`
- 回测任务禁止查询交易账户/持仓/实例状态：这些属于部署与交易环节，不属于回测
- 现有平台已经具备后端能力时，不要建议改走 Backtrader、Zipline 或另搭独立框架
- 重要：工具调用失败时不要"穷举试错"多个 API 路径；应停止并把错误码/错误信息原样返回给用户，等待下一步指令

## 常见错误语义

- `backend_unreachable`
  - Windows 后端不可达，优先检查后端是否启动、IP 是否可访问、端口是否正确
- `http_error`
  - 后端已收到请求，但业务校验失败或接口返回错误
- `strategy_semantics_mismatch`
  - 对话层理解正确，但生成结果仍像固定模板，优先检查是否误用了 `mock` 模式
- `confirmation_required`
  - 高风险交易命令缺少确认
- `insufficient_quota`
  - 部署账户额度不足，需要更换账户或降低 `initial-cash`
```

**与原文的唯一差异**：顶部新增了三行定位说明（作用域声明），正文所有技术内容一字未改。

## 步骤 2：替换根目录 `~/.openclaw/workspace/TOOLS.md`

把根目录原来的 TOOLS.md **整个替换**为我上一轮给你的"路由层 TOOLS.md"文本（技能地图 + 技能分诊 + 全局约束 + 迁出说明那一份）。如果需要我再贴一次告诉我。

## 步骤 3：安全检查（动手前 10 秒确认）

为防止误操作后无法回滚，执行前先确认备份：

```bash
# 1. 确认根 TOOLS.md 当前确实存在（非空）
ls -la ~/.openclaw/workspace/TOOLS.md

# 2. 在工作区外备份一份原文
cp ~/.openclaw/workspace/TOOLS.md ~/tools_md_root_backup_$(date +%Y%m%d).md

# 3. 再新建 skill 私有文件 + 替换根文件
```

备份那步不要省。万一烟测出问题要回滚，有原文可以立刻还原。

## 完成后

两个文件都就位后，直接告诉我"P0 完成"，我们进烟测 A/B。烟测失败不要自己改 prompt，先把失败的 trace（或飞书里它的回复 + 后台调用日志）贴回来，我们一起判因。

