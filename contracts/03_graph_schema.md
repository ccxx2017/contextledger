# 图 Schema 与失效语义 [PROVISIONAL]
# 注意:invalidates/supersedes 语义尚在真实冲突上验证中,本文件可能调整。
# 在验证通过前,下游(04 装配)不得依赖本契约构建。

## 节点
  { id, type, content, entity_ref, state, status, source, created_turn }

  type   ∈ { UserGoal, Constraint, Fact, Decision, OpenTask, ToolResult, FileArtifact }
  status ∈ { active, superseded }          # 图生命周期:是否仍是当前真相(机械层裁定)
  state  ∈ { open, in_progress, blocked,   # 领域生命周期:实体在现实中的状态
             implemented, deployed,
             resolved, cancelled, unknown, null }
  entity_ref : 稳定实体标识(路径/工单/组件),无明确实体填 null
             命名规范见 entity_naming.md

## 按节点类型的 state 合法集
- `Decision` ∈ { `open`, `resolved`, `cancelled`, `unknown`, `null` }
- `Decision` 不得使用 `implemented` / `deployed`
- 理由：`Decision.state` 跟踪的是“决策点自身是否已裁定”，不是“该决策对应方案是否已实现”
- 例：
  - “是否采用方案 A，待拍板” → `open`
  - “已决定采用方案 A” → `resolved`
  - “该决策点作废/不再需要” → `cancelled`

  # status 与 state 是两个维度,不可混用:
  #   status = 这个节点在图里还算不算数(active/superseded)
  #   state  = 它描述的那个实体现在处于什么状态(open/deployed/...)
  #   当前态集合(current adjudicated belief state)的成员资格只允许由 status 决定。
  #   任何脚本/装配/查询若用 state 替代 status 计算"当前什么成立",均属违约。

## 边
  { from, to, relation, created_turn }
  relation ∈ { invalidates, supersedes, depends_on, relates }
  # invalidates : from 使 to 变为"假"(矛盾)
  # supersedes  : from 替代 to(to 历史上仍为真,但已陈旧/被取代);supersedes 蕴含 invalidates

## 失效裁定(待验证确认)
- 触发条件:新节点与某 active 旧节点 entity_ref 相同(且非 null)
- 比较二者 state,按下方【互斥矩阵】判定:
    - 矛盾(contradiction) → 加 invalidates 边,旧节点 status=superseded
    - 进阶(progression)   → 加 supersedes 边, 旧节点 status=superseded
    - 相同(identical)     → no-op,不动图
    - 正交(coexist)       → 不冲突,两节点均保持 active
- 装配只读取 status=active 的节点

## 当前态裁定纪律
- "当前什么成立"、"节点是否仍有效"、"must_include 候选集是否仍保留"——
  这些问题一律只看 `status`
- `state` 只用于同一 entity_ref 下的领域状态比较(如 open → resolved / blocked → deployed)
- 被 supersede 的节点必须表现为: `status=superseded`
- 一个节点即便 `priority=must_include`,只要 `status!=active`,也必须退出当前态集合

## state 互斥矩阵(按 node type)

### OpenTask —— 单状态实体:同一任务任一时刻只处于一个 state
  任意 state 改变 → supersedes(替代,旧状态历史为真)
  例外:
    open/in_progress/blocked  互相切换 → supersedes
    → resolved / → cancelled            → supersedes(终态)
    resolved/cancelled → 重新激活        → supersedes(reopen/复活,保留痕迹)
  说明:不为 OpenTask 设"并存"情形;blocked 视为独占状态而非 in_progress 的子态。
       "内容显示已完成但 state≠resolved" 属 lint 检查,不在此处。

### Constraint —— 在force/不在force,state 恒为 null
  同 entity_ref 出现新的 active 约束 → 旧约束 invalidates(旧约束不再成立=变假)
  例:"杠杆≤3x" 被 "杠杆≤5x" 取代 → 旧节点 invalidates + superseded

### Decision —— 决策点替换
  同 entity_ref 出现新决策 → supersedes(旧决策"曾被做出"但不再生效)
  例:"用 Kafka" → "改用 Redis Streams"
  合法 state 仅允许 `open/resolved/cancelled/unknown/null`；禁止把“方案已拍板”写成 `implemented/deployed`

### Fact —— state 描述其断言的实体;矛盾与进阶必须区分(评审重点)
  下表针对同一 entity_ref 的事实,old → new:

  | old \ new   | blocked      | implemented | deployed    |
  |-------------|--------------|-------------|-------------|
  | blocked     | identical    | supersedes  | invalidates |
  | implemented | invalidates  | identical   | supersedes  |
  | deployed    | invalidates  | invalidates | identical   |

  读法:
    blocked → deployed   = 矛盾(原先"阻塞=不可用",现已上线) → invalidates
    implemented → deployed = 进阶(已实现仍为真,被更强状态包含) → supersedes
    deployed → blocked   = 回退/故障(上线后又坏了)           → invalidates
  注:implemented vs deployed 是"先后/包含"关系,不是互斥;
     误把它判成 invalidates 会丢掉"已实现"这条仍然为真的事实。

### UserGoal / ToolResult / FileArtifact
  UserGoal:通常 entity_ref=null,目标变更走 supersedes;一般不参与机械强判定。
  ToolResult/FileArtifact:state 多为 null;同 entity_ref 新版本 → supersedes 旧版本。

## 手工期备注
- 本矩阵只覆盖当前真实会遇到的情形,遇到未覆盖的 state 对,当场补一行并记一次判定日志。
- "正交(coexist)"目前无明确实例;若出现两个 active 节点 entity_ref 相同却判为不冲突,
  必须在判定日志里写明理由——这通常是 entity_ref 用得过粗的信号。
