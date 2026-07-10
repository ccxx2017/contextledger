# 用户：
附件(TKT-2026-005B-vcp-breakout-entry.md)是修改后的TKT-2026-005B，现在你觉得可以将它交给feishu端的strategy_researcher去实施了吗？
# GPT5.5:
可以，**现在可以交给飞书端 `strategy_researcher` 执行**，但只能执行：

> **TKT-2026-005B Round 4 受限恢复 smoke**  
> 不是完整研究恢复。

这版工单已经满足关键条件：

- `ticket_id` 已修正为 `TKT-2026-005B`
- `assigned_to: agent-strategy-researcher`
- `intent_type: investigation`
- `status: ready_for_limited_resume`
- 已写明 `005C / 005D / 005E` 均完成
- 已明确从 **Round 4** 开始
- 已强制使用 `/strategy-builder/compile-ir`
- 已禁止旧 `/strategy-builder/invoke`
- 已保留 `symbols≤5 / years≤1 / timeout=90s / 失败一次暂停`

## 但派发前确认两个实际条件

1. 后端已部署并重启到包含 `005D/005E` 修改的版本。  
2. Ubuntu/OpenClaw 技能目录里的 `call_builder.py` 已是支持 `--endpoint` 的版本。

如果这两项也确认了，就可以派。

## 建议飞书指令

先不要让它直接跑，先让它做执行前检查：

```text
请对 TKT-2026-005B 执行正式恢复前检查，但暂不调用 builder/backtest/kb_query，不执行任何 scripts。

这是一次 Round 4 受限恢复 smoke，不是完整研究恢复。

请输出：
1. 本次你实际读取了哪些 .md 文件；
2. 你是否调用了任何 scripts/ 下的脚本；
3. 哪个文件是最高行为手册；
4. 正式执行时必须遵循哪些 Phase；
5. 是否已经满足正式执行条件；
6. 本轮资源预算；
7. 是否确认必须使用 call_builder.py --endpoint /strategy-builder/compile-ir；
8. 是否确认禁止使用 /strategy-builder/invoke；
9. 是否确认从 Round 4 开始，不重跑 Round 1/2/3。
```

它检查通过后，你再发第二条：

```text
确认执行 TKT-2026-005B Round 4 受限恢复 smoke。

硬限制：
- symbols ≤ 5
- years ≤ 1
- timeout = 90s
- 必须使用 call_builder.py --endpoint /strategy-builder/compile-ir
- 禁止 /strategy-builder/invoke
- 后端 5xx / 超时 / 连接失败一次即暂停
- 禁止自动重试
- 禁止 231 标的大回测
- 受限 smoke 结果不得作为完整研究结论
```

结论：**可以派给 Feishu 端 strategy_researcher，但必须按“先检查、再授权执行”的两步走。**
