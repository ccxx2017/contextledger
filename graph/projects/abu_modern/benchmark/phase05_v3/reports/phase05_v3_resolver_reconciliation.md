# Phase 0.5 v3 Resolver Reconciliation

本报告用于验证 benchmark harness 中的内联 resolver 是否与 `pending_merge_register` 的真实决策一致。

## 总览

- benchmark mentions 数量：`31`
- 覆盖到的 pending_merge 项数：`25`
- 已 resolved 项数：`16`
- 仍 tracked 项数：`9`
- 对账 mismatch 数量：`0`

## 对账结论

- 对账通过：所有已 resolved 的 pending_merge 决策都被内联 resolver 正确复现。

## 已 Resolved 决策

| raw_entity_ref | canonical_entity_ref | resolution | resolution_note |
|---|---|---|---|
| TKT-2026-005B_round5.1_audit | TKT-2026-005B_round5 | merged_into:n_0138 | Batch LIKELY_MERGE: confidence=0.8333, canonical=TKT-2026-005B_round5 |
| TKT-2026-005B_round5.3A_audit | TKT-2026-005B_round5 | merged_into:n_0146 | Benchmark MERGE: round5 lifecycle 单流推进，3A_audit 直接落回 round5 主链 |
| TKT-2026-005B_round5.3B_fix | TKT-2026-005B_round5 | merged_into:n_0146 | Benchmark MERGE: round5 lifecycle 单流推进，3B_fix 直接落回 round5 主链 |
| TKT-2026-005B_round5.3C_fix | TKT-2026-005B_round5.3B_fix | merged_into:n_0150 | Benchmark MERGE: round5 lifecycle 单流推进，3C_fix 归并到 fix 主链 |
| TKT-2026-005B_round5.3C_reverify | TKT-2026-005B_round5.3C_verify | merged_into:n_0151 | Batch MERGE: confidence=0.9677, canonical=TKT-2026-005B_round5.3C_verify |
| TKT-2026-005B_round5.3C_verify | TKT-2026-005B_round5 | merged_into:n_0146 | Benchmark MERGE: round5 lifecycle 单流推进，3C_verify 直接落回 round5 主链 |
| TKT-2026-005B_round5.3D_reconcile | TKT-2026-005B_round5.3B_fix | merged_into:n_0150 | Benchmark MERGE: round5 lifecycle 单流推进，3D_reconcile 继续沿 fix / reconcile 主链推进 |
| TKT-2026-005B_round5_result | TKT-2026-005B_round5 | merged_into:n_0138 | Batch MERGE: confidence=0.8511, canonical=TKT-2026-005B_round5 |
| TKT-2026-005C | TKT-2026-005 | kept_distinct | Benchmark KEEP_DISTINCT: TKT-2026-005C/D/E 属于同家族并行补丁工单，gold 期望 coexist 而非互相替换 |
| TKT-2026-005D | TKT-2026-005 | kept_distinct | Benchmark KEEP_DISTINCT: TKT-2026-005C/D/E 属于同家族并行补丁工单，gold 期望 coexist 而非互相替换 |
| TKT-2026-005E | TKT-2026-005 | kept_distinct | Benchmark KEEP_DISTINCT: TKT-2026-005C/D/E 属于同家族并行补丁工单，gold 期望 coexist 而非互相替换 |
| TKT-2026-005I-kb-minimum-sanity-check.md | TKT-2026-005B | kept_distinct | Batch KEEP_DISTINCT: confidence=0.4906 too low, treating as separate entity |
| identity_smoke_c | openclaw_identity_mechanism | kept_distinct | Batch KEEP_DISTINCT: confidence=0.5116 too low, treating as separate entity |
| run-54b-20250101-20251230-d37c696d | run-54b-20250101-20251230-dfc9611d | merged_into:n_0176 | Batch MERGE: confidence=0.9118, canonical=run-54b-20250101-20251230-dfc9611d |
| tkt_2026_005b_recovery_patch | TKT-2026-005B | kept_distinct | Batch KEEP_DISTINCT: confidence=0.5366 too low, treating as separate entity |
| ~/.openclaw/openclaw.json | openclaw_identity_mechanism | kept_distinct | Batch KEEP_DISTINCT: confidence=0.5000 too low, treating as separate entity |

## 仍 Tracked 的候选项

这些项在真实图里尚未形成最终 batch 决策，因此本次 harness 不强行 merge，只保留原实体键。

| raw_entity_ref | canonical_entity_ref | match_confidence | remediation_status |
|---|---|---:|---|
| TKT-2026-005B_round5 | TKT-2026-005B | 0.7879 | tracked |
| TKT-2026-005B_round5.2_reconciliation | TKT-2026-005B_round5 | 0.7812 | tracked |
| openclaw_skills/quant_assistant/TOOLS.md | openclaw_skills/quant-assistant | 0.8451 | tracked |
| openclaw_skills/strategy-researcher/prompts/research_workflow.md | openclaw_skills/strategy-researcher/SKILL.md | 0.7778 | tracked |
| openclaw_skills/strategy-researcher/scripts/call_backtest.py | openclaw_skills/strategy-researcher/scripts | 0.8350 | tracked |
| openclaw_skills/strategy-researcher/scripts/call_builder.py | openclaw_skills/strategy-researcher/scripts/call_backtest.py | 0.9076 | tracked |
| openclaw_workspace/AGENTS.md | openclaw_workspace_structure | 0.6786 | tracked |
| openclaw_workspace/IDENTITY.md | openclaw_workspace_structure | 0.6552 | tracked |
| run-e92b485b-20250101-20251230-820b8995 | run-54b-20250101-20251230-d37c696d | 0.7123 | tracked |
