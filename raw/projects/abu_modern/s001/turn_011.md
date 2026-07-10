# 用户：
Windows 后端的实际可达地址是http://192.168.1.136:8000
# Claude Opus4.7:
## TKT-2026-004 工单 + 3 份脚本代码

所有未知数闭合。下面是可以直接交给项目 AI 执行的完整工单，以及 3 份脚本的完整代码（脚本建议你先读一遍再交付，因为它们承载了上文讨论的所有设计决策）。

---

## 一、工单正文（可直接粘贴给 Ubuntu 侧项目 AI）

### TKT-2026-004：strategy-researcher Agent HTTP 适配脚本（3 个）

**背景**：strategy-researcher 运行在 Ubuntu 工作站，quant_trade_system 后端运行在 Windows 工作站（`http://192.168.1.136:8000`）。本工单产出 3 个 HTTP 薄封装脚本，让 Agent 的研究循环通过 HTTP 消费后端能力。

**交付物**：

```
strategy-researcher/
├── scripts/
│   ├── call_builder.py      # 调用 /strategy-builder/invoke
│   ├── call_backtest.py     # 调用 /backtests/execution-config
│   └── kb_query.py          # 调用 /api/v1/knowledge/*
└── README.md                # 更新：新增"HTTP 脚本使用"章节
```

**通用约定**：

1. **后端地址**：默认 `http://192.168.1.136:8000`，可通过环境变量 `QUANT_BACKEND_URL` 覆盖。
2. **输入**：所有脚本从 stdin 读 JSON 或从 `--arg` 读参数，具体见下。
3. **输出**：统一 `{"ok": true, ...}` / `{"ok": false, "error": "...", "detail": {...}}` 到 stdout，退出码 0（成功）/ 1（可重试错误）/ 2（不可恢复错误）。
4. **超时**：默认 300 秒（回测可能较长），可通过 `--timeout` 覆盖。
5. **依赖**：仅用 Python 标准库 `urllib` + `json` + `argparse`，不引入 `requests`（减少 Ubuntu 侧依赖安装负担）。

**验收标准**：

- 3 个脚本在 Ubuntu 上用 `python3 scripts/<name>.py --help` 能看到帮助。
- `call_backtest.py` 在遇到 `DATA_MISSING_SYNC_REQUIRED` 时自动剔除 missing_symbols 后重试一次，仍失败才返回错误。
- `kb_query.py` 支持 `index / log / archive <id> / archives` 四个子命令，都直接透传 markdown 字符串。
- 连通性失败（ConnectionError / Timeout）时退出码为 1（可重试），业务错误（400 / 404）时退出码为 2。
- 提供 `scripts/smoke_http_clients.sh` 在假设后端可达的前提下跑一遍 happy path。

---

## 二、三份脚本完整代码

### `scripts/call_builder.py`

```python
#!/usr/bin/env python3
"""Call /strategy-builder/invoke on the quant backend.

Input (stdin, JSON): the request body expected by the builder endpoint.
Output (stdout, JSON): {"ok": bool, "data"|"error": ..., "status": int}
Exit codes: 0 success, 1 retryable (network), 2 business error.
"""
from __future__ import annotations
import argparse, json, os, sys, urllib.request, urllib.error

DEFAULT_BASE = os.environ.get("QUANT_BACKEND_URL", "http://192.168.1.136:8000")
ENDPOINT = "/strategy-builder/invoke"


def main() -> int:
    ap = argparse.ArgumentParser(description="Invoke strategy-builder via HTTP.")
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--input-file", help="Read JSON body from file instead of stdin.")
    args = ap.parse_args()

    raw = open(args.input_file, "r", encoding="utf-8").read() if args.input_file else sys.stdin.read()
    try:
        body = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": "invalid_json_input", "detail": str(e)}))
        return 2

    url = args.base_url.rstrip("/") + ENDPOINT
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            print(json.dumps({"ok": True, "status": resp.status, "data": payload}, ensure_ascii=False))
            return 0
    except urllib.error.HTTPError as e:
        detail_raw = e.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(detail_raw)
        except json.JSONDecodeError:
            detail = {"raw": detail_raw}
        print(json.dumps({"ok": False, "error": f"http_{e.code}", "status": e.code, "detail": detail}, ensure_ascii=False))
        return 2
    except (urllib.error.URLError, TimeoutError) as e:
        print(json.dumps({"ok": False, "error": "network_error", "detail": str(e)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

### `scripts/call_backtest.py`

```python
#!/usr/bin/env python3
"""Call /backtests/execution-config with automatic retry on DATA_MISSING_SYNC_REQUIRED.

Input (stdin, JSON): {"execution_config": {...}, "run_id": "optional"}
Output (stdout, JSON): {"ok": bool, "run_id": "...", "status": "completed", "retried": bool, ...}
Exit codes: 0 success, 1 retryable (network), 2 business error.

Behavior:
- On HTTP 200, extract data.run_id / data.status and return.
- On HTTP 400 with code=DATA_MISSING_SYNC_REQUIRED, remove missing_symbols from
  execution_config.universe.symbols and retry ONCE. If still failing, return error.
- Other 400 codes (INVALID_EXECUTION_CONFIG / UNSUPPORTED_UNIVERSE_TYPE / EMPTY_UNIVERSE)
  are surfaced immediately so the caller LLM can revise the hypothesis.
"""
from __future__ import annotations
import argparse, json, os, sys, urllib.request, urllib.error
from typing import Any

DEFAULT_BASE = os.environ.get("QUANT_BACKEND_URL", "http://192.168.1.136:8000")
ENDPOINT = "/backtests/execution-config"


def _post(base_url: str, body: dict, timeout: float) -> tuple[int, dict]:
    url = base_url.rstrip("/") + ENDPOINT
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail_raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(detail_raw)
        except json.JSONDecodeError:
            return e.code, {"raw": detail_raw}


def _prune_universe(body: dict, missing: list[str]) -> dict:
    """Return a deep-enough copy with missing symbols removed from universe.symbols."""
    import copy
    pruned = copy.deepcopy(body)
    try:
        symbols = pruned["execution_config"]["universe"]["symbols"]
        pruned["execution_config"]["universe"]["symbols"] = [s for s in symbols if s not in set(missing)]
    except (KeyError, TypeError):
        pass
    return pruned


def _summarize_success(payload: dict, retried: bool) -> dict:
    data = payload.get("data", {}) if isinstance(payload, dict) else {}
    return {
        "ok": True,
        "retried": retried,
        "run_id": data.get("run_id"),
        "task_id": data.get("task_id"),
        "status": data.get("status"),
        "message": payload.get("message"),
        "raw": payload,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Invoke execution-config backtest via HTTP.")
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    ap.add_argument("--timeout", type=float, default=600.0)
    ap.add_argument("--input-file", help="Read JSON body from file instead of stdin.")
    ap.add_argument("--no-retry-on-missing-data", action="store_true",
                    help="Disable automatic retry after pruning missing_symbols.")
    args = ap.parse_args()

    raw = open(args.input_file, "r", encoding="utf-8").read() if args.input_file else sys.stdin.read()
    try:
        body = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": "invalid_json_input", "detail": str(e)}))
        return 2

    try:
        status, payload = _post(args.base_url, body, args.timeout)
    except (urllib.error.URLError, TimeoutError) as e:
        print(json.dumps({"ok": False, "error": "network_error", "detail": str(e)}))
        return 1

    if status == 200 and isinstance(payload, dict) and payload.get("success"):
        print(json.dumps(_summarize_success(payload, retried=False), ensure_ascii=False))
        return 0

    # HTTP 400 branch: inspect error code
    code = payload.get("code") if isinstance(payload, dict) else None
    if status == 400 and code == "DATA_MISSING_SYNC_REQUIRED" and not args.no_retry_on_missing_data:
        missing = payload.get("missing_symbols") or []
        if missing:
            pruned = _prune_universe(body, missing)
            remaining = pruned.get("execution_config", {}).get("universe", {}).get("symbols", [])
            if not remaining:
                print(json.dumps({
                    "ok": False, "error": "empty_universe_after_prune",
                    "status": 400, "missing_symbols": missing, "detail": payload,
                }, ensure_ascii=False))
                return 2
            try:
                status2, payload2 = _post(args.base_url, pruned, args.timeout)
            except (urllib.error.URLError, TimeoutError) as e:
                print(json.dumps({"ok": False, "error": "network_error_on_retry", "detail": str(e)}))
                return 1
            if status2 == 200 and isinstance(payload2, dict) and payload2.get("success"):
                summary = _summarize_success(payload2, retried=True)
                summary["pruned_symbols"] = missing
                print(json.dumps(summary, ensure_ascii=False))
                return 0
            print(json.dumps({
                "ok": False, "error": "retry_failed", "status": status2,
                "pruned_symbols": missing, "detail": payload2,
            }, ensure_ascii=False))
            return 2

    # Any other non-success
    print(json.dumps({
        "ok": False, "error": f"http_{status}", "status": status,
        "code": code, "detail": payload,
    }, ensure_ascii=False))
    return 2


if __name__ == "__main__":
    sys.exit(main())
```

### `scripts/kb_query.py`

```python
#!/usr/bin/env python3
"""Query the knowledge base HTTP API.

Subcommands:
  index                  -> GET /api/v1/knowledge/index
  log                    -> GET /api/v1/knowledge/log
  archives               -> GET /api/v1/knowledge/archives
  archive <strategy_id>  -> GET /api/v1/knowledge/archives/<id>

Output (stdout, JSON):
  index / log / archive -> {"ok": true, "content": "<markdown>"}
  archives              -> {"ok": true, "archives": [{...}, ...]}
  errors                -> {"ok": false, "error": "...", "status": int, "detail": ...}
Exit codes: 0 success, 1 retryable (network), 2 business error (incl. 404).
"""
from __future__ import annotations
import argparse, json, os, sys, urllib.request, urllib.error, urllib.parse

DEFAULT_BASE = os.environ.get("QUANT_BACKEND_URL", "http://192.168.1.136:8000")
PREFIX = "/api/v1/knowledge"


def _get(base_url: str, path: str, timeout: float) -> tuple[int, object]:
    url = base_url.rstrip("/") + path
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail_raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(detail_raw)
        except json.JSONDecodeError:
            return e.code, {"raw": detail_raw}


def main() -> int:
    ap = argparse.ArgumentParser(description="Knowledge-base HTTP client.")
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    ap.add_argument("--timeout", type=float, default=30.0)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("index")
    sub.add_parser("log")
    sub.add_parser("archives")
    p_arch = sub.add_parser("archive")
    p_arch.add_argument("strategy_id")
    args = ap.parse_args()

    if args.cmd == "index":
        path = f"{PREFIX}/index"
    elif args.cmd == "log":
        path = f"{PREFIX}/log"
    elif args.cmd == "archives":
        path = f"{PREFIX}/archives"
    elif args.cmd == "archive":
        path = f"{PREFIX}/archives/{urllib.parse.quote(args.strategy_id, safe='')}"
    else:
        print(json.dumps({"ok": False, "error": "unknown_subcommand"}))
        return 2

    try:
        status, payload = _get(args.base_url, path, args.timeout)
    except (urllib.error.URLError, TimeoutError) as e:
        print(json.dumps({"ok": False, "error": "network_error", "detail": str(e)}))
        return 1

    if status == 200:
        if args.cmd == "archives":
            print(json.dumps({"ok": True, "archives": payload}, ensure_ascii=False))
        elif args.cmd == "archive":
            # archive endpoint returns a dict {strategy_id, content, file_path}
            content = payload.get("content") if isinstance(payload, dict) else None
            print(json.dumps({
                "ok": True,
                "strategy_id": payload.get("strategy_id") if isinstance(payload, dict) else None,
                "content": content,
                "file_path": payload.get("file_path") if isinstance(payload, dict) else None,
            }, ensure_ascii=False))
        else:
            # index / log endpoints return a raw markdown string
            print(json.dumps({"ok": True, "content": payload}, ensure_ascii=False))
        return 0

    print(json.dumps({"ok": False, "error": f"http_{status}", "status": status, "detail": payload},
                     ensure_ascii=False))
    return 2


if __name__ == "__main__":
    sys.exit(main())
```

### `scripts/smoke_http_clients.sh`

```bash
#!/usr/bin/env bash
# Happy-path smoke test for the 3 HTTP client scripts.
# Requires backend reachable at $QUANT_BACKEND_URL (default 192.168.1.136:8000).
set -euo pipefail
cd "$(dirname "$0")/.."
BASE="${QUANT_BACKEND_URL:-http://192.168.1.136:8000}"
echo "== Backend: $BASE =="

echo "-- kb_query index --"
python3 scripts/kb_query.py --base-url "$BASE" index | head -c 400 ; echo

echo "-- kb_query archives --"
python3 scripts/kb_query.py --base-url "$BASE" archives | head -c 400 ; echo

echo "-- kb_query archive (expect 404 for fake id) --"
set +e
python3 scripts/kb_query.py --base-url "$BASE" archive nonexistent-xxx
rc=$?
set -e
[ "$rc" = "2" ] && echo "404 surfaced correctly (exit 2)" || { echo "unexpected rc=$rc"; exit 1; }

echo "-- kb_query log --"
python3 scripts/kb_query.py --base-url "$BASE" log | head -c 400 ; echo

echo "All smoke checks passed."
```

---

## 三、交付给项目 AI 时给它的话

> 请按 TKT-2026-004 实施。代码已在工单中给出完整版本，你需要：
> 
> 1. 把 3 个 `.py` 和 1 个 `.sh` 放到 `strategy-researcher/scripts/` 下，`.sh` 记得 `chmod +x`。
> 2. 在仓库根 `README.md` 新增"HTTP 脚本"一节，说明 3 个脚本的用途、默认后端地址、`QUANT_BACKEND_URL` 覆盖方式、输入/输出约定、退出码语义。
> 3. 跑一次 `bash scripts/smoke_http_clients.sh`，把输出贴回交付总结。
> 4. 交付总结额外报告：在 Windows 后端**未启动**时 3 个脚本的退出码是否都是 1（验证网络错误分支）。

---

## 四、等你收到项目 AI 回执后，我们的下一步

脚本落地后，strategy-researcher 的**研究循环主体**（Agent 的 prompt + 状态机）就是下一个主工单 TKT-2026-005。在写那个之前，我想先跟你聊一轮**研究循环的控制结构**——是每次让 Agent 跑完整一圈（假设→构建→回测→复盘→归档）就停，等你手动 review 后再触发下一圈；还是让它连续跑 N 圈后一起给你看？这个决策会影响 Agent 的 prompt 设计，不急，等你有时间我们再讨论。

