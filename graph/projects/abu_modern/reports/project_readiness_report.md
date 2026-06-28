# project_readiness_report

## 基本信息

- project_id: `abu_modern`
- turn_id: `turn_004`（推定值：当前 `graph_state.json` 的 `turn_counter=3`，因此下一个待处理 turn 应为 `turn_004`；但 `raw` 目录中已存在到 `turn_006`，仍需人工确认本轮到底处理哪一个 turn）
- 当前判断: `BLOCKED`
- 检查时间: `2026-06-28`

## 结论

当前仓库已经具备 graph 单轮闭环的大部分机械脚本与项目目录，但还不满足 runbook 要求的最小可启动条件。

主要阻塞不在脚本是否存在，而在以下三类关键前提仍未被明确：

1. `Extractor` 的调用方式未配置，无法进入 STEP 3。
2. `reconcile fail` 的最大重试次数 `N` 未在 contract 中定义。
3. `graph_lint` 后如何区分 `[L1] 本轮引入` 与 `[L2] 存量问题` 没有落地机制或脚本说明。

因此当前状态应判定为 `BLOCKED`，不应继续执行 `build_graph_slice`、Extractor 调用或 patch 生成。

## 已确认存在的文件与脚本

### 输入状态文件

- `graph/graph_state.seed.json`
- `graph/projects/abu_modern/graph_state.json`
- `graph/projects/abu_modern/run/graph_state.turn_001.json`
- `graph/projects/abu_modern/run/graph_state.turn_002.json`
- `graph/projects/abu_modern/run/graph_state.turn_003.json`

结论：
- 首轮输入 `seed state` 存在。
- 非首轮输入 `graph_state.json` 存在，且可读。

### raw 文件

- `raw/projects/abu_modern/s001/turn_001.md`
- `raw/projects/abu_modern/s001/turn_002.md`
- `raw/projects/abu_modern/s001/turn_003.md`
- `raw/projects/abu_modern/s001/turn_004.md`
- `raw/projects/abu_modern/s001/turn_005.md`
- `raw/projects/abu_modern/s001/turn_006.md`

结论：
- raw 文件存在且目录结构清晰。
- 但当前正式进入哪一轮仍需确认。

### 图切片脚本

- `graph/scripts/build_graph_slice.py`

已确认：
- 输入：`--graph` + `--turn`
- 输出：`--out` 指定文件；默认输出到 `graph_slices/slice_XXX.json`
- 输出中包含 `_runtime.next_node_id`

### prompt 组装脚本

- `graph/scripts/build_extractor_prompt.py`
- `graph/prompts/extractor_system.md`
- `graph/prompts/turn_prompts/`

已确认：
- 输入：`--slice` + `--turn`
- 输出：system + user 消息，支持 `single/split/user-only/api-json`
- 会主动剥离 `retrieval_trace`，不进入 Extractor prompt

### patch 复核脚本

- `graph/scripts/reconcile_patch.py`

已确认：
- 输入：`graph_state.json` 或 `seed state` + `patch.json`
- 输出：JSON 报告，包含 `ok/errors/warnings`
- 有错误时默认返回非零退出码

### apply patch 机制

- `graph/scripts/apply_patch.py`

已确认：
- 输入：`--graph` + `--patch`
- 输出：新的 `graph_state.json` 或指定 `--out`
- 支持 `--snapshot-dir` 写入 turn 快照
- 代码层面明确要求先有 patch 文件，再进行 apply

### 整图校验脚本

- `graph/scripts/graph_lint.py`

已确认：
- 输入：新的 `graph_state.json`
- 输出：JSON 报告，包含 `ok/errors/warnings`
- 有错误时默认返回非零退出码

### 失败隔离机制

- `graph/scripts/quarantine_patch.py`
- `graph/projects/abu_modern/quarantine/`

已确认：
- 失败 patch 可复制到隔离区
- 可保存失败阶段、错误报告、最大重试次数等元信息

### 已做的只读机械检查

- 本机 `Python 3.9.13` 可用
- 以下关键脚本已通过 `py_compile` 语法检查：
  - `build_graph_slice.py`
  - `build_extractor_prompt.py`
  - `reconcile_patch.py`
  - `apply_patch.py`
  - `graph_lint.py`

## 缺失文件清单

以下关键文件或配置未找到：

1. Extractor 调用配置文件
   - 未找到明确声明模型、endpoint、命令、环境变量的配置文件
   - `graph/env` 存在但为空

2. Extractor 调用封装脚本
   - 未找到负责“读取 prompt 产物并调用 LLM，再落盘 `patch.json`”的脚本或命令说明

## 不明确的 contract 清单

1. `turn_id` 选择规则不明确
   - `graph_state.json` 的 `turn_counter=3`
   - raw 中已有 `turn_004` 到 `turn_006`
   - runbook 需要明确本轮 `turn_id`，当前只能推定下一个应为 `turn_004`

2. `reconcile fail` 最大重试次数 `N` 未定义
   - runbook 要求 `N` 来自 contract
   - 仓库内未找到正式 contract
   - 历史文档中只出现经验表述 `N=2~3`
   - `quarantine_patch.py` 自带 `--max-retries` 默认值 `3`，但这只是脚本参数，不等同于 contract

3. patch 输出目录约定不明确
   - 历史命令文档使用 `patches/patch_XXX.json`
   - 但当前 `graph/projects/abu_modern/` 下没有明确的 `patches/` 目录与项目级约定说明

4. prompt 落盘约定不明确
   - `graph/prompts/turn_prompts/` 存在
   - 但没有看到面向 `abu_modern` 项目的项目级 prompt 产物落盘约定

5. lint `[L1]/[L2]` 归属判定机制不明确
   - `graph_lint.py` 只检查单份图状态
   - 当前未发现“应用前后对比”脚本或契约说明，无法机械区分“本轮引入”与“存量问题”

6. contract 目录索引与实际文件不一致
   - `contracts/README.md` 中列出 `05_normalized.md` 与 `06_entity_naming.md`
   - 但当前目录实际文件并不完全对应
   - 说明 contract 清单本身仍有不一致

## 需要 Boss / 评审员确认的问题

1. 本轮正式要处理的 `turn_id` 是什么？
   - 建议默认从 `turn_004` 开始，因为当前 `graph_state.json` 只推进到第 3 轮

2. STEP 3 的 Extractor 由谁调用？
   - 是人工在网页端调用、CLI 调用，还是应新增脚本负责调用？

3. Extractor 使用哪个模型与 endpoint？
   - 需要明确命令、环境变量名、密钥来源、输出文件路径

4. `reconcile` 最大重试次数 `N` 取多少？
   - 请将其写入 contract 或明确指定为项目执行常量

5. patch / prompt / lint report 的项目级落盘目录是什么？
   - 建议在 `graph/projects/abu_modern/` 下显式固定

6. lint 失败时 `[L1]/[L2]` 如何机械判定？
   - 是新增脚本对比应用前后图，还是由评审员人工判定并记录？

## 如果 BLOCKED，阻塞在哪一步

- 阻塞 STEP 3：缺少可执行的 Extractor 调用配置
- 阻塞 STEP 4 的重试回路：缺少 contract 化的最大重试次数 `N`
- 阻塞 STEP 6 的责任归属分流：缺少 `[L1]/[L2]` 机械判定机制

## 补充判断

- 就“脚本存在性”和“基础目录存在性”而言，仓库已经接近可运行。
- 就 runbook 要求的“可复现、可交接、可裁决”标准而言，当前还不能判为 `READY`。
- 在上述三类阻塞项被确认前，不建议进入正式 turn 流程。
