# Phase 0.5 v2 与 v1 对比

## 样本规模

- v1：`23` 条轨迹，以 synthetic 为主。
- v2：`17` 条轨迹，其中 real=`8`、synthetic=`9`，覆盖 `19` 个槽位。
- 备注：v2 的目标不是“更多条数”，而是把真实 abu_modern 轨迹拉进基准，并把 synthetic 只保留给真实数据缺失的类别。

## 关键指标对比

### phase0_current

- invalidation precision：v1=`0.316` -> v2=`0.500`
- invalidation recall：v1=`0.500` -> v2=`0.474`
- active-set Set-F1：v1=`0.850` -> v2=`0.848`
- must_include recall：v1=`0.827` -> v2=`0.878`
- valid-time accuracy：v1=`0.500` -> v2=`0.000`

### flat_rag

- invalidation precision：v1=`0.000` -> v2=`0.000`
- invalidation recall：v1=`0.000` -> v2=`0.000`
- active-set Set-F1：v1=`0.850` -> v2=`0.848`
- must_include recall：v1=`0.827` -> v2=`0.878`
- valid-time accuracy：v1=`0.500` -> v2=`0.000`

## 读法

- v2 把 real full / provenance / revival 样本拉进来后，`invalidation precision` 明显提高，说明当前基线对“是否该判失效”这件事的保守性更接近真实链。
- `partial`、`conditional` 在 v2 仍是 `recall=0`，符合“已知 schema 缺口要被诚实暴露”的预期。
- `revival recall` 从 v1 的 `0.500` 降到 v2 的 `0.167`，说明真实 revival 链比 v1 synthetic 更难，当前 schema 在真实回滚/复活场景下更脆弱。
- `valid-time accuracy` 降到 `0.000`，原因不是回归，而是 v2 的 out_of_order 只保留了 `observed_at` 在场的迟到样本，去掉了 fallback 可工作的宽松样本后，真实缺口被完整暴露。

## 结论

- v2 更接近“真实链条 + 必要 synthetic 补洞”的 benchmark 形态。
- 当前最硬的缺口仍是：`partial`、`conditional`、`revival`、`observed_at 在场的 out_of_order`。
- 下一步应基于 v2 报告推进 schema / adjudication 设计，而不是继续扩充 synthetic 数量。
