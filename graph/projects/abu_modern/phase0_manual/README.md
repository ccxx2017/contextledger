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

资产分层：
- 正式长期资产：
  - `patches/`：Phase 0 的手工 patch 样例，可用于回看 cold-start 的最小输入形状
  - `run/`：手工应用后的图状态快照，可用于对照早期图状态形状
  - `reports/`：Phase 0 的 lint 报告、执行报告与 ContextBundle 样例，保留为早期验证记录
- 可重生成但建议保留的快照：
  - `run/graph_state.json`
  - `reports/turn_001_execution_report.md`
  - `reports/turn_001_context_bundle.md`
  - 这些文件理论上可以通过同样的手工流程再生成，但建议保留为 Phase 0 冷启动快照
- 不建议删除：
  - 整个 `phase0_manual/` 目录不是临时目录，而是 `Phase 0` 的方法验证与形状留档

相关脚本：
- `graph/scripts/apply_patch.py`：将 patch 应用到图状态快照
- `graph/scripts/graph_lint.py`：对图状态执行 lint 校验
- `graph/scripts/build_context_bundle.py`：生成 ContextBundle，用于验证 Assembler 输出形状

`reports/` 文件说明：
- `turn_001_lint.txt`：该轮图状态的 lint 输出
- `turn_001_execution_report.md`：该轮手工执行说明与核对结果
- `turn_001_context_bundle.md`：手工 ContextBundle 样例，用于验证输出形状
- 后续若新增轮次，沿用相同命名规则补充

执行范围：
- 当前只执行冷启动第 1 轮
- 不覆盖项目主图
- 不把该沙箱结果视作正式生产图

对应输入：
- `raw/projects/abu_modern/s001/turn_001.md`
- `normalized/projects/abu_modern/s001/turn_001.norm.md`
- `normalized/projects/abu_modern/s001/turn_001.manifest.json`
