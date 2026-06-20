# 图 Schema 与失效语义 [PROVISIONAL]
# 注意:invalidates 语义尚在真实冲突上验证中,本文件可能调整。
# 在验证通过前,下游(04 装配)不得依赖本契约构建。

## 节点
  { id, type, content, status, source, created_turn }
  status ∈ { active, invalidated }

## 边
  { from, to, relation, created_turn }
  relation ∈ { invalidates, supersedes, relates }

## 失效语义(待验证确认)
- A --invalidates--> B : B.status 置为 invalidated
- supersedes 蕴含 invalidates,且 from 为替代者
- 装配只读取 status=active 的节点