# raw 锚点契约 [STABLE]

## raw ID 格式
raw 是全系统唯一真源,物理上只存在于根 `raw/`。
每个原始对话片段有全局唯一 ID:

    <project>/<session>/<turn>

例: open_skywing_lab/20260618_2319/0042

- project: 被服务项目标识,与 pack/projects/<project> 同名
- session: 会话目录名(时间戳)
- turn:    四位轮次号,会话内单调递增

## 反向指针(谁引用 raw)
graph 节点与 pack 段落都不存 raw 正文,只存指针:

    source: {
      raw_id: "open_skywing_lab/20260618_2319/0042",
      span:   [起始字符偏移, 结束字符偏移]   # 可选,无则指向整轮
    }

## 约束
- 一个 raw_id 物理上只对应一个文件,不得复制到模块内部
- 指针是单向的:节点/段 -> raw。raw 自身不记录谁引用了它
- raw 文件一旦写入即只读(append-only),不得回改;
  修正通过新增 raw + 图中的 supersedes 边表达

反向指针经 normalized 抽取时,span 必须翻译回 raw 偏移