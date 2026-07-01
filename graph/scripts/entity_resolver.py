#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, obj: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def extract_nodes(graph_state: dict[str, Any]) -> list[dict[str, Any]]:
    nodes = graph_state.get("nodes")
    if isinstance(nodes, dict):
        result = []
        for node_id, node in nodes.items():
            if isinstance(node, dict):
                item = dict(node)
                item.setdefault("node_id", node_id)
                result.append(item)
        return result
    if isinstance(nodes, list):
        return [dict(node) for node in nodes if isinstance(node, dict)]
    return []


def extract_new_nodes(patch: dict[str, Any]) -> list[dict[str, Any]]:
    new_nodes = patch.get("new_nodes", [])
    if isinstance(new_nodes, list):
        return [node for node in new_nodes if isinstance(node, dict)]
    return []


def normalize_ref(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().replace("\\", "/")


def is_active(node: dict[str, Any]) -> bool:
    return str(node.get("status", "active")).strip().lower() == "active"


def token_set(text: str) -> set[str]:
    lowered = text.lower()
    return {token for token in re.findall(r"[a-z0-9_./-]+", lowered) if len(token) >= 2}


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    surface = SequenceMatcher(None, a.lower(), b.lower()).ratio()
    tokens_a = token_set(a)
    tokens_b = token_set(b)
    if not tokens_a or not tokens_b:
        token_score = 0.0
    else:
        token_score = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
    return max(surface, token_score)


def parse_alias_registry(path: Path) -> dict[str, str]:
    registry: dict[str, str] = {}
    if not path.exists():
        return registry

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if "<-" not in line or line.startswith("#"):
            continue
        left, right = line.split("<-", 1)
        canonical = normalize_ref(left.strip())
        alias_part = right.split("|", 1)[0]
        aliases = [
            normalize_ref(item.strip())
            for item in re.split(r"\s+/\s+", alias_part)
            if normalize_ref(item.strip())
        ]
        for alias in aliases:
            registry[alias] = canonical
    return registry


def resolve_patch(
    *,
    graph_state: dict[str, Any],
    patch: dict[str, Any],
    alias_registry: dict[str, str],
    project_id: str,
    turn_id: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    active_nodes = [node for node in extract_nodes(graph_state) if is_active(node)]
    active_refs = sorted({normalize_ref(node.get("entity_ref")) for node in active_nodes if normalize_ref(node.get("entity_ref"))})

    resolved_patch = json.loads(json.dumps(patch))
    new_nodes = extract_new_nodes(resolved_patch)
    decisions: list[dict[str, Any]] = []
    pending_items: list[dict[str, Any]] = []

    for node in new_nodes:
        raw_entity_ref = normalize_ref(node.get("entity_ref"))
        decision = {
            "new_node_id": node.get("node_id"),
            "raw_entity_ref": raw_entity_ref or None,
            "resolved_entity_ref": raw_entity_ref or None,
            "match_confidence": 0.0,
            "merge_reason": "",
            "non_merge_reason": "",
            "candidate_aliases": [],
        }

        if not raw_entity_ref:
            decision["non_merge_reason"] = "entity_ref_missing"
            decisions.append(decision)
            continue

        if raw_entity_ref in active_refs:
            decision["match_confidence"] = 1.0
            decision["merge_reason"] = "exact_entity_ref_match"
            decisions.append(decision)
            continue

        if raw_entity_ref in alias_registry:
            canonical = alias_registry[raw_entity_ref]
            node["entity_ref"] = canonical
            decision["resolved_entity_ref"] = canonical
            decision["match_confidence"] = 0.95
            decision["merge_reason"] = "alias_registry_match"
            decision["candidate_aliases"] = [
                {
                    "canonical_entity_ref": canonical,
                    "match_confidence": 0.95,
                    "evidence": ["alias_registry"],
                }
            ]
            decisions.append(decision)
            continue

        candidates = []
        for existing_ref in active_refs:
            score = similarity(raw_entity_ref, existing_ref)
            if score < 0.45:
                continue
            evidence = ["surface_or_token_similarity"]
            candidates.append(
                {
                    "canonical_entity_ref": existing_ref,
                    "match_confidence": round(score, 4),
                    "evidence": evidence,
                }
            )

        candidates.sort(key=lambda item: item["match_confidence"], reverse=True)
        top_candidates = candidates[:5]
        decision["candidate_aliases"] = top_candidates

        if top_candidates:
            decision["match_confidence"] = top_candidates[0]["match_confidence"]
            decision["non_merge_reason"] = "needs_manual_merge_review"
            pending_items.append(
                {
                    "new_node_id": node.get("node_id"),
                    "raw_entity_ref": raw_entity_ref,
                    "candidate_aliases": top_candidates,
                    "match_confidence": top_candidates[0]["match_confidence"],
                    "merge_reason": "",
                    "non_merge_reason": "needs_manual_merge_review",
                }
            )
        else:
            decision["non_merge_reason"] = "no_candidate_found"

        decisions.append(decision)

    report = {
        "kind": "entity_resolution_report.phase1_prep.v1",
        "project_id": project_id,
        "turn_id": turn_id,
        "summary": {
            "new_nodes": len(new_nodes),
            "resolved_exact": sum(1 for item in decisions if item["merge_reason"] == "exact_entity_ref_match"),
            "resolved_alias": sum(1 for item in decisions if item["merge_reason"] == "alias_registry_match"),
            "pending_merge": len(pending_items),
            "unresolved": sum(1 for item in decisions if item["non_merge_reason"] in {"entity_ref_missing", "no_candidate_found"}),
        },
        "decisions": decisions,
    }

    pending_merge = {
        "project_id": project_id,
        "turn_id": turn_id,
        "generated_by": "graph/scripts/entity_resolver.py",
        "items": pending_items,
    }
    return resolved_patch, report, pending_merge


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 1-prep 的最小 Entity Resolver")
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--turn-id", required=True)
    parser.add_argument("--graph", required=True, help="graph_state.json")
    parser.add_argument("--patch", required=True, help="原始 patch.json")
    parser.add_argument("--out-patch", required=True, help="resolved patch 输出路径")
    parser.add_argument("--report-out", required=True, help="resolution report 输出路径")
    parser.add_argument("--pending-merge-out", required=True, help="pending_merge 输出路径")
    parser.add_argument(
        "--alias-contract",
        default="contracts/05_entity_naming.md",
        help="别名登记 contract 路径",
    )
    args = parser.parse_args()

    graph_state = load_json(args.graph)
    patch = load_json(args.patch)
    alias_registry = parse_alias_registry(Path(args.alias_contract))

    resolved_patch, report, pending_merge = resolve_patch(
        graph_state=graph_state,
        patch=patch,
        alias_registry=alias_registry,
        project_id=args.project_id,
        turn_id=args.turn_id,
    )

    write_json(args.out_patch, resolved_patch)
    write_json(args.report_out, report)
    write_json(args.pending_merge_out, pending_merge)
    print(f"Wrote resolved patch: {args.out_patch}")
    print(f"Wrote resolution report: {args.report_out}")
    print(f"Wrote pending merge: {args.pending_merge_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
