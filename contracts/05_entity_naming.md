# entity_ref 命名规范与最小 resolver 契约 [PROVISIONAL]

目的：
- 让“同一实体”在不同轮被命名成同一个 `entity_ref`
- 为 Phase 1-prep 的最小 `Entity Resolver` 与 `pending_merge/` 回路提供可执行格式

## 1. 基本命名规则

- 文件路径：一律相对项目根，去掉前导 `./` 和重复分隔符
  - `src/auth/login.py` ✓
  - `./auth/login.py` ✗
  - `auth\login.py` ✗
- 工单：统一 `TKT-YYYY-NNN`
  - `TKT-2026-002` ✓
  - `ticket-2` ✗
  - `#2` ✗
- 组件 / 模块：`snake_case`
  - `order_router` ✓
  - `OrderRouter` ✗
  - `order-router` ✗
- API 路径：保留原始 method + path
  - `GET /v1/orders` ✓
- 配置项 / 参数：点分层级
  - `risk.max_leverage` ✓

## 2. 拿不准就填 null

- 抽象原则、泛指的事实、无明确实体的目标 → `entity_ref = null`
- 宁缺毋滥：错填成“看似相同其实不同”比留空更危险，因为会触发误判 supersede，错杀仍有效事实

## 3. 别名映射表

格式：
- `规范 ref <- 曾出现过的写法 1 / 写法 2 ... | 首次登记轮次`

这张表既是人工登记表，也是最小 resolver 的静态别名源。

```text
src/auth/login.py  <-  auth/login.py / login.py          | turn_004
TKT-2026-003       <-  ticket-3 / 工单3                  | turn_006
risk.max_leverage  <-  最大杠杆 / leverage_limit         | turn_009
```

## 4. 最小 Entity Resolver 接口

Phase 1-prep 的最小 resolver 可以保守，但每个新节点必须输出以下字段：
- `match_confidence`
- `merge_reason`
- `non_merge_reason`
- `candidate_aliases`

允许的最小行为：
- 精确命中已存在 `entity_ref`：可直接判为已解析
- 命中别名映射表：可规范化到 canonical ref
- 只出现弱候选：不得自动合并，必须落 `pending_merge/`
- 无明确候选：保持原值或 `null`，并写出 `non_merge_reason`

## 5. pending_merge 文件格式

目录：
- `graph/projects/<project_id>/pending_merge/`

文件名建议：
- `pending_merge.<turn_id>.json`

最小结构：

```json
{
  "project_id": "abu_modern",
  "turn_id": "turn_004",
  "generated_by": "graph/scripts/entity_resolver.py",
  "items": [
    {
      "new_node_id": "n_0041",
      "raw_entity_ref": "ticket-2",
      "candidate_aliases": [
        {
          "canonical_entity_ref": "TKT-2026-002",
          "match_confidence": 0.61,
          "evidence": ["token_overlap"]
        }
      ],
      "match_confidence": 0.61,
      "merge_reason": "",
      "non_merge_reason": "needs_manual_merge_review"
    }
  ]
}
```

## 6. 边界纪律

- `entity_ref` 只标“是哪个实体”，不标“实体处于什么状态”；状态归 `state`
- 同一实体在一个项目内只能有一个 canonical ref；跨项目不共享
- 一旦某 ref 已被图引用，不直接改名；如需切换规范名，应通过 resolver 规范化新写入，并保留别名登记
