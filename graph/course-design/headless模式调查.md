📋 核心结论
                                                                                                          1. Headless 模式确实存在：通过 -p 或 --print 标志启用，对应源码中的 runHeadless()
  函数（src/cli/print.ts）。
  2. 命令语法基本正确：你提供的参数选项都是有效的 CLI 标志。
  3. 需要修正的小问题：你的示例中有两行重复的 claude -p "$TASK_DESCRIPTION"，实际只需一行。

  🔍 详细验证

  1. Headless 模式实现

  - 入口：src/main.tsx 第 968 行定义 -p, --print 选项
  .option('-p, --print', 'Print response and exit (useful for pipes). Note: The workspace trust dialog
  is skipped when Claude is run with the -p mode. Only use this flag in directories you trust.', () =>
  true)
  - 执行路径：启用 -p 后，程序会跳过交互式 TUI，直接调用 runHeadless() 函数（src/cli/print.ts 第 455
  行）。

  2. 支持的输出格式

  - --output-format <format> 选项接受 text、json、stream-json 三种值
  - 在 headless 模式下，stream-json 用于实时流式输出（NDJSON 格式）

  3. 工具权限控制

  - --allowedTools 和 --disallowedTools 支持权限规则语法：
    - "Read" - 允许所有 Read 操作
    - "Bash(git:*)" - 允许所有以 git 开头的 Bash 命令
    - "Bash(pytest:*)" - 允许所有以 pytest 开头的 Bash 命令
  - 语法解析由 parseToolListFromCLI() 函数处理（src/utils/permissions/permissionSetup.ts 第 813 行）

  4. 权限模式选项

  - --permission-mode <mode> 接受以下值（定义于 src/types/permissions.ts）：
    - plan - 计划模式（需要用户批准计划）
    - acceptEdits - 自动接受编辑
    - default - 默认模式（询问权限）
    - dontAsk - 不询问（直接拒绝未明确允许的操作）
    - bypassPermissions - 绕过所有权限检查（慎用）

  ✅ 修正后的命令示例

  claude -p "$TASK_DESCRIPTION" \
    --output-format stream-json \
    --allowedTools "Read,Edit,Write,Bash(git:*),Bash(pytest:*)" \
    --permission-mode plan

  ⚠️重要注意事项

  1. 信任警告：使用 -p 模式会跳过工作区信任对话框，仅应在可信目录中使用。
  2. bypassPermissions 风险：如你所说，应避免使用此模式，除非在完全受控的沙箱环境中。
  3. Bash 工具限制：Bash(git:*) 语法中的 :* 表示通配符，匹配所有以 git 开头的命令。
  4. 会话持久性：headless 模式默认不保存会话，如需恢复会话可添加 --continue 或 --resume 选项。

  📁 相关源码文件

  - src/main.tsx - CLI 选项定义和主逻辑分支
  - src/cli/print.ts - headless 模式核心实现
  - src/utils/permissions/permissionSetup.ts - 工具权限解析
  - src/types/permissions.ts - 权限模式类型定义
  - src/utils/permissions/PermissionMode.ts - 权限模式配置

●B调查结果：Claude Code 确实支持 headless 模式

  通过分析源码（基于 @anthropic-ai/claude-code@2.1.88 的 sourcemap 恢复），可以确认：                   
  ✅ Headless 模式真实存在                                                                              
  - 触发方式：使用 -p 或 --print 标志
  - 代码位置：src/main.tsx 中 program.option('-p, --print', ...) 定义，src/cli/print.ts 中的
  runHeadless() 函数实现
  - 作用：跳过交互式 TUI，直接执行提示并输出结果，适用于脚本、CI/CD 等非交互场景

  ✅ 命令行参数验证

  ┌───────────────────────────────────┬────────┬────────────────────────────────────────────────────┐
  │               参数                │ 是否支 │                        说明                        │
  │                                   │   持   │                                                    │
  ├───────────────────────────────────┼────────┼────────────────────────────────────────────────────┤
  │ -p, --print                       │ ✅     │ 启用 headless 模式                                 │
  ├───────────────────────────────────┼────────┼────────────────────────────────────────────────────┤
  │ --output-format <format>          │ ✅     │ 支持 text、json、stream-json（仅 --print           │
  │                                   │        │ 模式下有效）                                       │
  ├───────────────────────────────────┼────────┼────────────────────────────────────────────────────┤
  │ --allowedTools <tools...>         │ ✅     │ 支持逗号/空格分隔的工具列表，支持 Bash(git:*)      │
  │                                   │        │ 等权限规则语法                                     │
  ├───────────────────────────────────┼────────┼────────────────────────────────────────────────────┤
  │ --permission-mode <mode>          │ ✅     │ 支持 plan、acceptEdits、bypassPermissions、default │
  │                                   │        │ 、dontAsk（auto 为内部功能）                       │
  ├───────────────────────────────────┼────────┼────────────────────────────────────────────────────┤
  │ --input-format <format>           │ ✅     │ 支持 text、stream-json（仅 --print 模式）          │
  ├───────────────────────────────────┼────────┼────────────────────────────────────────────────────┤
  │ --verbose、--max-turns、--max-bud │ ✅     │ 其他 headless 专属参数                             │
  │ get-usd 等                        │        │                                                    │
  └───────────────────────────────────┴────────┴────────────────────────────────────────────────────┘

  📋 命令语法示例

  您提到的命令基本正确，但第二行是重复的（可能是笔误）：
  # 正确语法（单行或使用续行符）
  claude -p "$TASK_DESCRIPTION" \
    --output-format stream-json \
    --allowedTools "Read,Edit,Write,Bash(git:*),Bash(pytest:*)" \
    --permission-mode plan   # 或 acceptEdits，不要用 bypassPermissions

  🔧 关键细节

  1. 权限规则语法：Bash(git:*) 表示允许所有以 git 开头的 Bash 命令，这是官方支持的语法（见
  src/commands/commit.ts 等文件）
  2. 权限模式：
    - plan：计划模式（需要用户确认）
    - acceptEdits：自动接受编辑类操作
    - bypassPermissions：绕过所有权限检查（不建议在脚本中使用）
    - default：默认行为（询问）
    - dontAsk：不询问（拒绝未明确允许的操作）
  3. 输出格式：stream-json 会以 NDJSON 流式输出结果，适合程序化处理
  4. 工作目录信任：使用 -p 模式时会跳过工作空间信任对话框，仅应在可信目录中使用

  📁 源码证据

  - Headless 入口：src/main.tsx:968 定义 -p, --print 选项
  - Headless 实现：src/cli/print.ts:455 的 runHeadless() 函数
  - 工具解析：src/utils/permissions/permissionSetup.ts:813 的 parseToolListFromCLI() 函数
  - 权限模式：src/types/permissions.ts:16-22 定义的 EXTERNAL_PERMISSION_MODES
  - 权限规则示例：src/commands/commit.ts:7-9 使用 Bash(git add:*) 等语法

  ⚠️注意事项

  1. 命令中的第二行 claude -p "$TASK_DESCRIPTION" \ 是重复的，只需保留一次
  2. --permission-mode bypassPermissions 虽然存在，但官方文档建议不要使用（安全风险）
  3. --output-format stream-json 仅在 --print 模式下有效
  4. Headless 模式会跳过信任对话框，请确保在可信环境中使用

  结论：您提到的功能确实存在，Claude Code 提供了完善的 headless 模式，适合自动化工作流集成。