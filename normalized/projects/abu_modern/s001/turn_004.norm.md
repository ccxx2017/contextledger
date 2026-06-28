# turn_004.norm

来源文件：`raw/projects/abu_modern/s001/turn_004.md`

处理纪律：
- 只提取与 `strategy_research_agent.quant_assistant_relationship` 相关的最终裁定
- 保留“平行 Agent / 共享后端、不互相调用”的确认态语义
- 不把尚未确认的知识库暴露方式分支写入本轮 graph

## block_001_relationship_confirmed

- 裁定：`strategy-researcher` 与 `quant_assistant` 不重叠，二者是平行 Agent。
- 两个 Agent 共用同一个 Windows 后端 API，但不互相调用。
- `quant_assistant` 保持现状不变。
- `strategy-researcher` 应自行编排研究循环，并直接调用后端中的研究与回测相关接口。
