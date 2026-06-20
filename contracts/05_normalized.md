# normalized 派生契约 [PROVISIONAL]

## 定义
normalized = f(raw),纯函数派生物。
可随时删除,由 raw 重新生成。不持有 raw 里没有的信息。

## 铁律
1. 只做无损/可逆降噪(去寒暄、去重复、结构化),
   不得注入新信息、不得下判断。判断归 graph 或 pack。
2. 必须带可重放 manifest,记录:
   源 raw_id 列表、压缩 prompt 版本、模型、时间。
   不能重放的产物即偷偷固化的真源,禁止。
3. span 映射:抽取时 normalized 偏移必须翻译回 raw 偏移
   (见 01),反向指针一律落到 raw,normalized 对下游透明。

## manifest 存放
与产物贴身,每个 normalized 叶子目录里
"内容 + *.manifest.json" 成对存在,不抽成平级目录。