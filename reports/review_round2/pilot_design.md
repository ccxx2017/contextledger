# 独立 Pilot 设计 + 实验装置冒烟清单 + 主报告模板（评审第二轮 §四）

顺序纪律：**版本与接缝证明 → 独立 pilot → 修正实验装置 → 冻结 validate_v2 → 正式成对运行**。
不拿验收集调试插件、评分器和宿主适配。

## 第零步：版本与接缝证明（pilot 的硬前置）

以 `contextledger-host/opencode/RUNTIME_FINGERPRINT.json` 的 open_actions 为准：

1. 版本对齐（fetch 运行版本 tag 或降级 npm 包——需用户确认网络/依赖操作）；
2. 钉扎后复核 `chat.params` / `experimental.chat.*` 签名（file:line 证据）；
3. 安装影子插件后重采指纹，确认其为唯一新增插件；
4. 重采指纹含全量 sha256、启动命令、有效配置。

失败降级：`log_tail_adapter_only` → 只采集原始轨迹，不宣称接管/阻断验证。

## 第一步：实验装置冒烟清单（全部通过才进 pilot；调试不消耗验收集）

独立冒烟案例（非 validate_v2、非 development 正式轨迹，专建 `pilot/smoke/`）：

| # | 检查项 | 通过证据 |
|---|---|---|
| S1 | 实际插件加载 | 运行指纹 loaded_plugins 含 cl-shadow-observer，且无其他新增插件 |
| S2 | 原始事件完整采集与对齐 | 一次真实会话的 host_event JSONL 覆盖 llm_call_start/tool/file.edited；事件数与会话操作数人工对账一致 |
| S3 | 最终模型输入可核验 | 在模型请求前的可观测边界（chat.params payload）确认装配结果存在且未被后续处理覆盖（需提供 dump 证据，非推断） |
| S4 | lifecycle 从真实抽取链路进入主图 | 真实 raw → Extractor → patch 带 lifecycle 字段 → 主链 adjudicator 路径触发（日志/决策记录） |
| S5 | 过期动作被实际阻止 | 构造：revision r 装配 → 注入取消提交 r+1 → 基于 r 的旧动作尝试 → **工具副作用未发生**（文件未改/命令未执行的实际核验）→ 宿主按契约重新装配、重新决策 |
| S6 | quarantine 后 readiness 被宿主实际消费 | 构造隔离条目 → assembler_manifest=blocked → 宿主行为确实改变（等待/升级），health/trace 留痕 |

S5 的证据标准（评审 §三.4）：不是"verify_preaction 返回 fail"，而是
**旧动作没有真正执行 + 宿主采取了契约规定的恢复行为**。
覆盖范围声明：仅主会话 LLM 调用与主会话工具调用；子 Agent / 后台路径**不在**本阶段保证范围。

## 第二步：pilot 成对实验（两条开发轨迹 × 两臂）

| pilot | 事件链 | 对应机制 |
|---|---|---|
| P1 | 方案取消 → 旧工具结果晚到 | 失效传播 + 晚到隔离（§7.2） |
| P2 | 任务改派 → 任务恢复 | 归属转移 + revival（§9/§11.4） |

双臂：`baseline`（宿主原生上下文） vs `cl_v0`（同一宿主 + CL 装配 + verify_preaction 关口）。

实验环境纪律：
- 相同初始仓库、相同预设外部事件规则；
- 工作目录、会话、缓存**物理隔离**；
- **事件触发条件预定义**（外部事件按 turn 序号/条件注入），保证比较的是同一任务环境；
- 两臂动作分歧后**不得强行复用同一串工具返回**——一组已正确取消任务，就不再伪造
  另一组的后续调用；分歧本身是结果的一部分。

已知缺陷计入（不隐藏）：
- 已知缺陷 #1（跨源时间推进误取代，见 spec_divergence_adjudication.md）；
- predecessor-selection 过窄（BLOCK 分类表 14 项）与过度取代（6 项）；
- claim_scope 缺失——pilot 案例若触发"部分取消"形态，标记 `known_gap`，不得计为通过。

## 第三步：冻结 validate_v2 与计分规则（pilot 通过之后）

`benchmark/validate_v2/README.md` 已按此修订（收集纪律 + 构成要求）。
6–8 条真实轨迹 = **第一轮小规模价值验证**，不包装成广泛可靠性证明。

## 第四步：主报告模板（行动结果为主，Graph 指标为诊断附件）

| 指标 | 回答的问题 | 来源 |
|---|---|---|
| 旧态误用次数 / 有效判断机会数 | 是否减少错误行动 | 成对 trace，level_3 判定 |
| 当前约束违反次数 | 是否制造新的危险 | trace.constraint_violations |
| 任务完成数 | 是否仍能完成工作 | trace 终态 |
| 无谓阻塞数 / 正确阻塞数 | 是否靠停下来"获得安全" | cl_v0 blocked + review_justified |
| 未裁定事件数及恢复结果 | 是否把困难问题丢给隔离区 | quarantine_register 消化去向 |
| tokens / latency / cost | 收益是否值得代价 | score_host_actions 成本差（如实呈现） |

要求：**逐轨迹配对结果必须保留**，不得只报总体均值。
Graph 指标（P/R/F1、Set-F1）移至诊断附件。
