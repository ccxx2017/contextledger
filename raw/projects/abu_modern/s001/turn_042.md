# 用户：
@Gemini-3.5-Flash 好的，为了让你能够了解全貌，我给你提供了附件(修正员工实施中.md)背景信息，请你给出新的执行工单的内容，我将会让项目AI去实施，为了让项目AI能够能够的实施，你可以增加一些实施的背景信息。
# Gemini-3.5-Flash:
为了让你的项目 AI（如 Claude Code 或其他后端开发智能体）能够**零歧义、高质量地一次性完成**双接口分流与工具契约修复，我们需要为它量身定制一份具备“严格前置检查、防御性编程、明确读写边界与可验证路径”的工程实施工作单。

以下是为你起草的 **`TKT-2026-005D-auto-research-builder-api`** 完整工单。这份工单不仅包含了接口的改动，还融入了你系统特有的四层正交结构、安全护栏以及严格的验收路径。

---

# 工单：TKT-2026-005D-auto-research-builder-api

## 1. Frontmatter (工单元数据)
```yaml
ticket_id: TKT-2026-005D
title: 新增自动研究编译接口与修复回测异常序列化契约
status: open
assigned_to: project-ai-backend-developer  # 实施主体：项目AI/后端开发者 (非 strategy-researcher)
intent_type: infrastructure_patch
priority: P0
created_at: 2026-05-20
deadline: 2026-05-23
```

---

## 2. 背景与上下文 (Context)
在 `TKT-2026-005B` 的首次受限 Smoke Run 中，系统暴露了两个致命的工具契约缺陷，直接导致了自动研究员（`strategy-researcher`）的执行失败：
1. **Builder 交互式会话僵死**：现有的 `POST /strategy-builder/invoke` 接口是为人类交互和 `quant_assistant` 设计的，包含多轮追问机制（`pending_user_input`）。当自动研究员提交不完美的 IR 时，Builder 试图进行多轮会话，导致 Agent 陷入死循环。
2. **Backtest 500 异常未序列化**：当回测发生内部错误时，后端直接抛出 Python 异常（如 `ValueError`），导致 FastAPI 尝试序列化该 Exception 对象，触发 `TypeError: ValueError is not JSON serializable`，最终向客户端返回了非结构化的 HTTP 500 崩溃响应。

### 核心决策：双通道分流
为了不破坏人类在飞书端交互微调的灵活性，同时给自动研究员提供一个“无状态、单次提交、非交互”的编译环境，我们决定**不修改原有交互接口**，而是**新建一个 Auto Research 专用编译接口**，并彻底重构后端的错误捕获与响应契约。

---

## 3. 实施范围 (In Scope)

### 任务 3.1：新增非交互式编译端点 `POST /strategy-builder/compile-ir`
在后端路由中新增一个专为 `strategy-researcher` 服务的端点，其行为契约必须是**无状态且非交互**的：
* **请求格式**：
  * **Method**: `POST`
  * **Path**: `/strategy-builder/compile-ir`
  * **Payload (JSON)**: 必须包含完整的 `strategy_ir` 对象，以及可选的元数据。
    ```json
    {
      "strategy_ir": {
        "strategy_name": "VCP_Breakout_v1",
        "universe": ["600519.SH", "000001.SZ"],
        "phases": [...],
        "transitions": [...]
      },
      "metadata": {
        "ticket_id": "TKT-2026-005B",
        "round": 3
      }
    }
    ```
* **核心行为规则**：
  1. **禁止多轮追问**：无论 IR 校验是否通过，**绝对禁止**返回 `pending_user_input` 状态，禁止保存或依赖 Session 状态。
  2. **单次判定**：后端接收到请求后，立即调用 `knowledge_base.py` 相关的编译与校验逻辑。
  3. **自动落库（KB 写入桥）**：如果编译成功，后端必须在响应返回前，在侧作用域中自动调用 `create_strategy_archive()` 将策略写入 `data/knowledge/strategies/` 目录，并更新索引。
  4. **暂时关闭自动回测**：在此接口中，即使 `auto_backtest=true`，也应暂时将其硬编码为 `false`，回测必须由 Agent 侧的 `call_backtest.py` 显式触发，以隔离排障。
* **成功响应 (200 OK)**：
  ```json
  {
    "success": true,
    "strategy_id": "stg_20260520_xxxxxx",
    "compiler_status": "compiled",
    "archive_created": true,
    "warnings": []
  }
  ```
* **失败响应 (400 Bad Request)**：
  ```json
  {
    "success": false,
    "error": {
      "code": "IR_COMPILE_FAILED",
      "message": "因子定义或语法校验未通过",
      "field_errors": [
        {"field": "strategy_ir.phases[0].indicators", "reason": "因子不在注册表中"}
      ]
    }
  }
  ```

### 任务 3.2：修复 Backtest 500 异常序列化契约
重构回测接口（`POST /backtests/execution-config`）及全局异常处理器，确保任何后端崩溃都不会向客户端透传非 JSON 序列化的 Python 异常对象：
1. **全局异常捕获**：在 FastAPI 中注册全局异常 Handler，捕获所有的 `Exception`、`ValueError`、`KeyError` 等。
2. **统一 JSON 契约**：当发生未捕获异常时，统一返回 HTTP 400 或 500 状态码，且 Body 必须为标准结构化 JSON，格式如下：
  ```json
  {
    "success": false,
    "error": {
      "code": "BACKTEST_INTERNAL_ERROR",
      "message": "回测执行引擎发生未捕获异常: [异常简短描述]",
      "retryable": false
    }
  }
  ```
3. **禁止直接序列化 Exception**：在返回前，必须将 Exception 转换为 `str(e)` 或自定义的错误消息，严禁让 FastAPI 直接序列化异常实例本身。

---

## 4. 排除范围 (Out of Scope)
* **禁止**修改或破坏原有的交互式端点 `POST /strategy-builder/invoke` 的任何行为。
* **禁止**在此工单中实现后端异步队列（`POST /jobs`）——异步化留给 P1 阶段，本次仅修复同步模式下的契约与异常捕获。
* **禁止**修改 `strategy-researcher` 的 `SKILL.md` 或启动实际研究（本工单实施主体为开发 AI，不激活研究员 Agent）。

---

## 5. 严格执行前检查报告 (Pre-execution Checklist)
项目 AI 在开始编写代码前，**必须先读取并显式输出**以下检查报告：
1. **本次你实际读取了哪些 .md 文件**：(例如：`TKT-2026-005D.md`、`data/knowledge/schema.md`)
2. **你是否调用了任何 scripts/ 下的脚本**：(由于是后端开发任务，此时应回答“否”)
3. **哪个文件是最高行为手册**：(回答：`TKT-2026-005D-auto-research-builder-api.md` 本工单)
4. **正式执行时必须遵循哪些 Phase**：
   * **Phase 0**: 确认本地后端代码库处于最新分支。
   * **Phase 1**: 编写单元测试，复现 Backtest 500 序列化失败问题。
   * **Phase 2**: 实现 `POST /strategy-builder/compile-ir` 接口。
   * **Phase 3**: 重构全局异常处理器，修复序列化问题。
   * **Phase 4**: 运行本地测试，确保双接口分流且不互相干扰。
5. **是否已经满足正式执行条件**：(评估环境连通性与代码库只读访问，给出是/否结论)

---

## 6. 验收标准与验证路径 (Acceptance Criteria)

### 6.1 机械化代码审计
* 检查新端点 `/strategy-builder/compile-ir` 源码，确认其中没有任何读取 Session、返回 `pending_user_input` 或支持多轮对话的代码。
* 检查 FastAPI 异常处理器，确认所有 `except Exception as e` 分支中，返回的 JSON Payload 均不包含原始 Exception 对象，而是将其转化为字符串。

### 6.2 接口行为验证 (需提供 curl 运行日志)
1. **验证通道 A (旧接口不受影响)**：
   * 发送不完整请求至 `/strategy-builder/invoke`，验证其依然能返回 `pending_user_input` 并维持 Session。
2. **验证通道 B (新接口严格编译)**：
   * 提交一个合法的 `strategy_ir`，验证返回 `200 OK`，且 `archive_created` 为 `true`，在 `data/knowledge/strategies/` 下成功生成了对应的 markdown 档案。
   * 提交一个包含未知因子的非法 `strategy_ir`，验证其立即返回 `400 Bad Request` 和结构化 JSON 错误，**没有**进入多轮会话。
3. **验证异常序列化修复**：
   * 故意向回测端点发送一个会触发后端 `ValueError` 的极端请求，验证其返回合法的 JSON 格式错误（状态码 500 或 400），且不出现 `TypeError: ValueError is not JSON serializable` 报错。

---

## 7. 交付物清单 (Deliverables)
1. 后端新增端点 `/strategy-builder/compile-ir` 的实现代码。
2. 修复后的后端异常捕获与序列化模块代码。
3. 本地验证测试脚本或 `curl` 测试命令及其实际输出日志。
4. 在工单末尾追加 Worklog，记录修改的文件列表及测试通过证明。

