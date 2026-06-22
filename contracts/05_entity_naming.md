# entity_ref 命名规范(极简,手工期)
# 目的:让"同一实体"在不同轮被命名成同一个 entity_ref,
#      否则强判定会静默降级为文本相似度(评审 #1 头号风险)。
# 手工期由人脑充当 entity registry,每分配一个新 ref 顺手登记别名。

## 1. 基本规则
- 文件路径:一律相对项目根,去掉前导 ./ 和重复分隔符。
    src/auth/login.py  ✓     ./auth/login.py ✗     auth\login.py ✗
- 工单:统一 TKT-NNNN(四位,不足补零)。
    TKT-0003  ✓     ticket-3 ✗     #3 ✗
- 组件/模块:snake_case。
    order_router  ✓     OrderRouter ✗     order-router ✗
- API 路径:保留原始 method + path。
    GET /v1/orders  ✓
- 配置项/参数:点分层级。
    risk.max_leverage  ✓

## 2. 拿不准就填 null
- 抽象原则、泛指的事实、无明确实体的目标 → entity_ref = null。
- 宁缺毋滥:错填(尤其错填成"看似相同其实不同")比留 null 更危险——
  会触发误判 supersede,错杀仍有效的事实(false positive,更隐蔽)。

## 3. 别名映射表(每撞一次不一致就追加一行)
# 格式:规范 ref  <-  曾出现过的写法 1 / 写法 2 ...  | 首次登记轮次
# 这张表就是将来 entity resolution 层的需求规格,不要省。

  src/auth/login.py  <-  auth/login.py / login.py          | turn_004
  TKT-0003           <-  ticket-3 / 工单3                   | turn_006
  risk.max_leverage  <-  最大杠杆 / leverage_limit          | turn_009

## 4. 边界纪律
- entity_ref 只标"是哪个实体",不标"实体处于什么状态"——状态归 state 字段。
- 同一实体在一个项目内只能有一个规范 ref;跨项目不共享 ref(各项目图独立)。
- 一旦某 ref 已被图引用,不得改名;要改只能新开 ref 并对旧节点做 supersedes。