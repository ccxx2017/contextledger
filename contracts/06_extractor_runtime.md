# Extractor 调用契约 [PROVISIONAL]

本文件定义 Phase 1-prep 的 Extractor 调用约定。
目标是让 `build_graph_slice.py -> build_extractor_prompt.py -> Extractor -> patch.json`
形成可重复执行的主项目级闭环。

## 1. 模型与 endpoint

- 默认模型：`deepseek-v4-flash`
- 默认接口协议：OpenAI-compatible Chat Completions
- 默认 endpoint：
  - `https://api.deepseek.com/v1/chat/completions`
- 若宿主侧另有代理 / 网关，可通过 env 覆盖 endpoint

## 2. 环境变量

建议写入仓库根目录 `.env` / `env`，或 `graph/env`，也可直接注入宿主进程环境：

- `EXTRACTOR_API_KEY`
- `EXTRACTOR_BASE_URL`
- `EXTRACTOR_MODEL`
- `EXTRACTOR_TIMEOUT_SECONDS`

默认值：
- `EXTRACTOR_MODEL=deepseek-v4-flash`
- `EXTRACTOR_BASE_URL=https://api.deepseek.com/v1/chat/completions`
- `EXTRACTOR_TIMEOUT_SECONDS=120`

硬要求：
- `EXTRACTOR_API_KEY` 不能为空

## 3. 调用脚本

Phase 1-prep 参考实现脚本：
- `graph/scripts/invoke_extractor.py`

职责：
1. 读取 `extractor_context_pack.json`
2. 读取本轮 `turn_xxx.md`
3. 组装 system + user 消息
4. 调用 Extractor 模型
5. 解析模型输出中的 Graph Patch JSON
6. 将 `patch.json`、原始响应、prompt 快照落盘到项目目录

## 4. 输入与输出

输入：
- `--project-id`
- `--turn-id`
- `--slice`
- `--turn`
- `--env-file`（可选；缺省时自动按 `env -> graph/env` 顺序查找）

默认输出路径约定：
- `patch.json`
  - `graph/projects/<project_id>/patches/patch_<turn_id_numeric>.json`
- 原始响应：
  - `graph/projects/<project_id>/reports/extractor_raw_response.<turn_id>.txt`
- prompt 快照：
  - `graph/projects/<project_id>/reports/extractor_prompt.<turn_id>.json`

说明：
- `turn_id_numeric` 指不带 `turn_` 前缀的三位数字形式，例如 `turn_004 -> patch_004.json`
- prompt 快照允许用于审计，但不得替代 raw 与 patch 作为事实源

## 5. 命令示例

```powershell
python graph/scripts/invoke_extractor.py `
  --project-id abu_modern `
  --turn-id turn_004 `
  --slice graph/projects/abu_modern/graph_slices/slice_004.json `
  --turn raw/projects/abu_modern/s001/turn_004.md `
  --env-file graph/env
```

## 6. 输出约束

- 模型返回内容必须可被解析为单个 Graph Patch JSON
- 若返回 Markdown code fence，调用脚本负责剥离 fence 后再解析
- 若解析失败，脚本必须返回非零退出码，并保留原始响应文本
- 调用脚本不得手改 patch 语义，只做：
  - JSON 解析
  - 可选的顶层结构检查
  - 落盘
