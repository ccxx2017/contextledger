# contracts/

graph 与 pack 之间的单一契约真源。
任何跨模块的格式、引用、归属约定，正文只写在这里；
`graph/` 和 `pack/` 的代码与文档只引用本目录，不重述。

状态标记：
- `[STABLE]` 已验证，改动需同步双侧
- `[PROVISIONAL]` 随机制验证可能调整
- `[PLACEHOLDER]` 尚未启用，仅占位

## 当前文件索引

| 文件 | 内容 | 状态 |
|------|------|------|
| `01_raw_anchors.md` | raw ID 与反向指针（脊柱）格式 | STABLE |
| `02_ownership.md` | 任一知识正文的唯一归属 | STABLE |
| `03_graph_schema.md` | 图节点/边/失效语义 | PROVISIONAL |
| `04_assembly.md` | Phase 1 Assembler v1 装配契约 | PROVISIONAL |
| `05_entity_naming.md` | entity_ref 命名规范与最小 resolver / pending_merge 约定 | PROVISIONAL |
| `06_extractor_runtime.md` | Extractor 调用 contract、env、输入输出与落盘约定 | PROVISIONAL |
| `07_turn_runtime.md` | turn checkpoint、retry、目录约定、[L1]/[L2] 责任归属判定 | PROVISIONAL |

## 说明

- `05_normalized.md` 当前仓库中并不存在；若后续恢复该契约，应以真实文件落盘后再登记。
- `04_assembly.md` 已从单纯占位升级为 Phase 1-prep 可执行契约。
- `05_entity_naming.md` 仍保留“命名规范”为主轴，但已补入最小 resolver 接口与 `pending_merge/` 格式，供 Phase 1-prep 使用。
