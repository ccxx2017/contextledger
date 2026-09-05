# 冒烟测试命令

约定：在**仓库根目录**执行；路径相对仓库根、正斜杠。
冒烟夹具已预置于 `graph/tests/smoke/taskgraph_contract/`
（`slice_001.json`、`prompt_001.md` 由夹具数据生成，不依赖已移除的 `original_dialogs/`）。

## 01 reconcile（应用前机械复核）

```bash
python graph/scripts/reconcile_patch.py \
  graph/tests/smoke/taskgraph_contract/graph_state.seed.json \
  graph/tests/smoke/taskgraph_contract/patch_001.smoke.json
```

## 02 apply（应用 patch 生成候选态）

```bash
python graph/scripts/apply_patch.py \
  --graph graph/tests/smoke/taskgraph_contract/graph_state.seed.json \
  --patch graph/tests/smoke/taskgraph_contract/patch_001.smoke.json \
  --out graph/tests/smoke/taskgraph_contract/graph_state.after_001.json
```

## 03 lint（整图校验）

```bash
python graph/scripts/graph_lint.py \
  graph/tests/smoke/taskgraph_contract/graph_state.after_001.json
```

## 04 运行时守卫单元测试

```bash
python -m unittest discover -s graph/tests -v
```
