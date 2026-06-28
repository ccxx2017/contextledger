# abu_modern · phase0_manual

这是 `abu_modern` 的白皮书 `Phase 0` 手工代行沙箱。

目的：
- 不覆盖现有 `graph/projects/abu_modern/graph_state.json`
- 以 `raw/projects/abu_modern/s001/turn_001.md` 为输入
- 手工跑通 `Normalized -> Patch -> Apply -> Lint`
- 额外给出一份手工 `ContextBundle` 形状样例，验证白皮书所说的 Assembler 输出形状

目录约定：
- `patches/`：手工 patch 产物
- `run/`：应用后的图状态快照
- `reports/`：lint 报告、执行报告、ContextBundle 样例

执行范围：
- 当前只执行冷启动第 1 轮
- 不覆盖项目主图
- 不把该沙箱结果视作正式生产图

对应输入：
- `raw/projects/abu_modern/s001/turn_001.md`
- `normalized/projects/abu_modern/s001/turn_001.norm.md`
- `normalized/projects/abu_modern/s001/turn_001.manifest.json`
