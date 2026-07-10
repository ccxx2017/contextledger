# 用户：
我把TKT-2026-005B附件(TKT-2026-005B-vcp-breakout-entry.md)给你，它现在在blocked文件夹中，我直接把它交给项目AI去实施吗？
# GPT5.5:
不建议**直接把 005B 交给项目AI去实施研究**。

原因很简单：

> **005B 是 investigation 工单，实施主体应该是 `agent-strategy-researcher`，不是项目AI。**  
> 项目AI只能做“恢复前补丁/工单修正/技能文档同步”，不能代替研究员执行研究。

现在正确路径是：

## 结论

你应该分两步走：

1. **先让项目AI做 005B 恢复补丁**  
   只改工单状态、补充恢复条件、修正调用新接口的要求，不执行研究、不调用 builder/backtest。

2. **再把恢复后的 005B 派给 strategy-researcher 做受限研究 smoke**  
   由飞书数字员工按 `research_workflow.md` 执行。

---

## 项目AI现在应该做什么？

让项目AI执行一个很小的“行政恢复补丁”，不是研究执行。

### 需要改 005B 的内容

1. **修正 frontmatter**
   现在里面还是：

```yaml
ticket_id: TKT-2026-00X
```

应改为：

```yaml
ticket_id: TKT-2026-005B
```

报告名也从：

```text
TKT-2026-00X-vcp-breakout-entry.md
```

改成：

```text
TKT-2026-005B-vcp-breakout-entry.md
```

2. **从 blocked 移回 open**

```text
aos/runtime/tickets/blocked/TKT-2026-005B...
```

移回：

```text
aos/runtime/tickets/open/TKT-2026-005B...
```

3. **状态改为**

```yaml
status: ready_for_limited_resume
```

4. **追加 Boss Worklog**

说明：

- `TKT-2026-005C` 已完成资源闸；
- `TKT-2026-005D` 已完成 auto research 专用接口；
- `TKT-2026-005E` 技术 E2E smoke 已通过；
- 允许进入 **受限恢复 smoke**，不是完整研究。

5. **新增恢复硬约束**

必须写清楚：

- 从 **Round 4** 开始，不要重跑 Round 1/2/3；
- 必须使用新接口：

```text
/strategy-builder/compile-ir
```

- `call_builder.py` 必须带：

```bash
--endpoint /strategy-builder/compile-ir
```

- 禁止使用旧接口：

```text
/strategy-builder/invoke
```

- 第一轮恢复仍然限制：
  - symbols ≤ 5
  - years ≤ 1
  - timeout = 90s
- 后端 5xx / 超时 / 连接失败一次即暂停；
- 禁止自动重试；
- 禁止 231 标的大回测；
- 受限 smoke 结果不能作为完整研究结论。

---

## 给项目AI的指令可以这样写

你可以直接发：

```text
请只对 TKT-2026-005B 做恢复前补丁，不执行研究，不调用 builder/backtest/kb_query，不调用任何 scripts，不产生网络请求。

目标：
1. 将 ticket_id 从 TKT-2026-00X 修正为 TKT-2026-005B。
2. 将报告名修正为 TKT-2026-005B-vcp-breakout-entry.md。
3. 将工单从 blocked 移回 open。
4. 将 status 改为 ready_for_limited_resume。
5. 在 Worklog 追加 Boss 授权记录：
   - TKT-2026-005C 资源闸已完成；
   - TKT-2026-005D auto research 编译接口已完成；
   - TKT-2026-005E 技术 E2E smoke 已通过；
   - 允许进入受限恢复 smoke，但不是完整研究恢复。
6. 明确恢复时从 Round 4 开始。
7. 明确 strategy-researcher 必须调用 call_builder.py --endpoint /strategy-builder/compile-ir。
8. 明确禁止旧 /strategy-builder/invoke。
9. 保留 symbols≤5、years≤1、timeout=90s、失败一次即暂停、禁止自动重试、禁止 231 标的大回测等限制。
10. 完成后只提交工单修改，不运行任何研究流程。

输出：
- 实际读取了哪些 .md 文件；
- 是否调用 scripts/ 下脚本；
- 最高行为手册是哪一个；
- 修改了哪些文件；
- git diff 摘要。
```

---

## 然后才派给 strategy-researcher

项目AI补丁完成后，再通过飞书派发给 `agent-strategy-researcher`。

派发前让它先做正式执行前检查，必须输出：

1. 本次实际读取了哪些 `.md` 文件；
2. 是否调用了任何 `scripts/` 下脚本；
3. 最高行为手册是哪一个；
4. 正式执行必须遵循哪些 Phase；
5. 是否满足正式执行条件；
6. 本轮资源预算；
7. 本轮是否确认使用 `/strategy-builder/compile-ir`。

---

## 最重要的提醒

如果现在直接把 blocked 里的 005B 丢给项目AI“实施”，容易再次混淆：

```text
项目AI = 修后端/修工单/修工具
strategy-researcher = 执行研究
```

所以正确做法是：

```text
项目AI先修复并恢复005B状态
→ Boss确认
→ 飞书派给strategy-researcher执行受限Round 4 smoke
```

不要让项目AI直接代跑 005B 研究。
