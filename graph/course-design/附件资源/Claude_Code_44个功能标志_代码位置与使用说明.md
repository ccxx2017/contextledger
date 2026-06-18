# Claude Code：44个功能标志的代码位置与使用说明

## 说明
- 本报告基于项目源码中对 bun:bundle 的 `feature('FLAG')` 编译期特性扫描与人工归类整理而成。
- 实际扫描共发现 80+ 个特性开关；为契合文章主题，这里精选了 44 个具备代表性的核心/架构级功能进行归档。
- 这些开关为编译期特性，普通用户无法在不重打包的前提下直接切换；部分功能在运行期还需要配合环境变量或设置项。

## 使用总览（重要）
- 编译期：源码通过 `feature('...')` 做条件编译，是否生效取决于官方构建配置。还原源码环境中无法直接在运行时开启/关闭。
- 运行期约束：部分功能在代码里同时检查环境变量或设置项才会走到对应分支，例如：
  - 协调器模式需检测 `CLAUDE_CODE_COORDINATOR_MODE` 等环境变量
  - 某些内部 Beta 仅在 `process.env.USER_TYPE === 'ant'` 时启用（参考 [betas.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/constants/betas.ts)）
- 学习与验证建议：阅读下方“关键文件”链接中的实现与调用路径，理解控制流与影响面；如需实验，可在本地以“阅读/学习”为目的做条件常量替换或插桩，但请勿将修改版分发或用于商用。

---

## 功能清单（44 项）

### 1. KAIROS（自主常驻代理/通道）
- 作用：支持持续运行的自主代理与频道消息、简报等能力
- 关键文件：
  - [bridgeMain.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/bridge/bridgeMain.ts)
  - [systemPrompt.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/systemPrompt.ts)
  - [conversationRecovery.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/conversationRecovery.ts)
- 使用提示：官方内建；学习时可阅读 system prompt 与会话恢复逻辑；部分路径还依赖设置中的 kairosEnabled

### 2. COORDINATOR_MODE（多智能体协调）
- 作用：启用协调者/工作者式多 Agent 调度
- 关键文件：
  - [toolPool.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/toolPool.ts)
  - [sessionRestore.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/sessionRestore.ts)
  - [processSlashCommand.tsx](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/processUserInput/processSlashCommand.tsx)
- 使用提示：常与 `CLAUDE_CODE_COORDINATOR_MODE` 环境变量共同判断；属于编译期+运行期双重门控

### 3. REACTIVE_COMPACT（上下文自适应压缩）
- 作用：基于会话与工具结果的动态压缩/折叠
- 关键文件：
  - [compact.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/commands/compact/compact.ts)
  - [autoCompact.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/services/compact/autoCompact.ts)
  - [query.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/query.ts)
- 使用提示：学习实现时关注何时触发压缩与摘要写盘/引用策略

### 4. ABLATION_BASELINE（消融研究基线）
- 作用：内部对照/基线路径，便于评估模块价值
- 关键文件：
  - [cli.tsx](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/entrypoints/cli.tsx)
- 使用提示：仅供研究评估，非面向用户特性

### 5. DUMP_SYSTEM_PROMPT（输出系统提示词）
- 作用：调试时输出完整系统提示词
- 关键文件：
  - [cli.tsx](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/entrypoints/cli.tsx)
- 使用提示：用于可观测性与提示词排障

### 6. DAEMON（守护进程模式）
- 作用：以常驻方式处理异步/长连任务
- 关键文件：
- [commands.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/commands.ts)
- [cli.tsx](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/entrypoints/cli.tsx)
- 使用提示：与桥接/远程控制等能力配合

### 7. ANTI_DISTILLATION_CC（对抗蒸馏防护）
- 作用：对抗蒸馏/投毒相关的防御性逻辑
- 关键文件：
  - [claude.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/services/api/claude.ts)
- 使用提示：聚焦安全与提示注入防护

### 8. VOICE_MODE（语音模式）
- 作用：语音交互相关能力
- 关键文件：
  - [voiceModeEnabled.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/voice/voiceModeEnabled.ts)
  - [commands.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/commands.ts)
- 使用提示：界面与输入设备支持相关

### 9. TEAMMEM（团队记忆）
- 作用：团队级记忆文件的识别、读写与统计
- 关键文件：
  - [sessionFileAccessHooks.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/sessionFileAccessHooks.ts)
  - [memoryFileDetection.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/memoryFileDetection.ts)
- 使用提示：涉及文件定位、读写与统计埋点

### 10. MEMORY_SHAPE_TELEMETRY（记忆形态遥测）
- 作用：对记忆文件形状/规模进行遥测
- 关键文件：
  - [sessionFileAccessHooks.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/sessionFileAccessHooks.ts)
- 使用提示：配合 TEAMMEM 使用以监控效果

### 11. HISTORY_SNIP（历史片段裁剪）
- 作用：在消息/搜索折叠中识别并引用历史片段
- 关键文件：
  - [messages.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/messages.ts)
  - [collapseReadSearch.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/collapseReadSearch.ts)
- 使用提示：与大上下文管理策略协同

### 12. SHOT_STATS（统计面板/镜头分布）
- 作用：统计与可视化会话/调用分布
- 关键文件：
  - [stats.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/stats.ts)
  - [Stats.tsx](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/components/Stats.tsx)
- 使用提示：面板展示及缓存/迁移逻辑

### 13. PERFETTO_TRACING（Perfetto 追踪）
- 作用：接入 Perfetto 进行性能/事件追踪
- 关键文件：
  - [perfettoTracing.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/telemetry/perfettoTracing.ts)
- 使用提示：性能调优与问题定位

### 14. ENHANCED_TELEMETRY_BETA（增强遥测 Beta）
- 作用：更丰富的会话/事件遥测
- 关键文件：
  - [sessionTracing.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/telemetry/sessionTracing.ts)
- 使用提示：内部 Beta，通常与 `USER_TYPE==='ant'` 环境相关

### 15. ULTRATHINK（深度思考）
- 作用：加深推理/思考链条的策略
- 关键文件：
  - [thinking.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/thinking.ts)
- 使用提示：与提示词与工具调用节奏配合

### 16. ULTRAPLAN（高级规划）
- 作用：更结构化的规划/计划模式
- 关键文件：
  - [commands.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/commands.ts)
  - [PromptInput.tsx](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/components/PromptInput/PromptInput.tsx)
- 使用提示：常与权限与退出计划流控协同

### 17. WORKFLOW_SCRIPTS（工作流脚本）
- 作用：启用脚本化工作流工具
- 关键文件：
  - [PermissionRequest.tsx](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/components/permissions/PermissionRequest.tsx)
  - [classifierDecision.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/permissions/classifierDecision.ts)
- 使用提示：以工具接口暴露，受权限模型约束

### 18. TERMINAL_PANEL（终端捕获/面板）
- 作用：终端输出捕获、面板化展示与相关快捷键
- 关键文件：
  - [defaultBindings.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/keybindings/defaultBindings.ts)
  - [tools.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/tools.ts)
- 使用提示：与权限请求及键位绑定相关

### 19. OVERFLOW_TEST_TOOL（溢出测试工具）
- 作用：内部溢出/上限测试用工具
- 关键文件：
  - [classifierDecision.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/permissions/classifierDecision.ts)
- 使用提示：测试用途，非面向普通用户

### 20. TRANSCRIPT_CLASSIFIER（转录/对话分类器）
- 作用：基于分类器的权限/模式判定
- 关键文件：
  - [permissions.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/permissions/permissions.ts)
  - [yoloClassifier.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/permissions/yoloClassifier.ts)
- 使用提示：大量权限分支受其控制，内部构建优先

### 21. BASH_CLASSIFIER（Bash 权限分类器）
- 作用：对 Bash 操作进行更细粒度指导与安全建议
- 关键文件：
  - [yoloClassifier.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/permissions/yoloClassifier.ts)
  - [structuredIO.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/cli/structuredIO.ts)
- 使用提示：与 TRANSCRIPT_CLASSIFIER 共用部分模板

### 22. POWERSHELL_AUTO_MODE（PowerShell 自动模式引导）
- 作用：为 PowerShell 提供自动模式引导与指令模板
- 关键文件：
  - [permissions.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/permissions/permissions.ts)
  - [yoloClassifier.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/permissions/yoloClassifier.ts)
- 使用提示：Windows 场景专用分支

### 23. CCR_AUTO_CONNECT（远程控制自动连接）
- 作用：CCR/远控模式下自动连接策略
- 关键文件：
  - [bridgeEnabled.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/bridge/bridgeEnabled.ts)
  - [config.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/config.ts)
- 使用提示：与桥接/远控流程配合

### 24. BG_SESSIONS（后台并发会话）
- 作用：启用/管理后台会话并行与切换
- 关键文件：
  - [concurrentSessions.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/concurrentSessions.ts)
  - [main.tsx](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/main.tsx)
- 使用提示：涉及消息队列与 UI 状态同步

### 25. CHICAGO_MCP（计算机使用/执行器接入）
- 作用：本地执行器/计算机使用相关包装与清理
- 关键文件：
  - [wrapper.tsx](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/computerUse/wrapper.tsx)
  - [cleanup.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/computerUse/cleanup.ts)
- 使用提示：内部能力，运行期还受配置与二进制依赖

### 26. MCP_SKILLS（MCP 作为技能）
- 作用：将 MCP 客户端能力暴露为技能/工具
- 关键文件：
  - [client.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/services/mcp/client.ts)
  - [commands.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/commands.ts)
- 使用提示：与 MCP_RICH_OUTPUT 协同以改进展示

### 27. WEB_BROWSER_TOOL（浏览器工具）
- 作用：浏览器/网页抓取与展示工具
- 关键文件：
  - [REPL.tsx](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/screens/REPL.tsx)
  - [main.tsx](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/main.tsx)
- 使用提示：与权限与 UI 组件配合

### 28. FILE_PERSISTENCE（大输出写盘与引用）
- 作用：对过大工具结果写盘并以引用注入上下文
- 关键文件：
  - [filePersistence.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/filePersistence/filePersistence.ts)
  - [cli/print.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/cli/print.ts)
- 使用提示：与上下文膨胀控制相关

### 29. COMMIT_ATTRIBUTION（提交归因）
- 作用：提交/变更归因与元数据关联
- 关键文件：
  - [worktree.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/worktree.ts)
  - [bashProvider.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/shell/bashProvider.ts)
- 使用提示：会影响部分提交/还原展示逻辑

### 30. DIRECT_CONNECT（直连模式）
- 作用：直连服务端/绕过中转的连接策略
- 关键文件：
  - [main.tsx](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/main.tsx)
- 使用提示：网络/权限前置条件较多

### 31. SSH_REMOTE（SSH 远程）
- 作用：通过 SSH 建立远程控制/开发会话
- 关键文件：
  - [main.tsx](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/main.tsx)
- 使用提示：与远控与会话镜像组合

### 32. FORK_SUBAGENT（分叉子代理）
- 作用：在不污染主循环的前提下分叉子 Agent
- 关键文件：
  - [forkSubagent.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/tools/AgentTool/forkSubagent.ts)
  - [commands/branch](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/commands/branch/index.ts)
- 使用提示：摘要/回忆提取/后台分析等场景

### 33. VERIFICATION_AGENT（验证代理）
- 作用：独立的代码/结果验证代理与提示模板
- 关键文件：
  - [prompts.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/constants/prompts.ts)
  - [builtInAgents.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/tools/AgentTool/builtInAgents.ts)
- 使用提示：结合评审/回归校验流程

### 34. RUN_SKILL_GENERATOR（技能生成器）
- 作用：运行技能生成/探索型代理
- 关键文件：
  - [skills/bundled/index.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/skills/bundled/index.ts)
- 使用提示：实验性/探索性能力

### 35. KAIROS_CHANNELS（KAIROS 频道）
- 作用：KAIROS 频道消息/队列处理
- 关键文件：
  - [messageQueueManager.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/messageQueueManager.ts)
  - [messages.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/messages.ts)
- 使用提示：与 KAIROS 主流程耦合

### 36. KAIROS_BRIEF（KAIROS 简报）
- 作用：面向 KAIROS 的快速简报工具与权限
- 关键文件：
  - [brief.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/commands/brief.ts)
  - [permissionRuleParser.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/permissions/permissionRuleParser.ts)
- 使用提示：与权限/工具白名单协同

### 37. KAIROS_GITHUB_WEBHOOKS（KAIROS GitHub 钩子）
- 作用：接入 GitHub Webhook 的自动化事件通道
- 关键文件：
  - [commands.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/commands.ts)
- 使用提示：需要远程与鉴权配置

### 38. MCP_RICH_OUTPUT（MCP 富输出）
- 作用：MCP 工具在 UI 中的富展示能力
- 关键文件：
  - [MCPTool/UI.tsx](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/tools/MCPTool/UI.tsx)
- 使用提示：与 MCP_SKILLS 一起使用体验最佳

### 39. TEMPLATES（模板系统）
- 作用：支持模板目录加载与解析
- 关键文件：
  - [markdownConfigLoader.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/markdownConfigLoader.ts)
- 使用提示：需准备模板目录结构与文件

### 40. QUICK_SEARCH（快速搜索）
- 作用：输入框内的快速搜索/提示能力
- 关键文件：
  - [PromptInput.tsx](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/components/PromptInput/PromptInput.tsx)
- 使用提示：与键位绑定/输入法交互相关

### 41. TOKEN_BUDGET（Token 预算）
- 作用：对上下文与工具调用的 Token 预算控制
- 关键文件：
  - [prompts.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/constants/prompts.ts)
  - [Spinner.tsx](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/components/Spinner.tsx)
- 使用提示：影响提示模板与 UI 提示

### 42. STREAMLINED_OUTPUT（精简输出）
- 作用：对输出进行精简/聚焦展示
- 关键文件：
  - [cli/print.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/cli/print.ts)
- 使用提示：与长输出写盘/引用策略联动

### 43. REVIEW_ARTIFACT（评审工件）
- 作用：在权限请求与工件展示中支持评审项
- 关键文件：
  - [PermissionRequest.tsx](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/components/permissions/PermissionRequest.tsx)
- 使用提示：与权限模型/工件上传协同

### 44. PROACTIVE（主动模式）
- 作用：系统主动发起建议/诊断/提醒的行为
- 关键文件：
  - [systemPrompt.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/systemPrompt.ts)
  - [sessionStorage.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/utils/sessionStorage.ts)
- 使用提示：常与 KAIROS 组合触发

---

## 运行期常见控制点（补充）
- 协调器模式：`CLAUDE_CODE_COORDINATOR_MODE` 环境变量需为真，同时要求构建已启用该特性
- 内部 Beta：`process.env.USER_TYPE === 'ant'` 时启用部分增强遥测/内部工具
- KAIROS：代码中还会判断 `kairosEnabled` 等设置项
- API Beta Header：部分 API 相关能力依赖 Beta Header（见 [betas.ts](file:///d:/AI-practicing/claude-code-sourcemap/restored-src/src/constants/betas.ts)）

## 学习路线建议
- 从上表的“关键文件”切入，先理解特性在控制流中的位置与数据流
- 对涉及权限/工具/上下文管理的特性，配合阅读 `utils/permissions/*`、`utils/collapseReadSearch.ts`、`constants/prompts.ts`
- 对涉及遥测/性能的特性，配合阅读 `utils/telemetry/*` 与 `utils/stats*.ts`

> 提示：本报告仅为学习使用，切勿将含有修改的构建二次分发或用于商用。

