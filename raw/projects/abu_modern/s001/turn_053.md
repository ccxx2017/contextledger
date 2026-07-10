# 用户：
但是上面的那个问题项目AI的回复如下，该怎么办呢？
'''
我看完了三个 archive。没有一个是现过 ## 档案元数据 JSON 区块，也没有任何 sanity_check_failed 或 passed 字段。

所有 archive 的 markdown 结构是：

# <strategy_id>
- **Intent**: ...
- **Created**: ...
- **IR Summary**: ...
- **Universe**: ...
## 假设
## 回测记录（含 run 明细）
## 分析
## 关联策略



没有独立的元数据区块，也没有位置字段来表达 sanity check 的通过/失败状态。

这个结论说明什么？取决于你的预期：
预期有但实际没有 — 这意味着后端在 compile-ir 后的 KB 写入侧并没有产出那个 ## 档案元数据 | status: sanity_check_failed/passed 区块。可能是后端版本落后于文档，或者那个字段是待实现的设计意图。
预期没有（字段藏在某处而非独立标题） — 目前确实没有。IR Summary 里也没有 sanity_check 相关的 key。
你要我进一步查一下后端是否在别的地方暴露了这个状态（比如通过 index 的元数据、或者 log 追踪），还是直接确认这就是"该功能尚未上线的现状"？
'''
# GPT5.5:
这件事要**暂停验收 005I**，先不要恢复 `005B Round 5`。

项目AI这个回复说明：**005I 的“测试通过/实现完成”与真实 KB archive 输出不一致**。这不是小问题，而是典型的“代码路径或部署路径没有真正进入主链路”。

你现在应该把 005I 标记为：

> **implementation_claimed_but_live_archive_not_verified**

也就是：代码声称完成，单测通过，但 live archive 证据不成立。

---

# 1. 当前判断

项目AI说：

> 看了三个 archive，没有 `## 档案元数据 JSON`，也没有 `sanity_check_failed` 或 `passed` 字段。

这直接推翻了我前面建议的轻量确认项。  
所以现在不能认为 005I 验收通过。

目前有三种可能：

## 可能 A：看的是旧 archive

005I 之前生成的 archive 本来不会有新区块。  
如果项目AI查看的是旧的三个档案，那没有新区块是正常的。

这种情况只需要用 **005I 之后新建的 compile-ir archive** 验证。

## 可能 B：后端代码改了，但运行中的后端不是新版

这是很常见的情况：

- 项目AI改了 Windows 工作区代码；
- 但 FastAPI 服务没有重启；
- 或重启的是另一个环境；
- 或 OpenClaw 调用的后端地址仍指向旧服务。

这种情况单测会通过，但 live archive 没变化。

## 可能 C：实现写在了某条非主路径，实际 `compile-ir` 没走到

比如：

- 单测直接调用了 `knowledge_base.py`；
- 但 `/strategy-builder/compile-ir` 实际调用了另一套 archive writer；
- 或 `append_backtest_result()` 写的是旧 markdown 模板；
- 或 `kb_query archive` 读的是另一个 `data/knowledge` 路径。

这种情况最危险，说明 005I 修的是“看起来对”的代码，而不是实际生产路径。

---

# 2. 现在不要做什么

现在不要：

- 不要恢复 005B；
- 不要让 strategy_researcher 继续 Round 5；
- 不要直接相信“测试 14 passed”；
- 不要继续往后开 005J/005K；
- 不要把旧 archive 缺字段解释为“无所谓”。

因为 KB sanity 的目的就是让研究员可以从 archive 文本中判断档案是否合格。  
如果 archive 里看不到状态字段，这个机制对运行时员工就是不存在的。

---

# 3. 立刻让项目AI做“005I live path 验证”

你可以直接把下面这段发给项目AI。

```text
请暂停 005I 验收。你前面检查 archive 后发现没有 “## 档案元数据 JSON” 区块，也没有 sanity_check_failed / passed 字段，这说明 005I 的实现声明和 live archive 输出不一致。

现在请做 TKT-2026-005I 的 live path verification，不要做任何研究任务，不要调用 strategy_researcher，不要恢复 005B。

目标：
确认 005I 的代码是否真的进入当前 live compile-ir -> KB archive 主链路。

请按以下步骤执行：

1. 说明你刚才检查的三个 archive 是旧档案还是 005I 之后新生成的档案。
   - 列出 strategy_id
   - 列出 created 时间
   - 列出对应文件路径
   - 判断是否能用于验证 005I

2. 确认当前运行中的后端代码版本。
   - 当前 FastAPI 服务是否已重启到包含 005I 修改的代码；
   - 当前服务进程的工作目录；
   - 当前服务读取的 data/knowledge 实际路径；
   - `/strategy-builder/compile-ir` 实际调用的 archive 创建函数路径；
   - `/knowledge/strategies/{id}` 实际读取的 archive 文件路径。
   不要只看源码，请尽量用日志、打印、临时只读诊断、或明确路径输出证明。

3. 新建一个 005I 专用 live test archive。
   - 使用 `/strategy-builder/compile-ir`；
   - metadata 中必须传真实 universe，例如 ["600519.SH"]；
   - strategy_name 中包含 `005I_live_verify`；
   - 不要使用旧 invoke；
   - 不需要跑大回测，最多可以只做 compile-ir 建档验证。
   然后用 `/knowledge/strategies/{strategy_id}` 或 kb_query archive 读取该新档案。

4. 验证新档案中是否出现：
   - `## 档案元数据 JSON`
   - strategy_id
   - strategy_ir
   - universe
   - sanity_check_failed 或 passed
   - sanity_missing_fields
   - sanity_failure_reasons

5. 如果 compile-ir 初始建档没有 run_id / metrics 等字段，请确认是否应显示 sanity_check_failed。
   如果显示 passed，则说明 sanity 规则错误。
   如果什么状态都没有，说明 005I 未进入 live archive 主链路。

6. 如果发现后端未重启、读错路径、或 compile-ir 没走新函数，请修复到 live 路径可见为止。
   修复后重新执行第 3-4 步。

7. 输出一份验证报告：
   - 结论只能是 live_verified_passed / live_verified_failed / inconclusive 三选一；
   - 附 strategy_id；
   - 附 archive 文件路径；
   - 附关键 markdown 摘录；
   - 附当前后端代码路径与知识库路径；
   - 明确是否可以验收 005I；
   - 明确是否允许恢复 005B Round 5。

注意：
- 不要只说单测通过。
- 不要只检查旧 archive。
- 不要改动 005B。
- 不要启动研究。
- 不要调用 231 标的大回测。
```

---

# 4. 你要重点看项目AI的下一次回复

它下一次回复里，必须出现这些证据：

## 必须有一个新 strategy_id

例如：

```text
strategy_id = ir_005i_live_verify_xxx
```

如果它还在看旧 archive，那不算。

## 必须有真实文件路径

例如：

```text
data/knowledge/strategies/ir_005i_live_verify_xxx.md
```

并且要确认 `/knowledge/strategies/{id}` 读的就是这个文件。

## 必须有 markdown 摘录

至少应该看到类似：

```markdown
## 档案元数据 JSON

```json
{
  "strategy_id": "...",
  "universe": ["600519.SH"],
  "sanity_status": "sanity_check_failed",
  "sanity_missing_fields": ["run_id", "metrics", "train_metrics", "test_metrics", "phase_stats"],
  ...
}
```
```

如果初始 compile-ir 后还没有回测，这时状态应该大概率是 `sanity_check_failed`，因为 `run_id / metrics / train_metrics / test_metrics / phase_stats` 尚未回填。

## 如果没有这些，005I 就没过

不管单测多少 passed，都不能验收。

---

# 5. 如果最后验证失败，怎么处理？

如果项目AI确认 live failed，则新开或重开一个修复工单：

`TKT-2026-005I-R1-live-archive-sanity-fix.md`

目标非常窄：

> 让 `/strategy-builder/compile-ir → create_strategy_archive → /knowledge/strategies/{id}` 这条 live 路径实际产出 `## 档案元数据 JSON` 与 sanity 状态。

验收标准：

1. 新 compile-ir archive 初始状态能看到 `sanity_check_failed`；
2. 回测 append 后能变成 `passed`；
3. `/knowledge/strategies/{id}` 能读到同一状态；
4. `kb_query archive` 能读到同一状态；
5. 旧 archive 不要求 retroactive 改写。

---

# 6. 如果验证通过，怎么办？

如果发现项目AI之前看的只是旧 archive，而新的 live archive 正常，那就可以：

1. 验收 005I；
2. 追加一条 005I 验证记录；
3. 恢复 005B Round 5 执行前检查；
4. 继续单变量趋势过滤实验。

---

# 总结

现在的正确动作是：

> **冻结 005B，暂停 005I 验收，要求项目AI做 005I live path verification。**

这不是倒退，而是非常重要的工程治理节点。  
因为我们正在从“代码说它做了”转向“运行时证据证明它做了”。只有这个证据成立，`strategy_researcher` 后续产出的研究档案才值得信任。

