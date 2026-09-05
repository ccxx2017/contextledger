# RUNBOOK · baseline_replay (工作包 A 基线冻结与重放)

# 目的: 为后续变更登记可信比较起点。任何触及 reconcile/apply/assembler/
#       resolver/lifecycle 的改动，合并前必须在基线 commit 上重跑本命令并对比。

## 一键命令（仓库根目录执行）

```bash
python graph/scripts/replay_and_eval.py
```

产物：
- `reports/baseline_A/state_manifest.json` — 状态 manifest（HEAD、patch 链、契约版本、图统计）
- `reports/baseline_A/baseline_summary.json` — 基线汇总（步骤结果、基准分数、shadow gate、致命项）
- `reports/baseline_A/lint_delta_vs_baseline.json` — 当前图 vs lint 基线的存量对照
- `reports/quarantine_register_check.json` — 隔离登记簿检查结论

## 通过条件

1. 退出码 0，`baseline_status: FROZEN`；
2. 连续两次运行，除时间戳/run_id 外指标块完全一致（机械核确定性）；
3. `benchmark_metrics` 与冻结值可复现（v3: P=0.6087 / R=0.7368 / Set-F1=0.8980 / must=1.0，TP=14/FP=9/FN=5）；
4. `external_unreproducible` 区块中的叙事数字（0.550/0.579/0.856、20.8% 隔离率）只作历史引用，
   禁止再当作可比较基线。

## 已知非阻断项

- shadow 三个 split（development/regression/adversarial）gate 为 BLOCK——这是 stage04c123
  封存的已知状态（20 个已归因回归），如实带入基线，由 B/C 的改动来消除，不在 A 包处理。

## 封存纪律

- `replay_and_eval.py` 永不运行 blind_holdout（代码级拒绝）；
- 如确要消耗封存集，只能显式运行
  `benchmark_shadow_runner.py --split blind_holdout --i-understand-this-consumes-blind-holdout`，
  消耗行为登记进 `reports/blind_holdout_consumption.json`，该集即告失效。

## 冻结点约定

- 包含基线产物的那个 commit 即冻结点；
- 在冻结点 commit 上重跑本命令，指标块应逐字节复现 `baseline_summary.json`；
- 后续工作包（B/C）的重放差异都必须对照冻结点解释。

## 变更历史

- 2026-09-05 工作包 A 初次冻结：
  - 修复 phase0_manual 封存证据缺失（f8c11bc 误删，从 git 历史恢复）；
  - `replay_phase0_seal.py --reseed`：apply_patch 节点结构演进（created_turn）后以当前工具链
    重建 canonical 快照，seed 与 patch 链未动；
  - 主图 5 处存量 lint 违例 + 1 警告按 [L2] 纪律登记进 lint_baseline（修复期限 turn_090）；
  - D1/D2 decoder 身份漂移以 implementation_ref 修正（freeze v1 → v1.1，PATCH）。
