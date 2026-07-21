# 用户：给出标题+简介的课程大纲
@Claude-Fable-5 请你重新给出标题+简介的课程大纲
# Claude-Fable-5：看得见的AI：从会说话的大模型到会行动的智能体
*Thinking...*

> I need to restructure the course outline based on the feedback, reorganizing the 10 cycles and 30 lessons around four new thematic pillars: AI systems and automation, data and models, generative AI and information evaluation, and task delegation with structured messaging.
> 
> The remaining cycles cover action and recovery, context and memory, skills and automation, system collaboration, safety and fairness, and human-centered AI design. I'll need to revise the lesson titles and descriptions to incorporate the terminology fixes—like clarifying what rule systems versus model systems excel at, how humans design sensors and data representation, and using "系统证据面板" instead of the transparency panel framing. I should maintain the space station narrative and three-lesson structure while keeping descriptions concise and copy-paste ready in Chinese. 11课 covers structured messaging with JSON as an example for precise component communication. 第12课 introduces tools as AI's interface to act, including tool lists and permission constraints. Then I'm mapping out cycles 5 through 8: action execution and feedback loops, context and external memory with privacy considerations, reusable skills and automation decisions, and finally system architecture with multiple components and responsibility distribution.
> 
> Now I'm working through cycle 9 on safety and fairness. I need to restructure the lessons to cover safety validators and permission tiers, comprehensive testing across normal/boundary/adversarial/fairness scenarios, and the invisible influence of AI systems like recommendation algorithms on daily life. I'm also considering where to integrate an "AI family map" showing different AI types—maybe folding that into an early lesson—and how to properly position recommendation systems and fairness within the curriculum.
> 
> For cycle 10, I'm outlining a human-centered design approach where students first question whether a problem actually needs AI, then build and test a minimal viable agent with different instruction types, and finally present their work with a system card documenting what the agent does, shouldn't do, oversight mechanisms, and appeal processes. I'm also renaming the transparency panel to "system evidence panel" throughout. For the course title, I'm considering repositioning it to emphasize the agent-centered learning thread and the idea of building, questioning, and protecting AI systems—something like "看得见的AI：搭建、质疑并守护你的智能体"—while keeping the format as a structured outline with cycle headings and lesson descriptions in prose.

## 《看得见的AI：从会说话的大模型到会行动的智能体》

**课程定位：以智能体为主线的青少年AI素养与系统设计课程**（10个学习闭环 / 30节课 / 每节60分钟）

---

### 第一闭环：AI系统、自动化与感知

#### 第1课：空间站里来了一个AI助手

学生进入Godot智能体实验室，向AI发出"帮我找到氧气瓶"等任务并预测结果，通过首次失败发现AI会说话却不知道游戏世界正在发生什么。课程同时给出"AI家族地图"，用定时器、自动门、推荐系统、人脸识别、聊天模型等案例分类，理解自动化、算法与AI有联系但不能画等号。

#### 第2课：AI为什么看不见我们看见的东西

打开系统证据面板，比较"人类看到的画面"与"AI实际获得的数据"。通过关闭位置、物品和危险区域数据，理解环境中存在信息不代表AI已经感知到信息，而AI能感知什么是由人设计决定的。

#### 第3课：给AI安装第一双眼睛

学生逐步开启坐标、物品和危险传感器，重新执行任务并比较前后结果。同时讨论传感器边界问题：眼睛该不该看到私人区域？最后将"传感器决定AI获得什么信息"迁移到扫地机器人、自动驾驶和校园巡检机器人。

---

### 第二闭环：数据、规则、模型与训练

#### 第4课：规则系统和模型系统各擅长什么

用离线规则系统和在线语言模型在5～10个任务条件下完成对照实验，比较成功率、稳定性和新任务适应能力。本课引入贯穿全程的"AI实验记录卡"：一次运行不能证明结论，对照实验要控制变量、记录条件、比较成功率。

#### 第5课：人怎样把世界变成AI能处理的数据

将人物、物品、房间和危险表示成名称、类型、坐标和状态。学生通过面板观察世界状态，理解采集什么、不采集什么、怎样分类和贴标签都由人决定，数据表示本身就可能带有选择和偏见。

#### 第6课：训练一个太空矿石分类器

通过极简分类器完成"样本→特征与标签→训练→模型→预测新样本→发现错误"的最小链条。学生给分类器喂两套不均衡数据，观察它对某类矿石识别更差，初步理解偏见来源；同时区分"模型训练出的能力"与"保存在外部的记忆"是两回事。

---

### 第三闭环：生成式AI与信息判断

#### 第7课：语言模型为什么能接着说下去

通过文字预测游戏和空间站对话实验，理解语言模型根据数据模式和上下文生成可能的后续内容，而不具有人的意图和经验。学生认识"语言通顺"与"事实正确"不是一回事。

#### 第8课：AI为什么会自信地说错话

向AI提出信息不足、无法感知和超出工具能力的问题，观察猜测、幻觉与编造。学生修改提示和系统规则，让AI在无法确定时说明依据、请求补充信息或诚实回答"不知道"，并理解提示词改进不能彻底消除错误。

#### 第9课：接受、修改、核验还是拒绝

建立面对AI输出的固定处理框架：每个输出必须被判定为接受、修改、核验或拒绝之一。学生练习追查信息来源、交叉验证、检查引用是否真实存在，并讨论AI生成的图像和语音等合成内容为什么需要标识。

---

### 第四闭环：任务委派、结构化消息与工具

#### 第10课：什么任务应该交给AI

围绕"把能源模块送到控制室"，学生先判断这个任务是否适合委派给AI、成功标准是什么、AI缺少哪些信息和权限，再把任务分解为观察、定位、移动、拾取、返回和交付，理解目标、计划与动作的区别。

#### 第11课：结构化消息——让组件准确沟通

学生比较自然语言说明与结构化动作的差异，把行动计划改写为包含动作名称、目标和参数的结构化消息（以JSON为例），理解系统组件必须遵守共同的通信协议，而JSON只是常见格式之一。

#### 第12课：工具是AI的手

逐步为AI开放观察、移动、拾取、交付等工具。学生修改工具列表并重复任务，验证AI能执行什么不只取决于它是否理解任务，还取决于系统提供了什么工具和权限，初步体会"最小权限"原则。

---

### 第五闭环：行动、反馈与异常恢复

#### 第13课：AI的身体怎样执行决定

观察AI角色移动、绕障和拾取物品。通过改变目标位置与地图障碍，认识路径规划、动作执行、目标不可达和执行结果反馈，并按实验记录卡多次运行、比较结果。

#### 第14课：AI为什么需要一边行动一边观察

在AI行动途中移动物品、封闭道路或增加危险区域。学生预测原计划能否继续成功，并通过系统证据面板发现：只在任务开始时感知一次，不能应对不断变化的环境。

#### 第15课：失败、撤销与求助

学生为AI加入执行反馈和重新感知机制，处理目标消失、路径堵塞和工具失败。除重新规划外，还要回答：这个动作能撤销吗？执行到一半怎样停下并进入安全状态？连续失败几次后应该请求人类帮助？

---

### 第六闭环：上下文、外部记忆与隐私

#### 第16课：没有记忆的AI会发生什么

学生连续告诉AI玩家偏好、基地位置和任务历史，重启后发现全部丢失。通过对照实验区分四类"记忆"：当前输入、对话上下文、外部长期记忆和模型参数中的训练结果——它们经常被混为一谈。

#### 第17课：AI应该记住什么，谁说了算

学生把记忆分为偏好、事实和任务历史，并为每条记忆标注内容、来源、保存原因、有效期限、谁能读取和如何删除。课程讨论哪些信息值得保存、哪些不应收集，以及保存前是否需要知情同意。

#### 第18课：记住、修改与忘记

学生故意写入错误或过期记忆，观察AI因此产生的错误行为，再修改、删除并重新验证。最后迁移到聊天助手、推荐系统和校园AI中的隐私、知情同意与删除权问题。

---

### 第七闭环：技能、自动化与创造

#### 第19课：重复的任务能不能存下来

让AI多次完成寻找和搬运任务，比较每次临时规划与调用固定流程的差异。学生明确：这里的"技能"是被保存并复用的工作流程，模型本身并没有被重新训练——"存住了流程"不等于"学会了本领"。

#### 第20课：一个技能由什么组成

学生拆解"安全搬运氧气瓶"技能，确定其目标、工具、步骤、前置条件、完成标准与失败处理，并通过修改技能参数观察技能定义怎样改变AI行为。

#### 第21课：这个任务应该被自动化吗

学生设计并测试一个新技能，用正常、缺物品、堵路和工具失效等条件验证。随后讨论：这个任务适合自动化吗？自动化后谁受益、谁失去控制、哪一步必须保留人工判断？使用AI辅助完成的成果，人的贡献和模型的贡献怎样区分和说明？

---

### 第八闭环：系统组件怎样协作与担责

#### 第22课：一个AI需要承担所有工作吗

将智能体拆分为观察员、规划员、安全员、执行员和记忆管理员。学生判断哪些组件是AI模型，哪些是传感器、规则程序、数据库或执行器，避免把所有自动化组件都称为AI。

#### 第23课：组建空间站智能体小队

学生分别承担观察、规划、审批和执行角色，通过消息协作完成任务（1对4分角色，1对1轮换，教师或规则系统补足其余角色），体会职责边界和信息传递为什么必须清晰。

#### 第24课：出错以后，责任落在哪里

教师故意制造感知遗漏、协议错误、审批拒绝和执行失败。学生通过组件日志定位故障环节，填写"事件—提出者—审批者—执行者—证据—责任人"的责任追踪表，理解复杂系统的责任要靠角色、权限、日志和审计落实，而不是一句"AI负责"。

---

### 第九闭环：安全、公平与社会影响

#### 第25课：能理解不代表应该执行

学生向AI提出越界移动、大量拿取物品和修改整个空间站等任务，预测是否应被执行。随后建立工具白名单、参数范围和权限校验，把动作划分为直接执行、限制执行、需要确认和永久禁止四级，理解安全不能只靠模型"自觉"。

#### 第26课：四种测试——正常、边界、对抗与公平

学生系统地测试自己的安全规则：正常测试看能否完成任务，边界测试看参数临界情况，对抗测试模拟用户绕过规则，公平测试检查系统对不同用户和场景是否表现一致。所有危险指令保持在封闭沙盒中。

#### 第27课：屏幕背后的AI与真实世界

从空间站回到日常生活：推荐和排序算法怎样影响我们看到什么、相信什么？AI运行需要芯片、数据中心、电力和水，它不是无形魔法。学生讨论AI出错时用户、开发者和管理者各自的责任，理解"看不见的AI"可能比会行动的智能体影响更大。

---

### 第十闭环：以人为本的AI系统设计

#### 第28课：这个问题真的需要AI吗

学生从校园、家庭、图书馆或环境保护中选择一个问题，先画利益相关者图：谁是使用者？谁不用它但会受影响？不用AI是否更简单？确认必要性后，再画出感知、决策、工具、记忆、安全与反馈组成的系统图。

#### 第29课：建立并测试最小智能体

学生利用实验室中的传感器、工具、技能和规则配置一个最小可用智能体，先完成一个核心任务，再用正常、模糊、错误和危险四类指令测试，按实验记录卡保存成功与失败证据。

#### 第30课：展示、答辩与系统说明卡

学生根据测试结果改进系统并完成前后对比，答辩必须回答"为什么需要AI"而不只是"用了哪些组件"。每人提交一页系统说明卡：系统用来做什么、不应用来做什么、需要什么数据、何时可能失败、谁必须监督、用户如何纠错和退出，并将架构迁移到现实应用方向。

---

### 能力成长线（修订后）

| 闭环 | 课次 | AI助手获得的能力 | 学生形成的核心认识 |
|---|---:|---|---|
| AI系统与感知 | 1～3 | 结构化感知 | 人类看见不等于AI看见；自动化不都是AI |
| 数据、规则与训练 | 4～6 | 数据表示与两种大脑 | 数据由人设计，偏见有来源 |
| 生成与判断 | 7～9 | 诚实表达 | 通顺不等于正确，输出必须核验 |
| 委派、消息与工具 | 10～12 | 计划、协议与工具 | 委派任务需要标准，执行需要协议和权限 |
| 行动与恢复 | 13～15 | 反馈、重规划与求助 | 智能体要持续观察，失败要能恢复 |
| 记忆与隐私 | 16～18 | 记住、修改和忘记 | 记忆需要来源、期限、同意与删除权 |
| 技能与创造 | 19～21 | 可复用流程 | 存流程不是学本领；不是一切都该自动化 |
| 协作与责任 | 22～24 | 分工、通信与审计 | 责任靠角色、日志和治理落实 |
| 安全与社会影响 | 25～27 | 校验、审批与测试 | 能理解不代表应执行；看不见的AI也在影响你 |
| 以人为本设计 | 28～30 | 完整系统 | 先问要不要AI，再问怎么做AI |

---

三课闭环结构、60分钟课堂容量结构和线上班型实施方式沿用原稿，仅将"透明过程面板"统一更名为**"系统证据面板"**，并在教师手册注明：面板展示的是系统记录和结构化输出，不等同于模型内部真实的计算过程。

# 用户：上述大纲落实到开发中的操作指引
好的，我打算使用的工作流如下：
'''
“编码智能体+Godot MCP+设计文档”工作流可以用来加速Godot智能体实验室的开发。
这套工作流适合项目的原因在于Godot MCP使AI能直接创建场景、添加节点、配置动画、运行测试并读取报错截图后修正，特别适合由WorldSense、WorldActions、ActionValidator等独立组件构成的透明智能体实验室。工作流是“人类完成详细设计，AI读取结构化文档后负责高速实施与迭代”。这恰好匹配用户已有的教学目标、智能体架构和Godot教学经验，缺少的只是将思想快速转换为可运行软件，而这正是编码智能体擅长的。

由于项目目标是教育实验平台而非展示型游戏，教学正确性和系统透明性优先于内容数量和画面效果，建议采用文档驱动加垂直切片方式推进。第一阶段先准备产品愿景、课程目标、MVP范围、架构、动作协议、安全规则和智能体指引等文档，规定组件职责边界和编码规范，AI只读不改。第二阶段仅创建工程骨架，包含基础场景、组件接口和空透明面板，不含游戏内容。第三阶段完成一个完整垂直切片，仅实现“玩家指令→AI读取物品位置→规划拾取→安全校验→角色执行→面板显示”的闭环，只涉及两个动作、一种感知、一条安全规则和一个教学面板，跑通后再扩展。

由于MCP使AI能直接修改场景和脚本，必须使用Git分支和检查点控制风险，每个任务前后提交、创建功能分支、运行测试并人工审查差异。美术MCP可用但非MVP必需，第一阶段用简单色块和占位素材即可，核心验证的是学生能否通过透明面板理解智能体，而非美术产出速度。
'''
我需要把上述教学大纲逐课落实，我本身也是教Blender+Godot课程体系的，请你给我指出具体如何把上述大纲落实到开发中的操作指引(我现在还不需要生成所有的教案，只要上述大纲确定了后，我会一课一课的逐课落实设计)

# GPT-5.6-Sol：开发的具体指引

你的工作流方向是正确的，但我建议做一个关键调整：

> **不要按照30节课依次开发30套功能，而要先开发一个可配置、可观测、可测试的“AI教学实验操作系统”，再把每节课制作成这个系统上的实验包。**

否则开发到第十几课时，很容易出现大量重复场景、重复脚本和只适用于单节课的临时代码。

Godot MCP可以帮助编码智能体操作场景、节点、资源、脚本、截图和运行时错误，但它本质上只是执行工具，不会自动保证架构合理、教学目标正确。MCP规范也建议工具调用保留人工批准和拒绝能力，因此你的“设计文档约束＋小任务执行＋Git检查点＋人工验收”应成为正式开发制度，而不只是工作习惯。([modelcontextprotocol.io](https://modelcontextprotocol.io/specification/draft/server/tools?utm_source=openai))

---

## 一、先把项目重新定义成三个产品

你实际需要开发的不是一个产品，而是三个相互分离的部分。

### 1. 智能体实验平台

负责通用能力：

- 世界与实体；
- 感知；
- 规划；
- 工具；
- 校验；
- 执行；
- 反馈；
- 记忆；
- 技能；
- 多组件协作；
- 日志与证据面板。

这是稳定的技术底座。

### 2. 教学实验框架

负责教学流程：

- 导入课程；
- 提出任务；
- 记录学生预测；
- 设置实验变量；
- 运行基线实验；
- 保存实验结果；
- 显示系统证据；
- 支持修改与重新运行；
- 收集学习证据；
- 判断是否达到课程目标。

这是平台和课程之间的中间层。

### 3. 课程内容包

每节课只是一个配置包，包含：

- 本课标题；
- 学习目标；
- 初始场景；
- 可用传感器；
- 可用工具；
- 安全规则；
- 预设任务；
- 故障条件；
- 引导问题；
- 学习证据；
- 完成条件。

因此，理想结构不是：

```text
第1课场景
第2课场景
第3课场景
……
第30课场景
```

而是：

```text
通用实验平台
├─ 通用世界
├─ 通用智能体管线
├─ 通用证据系统
├─ 通用课程运行器
└─ 30个课程配置包
```

---

## 二、开发时必须固定的四层架构

建议从一开始就把项目划分为以下四层。

### 第一层：领域核心层 Domain Core

只处理AI实验逻辑，不依赖具体UI和动画：

- `WorldState`
- `WorldEntity`
- `Observation`
- `ActionRequest`
- `ValidationResult`
- `ActionResult`
- `MemoryEntry`
- `SkillDefinition`
- `EvidenceEvent`

这一层尽量使用：

- `Resource`
- `RefCounted`
- 类型化数据类；
- 纯函数；
- 可独立测试的服务。

不要把每一种数据都做成Node。Godot官方最佳实践本身也区分了场景、脚本、资源、Autoload和普通数据对象的适用范围；静态类型和警告系统可以在编码阶段发现更多结构性错误。([docs.godotengine.org](https://docs.godotengine.org/en/stable/tutorials/best_practices/index.html?utm_source=openai))

### 第二层：智能体运行层 Agent Runtime

建议采用固定管线：

```text
UserTask
→ WorldSense
→ ContextBuilder
→ BrainProvider
→ ActionParser
→ ActionValidator
→ WorldActions
→ ActionFeedback
→ EvidenceRecorder
```

这一层最重要的原则是：

> **模型、规则大脑和规划器都不能直接修改游戏世界。**

只有`WorldActions`可以改变世界状态。

具体职责如下：

| 组件 | 只负责什么 | 不允许做什么 |
|---|---|---|
| `WorldSense` | 读取允许暴露的世界信息 | 修改世界 |
| `ContextBuilder` | 组装任务、感知和记忆 | 决定动作是否合法 |
| `BrainProvider` | 生成计划或动作请求 | 直接移动角色 |
| `ActionParser` | 解析并规范化结构化消息 | 猜测缺失的危险参数 |
| `ActionValidator` | 校验动作、参数和权限 | 执行动作 |
| `WorldActions` | 执行已批准动作 | 绕过校验器 |
| `ActionFeedback` | 生成成功或失败结果 | 修改历史日志 |
| `EvidenceRecorder` | 保存可观察事件 | 声称展示模型真实思维 |

### 第三层：教学运行层 Pedagogy Runtime

建议建立：

- `LessonRunner`
- `ScenarioLoader`
- `ExperimentController`
- `PredictionRecorder`
- `EvidenceCollector`
- `StudentModificationController`
- `AssessmentTracker`
- `TeacherController`

它们负责把普通智能体模拟变成教学活动。

### 第四层：呈现层 Presentation

包括：

- 2D空间站世界；
- 玩家与智能体动画；
- 学生任务面板；
- 系统证据面板；
- 实验变量面板；
- 教师控制面板；
- 实验记录与导出界面。

呈现层只能通过公开接口和信号读取系统状态，不能越过校验器直接修改核心数据。Godot信号适合让组件对事件作出响应，同时减少彼此的直接引用和耦合。([docs.godotengine.org](https://docs.godotengine.org/en/4.2/tutorials/best_practices/scene_organization.html?utm_source=openai))

---

## 三、把“系统证据面板”设计成平台中枢

证据面板不是附加UI，而是这个项目最核心的教学功能。

建议所有组件都向统一的`EvidenceBus`发送结构化事件：

```gdscript
class_name EvidenceEvent
extends Resource

@export var event_id: String
@export var run_id: String
@export var correlation_id: String
@export var component: String
@export var event_type: String
@export var summary: String
@export var payload: Dictionary
@export var simulation_time: float
```

一次完整任务应产生类似事件：

```text
TASK_RECEIVED
SENSE_REQUESTED
OBSERVATION_CREATED
PLAN_PROPOSED
ACTION_PARSED
ACTION_VALIDATION_STARTED
ACTION_APPROVED
ACTION_EXECUTION_STARTED
ACTION_SUCCEEDED
WORLD_STATE_CHANGED
TASK_COMPLETED
```

失败时可能出现：

```text
SENSOR_DATA_MISSING
ACTION_SCHEMA_INVALID
ACTION_REJECTED
TARGET_NOT_FOUND
PATH_BLOCKED
TOOL_UNAVAILABLE
HUMAN_CONFIRMATION_REQUIRED
REPLAN_REQUESTED
```

### 面板必须支持三种显示模式

#### 学生简化模式

显示：

```text
AI看到了什么
→ AI提出了什么
→ 安全员是否允许
→ 身体做了什么
→ 最后发生了什么
```

#### 标准实验模式

显示：

- 组件；
- 输入；
- 输出；
- 时间顺序；
- 成功或失败；
- 相关动作；
- 规则命中情况。

#### 教师调试模式

额外显示：

- 完整payload；
- 原始模型输出；
- JSON解析结果；
- 组件耗时；
- 异常堆栈；
- 场景和实体ID；
- 本次运行配置。

三种模式使用同一批事件数据，只是显示深度不同。这样既能适配年龄差异，又不需要维护三套系统。

---

## 四、先定义四个核心协议，再让编码智能体工作

不要先让编码智能体创建大量节点。先由你亲自确定四个协议。

### 1. 感知协议

```json
{
  "observation_id": "obs_001",
  "observer_id": "agent_01",
  "visible_entities": [
    {
      "entity_id": "oxygen_01",
      "entity_type": "oxygen_tank",
      "position": [320, 180],
      "distance": 126,
      "state": "available"
    }
  ],
  "hazards": [],
  "missing_fields": []
}
```

必须允许故意关闭字段，例如：

- 不提供位置；
- 不提供类型；
- 不提供危险信息；
- 只提供一定距离内的信息；
- 提供过期信息。

这样才能支撑第1～3课以及后续故障实验。

### 2. 动作请求协议

```json
{
  "request_id": "act_001",
  "actor_id": "agent_01",
  "action": "pick_up",
  "arguments": {
    "target_id": "oxygen_01"
  },
  "reason_summary": "任务要求搬运氧气瓶"
}
```

`reason_summary`只是模型或规则系统提供的说明，不应被当成真实内部思维。

### 3. 校验结果协议

```json
{
  "request_id": "act_001",
  "status": "rejected",
  "rule_id": "DISTANCE_LIMIT",
  "reason": "目标距离超过拾取范围",
  "recoverable": true,
  "suggested_next_step": "move_closer"
}
```

建议统一三种结果：

```text
APPROVED
REJECTED
REQUIRES_HUMAN_CONFIRMATION
```

### 4. 执行结果协议

```json
{
  "request_id": "act_001",
  "status": "failed",
  "error_code": "TARGET_MOVED",
  "world_changed": false,
  "recoverable": true
}
```

所有后续记忆、技能、协作和安全课程，都建立在这四个协议上。

---

## 五、不要用代码硬编码30节课：建立Lesson Package

建议每节课都用一个自定义`Resource`描述。

```gdscript
class_name LessonDefinition
extends Resource

@export var lesson_id: String
@export var title: String
@export_multiline var introduction: String
@export var learning_objectives: Array[String]
@export var misconception_targets: Array[String]

@export var scenario: ScenarioDefinition
@export var available_sensors: Array[SensorDefinition]
@export var available_tools: Array[ToolDefinition]
@export var active_rules: Array[SafetyRuleDefinition]

@export var student_controls: Array[String]
@export var required_experiments: Array[ExperimentDefinition]
@export var evidence_requirements: Array[EvidenceRequirement]
@export var completion_rules: Array[CompletionRule]
```

Godot支持将自定义Resource作为导出属性，并在Inspector中直接配置和引用，非常适合课程定义、工具定义和安全规则等数据驱动内容。([docs.godotengine.org](https://docs.godotengine.org/en/4.6/tutorials/scripting/gdscript/gdscript_exports.html?utm_source=openai))

推荐目录：

```text
res://
├─ core/
│  ├─ domain/
│  ├─ protocols/
│  ├─ events/
│  └─ utilities/
├─ agent/
│  ├─ sensing/
│  ├─ brains/
│  ├─ planning/
│  ├─ validation/
│  ├─ actions/
│  ├─ memory/
│  └─ skills/
├─ pedagogy/
│  ├─ lesson_runner/
│  ├─ experiments/
│  ├─ assessment/
│  └─ evidence/
├─ presentation/
│  ├─ world/
│  ├─ evidence_panel/
│  ├─ student_ui/
│  └─ teacher_ui/
├─ content/
│  ├─ shared/
│  ├─ lessons/
│  │  ├─ cycle_01/
│  │  ├─ cycle_02/
│  │  └─ ...
│  └─ scenarios/
├─ tests/
├─ addons/
└─ docs/
```

---

## 六、把十个学习闭环转换为十个开发能力包

不必立即逐课开发，但必须知道每个闭环依赖哪个平台能力。

| 学习闭环 | 需要开发的平台能力 |
|---|---|
| 1. AI系统与感知 | 实体注册、世界状态、传感器开关、感知范围、字段屏蔽 |
| 2. 数据、规则与训练 | 多Brain Provider、实验重复运行、数据集与简单分类器 |
| 3. 生成与判断 | LLM代理、预设输出、来源字段、不确定性与核验活动 |
| 4. 委派、消息与工具 | Action Schema、工具注册表、参数解析、权限控制 |
| 5. 行动与恢复 | 动态世界、路径执行、失败反馈、取消、重规划、求助 |
| 6. 记忆与隐私 | Memory Store、来源、有效期、权限、修改和删除 |
| 7. 技能与自动化 | Skill Registry、前置条件、步骤、失败策略、技能测试 |
| 8. 协作与责任 | 消息总线、角色权限、组件日志、故障注入、责任追踪 |
| 9. 安全与公平 | Validator Chain、风险等级、人工审批、批量测试 |
| 10. 自主设计 | 配置编辑器、项目模板、测试报告、成果导出 |

### 推荐开发顺序

开发顺序不必完全服从课程顺序：

```text
世界与实体
→ 感知
→ 动作协议
→ 校验
→ 执行
→ 证据事件
→ 课程运行器
→ 实验控制
→ 规则大脑
→ 在线模型适配器
→ 记忆
→ 技能
→ 多组件
→ 高级安全
→ 学生项目编辑器
```

---

## 七、第一个垂直切片应该怎样具体实施

你提出的垂直切片方向正确，建议把它正式定义为：

> **VS-001：安全拾取氧气瓶**

### 场景中只放置

- 一个玩家；
- 一个AI角色；
- 一个氧气瓶；
- 一个障碍；
- 一个目标区域；
- 一个危险区域。

### 只实现一种感知

```text
读取可见物品的ID、类型和位置
```

### 只实现两个工具

```text
move_to(target_position)
pick_up(target_id)
```

### 只实现一条安全规则

```text
AI不得进入危险区域
```

### 只实现一种任务

```text
找到氧气瓶并拾取
```

### 只实现一个证据时间线

```text
收到任务
→ 读取世界
→ 发现氧气瓶
→ 提议移动
→ 通过校验
→ 执行移动
→ 提议拾取
→ 通过校验
→ 执行拾取
→ 任务完成
```

### 必须包含五个失败测试

1. 没有位置传感器；
2. 氧气瓶不存在；
3. 氧气瓶在危险区域；
4. `pick_up`工具没有开放；
5. 动作消息缺少`target_id`。

### 垂直切片验收标准

#### 技术验收

- 规则大脑可离线完成任务；
- 所有动作必须经过Validator；
- 任何组件不能直接绕过`WorldActions`修改世界；
- 每个动作都有唯一`request_id`；
- 成功与失败都产生完整日志；
- 重新运行可恢复初始状态。

#### 教学验收

学生能够回答：

- AI获得了什么信息？
- AI缺少什么信息时会失败？
- 它提出了什么动作？
- 为什么某个动作被拒绝？
- 工具和传感器有什么不同？
- 修改哪个条件能使任务成功？

#### 课堂验收

- 教师能在30秒内重置；
- 能切换正常和故障条件；
- 单次实验控制在1～3分钟；
- 学生不需要打开Godot编辑器才能完成核心实验；
- 错误不会让整个课程停止。

只有这个垂直切片通过三类验收，才继续扩展。

---

## 八、逐课落实时使用统一的“课程转开发”流程

将来每设计一课，都按照以下七步处理。

### 第一步：填写课程设计卡

每课先回答：

```text
学生要形成什么认识？
学生原本可能有什么错误观念？
必须让学生观察到什么现象？
学生可以改变哪个变量？
需要保存什么证据？
如何判断学生不是猜对，而是真的理解？
```

例如第2课：

```text
核心认识：
人看到的信息不等于AI获得的信息。

错误观念：
屏幕上存在的物品，AI自然就知道。

关键现象：
关闭位置字段后，AI知道有氧气瓶，却不能移动到它。

学生变量：
物品类型、位置、危险区域三个传感器开关。

学习证据：
学生能根据失败日志指出缺少的是位置数据。
```

### 第二步：转换成实验规格

```text
初始状态
自变量
控制变量
观察指标
预期现象
失败分支
重置方式
```

### 第三步：列出平台复用与新增功能

必须分开写：

```text
本课复用：
WorldSense、EvidencePanel、LessonRunner

本课新增：
PositionSensorToggle

禁止为本课专门复制：
Agent、WorldActions、EvidencePanel
```

### 第四步：先写验收测试

例如：

```text
Given 物品类型和位置传感器都开启
When AI执行寻找氧气瓶任务
Then AI能够生成正确目标位置

Given 位置传感器关闭
When AI执行同一任务
Then 系统产生SENSOR_DATA_MISSING事件
And 不产生未经校验的move_to执行
```

### 第五步：拆成编码智能体任务

不要给编码智能体：

> “请完成第2课。”

要给它：

> “根据指定接口新增PositionSensor组件；不得修改WorldSense公共接口；新增两个自动测试；在示例场景加入一个可配置开关；完成后运行测试并报告变更文件。”

每个任务应包含：

- 允许修改的目录；
- 禁止修改的文件；
- 输入文档；
- 接口约束；
- 验收条件；
- 必须运行的测试；
- 输出格式。

### 第六步：技术审查

你检查：

- 是否违反组件边界；
- 是否直接跨层访问；
- 是否硬编码课程内容；
- 是否复制现有逻辑；
- 是否产生不可解释的自动行为；
- 是否新增未记录的Autoload；
- 是否改变公共协议。

### 第七步：教学审查

你亲自扮演学生，检查：

- 学生能否发现目标现象；
- 面板是否提前泄露答案；
- 操作是否比概念本身更难；
- 失败是否有教育意义；
- 是否能重现；
- 是否能形成截图、记录或解释证据。

---

## 九、给编码智能体准备哪些设计文档

建议建立以下文档体系。

```text
docs/
├─ locked/
│  ├─ 00_product_vision.md
│  ├─ 01_curriculum_principles.md
│  ├─ 02_system_architecture.md
│  ├─ 03_component_boundaries.md
│  ├─ 04_action_protocol.md
│  ├─ 05_evidence_event_protocol.md
│  ├─ 06_security_invariants.md
│  ├─ 07_coding_standards.md
│  └─ 08_agent_instructions.md
├─ specifications/
│  ├─ lesson_package_spec.md
│  ├─ scenario_spec.md
│  ├─ experiment_spec.md
│  └─ assessment_spec.md
├─ decisions/
│  ├─ ADR-001-domain-model.md
│  ├─ ADR-002-event-bus.md
│  └─ ADR-003-brain-provider.md
└─ tasks/
   ├─ active/
   ├─ completed/
   └─ rejected/
```

### `locked`文档的规则

编码智能体：

- 可以读取；
- 不得直接修改；
- 发现冲突时停止；
- 只能提交“建议修改报告”；
- 由你决定是否修改。

### ADR的作用

每个重要架构决定写明：

```text
背景
决定
原因
替代方案
后果
允许修改的条件
```

例如：

> 为什么所有世界修改只能经过WorldActions？

这样几个月后编码智能体不会“为了方便”让Planner直接修改角色位置。

---

## 十、给编码智能体制定硬性不变量

建议把以下内容写进`08_agent_instructions.md`。

### 架构不变量

1. Brain不得直接访问或修改场景节点；
2. 所有动作必须形成`ActionRequest`；
3. 所有动作必须经过`ActionValidator`；
4. 只有`WorldActions`可以改变模拟世界；
5. 所有关键步骤必须产生`EvidenceEvent`；
6. UI不得成为业务逻辑的唯一存储位置；
7. 课程内容不得硬编码在核心组件中；
8. 在线模型不可用时，核心课程必须可运行；
9. 不得把模型生成的说明称为真实思维过程；
10. 不得在未批准的情况下新增依赖、插件或Autoload。

### 修改不变量

编码智能体每次必须：

```text
读取任务
→ 列出计划
→ 报告预计修改文件
→ 创建或确认分支
→ 实施
→ 运行静态检查
→ 运行测试
→ 启动指定场景
→ 检查运行时错误
→ 截图
→ 汇报差异和遗留问题
```

### 停止条件

遇到以下情况不得自行猜测：

- 设计文档相互冲突；
- 需要改变公共协议；
- 需要新增第三方插件；
- 需要删除大量资源；
- 测试与设计目标冲突；
- 不清楚某个UI究竟是学生端还是教师端；
- 需要处理真实学生数据；
- 需要更改安全不变量。

---

## 十一、Git工作流要比普通小项目更严格

推荐：

```text
main
├─ develop
├─ feature/VS-001-world-sense
├─ feature/VS-001-action-validator
├─ lesson/L01-scenario
└─ fix/evidence-event-order
```

### 每个编码任务至少有三个检查点

```text
Checkpoint A：开始任务前
Checkpoint B：代码与场景完成后
Checkpoint C：测试与截图验收后
```

### 不要让AI一次同时修改

- 核心协议；
- 场景结构；
- UI；
- 课程内容；
- 测试框架。

一次任务最多集中在一个主要关注点，否则人工审查会非常困难。

### MCP权限建议

- 只开放项目目录；
- 不开放个人目录和无关仓库；
- 默认禁止网络和Shell高危命令；
- 插件版本固定；
- MCP工具清单固定；
- 新工具需要人工确认；
- 每次调用保留日志；
- 不把学生数据、API密钥写入项目或提示上下文。

MCP工具能够形成广泛的数据访问和代码执行路径，因此官方规范强调用户同意、权限边界和人工控制；你的开发环境应按“最小权限”配置。([modelcontextprotocol.io](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices?utm_source=openai))

---

## 十二、测试体系应分成四级

### 1. 领域单元测试

测试纯逻辑：

- 感知过滤；
- 参数解析；
- 权限判断；
- 风险分级；
- 记忆过期；
- 技能前置条件。

### 2. 组件集成测试

测试：

```text
Sense → Brain → Parse → Validate → Execute
```

但不必运行完整课程UI。

### 3. 场景验收测试

自动启动测试场景，检查：

- 节点是否存在；
- 信号是否连接；
- 世界是否重置；
- 角色能否执行动作；
- 事件顺序是否正确；
- 是否出现运行时错误。

Godot支持命令行启动项目和调试模式，因此可以把运行检查纳入编码智能体工作流。([docs.godotengine.org](https://docs.godotengine.org/en/4.4/tutorials/editor/command_line_tutorial.html?utm_source=openai))

### 4. 教学验收测试

这一层主要由人完成：

- 学生是否理解；
- 操作负担是否合适；
- 面板是否提供了有效证据；
- 活动是否出现错误暗示；
- 60分钟是否真的装得下；
- 1对1和1对4是否都能实施。

> **自动测试可以证明软件按规则运行，不能证明学生因此学会了。**

---

## 十三、在线模型与离线规则大脑必须共用接口

建议：

```gdscript
class_name BrainProvider
extends RefCounted

func generate_action(context: AgentContext) -> ActionRequest:
    push_error("Not implemented")
    return null
```

实现：

```text
RuleBrainProvider
ReplayBrainProvider
LLMBrainProvider
StudentBrainProvider
```

### 四种Provider的意义

#### `RuleBrainProvider`

- 离线保障；
- 确定性基线；
- 适合单元测试；
- 便于比较规则与模型。

#### `ReplayBrainProvider`

使用预先保存的模型输出：

- 网络故障时仍可演示；
- 教师可以稳定复现幻觉；
- 避免课堂中的模型输出不可控；
- 适合第7～9课。

#### `LLMBrainProvider`

通过教师代理服务调用模型：

- 不把密钥放入客户端；
- 对输入输出做日志和过滤；
- 对超时、限流和格式错误提供降级。

#### `StudentBrainProvider`

由学生扮演规划员，手动选择或填写动作：

- 支持角色扮演；
- 帮助理解组件职责；
- 不依赖真实模型；
- 适合第10～12课和第22～24课。

---

## 十四、Blender和美术资产如何进入工作流

你的判断是对的：MVP阶段不要让美术成为瓶颈。

### MVP阶段

使用：

- 色块；
- 简单图标；
- 基础Sprite；
- 统一尺寸碰撞体；
- 明确颜色语义。

例如：

```text
蓝色：玩家
绿色：AI助手
白色：普通物品
黄色：任务目标
红色：危险区域
紫色：记忆或数据对象
```

### Blender的第一批实际用途

等核心垂直切片稳定后，再制作：

- 空间站模块；
- 氧气瓶；
- 能源模块；
- 机器人角色；
- 危险标志；
- 控制台；
- 传感器视觉效果。

如果仍使用2D平台，可以从Blender统一渲染：

- 正交视角Sprite；
- 角色方向图；
- 物品图标；
- 教学动画；
- 分层背景。

### 资产必须带语义元数据

不要让教学逻辑通过文件名猜测物品类型。

错误方式：

```text
if sprite.texture.resource_path.contains("oxygen"):
```

正确方式：

```text
entity_id = "oxygen_01"
entity_type = "oxygen_tank"
tags = ["portable", "life_support", "restricted"]
```

视觉资产可以更换，语义ID和实验行为必须保持稳定。

---

## 十五、推荐的阶段路线图

### 阶段0：课程与架构冻结

产出：

- 课程能力矩阵；
- 核心术语表；
- 四个协议；
- 组件边界；
- 证据事件规范；
- Lesson Package规范；
- 编码智能体指引；
- Git和MCP安全规则。

### 阶段1：工程骨架

只创建：

- 目录；
- 核心类型；
- 空组件；
- 信号；
- 空证据面板；
- 测试入口；
- 示例课程资源。

不创建大量游戏内容。

### 阶段2：VS-001垂直切片

完成：

```text
指令
→ 感知
→ 规则规划
→ 动作解析
→ 校验
→ 移动与拾取
→ 反馈
→ 证据面板
```

### 阶段3：前三个闭环的平台能力

完成：

- 传感器开关；
- 多大脑Provider；
- 重复实验；
- 简单分类器；
- 预设生成式AI错误案例；
- 接受、修改、核验、拒绝活动。

此时先制作第1～9课原型。

### 阶段4：行动系统

完成：

- 工具注册表；
- 动态世界；
- 路径失败；
- 取消；
- 重规划；
- 求助。

制作第10～15课原型。

### 阶段5：记忆、技能和协作

制作第16～24课。

### 阶段6：安全与学生设计工具

制作第25～30课。

### 阶段7：课程产品化

补充：

- 教师控制台；
- 学习证据导出；
- 课程重置；
- 账号与数据策略；
- 低配置适配；
- 线上小班操作模式；
- 教师手册；
- 课堂试教反馈。

---

## 十六、每一课的完成定义

以后不能以“场景运行成功”作为一课开发完成的标准。

建议使用四重Definition of Done。

### 技术完成

- 无阻塞性报错；
- 核心测试通过；
- 可以稳定重置；
- 在线和离线模式至少一种可完整运行；
- 事件日志完整；
- 不违反组件边界。

### 教学完成

- 学习目标可观察；
- 有明确错误观念；
- 有预测活动；
- 有可修改变量；
- 有前后对比；
- 有学习证据；
- 有现实迁移问题。

### 课堂完成

- 60分钟容量经过试讲；
- 1对1可实施；
- 1对4有角色分工；
- 学生操作说明足够清晰；
- 失败后教师能快速恢复；
- 备用活动可在系统故障时使用。

### 安全完成

- 不收集不必要的数据；
- 学生无法越权访问教师功能；
- 在线模型有降级路径；
- 危险操作仅存在于沙盒；
- 日志不暴露API密钥或个人信息；
- AI生成内容有明确身份标识。

---

## 最后的实施原则

你可以把整个开发方法压缩为下面这条流水线：

```text
课程目标
→ 错误观念
→ 可观察现象
→ 实验变量
→ 平台能力
→ 结构化协议
→ 验收测试
→ 编码智能体实施
→ MCP运行与截图
→ 人工代码审查
→ 教学试验
→ 课程包定稿
```

其中最重要的是三条：

1. **先开发通用实验平台，再制作30个课程包；**
2. **所有智能体行为必须经过结构化协议、校验、执行和证据记录；**
3. **编码智能体负责高速实施，你负责课程正确性、架构决策和最终验收。**

你当前最应该做的下一步，不是开始设计第1课完整教案，也不是让AI一次性建立整个工程，而是先完成以下五份文件：

```text
01_system_architecture.md
02_component_boundaries.md
03_action_and_evidence_protocols.md
04_lesson_package_spec.md
05_VS-001_acceptance_spec.md
```

这五份文件完成后，再让编码智能体创建工程骨架和第一个垂直切片。这样后续逐课落实时，新增的主要是**实验配置、故障条件和学习证据**，而不是每节课重新发明一套智能体系统。
