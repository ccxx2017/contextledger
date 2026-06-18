以下是当前任务的结构化上下文，请基于它继续执行任务。

任务 ID：task_0001
当前轮次：3
当前焦点节点：n_0031
当前焦点：第4周AOS闭环交付：duty_reporter完整集成研究进度，写阶段1 retrospective

## 任务目标
- 从策略发现到数字组织演进，实现量化研究的知识积累循环

## 有效约束
- 无

## 当前有效决策
- 无

## 相关事实
- 当前真实状态：量化研究主线有4条有效策略入库、schema验证、复合条件编译修复，但Strategy Research Agent未真正跑起来，知识积累循环未启动
- 风险1：基础设施惯性——项目持续在基建层打转，未进入知识积累循环
- 风险2：身份混淆——既是量化研究者又是AOS架构师，AOS成为目的而非手段
- 风险3：Strategy Research Agent半成品税——搁置越久，上下文重建成本越高，可能被推倒重来
- 阶段1成功定义五条：1)产出≥10个入库策略档案；2)自主性：Boss提工单后无需干预跑完≥5次假设迭代；3)可信性：抽查3个新档案指标自洽且IR语义正确；4)AOS-native：工单驱动，产出沉淀runtime，日报汇报进度；5)可复盘：每次迭代有完整trace
- 一级风险：结构化输出稳定性、假设生成语义多样性、失败循环退出条件
- 二级风险：prompt资产版本管理、token成本失控、回测耗时
- OpenClaw框架下skill的实际位置：根目录D:\智能投顾\量化相关\abu_modern\openclaw_skills，包含duty-reporter、quant_assistant等skill，每个skill有SKILL.md、TOOLS.md和scripts/目录
- data/knowledge目录已存在并包含策略档案：strategies/下有5个stg_*.md文件，以及market_insights/、index.md、log.md、piercing_report.json、piercing_report.md、schema.md、semantic_phrase_coverage.md

## 待办事项
- 阶段0：duty_reporter维稳（本周，0.5天），包含v0.5降级为后台任务以验证LLM基础设施，冻结Wiki Agent/指挥舱UI等。后续需升级v0.6以集成策略研究进度汇报。
- 阶段1：复活Strategy Research Agent（3-4周），作为AOS第一个领域employee，产出可信策略档案。成功标准包括：产出≥10入库策略、自主运行≥5次假设迭代、可信性验证、AOS-native、可复盘。技术方案含Structured Output、假设多样性、退出闸、prompt版本管理、token监控、回测测量。时间线分4周。
- 阶段2：根据阶段1产物决定下一个employee（5-8周后），可能选项包括Wiki Agent、Triage Agent、Quant Reviewer Agent、指挥舱UI
- 阶段3：指挥舱MVP（不早于2个月后），基于已有2-3个employee稳定工作
- 决策2：决定v0.5（LLM摘要节点）是否值得做，或跳过直接到阶段1
- 决策4：确定节奏快慢（基于每天2-4小时投入的3-4周，或按实际投入调整）
- 整理ROADMAP_v2.md，写入aos/projects/abu_modern/，固化路线图
- 开一张工单：TKT-2026-002 'Strategy Research Agent v1 - 阶段 1 启动'，包含顶层工单及按周拆分子工单，验收标准为阶段1五条成功定义。
- 冻结其他诱惑：在aos/runtime/中创建_frozen_ideas.md，列出Wiki Agent/指挥舱UI等，标注阶段1完成前不启动
- 实现Structured Output改造：用Function Calling/response_format强制约束strategy_ir输出，替代自由文本解析
- 实现假设多样性机制：注入已有策略统计摘要和排斥规则，避免重复生成相似策略
- 实现退出条件三道闸：硬上限迭代≥10、资源闸累计token超预算、价值闸连续3次假设未通过验收
- 建立Prompt资产管理：在prompts/下按版本号新建文件，维护CHANGELOG，使用软链接指向current
- 实现Token监控装饰器：记录每次LLM调用的token消耗，写入runtime/metrics/llm_usage/，并集成到duty_reporter日报
- 建立AOS目录骨架：创建org/agents/agent-strategy-researcher.md和openclaw_skills/strategy-researcher/完整结构（含SKILL.md、TOOLS.md、scripts/），而非之前建议的projects/abu_modern/aos/agents/strategy-researcher/
- 实现工单驱动循环：解析工单意图与约束，循环生成假设、回测、分析、判断，产出归档到runs/
- 第1周地基交付：Structured Output demo、token监控、AOS目录骨架、单次闭环脚本
- 第2周Loop交付：完整的5+假设自主循环工单，至少1个入库策略
- 第3周稳定性交付：连续5张不同意图工单，每张≥1入库策略，无人工干预
- 第4周AOS闭环交付：duty_reporter完整集成研究进度，写阶段1 retrospective

## 相关文件
- 无

## 已推翻或废弃内容
- 无

请注意：
- 不要继续采用已推翻或 superseded 的方案。
- 必须遵守有效约束。
- 优先围绕当前焦点继续推进。