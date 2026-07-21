#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate lifecycle fixtures against the fixture schema.

Run from repository root.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = REPO_ROOT / "graph" / "projects" / "abu_modern" / "fixtures" / "lifecycle"
SCHEMA_PATH = FIXTURES_DIR / "fixture_schema.json"
FIXTURES_GLOB = FIXTURES_DIR / "fixtures" / "lc_*.json"

REQUIRED_CATEGORIES = {
    "lifecycle_identity",
    "revival",
    "provenance_conflict",
    "late_arrival",
    "legacy_migration",
    "alias_abstain",
    "sequence_collision",
    "replay_determinism",
}


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_type(value: Any, expected: str | list[str], path: str) -> list[str]:
    errors: list[str] = []
    if isinstance(expected, list):
        if not any(value is None if t == "null" else isinstance(value, _json_type(t)) for t in expected):
            errors.append(f"{path}: expected one of {expected}, got {type(value).__name__}")
    else:
        if expected == "null":
            if value is not None:
                errors.append(f"{path}: expected null, got {type(value).__name__}")
        elif not isinstance(value, _json_type(expected)):
            errors.append(f"{path}: expected {expected}, got {type(value).__name__}")
    return errors


def _json_type(t: str) -> type:
    return {
        "string": str,
        "integer": int,
        "boolean": bool,
        "array": list,
        "object": dict,
    }.get(t, object)


def validate_against_schema(data: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []
    if schema.get("type") == "object":
        if not isinstance(data, dict):
            return [f"{path}: expected object, got {type(data).__name__}"]
        for key in schema.get("required", []):
            if key not in data:
                errors.append(f"{path}: missing required field '{key}'")
        for key, sub_schema in schema.get("properties", {}).items():
            if key in data:
                errors.extend(validate_against_schema(data[key], sub_schema, f"{path}.{key}"))
    elif schema.get("type") == "array":
        if not isinstance(data, list):
            return [f"{path}: expected array, got {type(data).__name__}"]
        item_schema = schema.get("items", {})
        for i, item in enumerate(data):
            errors.extend(validate_against_schema(item, item_schema, f"{path}[{i}]"))
    elif schema.get("type") == "string":
        errors.extend(validate_type(data, "string", path))
        if isinstance(data, str) and "enum" in schema and data not in schema["enum"]:
            errors.append(f"{path}: value '{data}' not in enum {schema['enum']}")
        if isinstance(data, str) and "pattern" in schema:
            import re
            if not re.match(schema["pattern"], data):
                errors.append(f"{path}: value '{data}' does not match pattern {schema['pattern']}")
    elif schema.get("type") == "integer":
        errors.extend(validate_type(data, "integer", path))
    elif schema.get("type") == "boolean":
        errors.extend(validate_type(data, "boolean", path))
    elif isinstance(schema.get("type"), list):
        errors.extend(validate_type(data, schema["type"], path))
    return errors


def validate() -> list[str]:
    errors: list[str] = []
    if not SCHEMA_PATH.exists():
        errors.append(f"missing schema: {SCHEMA_PATH}")
        return errors
    schema = load_json(SCHEMA_PATH)

    fixture_paths = sorted(FIXTURES_GLOB.parent.glob("lc_*.json"))
    if not fixture_paths:
        errors.append(f"no fixtures found in {FIXTURES_GLOB.parent}")
        return errors

    seen_categories: set[str] = set()
    seen_ids: set[str] = set()

    for p in fixture_paths:
        try:
            data = load_json(p)
        except json.JSONDecodeError as e:
            errors.append(f"{p.name}: invalid JSON: {e}")
            continue
        errors.extend(validate_against_schema(data, schema))
        fid = data.get("fixture_id", "")
        expected_name = f"{fid}.json"
        if p.name != expected_name:
            errors.append(f"{p.name}: fixture_id '{fid}' does not match filename")
        if fid in seen_ids:
            errors.append(f"{p.name}: duplicate fixture_id '{fid}'")
        seen_ids.add(fid)
        cat = data.get("category")
        if cat:
            seen_categories.add(cat)

    missing = REQUIRED_CATEGORIES - seen_categories
    if missing:
        errors.append(f"missing required categories: {sorted(missing)}")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("VALIDATION FAILED")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("VALIDATION PASSED")
    print(f"  schema: {SCHEMA_PATH.relative_to(REPO_ROOT)}")
    print(f"  fixtures: {len(list(FIXTURES_GLOB.parent.glob('lc_*.json')))}")
    print(f"  categories covered: {sorted(REQUIRED_CATEGORIES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
