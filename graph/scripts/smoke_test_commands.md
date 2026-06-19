01
python scripts/build_graph_slice.py --graph tests/smoke/taskgraph_contract/graph_state.seed.json --turn original_dialogs/turn_001.md --out tests/smoke/taskgraph_contract/slice_001.json
02
python scripts/build_extractor_prompt.py --slice tests/smoke/taskgraph_contract/slice_001.json --turn original_dialogs/turn_001.md --mode api-json --out tests/smoke/taskgraph_contract/prompt_001.md

03
python scripts\reconcile_patch.py `
>>   tests\smoke\taskgraph_contract\graph_state.seed.json `
>>   tests\smoke\taskgraph_contract\patch_001.smoke.json


04
python scripts\apply_patch.py --graph graph_state.json --patch patches\patch_005.json --out graph_se.json --snapshot-dir run

05
python scripts\graph_lint.py tests\smoke\taskgraph_contract\graph_state.after_001.json

