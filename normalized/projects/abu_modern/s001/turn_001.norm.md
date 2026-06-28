# turn_001.norm

来源文件：`raw/projects/abu_modern/s001/turn_001.md`

处理纪律：
- 只做无损降噪，不做失效判断
- 保留路线图、阶段任务、立即动作
- 删除寒暄、重复强调和修辞性延展

## block_001_goal

- 总目标：回归主线，AOS 反哺。
- 核心含义：让 AOS 的下一个 employee 直接服务于量化主线，而不是继续服务于 AOS 自己。

## block_002_phase0

- 阶段 0：先维稳 `duty_reporter`。
- 可选增加后台 LLM 摘要节点，用于验证 LLM 基础设施。
- 暂不启动 Wiki Agent、指挥舱 UI、第二个 employee。

## block_003_phase1

- 阶段 1：复活 `Strategy Research Agent`，作为 AOS 的第一个领域 employee。
- 目标：恢复量化主线，持续产出可信策略档案。
- 已知攻坚点：LLM 解析稳定性、假设多样性、失败兜底。

## block_004_phase2

- 阶段 2：根据阶段 1 的产物决定下一个 employee。
- 候选：Wiki Agent、Triage Agent、Quant Reviewer Agent、指挥舱 UI。

## block_005_phase3

- 阶段 3：在有 2-3 个稳定 employee 后，再做指挥舱 MVP。

## block_006_decision3_pending

- 决策 3 待确认：阶段 1 的 `Strategy Research Agent` 实现方式尚未确定。
- 候选实现方式：
  - `AOS-native`
  - `quant-native`
- 当前轮只提出待确认问题，不形成最终裁定。

## block_006_actions

- 立即动作 1：整理 `ROADMAP_v2.md`，落盘到 `aos/projects/abu_modern/`。
- 立即动作 2：开立 `TKT-2026-XXX` 工单，启动 `Strategy Research Agent` 阶段 1 调研。
- 立即动作 3：在 `aos/runtime/` 创建 `_frozen_ideas.md`，冻结非主线想法。
