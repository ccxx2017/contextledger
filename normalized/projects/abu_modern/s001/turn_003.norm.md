# turn_003.norm

来源文件：`raw/projects/abu_modern/s001/turn_003.md`

处理纪律：
- 只做无损降噪，不做失效判断
- 保留对 OpenClaw 目录布局、领域知识目录位置、agent 关系裁定的关键信息
- 删除解释性延展和重复论证，保留可直接写入 graph 的稳定内容

## block_001_skill_layout

- 在 OpenClaw 框架下，`strategy-researcher` 的 skill 目录应放在 `openclaw_skills/strategy-researcher/`。
- 该目录应与现有 `duty-reporter`、`quant_assistant` 采用同构布局：`SKILL.md + TOOLS.md + scripts/`。
- 不应再把 `SKILL.md` 放到代码仓中与业务代码同居。

## block_002_knowledge_location

- `data/knowledge/` 不要移动，当前位置已经正确。
- 它属于领域知识层，不属于组织契约层或架构文档层。
- `strategy-researcher` 的策略入库路径应为 `data/knowledge/strategies/`。
- 写入时应遵守 `data/knowledge/schema.md` 的现有格式约束。

## block_003_quant_relationship_pending

- `strategy-researcher` 与 `quant_assistant` 的关系仍需最终裁定。
- 当前推荐方向是关系 A：`quant_assistant` 作为工具底座，由 `strategy-researcher` 调用。
- 该判断尚未最终定案，仍需结合 `quant_assistant` 的实际成熟度与使用情况确认。
