# 用户：
我想问下，我们是应该是采取限制措施还是重新改造后端的措施呢？
# Claude Opus4.7:
*Thinking...*

>  I'm weighing whether to implement restrictive measures like capping symbols or redesigning the backend architecture. This is fundamentally a tradeoff between quick constraints versus a more robust long-term solution.
> 
> The real answer is doing both, but sequenced differently. I need immediate restrictions to stabilize the system—capping agent behavior and adding timeouts in scripts—while planning backend improvements like async job queues and resource isolation for the medium term. Restricting alone means the research system never reaches its full potential, but only redesigning means the agent keeps crashing the backend while we wait for the fix. So the path forward is: apply limits today to stop the bleeding, add backend timeout and cancellation logic within a couple weeks, then move toward true async architecture afterward.

**两个都要做，但有先后顺序。只做一边都不行。**

## 短答

**先限制，再改造。** 不是二选一。

## 为什么不能只限制

只加限制等于把 quant 系统永远关在小笼子里：

- 5-20 标的、1-2 年的回测，做不了真正的策略研究；
- 每个工单都要 Boss 手动放行大 universe；
- 根因（后端没有超时/取消/隔离）一直在，下一次只要 agent 或人手抖一下，照样打挂。

## 为什么不能只改造后端

后端改造至少 1-2 周。这期间：

- agent 还会继续打大请求；
- 后端还会继续被打挂；
- Ticket B / C / D 全部跑不动；
- 你每天都要重启后端。

## 建议的顺序

### 第 1 天（止血，必须做）

agent + 脚本侧加硬限制：

- `call_backtest.py` 默认 `max_symbols ≤ 20`、`max_years ≤ 3`；
- 超过阈值必须 Boss 授权 token；
- 单请求超时 ≤ 90s；
- backend 非响应 1 次即 `paused_for_boss_review`，不准重试。

这一步只是为了让 Ticket B 这周能跑起来。

### 第 1-2 周（根治后端）

后端必须加四件事，缺一不可：

1. **请求级超时**：FastAPI handler 超时即返回 `408`，不允许无限阻塞。
2. **回测异步化**：回测走 job queue（Celery / RQ / 自建），HTTP 只返回 `run_id`，agent 用 `GET /runs/{id}` 轮询。
3. **取消接口**：`POST /runs/{id}/cancel`，能真正杀掉子进程。
4. **并发隔离**：单用户/单 agent 的回测 worker 限并发 1-2，避免一个大请求阻塞所有人。

### 第 3 周起（可放开限制）

后端能扛住后，再把 agent 侧的硬限制改成软限制（警告 + 默认值，可被 Boss 覆盖）。

## 一句话结论

**先用限制把出血点压住，再用后端改造把伤口缝好。** 跳过限制直接改造，期间会一直流血；跳过改造只做限制，等于永久残疾。

如果你只能做一件事，选**限制**——因为它今天能落地，而且为后端改造争取时间。

