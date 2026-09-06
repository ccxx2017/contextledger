# 20 项 BLOCK 放行分类（评审第二轮 §三.2）

依据评审分类表逐项裁定。数据源：最新一次 regression split 运行
（`runs/stage04b/regression/stage04b_20260906T015951_regression`，6 案例，20 regressions，
0 blockers，0 unexplained，submission_coverage=1.0）。

## 逐案构成

| 案例 | 回归数 | 具体形态 | 方向 |
|---|---|---|---|
| `tr_full_tkt_006` | 6 | "Unexpected supersedes"：oracle 把 gold 判定应保留的 claim 取代了 | **过度失效**（假阳性） |
| `tr_revival_round5x` | 14 | "gold_relation=SUPERSEDES / shadow_relation=UNRELATED"：gold 判定应失效的 claim 仍 active（active_set_f1=0.3333） | **漏失效**（假阴性） |

## 分类裁定（按评审五类）

| 评审类别 | 本轮 20 项归属 | 裁定 |
|---|---|---|
| gold、评分器或事件对齐错误（正式验收前必须修复） | **0 项** | 比较器工作正常：20 项 diff 均被正确检出并归类（blocking=false 的 relation 级回归），gold 来自冻结文件（逐文件 sha256），事件对齐无缺采（submission_coverage=1.0、unexplained=0）。测量系统本身未发现失真 |
| 插件没加载、事件漏采、最终输入不可确认（正式验收前必须修复） | **0 项**（离线评测不涉及宿主；该项约束作用于 pilot 的冒烟清单，见 pilot_design.md） | — |
| **CL 的真实语义错误（保留，必须计入结果）** | **20 项全部** | 两个真实缺陷，均已定位到决策表级： ① `tr_revival_round5x` 的 **predecessor-selection 收窄过矫正**——stage04c 修复 fan-out 后只选"直接前驱"，同键更早的应失效 claim 不再被取代（RFC §16.1 对该轨迹的验收目标 TP=4/4 明确未达成）；② `tr_full_tkt_006` 的**过度取代**——同槽位推进取代了 gold 认为应并存的 claim。二者方向相反，共同根源是"取代范围"缺少与 gold 对齐的规则 |
| readiness 正确阻塞任务（计入阻塞与完成率，不算成功） | 本轮 0 项（离线评测无 readiness 参与）；该项约束作用于成对运行的 needless_block/正确阻塞计数 | — |
| 明确超出支持范围（事先声明，单列） | 0 项新增。既有单列项：claim_scope（见 spec_divergence_adjudication.md 影响面节）；缺 effective_at 硬隔离（deliberate 偏离，规则已细化） | — |

## 结论

- 20/20 属"**真实语义错误**"类：**保留、计入结果、不作为放行障碍**——它们正是
  lifecycle 改进要消减的对象，也是成对运行的基线事实。
- 测量系统（gold/比较器/对齐）经裁定无失真 → **实验可解释性成立**，
  满足评审"不要求清零，但不得破坏可解释性"的要求。
- 修复归属：两个语义缺陷的消减属于 B 线后续轮次（predecessor-selection 范围规则），
  在 pilot 之前**不做**——pilot 用现有实现测真实收益，缺陷计入结果。
