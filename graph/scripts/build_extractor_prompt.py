#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


NODE_ID_RE = re.compile(r"\bn_(\d+)\b")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_turn_id(path: Path) -> int | None:
    for pattern in [r"turn[_-]?(\d+)", r"slice[_-]?(\d+)"]:
        m = re.search(pattern, path.stem, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None


def scan_max_node_id(obj: Any) -> int:
    max_id = 0

    def walk(x: Any) -> None:
        nonlocal max_id
        if isinstance(x, dict):
            for k, v in x.items():
                if k == "node_id" and isinstance(v, str):
                    m = NODE_ID_RE.search(v)
                    if m:
                        max_id = max(max_id, int(m.group(1)))
                else:
                    walk(v)
        elif isinstance(x, list):
            for item in x:
                walk(item)

    walk(obj)
    return max_id


def next_node_id_from_pack_fallback(pack: dict[str, Any]) -> str:
    max_id = scan_max_node_id(pack)
    print(
        "WARNING: next_node_id is inferred only from slice. "
        "This may be unsafe if slice is not full graph.",
        file=sys.stderr,
    )
    return f"n_{max_id + 1:04d}"


def choose_fence(text: str) -> str:
    max_run = 3
    for m in re.finditer(r"`+", text):
        max_run = max(max_run, len(m.group(0)) + 1)
    return "`" * max_run


def fenced(lang: str, text: str) -> str:
    fence = choose_fence(text)
    return f"{fence}{lang}\n{text}\n{fence}"


def split_runtime_from_pack(raw_pack: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    pack = dict(raw_pack)
    runtime = dict(pack.pop("_runtime", {}) or {})

    # 兼容旧格式：如果有人把 next_node_id 放在顶层，这里拿出来。
    if "next_node_id" in pack:
        runtime.setdefault("next_node_id", pack.pop("next_node_id"))
    # 诊断字段不入模型上下文
    pack.pop("retrieval_trace", None)
    return pack, runtime


def build_user_message(
    pack: dict[str, Any],
    turn_text: str,
    task_id: str,
    turn_id: int,
    next_node_id: str,
) -> str:
    pack_json = json.dumps(pack, ensure_ascii=False, indent=2)

    return f"""你现在收到本轮 Task Graph Extractor 的动态输入。

请严格遵守 system message 中的规则。
你不是回答用户，而是只输出 Graph Patch JSON。

## Runtime Control

task_id: {task_id}
turn_id: {turn_id}
next_node_id: {next_node_id}

## extractor_context_pack.json

{fenced("json", pack_json)}

## turn_text

{fenced("markdown", turn_text)}

请只输出 Graph Patch JSON。
"""


def resolve_prompt_components(
    system_path: Path,
    slice_path: Path,
    turn_path: Path,
    *,
    task_id_override: str | None = None,
    turn_id_override: int | None = None,
    next_node_id_override: str | None = None,
) -> dict[str, Any]:
    system_text = system_path.read_text(encoding="utf-8")
    raw_pack = load_json(slice_path)
    turn_text = turn_path.read_text(encoding="utf-8")

    pack, runtime = split_runtime_from_pack(raw_pack)

    task_id = task_id_override or pack.get("task_id") or "task_default"
    turn_id = turn_id_override
    if turn_id is None:
        turn_id = pack.get("turn_id")
    if turn_id is None:
        turn_id = parse_turn_id(turn_path)

    if turn_id is None:
        raise ValueError("cannot infer turn_id. Use --turn-id.")

    next_node_id = (
        next_node_id_override
        or runtime.get("next_node_id")
        or next_node_id_from_pack_fallback(pack)
    )

    user_message = build_user_message(
        pack=pack,
        turn_text=turn_text,
        task_id=str(task_id),
        turn_id=int(turn_id),
        next_node_id=str(next_node_id),
    )

    return {
        "system_text": system_text,
        "user_message": user_message,
        "task_id": str(task_id),
        "turn_id": int(turn_id),
        "next_node_id": str(next_node_id),
        "pack": pack,
        "runtime": runtime,
        "turn_text": turn_text,
    }


def build_chat_messages(
    system_path: Path,
    slice_path: Path,
    turn_path: Path,
    *,
    task_id_override: str | None = None,
    turn_id_override: int | None = None,
    next_node_id_override: str | None = None,
) -> list[dict[str, str]]:
    components = resolve_prompt_components(
        system_path=system_path,
        slice_path=slice_path,
        turn_path=turn_path,
        task_id_override=task_id_override,
        turn_id_override=turn_id_override,
        next_node_id_override=next_node_id_override,
    )
    return [
        {"role": "system", "content": components["system_text"]},
        {"role": "user", "content": components["user_message"]},
    ]


def main() -> None:
    script_dir = Path(__file__).parent.resolve()
    default_system = script_dir.parent / "prompts" / "extractor_system.md"

    parser = argparse.ArgumentParser()
    parser.add_argument("--system", default=str(default_system))
    parser.add_argument("--slice", required=True)
    parser.add_argument("--turn", required=True)
    parser.add_argument("--out")
    parser.add_argument(
        "--mode",
        choices=["single", "split", "user-only", "api-json"],
        default="single",
    )
    parser.add_argument("--task-id")
    parser.add_argument("--turn-id", type=int)
    parser.add_argument("--next-node-id")
    args = parser.parse_args()

    system_path = Path(args.system)
    slice_path = Path(args.slice)
    turn_path = Path(args.turn)

    try:
        components = resolve_prompt_components(
            system_path=system_path,
            slice_path=slice_path,
            turn_path=turn_path,
            task_id_override=args.task_id,
            turn_id_override=args.turn_id,
            next_node_id_override=args.next_node_id,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    system_text = components["system_text"]
    user_message = components["user_message"]

    if args.mode == "user-only":
        output = user_message

    elif args.mode == "split":
        output = f"""# SYSTEM MESSAGE

{system_text}

# USER MESSAGE

{user_message}
"""

    elif args.mode == "api-json":
        output = json.dumps(
            {"messages": build_chat_messages(system_path, slice_path, turn_path,
                                             task_id_override=args.task_id,
                                             turn_id_override=args.turn_id,
                                             next_node_id_override=args.next_node_id)},
            ensure_ascii=False,
            indent=2,
        )

    else:
        output = f"""# SYSTEM MESSAGE

{system_text}

# USER MESSAGE

{user_message}
"""

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
        print(f"Wrote {out_path}")
    else:
        print(output)


if __name__ == "__main__":
    main()
