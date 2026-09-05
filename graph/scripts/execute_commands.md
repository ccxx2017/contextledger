# graph 侧常用命令速查

约定：以下全部命令在**仓库根目录**（`D:\CCXXLESSON\contextledger`）执行，
路径一律相对仓库根、使用正斜杠。流程语义以 `runbook/process_turn.md` 为准，
本文只提供可直接复制运行的命令形态。

## 00 一键单轮闭环（推荐入口）

```bash
# 完整执行：slice → prompt → extractor → reconcile → apply(candidate) → lint → 发布/隔离 → bundle
python graph/scripts/run_auto_turn.py abu_modern turn_085

# 试运行：只生成 scratch 产物，不提交主图
python graph/scripts/run_auto_turn.py abu_modern turn_085 --dry-run
```

前置：`env`（从 `env.example` 复制）已配置 Extractor LLM 的 API。

## 01 手工分步（对应 runbook STEP 1–7）

```bash
# STEP 1 构建切片（STATE 始终用完整图，不是切片）
python graph/scripts/build_graph_slice.py \
  --graph graph/projects/abu_modern/graph_state.json \
  --turn raw/projects/abu_modern/s001/turn_085.md \
  --out graph/projects/abu_modern/graph_slices/slice_085.json

# STEP 2 组装 Extractor prompt
python graph/scripts/build_extractor_prompt.py \
  --slice graph/projects/abu_modern/graph_slices/slice_085.json \
  --turn raw/projects/abu_modern/s001/turn_085.md \
  --mode api-json \
  --out graph/projects/abu_modern/reports/turn_085_auto/extractor_prompt.turn_085.md

# STEP 3 调用 Extractor（需要 env 中已配置 API）
python graph/scripts/invoke_extractor.py \
  --project-id abu_modern \
  --turn-id turn_085 \
  --slice graph/projects/abu_modern/graph_slices/slice_085.json \
  --turn raw/projects/abu_modern/s001/turn_085.md \
  --system graph/prompts/extractor_system.md \
  --out graph/projects/abu_modern/patches/patch_085.json

# STEP 4 patch 前置机械复核（P4：未过 reconcile 绝不允许 apply）
python graph/scripts/reconcile_patch.py \
  graph/projects/abu_modern/graph_state.json \
  graph/projects/abu_modern/patches/patch_085.json

# STEP 5 应用 patch（生成候选态；自动运行器中仅在 lint 全绿后才发布）
python graph/scripts/apply_patch.py \
  --graph graph/projects/abu_modern/graph_state.json \
  --patch graph/projects/abu_modern/patches/patch_085.json \
  --expected-turn turn_085 \
  --in-place --snapshot-dir graph/projects/abu_modern/run

# STEP 6 整图校验
python graph/scripts/graph_lint.py \
  graph/projects/abu_modern/graph_state.json \
  --expected-turn turn_085 \
  --newer-than graph/projects/abu_modern/patches/patch_085.json

# STEP 7 装配上下文 bundle
python graph/scripts/build_context_bundle.py \
  --project-id abu_modern \
  --turn-id turn_085 \
  --max-nodes 12 \
  --budget-profile phase1_prep_baseline
```

## 02 机械核重放与基线

```bash
# 重放 patch 链并与 run/ 快照逐字节比对（机械核确定性封存）
python graph/scripts/replay_phase0_seal.py --project-id abu_modern

# 生成状态 manifest（基线登记；--out 可另存副本）
python graph/scripts/generate_state_manifest.py

# 证据哈希校验
python graph/scripts/verify_canonical_evidence_hashes.py --policy canonical_lf_v1
```

## 03 评测

```bash
# 影子重放评测（split: development | regression | blind_holdout | adversarial）
# 注意：blind_holdout 为封存集，未经封存解锁流程不得执行
python graph/projects/abu_modern/shadow_replay/scripts/benchmark_shadow_runner.py --split development

# 生命周期 fixture 规格校验
python graph/scripts/validate_lifecycle_fixtures.py
```

## 04 可视化

```bash
python graph/scripts/to_mermaid.py \
  --graph graph/projects/abu_modern/graph_state.json \
  --out graph/projects/abu_modern/run/graph.mmd
```

## 05 失败隔离（一般由 run_auto_turn 自动触发，手工补救时使用）

```bash
python graph/scripts/quarantine_patch.py --help
```
