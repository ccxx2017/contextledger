# contracts/

graph 与 pack 之间的单一契约真源。
任何跨模块的格式、引用、归属约定,正文只写在这里;
graph/ 和 pack/ 的代码与文档只引用本目录,不重述。

状态标记:
- [STABLE]   已验证,改动需同步双侧
- [PROVISIONAL] 随机制验证可能调整
- [PLACEHOLDER] 尚未启用,仅占位

| 文件 | 内容 | 状态 |
|------|------|------|
| 01_raw_anchors.md | raw ID 与反向指针(脊柱)格式 | STABLE |
| 02_ownership.md   | 任一知识正文的唯一归属 | STABLE |
| 03_graph_schema.md| 图节点/边/失效语义 | PROVISIONAL |
| 04_assembly.md    | 下游装配消费契约 | PLACEHOLDER |
|05_normalized.md | normalized 派生契约 | PROVISIONAL