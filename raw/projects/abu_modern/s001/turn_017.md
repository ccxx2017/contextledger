# 用户：
 但是，我还是很迷惑，我在飞书对话去给机器人下任务时，openclaw端的智能体如何区分它的身份，比如，有两个数字员工，一个是strategy-researc 
# 项目AI：
现在你问到了一个真正的痛点。答案很明确：

  真相：你现在的设置下根本不存在"两个智能体"                                                                                           
  你只是在 workspace/skills/ 下建了两个文件夹，里面放了 SKILL.md。这意味着：                                                           
  只有"一个默认 agent + 两个可用技能"                                                                                                  
  源代码证实（src/routing/resolve-route.ts 第835行）：

  return choose(resolveDefaultAgentId(input.cfg), "default");

  当你在 cfg.agents.list 中没有配置任何 agent 时，所有消息都路由到唯一一个默认 agent。这个默认 agent 会加载 workspace/skills/ 下所有
  SKILL.md。

  LLM 看到的系统提示词大概是这样的：

  Runtime: agent=default ...

  ## Skills (mandatory)
  Before replying: scan <available_skills> <description> entries.
  - If exactly one skill clearly applies: read its SKILL.md ...
  - If multiple could apply: choose the most specific one...

  <available_skills>
    <skill>
      <name>strategy_researcher</name>
      <description>策略研究与回测分析</description>
      <location>/workspace/skills/strategy_researcher/SKILL.md</location>
    </skill>
    <skill>
      <name>duty_reporter</name>
      <description>值班报告生成与日报编写</description>
      <location>/workspace/skills/duty_reporter/SKILL.md</location>
    </skill>
  </available_skills>

  这里的问题在于

  1. 没有独立的会话/记忆——两套技能共享同一段对话历史。你今天让它写策略，明天让它写日报，所有对话混在一起
  2. LLM 自己决定用哪个技能——它根据用户消息和 description 字段"猜"该激活哪个 SKILL.md。猜错了你也没办法
  3. agent ID 始终是 default（第947行 agent=${runtimeInfo.agentId}），LLM 看到的是 "agent=default"，不是 "agent=strategy-researcher"

  两个方案

  方案 A：维持一个 agent，靠技能区分（你现在的方式）

  你目前的设置可以工作，但限制是：
  - 所有任务混在同一个对话上下文里
  - LLM 自行决定何时读 strategy_researcher/SKILL.md，何时读 duty_reporter/SKILL.md
  - 关键：在每个技能文件夹的 prompts/ 目录下放的文件不会被自动读取，必须在 SKILL.md 主流程中显式写 read prompts/xxx.md

  方案 B：配置真正的多 agent（推荐，如果你想要独立的"数字员工"）

  在 OpenClaw 配置中定义两个 agent：

  # openclaw config
  agents:
    list:
      - id: strategy-researcher
        model: claude-opus-4-6
        skills: ["strategy_researcher"]   # 只加载这个技能
      - id: duty-reporter
        model: claude-haiku-4-5
        skills: ["duty_reporter"]         # 只加载这个技能

  bindings:
    - match:
        channel: feishu
        peer:
          kind: group
          id: "群A_ID"     # 策略研究群
      agentId: strategy-researcher
    - match:
        channel: feishu
        peer:
          kind: group
          id: "群B_ID"     # 值班日报群
      agentId: duty-reporter

  这样做的好处：
  - 每个 agent 有独立的对话历史和上下文
  - 每个 agent 只加载自己的技能，不会混淆
  - 每个 agent 可以用不同的模型（策略研究用 Opus，值班日报用 Haiku，省钱）
  - 飞书里的"身份"由路由绑定决定——群 A @机器人 → strategy-researcher，群 B @机器人 → duty-reporter

  你当前设置的最大风险是：LLM 可能在你问策略问题时读了 duty_reporter/SKILL.md，或者反过来。它只有一个大脑，你只是给了它两份工作说明书。

