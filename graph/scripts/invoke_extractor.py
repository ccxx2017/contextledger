#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from build_extractor_prompt import (
    build_chat_messages,
    parse_turn_id,
)


DEFAULT_BASE_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-v4-flash"
DEFAULT_TIMEOUT_SECONDS = 120
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_RETRY_BACKOFF_SECONDS = 2


def candidate_env_paths(explicit_env_file: str | None) -> list[Path]:
    candidates: list[Path] = []
    if explicit_env_file:
        candidates.append(Path(explicit_env_file))

    candidates.extend(
        [
            Path(".env"),
            Path("env"),
            Path("graph") / "env",
        ]
    )

    seen: set[str] = set()
    unique: list[Path] = []
    for path in candidates:
        key = str(path.resolve()) if path.exists() else str(path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def choose_env_file(explicit_env_file: str | None) -> Path:
    for path in candidate_env_paths(explicit_env_file):
        if path.exists():
            return path
    return Path(explicit_env_file) if explicit_env_file else Path("graph") / "env"


def load_env_file(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def resolve_setting(name: str, env_file_values: dict[str, str], default: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value is not None and value != "":
        return value
    value = env_file_values.get(name)
    if value is not None and value != "":
        return value
    return default


def normalize_base_url(base_url: str) -> str:
    normalized = base_url.strip().rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    if normalized.endswith("/v1"):
        return normalized + "/chat/completions"
    if normalized.endswith("/chat"):
        return normalized + "/completions"
    return normalized


def choose_output_path(project_id: str, turn_id: str, out: str | None) -> Path:
    if out:
        return Path(out)

    turn_numeric = parse_turn_id(Path(turn_id)) if turn_id.startswith("turn") else None
    if turn_numeric is None:
        m = re.search(r"(\d+)$", turn_id)
        if m:
            turn_numeric = int(m.group(1))
    if turn_numeric is None:
        raise ValueError(f"无法从 turn_id 推断数字部分: {turn_id}")

    return Path("graph") / "projects" / project_id / "patches" / f"patch_{turn_numeric:03d}.json"


def strip_code_fence(text: str) -> str:
    stripped = text.strip()
    fenced = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", stripped, re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()
    return stripped


def parse_patch_response(raw_text: str) -> dict[str, Any]:
    text = strip_code_fence(raw_text)
    return json.loads(text)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def call_extractor(
    *,
    base_url: str,
    api_key: str,
    model: str,
    timeout_seconds: int,
    messages: list[dict[str, str]],
    max_attempts: int,
    retry_backoff_seconds: int,
) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    current_url = base_url

    attempt = 1
    raw = ""
    last_error: Exception | None = None
    while attempt <= max_attempts:
        req = urllib.request.Request(
            current_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
            break
        except urllib.error.HTTPError as exc:
            redirect_location = exc.headers.get("Location")
            if exc.code in {307, 308} and redirect_location:
                current_url = redirect_location
                last_error = exc
                if attempt >= max_attempts:
                    break
                time.sleep(retry_backoff_seconds * attempt)
                attempt += 1
                continue
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Extractor HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            last_error = exc
        except http.client.IncompleteRead as exc:
            if exc.partial:
                raw = exc.partial.decode("utf-8", errors="replace")
                break
            last_error = exc
        except http.client.RemoteDisconnected as exc:
            last_error = exc

        if attempt >= max_attempts:
            break
        time.sleep(retry_backoff_seconds * attempt)
        attempt += 1
    else:
        raw = ""

    if not raw:
        if last_error is None:
            raise RuntimeError("Extractor 返回空响应")
        raise RuntimeError(f"Extractor 网络错误: {last_error}") from last_error

    obj = json.loads(raw)
    choices = obj.get("choices") or []
    if not choices:
        raise RuntimeError("Extractor 响应缺少 choices")

    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        content = "".join(parts)

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Extractor 响应缺少 message.content")

    return content


def main() -> int:
    parser = argparse.ArgumentParser(description="调用 Extractor 模型并落盘 patch.json")
    parser.add_argument("--project-id", required=True, help="项目 ID")
    parser.add_argument("--turn-id", help="例如 turn_004")
    parser.add_argument("--slice", required=True, help="extractor_context_pack.json 路径")
    parser.add_argument("--turn", required=True, help="raw turn markdown 路径")
    parser.add_argument("--system", default=str(Path(__file__).resolve().parent.parent / "prompts" / "extractor_system.md"))
    parser.add_argument("--env-file", help="env 文件路径；缺省时自动查找 .env / env / graph/env")
    parser.add_argument("--out", help="patch.json 输出路径")
    parser.add_argument("--raw-response-out", help="原始模型响应输出路径")
    parser.add_argument("--prompt-out", help="prompt 快照输出路径")
    args = parser.parse_args()

    env_path = choose_env_file(args.env_file)
    env_values = load_env_file(env_path)

    api_key = resolve_setting("EXTRACTOR_API_KEY", env_values)
    if not api_key:
        print("ERROR: 缺少 EXTRACTOR_API_KEY", file=sys.stderr)
        print(f"INFO: 已尝试读取 env 文件: {env_path}", file=sys.stderr)
        return 2

    base_url = resolve_setting("EXTRACTOR_BASE_URL", env_values, DEFAULT_BASE_URL) or DEFAULT_BASE_URL
    base_url = normalize_base_url(base_url)
    model = resolve_setting("EXTRACTOR_MODEL", env_values, DEFAULT_MODEL) or DEFAULT_MODEL
    timeout_seconds_str = resolve_setting(
        "EXTRACTOR_TIMEOUT_SECONDS",
        env_values,
        str(DEFAULT_TIMEOUT_SECONDS),
    ) or str(DEFAULT_TIMEOUT_SECONDS)
    max_attempts_str = resolve_setting(
        "EXTRACTOR_MAX_ATTEMPTS",
        env_values,
        str(DEFAULT_MAX_ATTEMPTS),
    ) or str(DEFAULT_MAX_ATTEMPTS)
    retry_backoff_seconds_str = resolve_setting(
        "EXTRACTOR_RETRY_BACKOFF_SECONDS",
        env_values,
        str(DEFAULT_RETRY_BACKOFF_SECONDS),
    ) or str(DEFAULT_RETRY_BACKOFF_SECONDS)

    try:
        timeout_seconds = int(timeout_seconds_str)
    except ValueError:
        print(f"ERROR: EXTRACTOR_TIMEOUT_SECONDS 非法: {timeout_seconds_str}", file=sys.stderr)
        return 2
    try:
        max_attempts = max(1, int(max_attempts_str))
    except ValueError:
        print(f"ERROR: EXTRACTOR_MAX_ATTEMPTS 非法: {max_attempts_str}", file=sys.stderr)
        return 2
    try:
        retry_backoff_seconds = max(0, int(retry_backoff_seconds_str))
    except ValueError:
        print(f"ERROR: EXTRACTOR_RETRY_BACKOFF_SECONDS 非法: {retry_backoff_seconds_str}", file=sys.stderr)
        return 2

    turn_id_for_messages = None
    if args.turn_id is not None:
        numeric_turn_id = parse_turn_id(Path(args.turn_id))
        if numeric_turn_id is None:
            print(f"ERROR: turn_id 格式非法: {args.turn_id}", file=sys.stderr)
            return 2
        turn_id_for_messages = numeric_turn_id

    messages = build_chat_messages(
        system_path=Path(args.system),
        slice_path=Path(args.slice),
        turn_path=Path(args.turn),
        turn_id_override=turn_id_for_messages,
    )

    turn_id = args.turn_id
    if turn_id is None:
        inferred = parse_turn_id(Path(args.turn))
        if inferred is None:
            print("ERROR: 无法从 turn 文件推断 turn_id", file=sys.stderr)
            return 2
        turn_id = f"turn_{inferred:03d}"

    patch_out = choose_output_path(args.project_id, turn_id, args.out).resolve()
    raw_response_out = Path(
        args.raw_response_out
        or Path("graph") / "projects" / args.project_id / "reports" / f"extractor_raw_response.{turn_id}.txt"
    ).resolve()
    prompt_out = Path(
        args.prompt_out
        or Path("graph") / "projects" / args.project_id / "reports" / f"extractor_prompt.{turn_id}.json"
    ).resolve()

    prompt_snapshot = {
        "base_url": base_url,
        "model": model,
        "messages": messages,
    }
    ensure_parent(prompt_out)
    prompt_out.write_text(json.dumps(prompt_snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Using env file: {env_path}")

    try:
        raw_text = call_extractor(
            base_url=base_url,
            api_key=api_key,
            model=model,
            timeout_seconds=timeout_seconds,
            messages=messages,
            max_attempts=max_attempts,
            retry_backoff_seconds=retry_backoff_seconds,
        )
    except Exception as exc:
        ensure_parent(raw_response_out)
        raw_response_out.write_text(str(exc) + "\n", encoding="utf-8")
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    ensure_parent(raw_response_out)
    raw_response_out.write_text(raw_text, encoding="utf-8")

    try:
        patch = parse_patch_response(raw_text)
    except Exception as exc:
        print(f"ERROR: patch JSON 解析失败: {exc}", file=sys.stderr)
        return 1

    ensure_parent(patch_out)
    patch_out.write_text(json.dumps(patch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote prompt snapshot: {prompt_out}")
    print(f"Wrote raw response: {raw_response_out}")
    print(f"Wrote patch: {patch_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
