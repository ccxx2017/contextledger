# abu_modern / patches

本目录用于存放主项目正式 turn 运行产出的 `patch.json`。

命名约定：
- `patch_004.json`
- `patch_005.json`

纪律：
- 只追加，不覆盖历史 patch
- `graph_state.json` 必须可由本目录中的 patch 序列确定性重放得到
