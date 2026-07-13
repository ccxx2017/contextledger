# Phase 0.5 v3 Resolver Candidate Priority

本报告用于给 batch-resolve 收敛提供优先级清单（仅针对 benchmark 覆盖到的 tracked 项）。

## 优先级规则

- `P0`：match_confidence >= 0.90
- `P1`：0.80 <= match_confidence < 0.90
- `P2`：0.70 <= match_confidence < 0.80
- `P3`：其余

## 候选清单

| priority | raw_entity_ref | canonical_entity_ref | match_confidence | remediation_status |
|---|---|---|---:|---|
| P0 | openclaw_skills/strategy-researcher/scripts/call_builder.py | openclaw_skills/strategy-researcher/scripts/call_backtest.py | 0.9076 | tracked |
| P1 | openclaw_skills/quant_assistant/TOOLS.md | openclaw_skills/quant-assistant | 0.8451 | tracked |
| P1 | openclaw_skills/strategy-researcher/scripts/call_backtest.py | openclaw_skills/strategy-researcher/scripts | 0.8350 | tracked |
| P2 | TKT-2026-005B_round5 | TKT-2026-005B | 0.7879 | tracked |
| P2 | TKT-2026-005B_round5.2_reconciliation | TKT-2026-005B_round5 | 0.7812 | tracked |
| P2 | openclaw_skills/strategy-researcher/prompts/research_workflow.md | openclaw_skills/strategy-researcher/SKILL.md | 0.7778 | tracked |
| P2 | run-e92b485b-20250101-20251230-820b8995 | run-54b-20250101-20251230-d37c696d | 0.7123 | tracked |
| P3 | openclaw_workspace/AGENTS.md | openclaw_workspace_structure | 0.6786 | tracked |
| P3 | openclaw_workspace/IDENTITY.md | openclaw_workspace_structure | 0.6552 | tracked |

## 重点建议

- 先处理 `P0/P1`：这些项最可能直接改变 resolver 的有效实体映射。
- 当前仍需优先人工裁决的候选：`openclaw_skills/strategy-researcher/scripts/call_builder.py`、`openclaw_skills/quant_assistant/TOOLS.md`、`openclaw_skills/strategy-researcher/scripts/call_backtest.py`。
