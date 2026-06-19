## 01 生成Graph Slice
首次
python scripts/build_graph_slice.py --graph graph_state.seed.json --turn original_dialogs/turn_001.md --out graph_slices/slice_001.json
从第二轮开始：
python scripts/build_graph_slice.py --graph graph_state.json --turn original_dialogs/turn_xxx.md --out graph_slices/slice_xxx.json

## 02 组合成Extractor LLM的Context
python scripts/build_extractor_prompt.py --slice graph_slices/slice_001.json --turn original_dialogs/turn_001.md --mode api-json --out prompts/turn_prompts/prompt_001.md

## 03 纯机械的 patch 前置校验器
首次
python scripts\reconcile_patch.py graph_state.seed.json patches/patch_001.json
从第二轮开始：
python scripts\reconcile_patch.py graph_state.json patches/patch_002.json

04
首轮
python scripts\apply_patch.py --graph graph_state.seed.json --patch patches\patch_001.json --out graph_state.json --snapshot-dir run
从第二轮开始
python scripts\apply_patch.py --graph graph_state.json --patch patches\patch_001.json --out graph_state.json --snapshot-dir run

05
python scripts\graph_lint.py graph_state.json

[06]
python scripts\to_mermaid.py --graph graph_state.json --out run/graph.turn_001.mmd 