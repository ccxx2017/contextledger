# validate_v2 · 独立验收集（评审 §四.2）

## 状态：未收集（收集规范先行落盘，防止边收边调）

## 用途

给 lifecycle 实现（工作包 B）与 readiness 声明（工作包 C）一个**诚实的泛化数字**。
seal 的 blind_holdout（2 条）继续封存；本集合是其可用替代：
规模够大（6–8 条）、且用完不消耗封存集。

## 收集纪律（在收集第一条轨迹之前确认）

1. **来源**：未参与任何 v1/v2/v3 规则调参的真实会话；不得从既有 17 条轨迹
   改名、改实体、改数值派生（模板泄漏检测同 v1_freeze）。
2. **按整条轨迹划分**：一个案例的轨迹与 gold 整体进或整体不进，不做事件级随机拆分。
3. **判据先于数据**：gold 标注规则沿用 phase05_v3 的 gold schema；
   若需修订 gold 规则，先在 development 集验证、再重标本集，禁止看完结果改 gold。
4. **一次性使用**：本集合在 B 收口与 C 收口各跑一次；第二次跑完后即转为历史结果，
   不得再作为泛化证据反复引用。
5. **覆盖要求**：6–8 条中至少包含——单流推进 1、同键不同 state_slot 共存 1、
   任务改派（编码视角）1、晚到旧工具结果 1、revival 1、provenance 冲突 1、非失效 decoy 1。
6. **入库**：每条轨迹 + gold 落 `trajectories/`、`gold/`；collect 完成后生成
   `validate_v2_manifest.json`（逐文件 sha256，格式同 v1_freeze），生成后集合冻结。

## 运行方式（集合冻结后）

```bash
python graph/scripts/score_phase05.py --project-dir graph/projects/abu_modern/benchmark/validate_v2
```

结果与 v1_freeze 的 baselines 对照，双分母（submitted_only / all_inputs）并报。
