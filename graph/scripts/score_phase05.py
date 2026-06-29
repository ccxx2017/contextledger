#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
score_phase05.py

Phase 0.5 失效回放基准评分器：
1. 校验 trajectories / gold 的数量、覆盖面与 schema-neutral 纪律
2. 对跑两条基线：phase0_current / flat_rag
3. 输出 coverage_matrix.md、gap_register.md、评分 JSON 与 Markdown 摘要
4. 额外比较 alias 上的 conservative vs aggressive 合并代价
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict, deque
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any


REQUIRED_TAGS = [
    "full",
    "partial",
    "conditional",
    "revival",
    "alias_trap",
    "provenance_conflict",
    "non_invalidation_decoy",
    "out_of_order_late",
]

BANNED_GOLD_TERMS = [
    r"\bstatus\b",
    r"\bstate\b",
    r"\bsupersede\b",
    r"\bsuperseded\b",
    r"\bopentask\b",
]

SOURCE_RANK = {
    "probe_log": 3,
    "warehouse_feed": 3,
    "queue_board": 3,
    "ops_chat": 2,
    "risk_memo": 2,
    "risk_note": 2,
    "policy_doc": 2,
    "release_note": 2,
    "incident_note": 2,
    "program_board": 2,
    "design_note": 2,
    "service_note": 2,
    "staff_note": 2,
    "ops_runbook": 2,
    "mode_sheet": 2,
    "release_sheet": 2,
    "naming_sheet": 2,
    "user_note": 1,
}


@dataclass
class StepPrediction:
    active_set: set[str]
    must_include: set[str]
    invalidations: list[dict[str, Any]]
    entity_clusters: list[dict[str, Any]]
    adjudications: dict[tuple[str, str], dict[str, Any]]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_exact(text: str) -> str:
    return " ".join(str(text).strip().lower().split())


def tokenize_aggressive(text: str) -> set[str]:
    lowered = str(text).lower()
    tokens = re.findall(r"[a-z0-9]+", lowered)
    return {token for token in tokens if token}


def build_clusters(mentions: list[str], strategy: str) -> list[dict[str, Any]]:
    unique_mentions = list(dict.fromkeys(mentions))
    if not unique_mentions:
        return []

    parent = {mention: mention for mention in unique_mentions}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra = find(a)
        rb = find(b)
        if ra != rb:
            parent[rb] = ra

    if strategy == "exact":
        groups: dict[str, list[str]] = defaultdict(list)
        for mention in unique_mentions:
            groups[normalize_exact(mention)].append(mention)
        for group in groups.values():
            for left, right in combinations(group, 2):
                union(left, right)
    elif strategy == "aggressive":
        token_map = {mention: tokenize_aggressive(mention) for mention in unique_mentions}
        for left, right in combinations(unique_mentions, 2):
            if token_map[left] & token_map[right]:
                union(left, right)
    else:
        raise ValueError(f"Unknown cluster strategy: {strategy}")

    grouped: dict[str, list[str]] = defaultdict(list)
    for mention in unique_mentions:
        grouped[find(mention)].append(mention)

    clusters = []
    for index, mentions_in_group in enumerate(sorted(grouped.values(), key=lambda items: items[0]), start=1):
        clusters.append(
            {
                "cluster_id": f"pred_{strategy}_{index:02d}",
                "mentions": sorted(mentions_in_group),
            }
        )
    return clusters


def extract_mentions_up_to(observations: list[dict[str, Any]], step_index: int) -> list[str]:
    mentions: list[str] = []
    for observation in observations[: step_index + 1]:
        mentions.extend(observation.get("mentions", []))
    return mentions


def claims_from_observation(observation: dict[str, Any]) -> list[dict[str, Any]]:
    return list(observation.get("payload", {}).get("claim_bundle", []))


def claims_to_ids(claims: list[dict[str, Any]]) -> set[str]:
    return {str(claim["claim_id"]) for claim in claims}


def critical_claim_ids(claims: list[dict[str, Any]]) -> set[str]:
    return {
        str(claim["claim_id"])
        for claim in claims
        if str(claim.get("importance")) == "critical"
    }


def observation_entity_key(observation: dict[str, Any]) -> str:
    mentions = observation.get("mentions", [])
    return normalize_exact(mentions[0]) if mentions else ""


def source_rank(observation: dict[str, Any]) -> int:
    channel = str(observation.get("source", {}).get("channel", ""))
    return SOURCE_RANK.get(channel, 0)


def predicted_clusters_for_step(observations: list[dict[str, Any]], step_index: int, strategy: str) -> list[dict[str, Any]]:
    mentions = extract_mentions_up_to(observations, step_index)
    return build_clusters(mentions, strategy)


def adjudication_snapshot_fallback_true(
    seen_observations: list[dict[str, Any]],
    strategy_name: str,
) -> dict[tuple[str, str], dict[str, Any]]:
    winners: dict[tuple[str, str], dict[str, Any]] = {}
    for observation in seen_observations:
        entity_key = observation_entity_key(observation)
        for claim in claims_from_observation(observation):
            winners[(entity_key, str(claim["dimension"]))] = {
                "winner_obs_id": observation["obs_id"],
                "fallback_used": True,
                "strategy": strategy_name,
            }
    return winners


def adjudication_snapshot_latest_by_exact_entity(
    active_observations: dict[str, dict[str, Any]],
    strategy_name: str,
) -> dict[tuple[str, str], dict[str, Any]]:
    winners: dict[tuple[str, str], dict[str, Any]] = {}
    for entity_key, observation in active_observations.items():
        for claim in claims_from_observation(observation):
            winners[(entity_key, str(claim["dimension"]))] = {
                "winner_obs_id": observation["obs_id"],
                "fallback_used": True,
                "strategy": strategy_name,
            }
    return winners


def run_phase0_current(observations: list[dict[str, Any]]) -> list[StepPrediction]:
    active_nodes: dict[str, dict[str, Any]] = {}
    seen_observations: list[dict[str, Any]] = []
    predictions: list[StepPrediction] = []

    for index, observation in enumerate(observations):
        seen_observations.append(observation)
        entity_key = observation_entity_key(observation)
        step_invalidations: list[dict[str, Any]] = []

        previous = active_nodes.get(entity_key)
        if previous is not None:
            step_invalidations.append(
                {
                    "source_obs_id": observation["obs_id"],
                    "target_obs_id": previous["obs_id"],
                    "kind": "full",
                    "dropped_claims": sorted(claims_to_ids(claims_from_observation(previous))),
                    "replacement_claims": sorted(claims_to_ids(claims_from_observation(observation))),
                }
            )

        active_nodes[entity_key] = observation

        active_claims: set[str] = set()
        must_include: set[str] = set()
        for node in active_nodes.values():
            claim_bundle = claims_from_observation(node)
            active_claims |= claims_to_ids(claim_bundle)
            must_include |= critical_claim_ids(claim_bundle)

        predictions.append(
            StepPrediction(
                active_set=active_claims,
                must_include=must_include,
                invalidations=step_invalidations,
                entity_clusters=predicted_clusters_for_step(observations, index, "exact"),
                adjudications=adjudication_snapshot_fallback_true(seen_observations, "phase0_current"),
            )
        )

    return predictions


def run_flat_rag(observations: list[dict[str, Any]]) -> list[StepPrediction]:
    latest_by_surface: dict[str, dict[str, Any]] = {}
    predictions: list[StepPrediction] = []

    for index, observation in enumerate(observations):
        entity_key = observation_entity_key(observation)
        latest_by_surface[entity_key] = observation

        active_claims: set[str] = set()
        must_include: set[str] = set()
        for node in latest_by_surface.values():
            claim_bundle = claims_from_observation(node)
            active_claims |= claims_to_ids(claim_bundle)
            must_include |= critical_claim_ids(claim_bundle)

        predictions.append(
            StepPrediction(
                active_set=active_claims,
                must_include=must_include,
                invalidations=[],
                entity_clusters=predicted_clusters_for_step(observations, index, "exact"),
                adjudications=adjudication_snapshot_latest_by_exact_entity(latest_by_surface, "flat_rag"),
            )
        )

    return predictions


def f1_score(predicted: set[str], expected: set[str]) -> float:
    if not predicted and not expected:
        return 1.0
    precision = len(predicted & expected) / len(predicted) if predicted else 0.0
    recall = len(predicted & expected) / len(expected) if expected else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def recall_score(predicted: set[str], expected: set[str]) -> float:
    if not expected:
        return 1.0
    return len(predicted & expected) / len(expected)


def invalidation_keys(
    trajectory_id: str,
    step_after_obs: str,
    invalidations: list[dict[str, Any]],
) -> set[tuple[str, str, str, str, str]]:
    keys = set()
    for item in invalidations:
        keys.add(
            (
                trajectory_id,
                step_after_obs,
                str(item.get("source_obs_id")),
                str(item.get("target_obs_id")),
                str(item.get("kind")),
            )
        )
    return keys


def compute_invalidation_stats(
    predicted_keys: set[tuple[str, str, str, str, str]],
    gold_keys: set[tuple[str, str, str, str, str]],
) -> dict[str, Any]:
    true_positive = len(predicted_keys & gold_keys)
    false_positive = len(predicted_keys - gold_keys)
    false_negative = len(gold_keys - predicted_keys)
    if predicted_keys:
        precision = true_positive / len(predicted_keys)
    else:
        precision = 1.0 if not gold_keys else 0.0
    recall = true_positive / len(gold_keys) if gold_keys else None
    return {
        "true_positive_count": true_positive,
        "false_positive_count": false_positive,
        "false_negative_count": false_negative,
        "predicted_count": len(predicted_keys),
        "gold_count": len(gold_keys),
        "precision": precision,
        "recall": recall,
    }


def mention_pair_truth(clusters: list[dict[str, Any]]) -> dict[tuple[str, str], bool]:
    mention_to_cluster: dict[str, str] = {}
    mentions: list[str] = []
    for cluster in clusters:
        cluster_id = str(cluster["cluster_id"])
        for mention in cluster.get("mentions", []):
            mention_to_cluster[str(mention)] = cluster_id
            mentions.append(str(mention))

    result: dict[tuple[str, str], bool] = {}
    for left, right in combinations(sorted(dict.fromkeys(mentions)), 2):
        result[(left, right)] = mention_to_cluster[left] == mention_to_cluster[right]
    return result


def compare_entity_clusters(
    gold_clusters: list[dict[str, Any]],
    predicted_clusters: list[dict[str, Any]],
) -> dict[str, float | int]:
    gold_pairs = mention_pair_truth(gold_clusters)
    predicted_pairs = mention_pair_truth(predicted_clusters)
    pair_keys = set(gold_pairs) | set(predicted_pairs)

    gold_same = 0
    gold_diff = 0
    false_split = 0
    false_merge = 0

    for pair in pair_keys:
        gold_same_pair = gold_pairs.get(pair, False)
        predicted_same_pair = predicted_pairs.get(pair, False)
        if gold_same_pair:
            gold_same += 1
            if not predicted_same_pair:
                false_split += 1
        else:
            gold_diff += 1
            if predicted_same_pair:
                false_merge += 1

    return {
        "gold_same_pairs": gold_same,
        "gold_diff_pairs": gold_diff,
        "false_split_count": false_split,
        "false_merge_count": false_merge,
        "false_split_rate": false_split / gold_same if gold_same else 0.0,
        "false_merge_rate": false_merge / gold_diff if gold_diff else 0.0,
    }


def score_baseline(
    trajectories: list[dict[str, Any]],
    golds: dict[str, dict[str, Any]],
    baseline_name: str,
) -> dict[str, Any]:
    if baseline_name == "phase0_current":
        runner = run_phase0_current
    elif baseline_name == "flat_rag":
        runner = run_flat_rag
    else:
        raise ValueError(f"Unknown baseline: {baseline_name}")

    invalidation_predicted_total: set[tuple[str, str, str, str, str]] = set()
    invalidation_gold_total: set[tuple[str, str, str, str, str]] = set()
    active_f1_values: list[float] = []
    must_include_recall_values: list[float] = []
    valid_time_total = 0
    valid_time_correct = 0
    valid_time_present_total = 0
    valid_time_present_correct = 0
    valid_time_absent_total = 0
    valid_time_absent_correct = 0
    entity_false_split_count = 0
    entity_false_merge_count = 0
    entity_gold_same_pairs = 0
    entity_gold_diff_pairs = 0
    per_trajectory: dict[str, Any] = {}
    invalidation_predicted_by_tag: dict[str, set[tuple[str, str, str, str, str]]] = {
        tag: set() for tag in REQUIRED_TAGS
    }
    invalidation_gold_by_tag: dict[str, set[tuple[str, str, str, str, str]]] = {
        tag: set() for tag in REQUIRED_TAGS
    }
    invalidation_fp_trajectories_by_tag: dict[str, set[str]] = {
        tag: set() for tag in REQUIRED_TAGS
    }
    invalidation_tp_trajectories_by_tag: dict[str, set[str]] = {
        tag: set() for tag in REQUIRED_TAGS
    }
    invalidation_fn_trajectories_by_tag: dict[str, set[str]] = {
        tag: set() for tag in REQUIRED_TAGS
    }

    for trajectory in trajectories:
        trajectory_id = str(trajectory["trajectory_id"])
        trajectory_tags = [tag for tag in trajectory.get("coverage_tags", []) if tag in REQUIRED_TAGS]
        predictions = runner(list(trajectory.get("observations", [])))
        gold = golds[trajectory_id]
        gold_steps = gold.get("steps", [])
        trajectory_debug = {
            "step_count": len(gold_steps),
            "steps": [],
        }
        trajectory_predicted_invalidation_keys: set[tuple[str, str, str, str, str]] = set()
        trajectory_gold_invalidation_keys: set[tuple[str, str, str, str, str]] = set()

        for gold_step, prediction in zip(gold_steps, predictions):
            expected_active = set(gold_step.get("expected_active_set", []))
            expected_must = set(gold_step.get("must_include", []))
            active_f1 = f1_score(prediction.active_set, expected_active)
            must_recall = recall_score(prediction.must_include, expected_must)
            active_f1_values.append(active_f1)
            must_include_recall_values.append(must_recall)

            step_key = str(gold_step["after_obs_id"])
            predicted_invalidation_keys = invalidation_keys(trajectory_id, step_key, prediction.invalidations)
            gold_invalidation_keys = invalidation_keys(trajectory_id, step_key, gold_step.get("expected_invalidations", []))
            invalidation_predicted_total |= predicted_invalidation_keys
            invalidation_gold_total |= gold_invalidation_keys
            trajectory_predicted_invalidation_keys |= predicted_invalidation_keys
            trajectory_gold_invalidation_keys |= gold_invalidation_keys

            adjudication_targets = gold_step.get("valid_time_adjudication", {}).get("adjudication_targets", [])
            gold_cluster_map = {cluster["cluster_id"]: cluster for cluster in gold_step.get("entity_clusters", [])}
            for target in adjudication_targets:
                valid_time_total += 1
                gold_cluster = gold_cluster_map.get(target["entity_cluster_id"], {})
                mentions = gold_cluster.get("mentions", [])
                lookup_key = normalize_exact(mentions[0]) if mentions else ""
                predicted = prediction.adjudications.get((lookup_key, str(target["dimension"])))
                target_uses_fallback = bool(target["fallback_used"])
                if target_uses_fallback:
                    valid_time_absent_total += 1
                else:
                    valid_time_present_total += 1
                is_correct = bool(
                    predicted
                    and predicted["winner_obs_id"] == target["winner_obs_id"]
                    and predicted["fallback_used"] == target["fallback_used"]
                )
                if is_correct:
                    valid_time_correct += 1
                    if target_uses_fallback:
                        valid_time_absent_correct += 1
                    else:
                        valid_time_present_correct += 1

            trajectory_debug["steps"].append(
                {
                    "after_obs_id": step_key,
                    "gold_active_set": sorted(expected_active),
                    "predicted_active_set": sorted(prediction.active_set),
                    "active_set_f1": round(active_f1, 4),
                    "gold_must_include": sorted(expected_must),
                    "predicted_must_include": sorted(prediction.must_include),
                    "must_include_recall": round(must_recall, 4),
                    "gold_invalidations": gold_step.get("expected_invalidations", []),
                    "predicted_invalidations": prediction.invalidations,
                    "gold_valid_time_targets": adjudication_targets,
                    "predicted_valid_time": [
                        {
                            "entity_key": key[0],
                            "dimension": key[1],
                            "winner_obs_id": value["winner_obs_id"],
                            "fallback_used": value["fallback_used"],
                        }
                        for key, value in sorted(prediction.adjudications.items())
                    ],
                }
            )

        final_gold_clusters = gold_steps[-1].get("entity_clusters", []) if gold_steps else []
        final_predicted_clusters = predictions[-1].entity_clusters if predictions else []
        cluster_compare = compare_entity_clusters(final_gold_clusters, final_predicted_clusters)
        entity_false_split_count += int(cluster_compare["false_split_count"])
        entity_false_merge_count += int(cluster_compare["false_merge_count"])
        entity_gold_same_pairs += int(cluster_compare["gold_same_pairs"])
        entity_gold_diff_pairs += int(cluster_compare["gold_diff_pairs"])
        trajectory_debug["entity_resolution"] = cluster_compare
        trajectory_fp_invalidation_keys = trajectory_predicted_invalidation_keys - trajectory_gold_invalidation_keys
        trajectory_tp_invalidation_keys = trajectory_predicted_invalidation_keys & trajectory_gold_invalidation_keys
        trajectory_fn_invalidation_keys = trajectory_gold_invalidation_keys - trajectory_predicted_invalidation_keys
        trajectory_debug["invalidation_event_summary"] = {
            "predicted_count": len(trajectory_predicted_invalidation_keys),
            "gold_count": len(trajectory_gold_invalidation_keys),
            "true_positive_count": len(trajectory_tp_invalidation_keys),
            "false_positive_count": len(trajectory_fp_invalidation_keys),
            "false_negative_count": len(trajectory_fn_invalidation_keys),
        }
        for tag in trajectory_tags:
            invalidation_predicted_by_tag[tag] |= trajectory_predicted_invalidation_keys
            invalidation_gold_by_tag[tag] |= trajectory_gold_invalidation_keys
            if trajectory_fp_invalidation_keys:
                invalidation_fp_trajectories_by_tag[tag].add(trajectory_id)
            if trajectory_tp_invalidation_keys:
                invalidation_tp_trajectories_by_tag[tag].add(trajectory_id)
            if trajectory_fn_invalidation_keys:
                invalidation_fn_trajectories_by_tag[tag].add(trajectory_id)
        per_trajectory[trajectory_id] = trajectory_debug

    overall_invalidation_stats = compute_invalidation_stats(invalidation_predicted_total, invalidation_gold_total)
    invalidation_precision = float(overall_invalidation_stats["precision"])
    overall_recall = overall_invalidation_stats["recall"]
    invalidation_recall = float(overall_recall) if overall_recall is not None else 1.0
    invalidation_by_tag: dict[str, Any] = {}
    for tag in REQUIRED_TAGS:
        tag_stats = compute_invalidation_stats(invalidation_predicted_by_tag[tag], invalidation_gold_by_tag[tag])
        tag_stats["trajectory_ids"] = sorted(
            str(trajectory["trajectory_id"])
            for trajectory in trajectories
            if tag in set(trajectory.get("coverage_tags", []))
        )
        tag_stats["false_positive_trajectory_ids"] = sorted(invalidation_fp_trajectories_by_tag[tag])
        tag_stats["true_positive_trajectory_ids"] = sorted(invalidation_tp_trajectories_by_tag[tag])
        tag_stats["false_negative_trajectory_ids"] = sorted(invalidation_fn_trajectories_by_tag[tag])
        invalidation_by_tag[tag] = tag_stats

    return {
        "baseline": baseline_name,
        "metrics": {
            "invalidation_precision": invalidation_precision,
            "invalidation_recall": invalidation_recall,
            "invalidation_event_summary": overall_invalidation_stats,
            "active_set_set_f1": sum(active_f1_values) / len(active_f1_values) if active_f1_values else 0.0,
            "must_include_recall": sum(must_include_recall_values) / len(must_include_recall_values) if must_include_recall_values else 0.0,
            "entity_resolution_false_merge_rate": entity_false_merge_count / entity_gold_diff_pairs if entity_gold_diff_pairs else 0.0,
            "entity_resolution_false_split_rate": entity_false_split_count / entity_gold_same_pairs if entity_gold_same_pairs else 0.0,
            "valid_time_adjudication_accuracy": valid_time_correct / valid_time_total if valid_time_total else 1.0,
            "valid_time_breakdown": {
                "observed_at_present_correct": valid_time_present_correct,
                "observed_at_present_total": valid_time_present_total,
                "observed_at_present_accuracy": (
                    valid_time_present_correct / valid_time_present_total if valid_time_present_total else 1.0
                ),
                "observed_at_absent_fallback_correct": valid_time_absent_correct,
                "observed_at_absent_fallback_total": valid_time_absent_total,
                "observed_at_absent_fallback_accuracy": (
                    valid_time_absent_correct / valid_time_absent_total if valid_time_absent_total else 1.0
                ),
            },
            "counts": {
                "steps": len(active_f1_values),
                "gold_invalidations": len(invalidation_gold_total),
                "predicted_invalidations": len(invalidation_predicted_total),
                "valid_time_targets": valid_time_total,
                "entity_gold_same_pairs": entity_gold_same_pairs,
                "entity_gold_diff_pairs": entity_gold_diff_pairs,
            },
        },
        "invalidation_by_tag": invalidation_by_tag,
        "per_trajectory": per_trajectory,
    }


def validate_phase05(trajectories: list[dict[str, Any]], golds: dict[str, dict[str, Any]]) -> dict[str, Any]:
    issues: list[str] = []
    tag_counter = {tag: 0 for tag in REQUIRED_TAGS}

    if len(trajectories) < 15:
        issues.append(f"轨迹数量不足：{len(trajectories)} < 15")

    for trajectory in trajectories:
        trajectory_id = str(trajectory["trajectory_id"])
        gold = golds.get(trajectory_id)
        if gold is None:
            issues.append(f"缺少 gold：{trajectory_id}")
            continue

        if gold.get("schema_neutral") is not True:
            issues.append(f"gold 缺少 schema_neutral=true：{trajectory_id}")

        trajectory_tags = trajectory.get("coverage_tags", [])
        for tag in trajectory_tags:
            if tag in tag_counter:
                tag_counter[tag] += 1

        observations = trajectory.get("observations", [])
        steps = gold.get("steps", [])
        if len(observations) != len(steps):
            issues.append(f"step 数与 observation 数不一致：{trajectory_id}")

        gold_text = json.dumps(gold, ensure_ascii=False)
        for pattern in BANNED_GOLD_TERMS:
            if re.search(pattern, gold_text, flags=re.IGNORECASE):
                issues.append(f"gold 出现禁用 Phase 0 词汇：{trajectory_id} / {pattern}")

    for tag, count in tag_counter.items():
        if count == 0:
            issues.append(f"覆盖矩阵缺失形态：{tag}")

    return {
        "ok": not issues,
        "trajectory_count": len(trajectories),
        "coverage_counts": tag_counter,
        "issues": issues,
    }


def render_coverage_matrix(trajectories: list[dict[str, Any]]) -> str:
    header = "| trajectory_id | " + " | ".join(REQUIRED_TAGS) + " |\n"
    separator = "|" + "---|" * (len(REQUIRED_TAGS) + 1) + "\n"
    rows = [header, separator]
    for trajectory in trajectories:
        tags = set(trajectory.get("coverage_tags", []))
        cells = ["Y" if tag in tags else "" for tag in REQUIRED_TAGS]
        rows.append("| " + str(trajectory["trajectory_id"]) + " | " + " | ".join(cells) + " |\n")
    return "".join(rows)


def alias_strategy_tradeoff(trajectories: list[dict[str, Any]], golds: dict[str, dict[str, Any]]) -> dict[str, Any]:
    trajectories_with_alias = [traj for traj in trajectories if "alias_trap" in set(traj.get("coverage_tags", []))]
    conservative_same = conservative_diff = conservative_split = conservative_merge = 0
    aggressive_same = aggressive_diff = aggressive_split = aggressive_merge = 0

    for trajectory in trajectories_with_alias:
        trajectory_id = str(trajectory["trajectory_id"])
        mentions = extract_mentions_up_to(trajectory.get("observations", []), len(trajectory.get("observations", [])) - 1)
        gold_clusters = golds[trajectory_id]["steps"][-1]["entity_clusters"]

        conservative = compare_entity_clusters(gold_clusters, build_clusters(mentions, "exact"))
        aggressive = compare_entity_clusters(gold_clusters, build_clusters(mentions, "aggressive"))

        conservative_same += int(conservative["gold_same_pairs"])
        conservative_diff += int(conservative["gold_diff_pairs"])
        conservative_split += int(conservative["false_split_count"])
        conservative_merge += int(conservative["false_merge_count"])

        aggressive_same += int(aggressive["gold_same_pairs"])
        aggressive_diff += int(aggressive["gold_diff_pairs"])
        aggressive_split += int(aggressive["false_split_count"])
        aggressive_merge += int(aggressive["false_merge_count"])

    result = {
        "conservative_exact_surface": {
            "false_split_count": conservative_split,
            "false_merge_count": conservative_merge,
            "gold_same_pairs": conservative_same,
            "gold_diff_pairs": conservative_diff,
            "false_split_rate": conservative_split / conservative_same if conservative_same else 0.0,
            "false_merge_rate": conservative_merge / conservative_diff if conservative_diff else 0.0,
        },
        "aggressive_token_overlap": {
            "false_split_count": aggressive_split,
            "false_merge_count": aggressive_merge,
            "gold_same_pairs": aggressive_same,
            "gold_diff_pairs": aggressive_diff,
            "false_split_rate": aggressive_split / aggressive_same if aggressive_same else 0.0,
            "false_merge_rate": aggressive_merge / aggressive_diff if aggressive_diff else 0.0,
        },
    }

    weighted_profiles = {
        "equal_cost": {"false_merge_weight": 1, "false_split_weight": 1},
        "merge_is_2x": {"false_merge_weight": 2, "false_split_weight": 1},
        "merge_is_5x": {"false_merge_weight": 5, "false_split_weight": 1},
        "split_is_2x": {"false_merge_weight": 1, "false_split_weight": 2},
    }
    weighted_costs: dict[str, dict[str, Any]] = {}
    for profile_name, weights in weighted_profiles.items():
        conservative_cost = conservative_merge * weights["false_merge_weight"] + conservative_split * weights["false_split_weight"]
        aggressive_cost = aggressive_merge * weights["false_merge_weight"] + aggressive_split * weights["false_split_weight"]
        if conservative_cost < aggressive_cost:
            preferred = "conservative_exact_surface"
        elif aggressive_cost < conservative_cost:
            preferred = "aggressive_token_overlap"
        else:
            preferred = "tie"
        weighted_costs[profile_name] = {
            "false_merge_weight": weights["false_merge_weight"],
            "false_split_weight": weights["false_split_weight"],
            "conservative_cost": conservative_cost,
            "aggressive_cost": aggressive_cost,
            "preferred_strategy": preferred,
        }
    result["weighted_cost_profiles"] = weighted_costs
    return result


def summarize_tag_failures(
    trajectories: list[dict[str, Any]],
    score_report: dict[str, Any],
) -> dict[str, dict[str, list[str]]]:
    result: dict[str, dict[str, list[str]]] = {}
    for tag in REQUIRED_TAGS:
        result[tag] = {"phase0_current": [], "flat_rag": []}

    for baseline_name in ("phase0_current", "flat_rag"):
        per_trajectory = score_report["baselines"][baseline_name]["per_trajectory"]
        for trajectory in trajectories:
            trajectory_id = str(trajectory["trajectory_id"])
            tags = set(trajectory.get("coverage_tags", []))
            trajectory_steps = per_trajectory[trajectory_id]["steps"]
            active_exact = all(step["active_set_f1"] == 1.0 for step in trajectory_steps)
            invalidation_exact = all(
                json.dumps(step["gold_invalidations"], ensure_ascii=False, sort_keys=True)
                == json.dumps(step["predicted_invalidations"], ensure_ascii=False, sort_keys=True)
                for step in trajectory_steps
            )
            entity_resolution = per_trajectory[trajectory_id].get("entity_resolution", {})
            entity_exact = (
                float(entity_resolution.get("false_split_rate", 0.0)) == 0.0
                and float(entity_resolution.get("false_merge_rate", 0.0)) == 0.0
            )
            failed = not (active_exact and invalidation_exact)
            if "alias_trap" in tags and not entity_exact:
                failed = True
            if failed:
                for tag in tags:
                    if tag in result:
                        result[tag][baseline_name].append(trajectory_id)
    return result


def format_score_or_na(value: float | None) -> str:
    if value is None:
        return "NA"
    return f"{value:.3f}"


def render_invalidation_breakdown_lines(
    baseline_name: str,
    invalidation_by_tag: dict[str, dict[str, Any]],
) -> list[str]:
    lines = [f"### {baseline_name}", ""]
    for tag in REQUIRED_TAGS:
        stats = invalidation_by_tag[tag]
        lines.append(
            "- "
            + f"{tag}: P=`{format_score_or_na(stats['precision'])}` / R=`{format_score_or_na(stats['recall'])}` "
            + f"(TP/FP/FN=`{stats['true_positive_count']}/{stats['false_positive_count']}/{stats['false_negative_count']}`; "
            + f"pred/gold=`{stats['predicted_count']}/{stats['gold_count']}`)"
        )
    lines.append("")
    return lines


def decoy_precision_sink_conclusion(score_report: dict[str, Any]) -> dict[str, Any]:
    phase0 = score_report["baselines"]["phase0_current"]
    overall = phase0["metrics"]["invalidation_event_summary"]
    decoy = phase0["invalidation_by_tag"]["non_invalidation_decoy"]
    overall_fp = int(overall["false_positive_count"])
    decoy_fp = int(decoy["false_positive_count"])
    decoy_share = decoy_fp / overall_fp if overall_fp else 0.0
    is_primary_sink = decoy_share >= 0.5
    if is_primary_sink:
        statement = (
            "phase0 在 non_invalidation_decoy 上过度失效，precision 损失主要来源集中于 decoy，"
            "印证了 §3.3 中激进失效的代价，Phase 1 的失效裁定必须默认保守。"
        )
    else:
        statement = (
            "phase0 在 non_invalidation_decoy 上同样出现过度失效，但 precision 损失并不只集中在 decoy；"
            "partial / conditional / revival / provenance 也共同贡献了大量假阳性。"
            "这说明 §3.3 的问题不只是 decoy 咬钩，而是当前失效裁定整体偏激进，Phase 1 仍须默认保守。"
        )
    return {
        "overall_false_positive_count": overall_fp,
        "decoy_false_positive_count": decoy_fp,
        "decoy_false_positive_share": decoy_share,
        "is_primary_sink": is_primary_sink,
        "statement": statement,
    }


def render_completion_lines(score_report: dict[str, Any]) -> str:
    phase0 = score_report["baselines"]["phase0_current"]["metrics"]
    phase0_valid = phase0["valid_time_breakdown"]
    invalidation_by_tag = score_report["baselines"]["phase0_current"]["invalidation_by_tag"]
    provenance = invalidation_by_tag["provenance_conflict"]
    decoy = invalidation_by_tag["non_invalidation_decoy"]
    partial = invalidation_by_tag["partial"]
    conditional = invalidation_by_tag["conditional"]
    revival = invalidation_by_tag["revival"]
    out_of_order = invalidation_by_tag["out_of_order_late"]

    lines = [
        "# Phase 0.5 Completion Lines",
        "",
        "本文件记录 Phase 0.5 封板后的完成线写法。",
        "原则：按形态分别定，不用单一全局阈值拍板。",
        "",
        "## Invalidation",
        "",
        f"- full：基线水位为 P/R=`{format_score_or_na(invalidation_by_tag['full']['precision'])}/{format_score_or_na(invalidation_by_tag['full']['recall'])}`，Phase 1 不能回退。",
        f"- partial：当前 P/R=`{format_score_or_na(partial['precision'])}/{format_score_or_na(partial['recall'])}`，完成线写法为“从 0 到非零”，即 precision 与 recall 都必须首次高于 0。",
        f"- conditional：当前 P/R=`{format_score_or_na(conditional['precision'])}/{format_score_or_na(conditional['recall'])}`，完成线写法为“从 0 到非零”，即 precision 与 recall 都必须首次高于 0。",
        f"- revival：当前 P/R=`{format_score_or_na(revival['precision'])}/{format_score_or_na(revival['recall'])}`，完成线写法为“至少把 revival 事件从 full replace 中分离出来”，即 precision 与 recall 均需高于当前水位。",
        (
            "- provenance_conflict：当前 P/R="
            + f"`{format_score_or_na(provenance['precision'])}/{format_score_or_na(provenance['recall'])}`，"
            + "完成线是保守性门禁，按本基准可操作化为“false_positive_count = 0”，"
            + "也即 provenance 冲突不得再被误判为失效事件。"
        ),
        (
            "- non_invalidation_decoy：当前 P/R="
            + f"`{format_score_or_na(decoy['precision'])}/{format_score_or_na(decoy['recall'])}`，"
            + "完成线是保守性门禁，按本基准可操作化为“false_positive_count = 0”，"
            + "也即 decoy 子集上不得再咬出任何失效事件。"
        ),
        (
            "- out_of_order_late：当前 P/R="
            + f"`{format_score_or_na(out_of_order['precision'])}/{format_score_or_na(out_of_order['recall'])}`，"
            + "完成线写法为“保持 recall 不回退，同时提升 precision”，"
            + "也即迟到旧观测不再误触发多余失效。"
        ),
        "- alias_trap：该形态在 invalidation 维度当前无事件，P/R=`1.000/NA` 仅表示 pred/gold=`0/0`；封板不为其单设 invalidation 阈值，交由实体解析的 false-merge / false-split 维度约束。",
        "",
        "## Valid-Time",
        "",
        (
            "- valid-time-present：这不是常规阈值项。当前 observed_at 在场=`"
            + f"{phase0_valid['observed_at_present_correct']}/{phase0_valid['observed_at_present_total']}`，"
            + "完成线写法是“从 0/4 变为非零即算 Phase 1 达标起点”。"
        ),
        (
            "- valid-time fallback：当前缺失 observed_at 时回退到达序=`"
            + f"{phase0_valid['observed_at_absent_fallback_correct']}/{phase0_valid['observed_at_absent_fallback_total']}`，"
            + "完成线是不得回退。"
        ),
        "",
        "## Retrieval Waterline",
        "",
        f"- active-set Set-F1：当前水位=`{phase0['active_set_set_f1']:.3f}`，先记作基线水位，等待 Phase 1 再看是否与朴素基线拉开分离。",
        f"- must_include recall：当前水位=`{phase0['must_include_recall']:.3f}`，同样先记作基线水位，不在 Phase 0.5 封板时强行拔高。",
        "",
    ]
    return "\n".join(lines)


def render_seal_report(score_report: dict[str, Any]) -> str:
    phase0 = score_report["baselines"]["phase0_current"]["metrics"]
    flat = score_report["baselines"]["flat_rag"]["metrics"]
    phase0_valid = phase0["valid_time_breakdown"]
    decoy_conclusion = decoy_precision_sink_conclusion(score_report)
    phase0_invalidation_by_tag = score_report["baselines"]["phase0_current"]["invalidation_by_tag"]
    invalidation_precision_delta = phase0["invalidation_precision"] - flat["invalidation_precision"]
    invalidation_recall_delta = phase0["invalidation_recall"] - flat["invalidation_recall"]
    valid_time_present_delta = (
        phase0_valid["observed_at_present_accuracy"] - flat["valid_time_breakdown"]["observed_at_present_accuracy"]
    )
    classified_false_positive_count = sum(
        int(phase0_invalidation_by_tag[tag]["false_positive_count"]) for tag in REQUIRED_TAGS
    )
    overall_false_positive_count = int(phase0["invalidation_event_summary"]["false_positive_count"])
    unclassified_false_positive_count = overall_false_positive_count - classified_false_positive_count

    lines = [
        "# Phase 0.5 Seal Report",
        "",
        "## 封板结论",
        "",
        "- Phase 0.5 封板完成：基准已经把能力缺口、样本覆盖与完成线写法固定下来。",
        f"- invalidation 是当前唯一明确分离的指标族：precision 差值=`{invalidation_precision_delta:.3f}`，recall 差值=`{invalidation_recall_delta:.3f}`。",
        f"- valid-time-present 仍为能力缺失：phase0 == flat_rag，差值=`{valid_time_present_delta:.3f}`，observed_at 在场=`{phase0_valid['observed_at_present_correct']}/{phase0_valid['observed_at_present_total']}`。",
        "- 必要性结论保持诚实：当前只构成弱证成立，真正的分离仍要等 Phase 1 把 partial / conditional / valid-time 做出来。",
        f"- FP 归位核对：classified=`{classified_false_positive_count}` / overall=`{overall_false_positive_count}` / unclassified=`{unclassified_false_positive_count}`。",
        "",
        "## Invalidation By Tag",
        "",
    ]
    lines.extend(render_invalidation_breakdown_lines("phase0_current", score_report["baselines"]["phase0_current"]["invalidation_by_tag"]))
    lines.extend(render_invalidation_breakdown_lines("flat_rag", score_report["baselines"]["flat_rag"]["invalidation_by_tag"]))
    lines.extend(
        [
            "## Decoy 结论",
            "",
            (
                "- non_invalidation_decoy: "
                + f"false_positive_count=`{decoy_conclusion['decoy_false_positive_count']}` / "
                + f"overall_false_positive_count=`{decoy_conclusion['overall_false_positive_count']}` "
                + f"(share=`{decoy_conclusion['decoy_false_positive_share']:.3f}`)"
            ),
            f"- 写实结论：{decoy_conclusion['statement']}",
            "",
            "## 完成线",
            "",
            "- 详见 `phase05_completion_lines.md`；封板后不再用一个全局阈值覆盖所有形态。",
            "",
        ]
    )
    return "\n".join(lines)


def render_gap_register(
    validation: dict[str, Any],
    score_report: dict[str, Any],
    tag_failures: dict[str, dict[str, list[str]]],
) -> str:
    phase0 = score_report["baselines"]["phase0_current"]["metrics"]
    flat = score_report["baselines"]["flat_rag"]["metrics"]
    tradeoff = score_report["alias_strategy_tradeoff"]
    phase0_valid = phase0["valid_time_breakdown"]
    flat_valid = flat["valid_time_breakdown"]
    invalidation_precision_delta = phase0["invalidation_precision"] - flat["invalidation_precision"]
    invalidation_recall_delta = phase0["invalidation_recall"] - flat["invalidation_recall"]
    valid_time_present_delta = (
        phase0_valid["observed_at_present_accuracy"] - flat_valid["observed_at_present_accuracy"]
    )
    decoy_conclusion = decoy_precision_sink_conclusion(score_report)
    phase0_invalidation_by_tag = score_report["baselines"]["phase0_current"]["invalidation_by_tag"]
    classified_false_positive_count = sum(
        int(phase0_invalidation_by_tag[tag]["false_positive_count"]) for tag in REQUIRED_TAGS
    )
    overall_false_positive_count = int(phase0["invalidation_event_summary"]["false_positive_count"])
    unclassified_false_positive_count = overall_false_positive_count - classified_false_positive_count

    lines = [
        "# Phase 0.5 Gap Register",
        "",
        "本文件登记当前基线在 `Phase 0.5` 失效回放基准上的失败点。",
        "原则：只登记，不修复；失败是基准有效性的证据，不是要被抹平的噪音。",
        "",
        "## 基线总览",
        "",
        f"- validation_ok: `{str(validation['ok']).lower()}`",
        f"- phase0_current: invalidation P/R=`{phase0['invalidation_precision']:.3f}/{phase0['invalidation_recall']:.3f}`，active-set Set-F1=`{phase0['active_set_set_f1']:.3f}`，must_include recall=`{phase0['must_include_recall']:.3f}`，valid-time=`{phase0['valid_time_adjudication_accuracy']:.3f}`",
        f"- phase0_current.valid_time_breakdown: observed_at 在场=`{phase0_valid['observed_at_present_correct']}/{phase0_valid['observed_at_present_total']}`，缺失回退=`{phase0_valid['observed_at_absent_fallback_correct']}/{phase0_valid['observed_at_absent_fallback_total']}`",
        f"- flat_rag: invalidation P/R=`{flat['invalidation_precision']:.3f}/{flat['invalidation_recall']:.3f}`，active-set Set-F1=`{flat['active_set_set_f1']:.3f}`，must_include recall=`{flat['must_include_recall']:.3f}`，valid-time=`{flat['valid_time_adjudication_accuracy']:.3f}`",
        f"- flat_rag.valid_time_breakdown: observed_at 在场=`{flat_valid['observed_at_present_correct']}/{flat_valid['observed_at_present_total']}`，缺失回退=`{flat_valid['observed_at_absent_fallback_correct']}/{flat_valid['observed_at_absent_fallback_total']}`",
        f"- invalidation 分离: precision 差值=`{invalidation_precision_delta:.3f}`，recall 差值=`{invalidation_recall_delta:.3f}`；这是当前两基线唯一明确发生分离的指标族",
        f"- valid-time-present: phase0 == flat_rag，差值=`{valid_time_present_delta:.3f}` -> 该能力缺失，列为 Phase 1 硬目标，不记作 Phase 0.5 失败",
        f"- FP 归位核对: classified=`{classified_false_positive_count}` / overall=`{overall_false_positive_count}` / unclassified=`{unclassified_false_positive_count}`",
        "",
        "## 形态缺口",
        "",
        "### invalidation_by_tag",
        f"- full: P/R=`{format_score_or_na(phase0_invalidation_by_tag['full']['precision'])}/{format_score_or_na(phase0_invalidation_by_tag['full']['recall'])}`，TP/FP/FN=`{phase0_invalidation_by_tag['full']['true_positive_count']}/{phase0_invalidation_by_tag['full']['false_positive_count']}/{phase0_invalidation_by_tag['full']['false_negative_count']}`",
        f"- partial: P/R=`{format_score_or_na(phase0_invalidation_by_tag['partial']['precision'])}/{format_score_or_na(phase0_invalidation_by_tag['partial']['recall'])}`，TP/FP/FN=`{phase0_invalidation_by_tag['partial']['true_positive_count']}/{phase0_invalidation_by_tag['partial']['false_positive_count']}/{phase0_invalidation_by_tag['partial']['false_negative_count']}`",
        f"- conditional: P/R=`{format_score_or_na(phase0_invalidation_by_tag['conditional']['precision'])}/{format_score_or_na(phase0_invalidation_by_tag['conditional']['recall'])}`，TP/FP/FN=`{phase0_invalidation_by_tag['conditional']['true_positive_count']}/{phase0_invalidation_by_tag['conditional']['false_positive_count']}/{phase0_invalidation_by_tag['conditional']['false_negative_count']}`",
        f"- revival: P/R=`{format_score_or_na(phase0_invalidation_by_tag['revival']['precision'])}/{format_score_or_na(phase0_invalidation_by_tag['revival']['recall'])}`，TP/FP/FN=`{phase0_invalidation_by_tag['revival']['true_positive_count']}/{phase0_invalidation_by_tag['revival']['false_positive_count']}/{phase0_invalidation_by_tag['revival']['false_negative_count']}`",
        f"- alias_trap: P/R=`{format_score_or_na(phase0_invalidation_by_tag['alias_trap']['precision'])}/{format_score_or_na(phase0_invalidation_by_tag['alias_trap']['recall'])}`，TP/FP/FN=`{phase0_invalidation_by_tag['alias_trap']['true_positive_count']}/{phase0_invalidation_by_tag['alias_trap']['false_positive_count']}/{phase0_invalidation_by_tag['alias_trap']['false_negative_count']}`",
        f"- provenance_conflict: P/R=`{format_score_or_na(phase0_invalidation_by_tag['provenance_conflict']['precision'])}/{format_score_or_na(phase0_invalidation_by_tag['provenance_conflict']['recall'])}`，TP/FP/FN=`{phase0_invalidation_by_tag['provenance_conflict']['true_positive_count']}/{phase0_invalidation_by_tag['provenance_conflict']['false_positive_count']}/{phase0_invalidation_by_tag['provenance_conflict']['false_negative_count']}`",
        f"- non_invalidation_decoy: P/R=`{format_score_or_na(phase0_invalidation_by_tag['non_invalidation_decoy']['precision'])}/{format_score_or_na(phase0_invalidation_by_tag['non_invalidation_decoy']['recall'])}`，TP/FP/FN=`{phase0_invalidation_by_tag['non_invalidation_decoy']['true_positive_count']}/{phase0_invalidation_by_tag['non_invalidation_decoy']['false_positive_count']}/{phase0_invalidation_by_tag['non_invalidation_decoy']['false_negative_count']}`",
        f"- out_of_order_late: P/R=`{format_score_or_na(phase0_invalidation_by_tag['out_of_order_late']['precision'])}/{format_score_or_na(phase0_invalidation_by_tag['out_of_order_late']['recall'])}`，TP/FP/FN=`{phase0_invalidation_by_tag['out_of_order_late']['true_positive_count']}/{phase0_invalidation_by_tag['out_of_order_late']['false_positive_count']}/{phase0_invalidation_by_tag['out_of_order_late']['false_negative_count']}`",
        "",
        "### partial",
        f"- 失败轨迹：phase0_current={tag_failures['partial']['phase0_current']}，flat_rag={tag_failures['partial']['flat_rag']}",
        "- 结论：现有基线把同实体重复观测视为整节点替换，无法保留旧观测中未被触碰的子句。",
        "- 映射：对应白皮书 §3.1 所说的二值单调 current set 无法表达 partial invalidation。",
        "",
        "### conditional",
        f"- 失败轨迹：phase0_current={tag_failures['conditional']['phase0_current']}，flat_rag={tag_failures['conditional']['flat_rag']}",
        "- 结论：现有基线既不会显式刻画 carve-out，也不会把“全局规则 + 条件例外”作为并存当前态。",
        "- 映射：对应 §3.1 的 conditional invalidation 未支持。",
        "",
        "### revival",
        f"- 失败轨迹：phase0_current={tag_failures['revival']['phase0_current']}，flat_rag={tag_failures['revival']['flat_rag']}",
        "- 结论：现有基线最多能把后到观测当成新的 full replace，无法把 rollback / re-enable 标成 revival 形态。",
        "- 映射：对应 §3.1 的 revival / rollback 未支持。",
        "",
        "### alias_trap",
        f"- 失败轨迹：phase0_current={tag_failures['alias_trap']['phase0_current']}，flat_rag={tag_failures['alias_trap']['flat_rag']}",
        f"- conservative_exact_surface: false_split=`{tradeoff['conservative_exact_surface']['false_split_rate']:.3f}` ({tradeoff['conservative_exact_surface']['false_split_count']}/{tradeoff['conservative_exact_surface']['gold_same_pairs']})，false_merge=`{tradeoff['conservative_exact_surface']['false_merge_rate']:.3f}` ({tradeoff['conservative_exact_surface']['false_merge_count']}/{tradeoff['conservative_exact_surface']['gold_diff_pairs']})",
        f"- aggressive_token_overlap: false_split=`{tradeoff['aggressive_token_overlap']['false_split_rate']:.3f}` ({tradeoff['aggressive_token_overlap']['false_split_count']}/{tradeoff['aggressive_token_overlap']['gold_same_pairs']})，false_merge=`{tradeoff['aggressive_token_overlap']['false_merge_rate']:.3f}` ({tradeoff['aggressive_token_overlap']['false_merge_count']}/{tradeoff['aggressive_token_overlap']['gold_diff_pairs']})",
        f"- weighted_cost.equal_cost: conservative=`{tradeoff['weighted_cost_profiles']['equal_cost']['conservative_cost']}`，aggressive=`{tradeoff['weighted_cost_profiles']['equal_cost']['aggressive_cost']}`，preferred=`{tradeoff['weighted_cost_profiles']['equal_cost']['preferred_strategy']}`",
        f"- weighted_cost.split_is_2x: conservative=`{tradeoff['weighted_cost_profiles']['split_is_2x']['conservative_cost']}`，aggressive=`{tradeoff['weighted_cost_profiles']['split_is_2x']['aggressive_cost']}`，preferred=`{tradeoff['weighted_cost_profiles']['split_is_2x']['preferred_strategy']}`",
        f"- weighted_cost.merge_is_5x: conservative=`{tradeoff['weighted_cost_profiles']['merge_is_5x']['conservative_cost']}`，aggressive=`{tradeoff['weighted_cost_profiles']['merge_is_5x']['aggressive_cost']}`，preferred=`{tradeoff['weighted_cost_profiles']['merge_is_5x']['preferred_strategy']}`",
        "- 结论：保守合并降低误杀但放大 false-split；激进合并减少 split 却在 `Phoenix / Phoenix desk` 一类轨迹上引入 false-merge。",
        "- 映射：对应白皮书 §3.3 的“合并保守是否优于激进”必须由基准裁定，不能先验封板。",
        "",
        "### provenance_conflict",
        f"- 失败轨迹：phase0_current={tag_failures['provenance_conflict']['phase0_current']}，flat_rag={tag_failures['provenance_conflict']['flat_rag']}",
        "- 结论：当前两条基线都没有 source/provenance 权重，遇到高可信探针与低可信口述冲突时只会按到达顺序或窗口保留。",
        "- 映射：该缺口不属于当前二值 schema 的单一字段补丁，需要显式裁决策略。",
        "",
        "### non_invalidation_decoy",
        f"- 失败轨迹：phase0_current={tag_failures['non_invalidation_decoy']['phase0_current']}，flat_rag={tag_failures['non_invalidation_decoy']['flat_rag']}",
        f"- 统计：false_positive_count=`{decoy_conclusion['decoy_false_positive_count']}` / overall_false_positive_count=`{decoy_conclusion['overall_false_positive_count']}` (share=`{decoy_conclusion['decoy_false_positive_share']:.3f}`)",
        f"- 结论：{decoy_conclusion['statement']}",
        "- 映射：这暴露了 node-atomic replace 对 set-like facts 的过拟合。",
        "",
        "### out_of_order_late",
        f"- 失败轨迹：phase0_current={tag_failures['out_of_order_late']['phase0_current']}，flat_rag={tag_failures['out_of_order_late']['flat_rag']}",
        f"- 分项现状：observed_at 在场=`{phase0_valid['observed_at_present_correct']}/{phase0_valid['observed_at_present_total']}`，缺失回退=`{phase0_valid['observed_at_absent_fallback_correct']}/{phase0_valid['observed_at_absent_fallback_total']}`",
        "- 结论：这不是“0.500 抛硬币”，而是 observed_at 在场改判能力根本不存在；缺失时退回到达序这条回退路径则可工作。",
        "- 写实结论：valid-time-present 上 phase0 与 flat_rag 打平，差值为 0，这表示能力缺失，而不是 Phase 0.5 里某个可微调的小失误。",
        "- 映射：对应白皮书 §1.5 中 `observed_at` 缺失前，valid≈tx 假设在乱序/迟到下崩掉。",
        "",
        "## 红线结论",
        "",
        "- 当前报告不是“现有 schema 全过了”，而是明确记录哪些形态按预期失败。",
        "- 若后续某次运行让 `partial / conditional / revival / out_of_order_late` 全部无差别通过，应先怀疑基准被 fix-to-pass 污染。 ",
        "",
    ]
    return "\n".join(lines)


def render_summary(score_report: dict[str, Any]) -> str:
    phase0 = score_report["baselines"]["phase0_current"]["metrics"]
    flat = score_report["baselines"]["flat_rag"]["metrics"]
    tradeoff = score_report["alias_strategy_tradeoff"]
    phase0_valid = phase0["valid_time_breakdown"]
    flat_valid = flat["valid_time_breakdown"]
    decoy_conclusion = decoy_precision_sink_conclusion(score_report)
    gain_active = phase0["active_set_set_f1"] - flat["active_set_set_f1"]
    gain_must = phase0["must_include_recall"] - flat["must_include_recall"]
    invalidation_precision_delta = phase0["invalidation_precision"] - flat["invalidation_precision"]
    invalidation_recall_delta = phase0["invalidation_recall"] - flat["invalidation_recall"]
    valid_time_present_delta = (
        phase0_valid["observed_at_present_accuracy"] - flat_valid["observed_at_present_accuracy"]
    )
    active_word = "提升" if gain_active >= 0 else "下降"
    must_word = "提升" if gain_must >= 0 else "下降"

    lines = [
        "# Phase 0.5 评分摘要",
        "",
        "## 两条基线",
        "",
        f"- phase0_current: invalidation P/R=`{phase0['invalidation_precision']:.3f}/{phase0['invalidation_recall']:.3f}`，active-set Set-F1=`{phase0['active_set_set_f1']:.3f}`，must_include recall=`{phase0['must_include_recall']:.3f}`，valid-time=`{phase0['valid_time_adjudication_accuracy']:.3f}`",
        f"- phase0_current.valid_time_breakdown: observed_at 在场=`{phase0_valid['observed_at_present_correct']}/{phase0_valid['observed_at_present_total']}`，缺失回退=`{phase0_valid['observed_at_absent_fallback_correct']}/{phase0_valid['observed_at_absent_fallback_total']}`",
        f"- flat_rag: invalidation P/R=`{flat['invalidation_precision']:.3f}/{flat['invalidation_recall']:.3f}`，active-set Set-F1=`{flat['active_set_set_f1']:.3f}`，must_include recall=`{flat['must_include_recall']:.3f}`，valid-time=`{flat['valid_time_adjudication_accuracy']:.3f}`",
        f"- flat_rag.valid_time_breakdown: observed_at 在场=`{flat_valid['observed_at_present_correct']}/{flat_valid['observed_at_present_total']}`，缺失回退=`{flat_valid['observed_at_absent_fallback_correct']}/{flat_valid['observed_at_absent_fallback_total']}`",
        "",
        "## 初版结论",
        "",
        "- Phase 0.5 已进入封板并完成封板动作：先拆 invalidation P/R，再定完成线，最后把必要性弱证与 valid-time 从零起步写实。",
        f"- active-set / must_include 仍打平：phase0_current 相较 Flat RAG 在 active-set Set-F1 上{active_word} `{gain_active:.3f}`，在 must_include recall 上{must_word} `{gain_must:.3f}`。",
        f"- invalidation P/R 已补回：phase0_current 相较 flat_rag 的 precision 差值=`{invalidation_precision_delta:.3f}`，recall 差值=`{invalidation_recall_delta:.3f}`；这是当前唯一明确发生分离的指标族。",
        f"- decoy 检查结果：false_positive_count=`{decoy_conclusion['decoy_false_positive_count']}` / overall_false_positive_count=`{decoy_conclusion['overall_false_positive_count']}` (share=`{decoy_conclusion['decoy_false_positive_share']:.3f}`)；{decoy_conclusion['statement']}",
        f"- valid-time-present 已写实：phase0 == flat_rag，差值=`{valid_time_present_delta:.3f}`；observed_at 在场=`{phase0_valid['observed_at_present_correct']}/{phase0_valid['observed_at_present_total']}`，这表示能力缺失，列为 Phase 1 硬目标，不记作 Phase 0.5 失败。",
        f"- valid-time fallback 可工作：缺失 observed_at 时回退到达序=`{phase0_valid['observed_at_absent_fallback_correct']}/{phase0_valid['observed_at_absent_fallback_total']}`。",
        "- 必要性结论保持诚实：当前是弱证成立。唯一分离的 invalidation P/R 里，flat_rag 的静默覆盖不计为失效事件，因此真正的能力分离仍要等 Phase 1 把 partial / conditional / valid-time 做出来。",
        f"- alias 策略对比：保守合并 false_split=`{tradeoff['conservative_exact_surface']['false_split_rate']:.3f}` / false_merge=`{tradeoff['conservative_exact_surface']['false_merge_rate']:.3f}`；激进合并 false_split=`{tradeoff['aggressive_token_overlap']['false_split_rate']:.3f}` / false_merge=`{tradeoff['aggressive_token_overlap']['false_merge_rate']:.3f}`。",
        f"- 加权代价：equal_cost 偏向 `{tradeoff['weighted_cost_profiles']['equal_cost']['preferred_strategy']}`，split_is_2x 偏向 `{tradeoff['weighted_cost_profiles']['split_is_2x']['preferred_strategy']}`，merge_is_5x 偏向 `{tradeoff['weighted_cost_profiles']['merge_is_5x']['preferred_strategy']}`。",
        "- 结论不是“保守永远更优”，而是“是否更优必须看 false-split 与 false-merge 的真实代价比”。",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Score Phase 0.5 invalidation replay benchmark.")
    parser.add_argument(
        "--project-dir",
        default=str(repo_root() / "graph" / "projects" / "abu_modern" / "phase05_replay"),
        help="Phase 0.5 sandbox directory",
    )
    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    trajectories_dir = project_dir / "trajectories"
    gold_dir = project_dir / "gold"
    reports_dir = project_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    trajectories = [
        load_json(path)
        for path in sorted(trajectories_dir.glob("*.json"))
    ]
    golds = {
        path.name.replace(".gold", "").replace(".json", ""): load_json(path)
        for path in sorted(gold_dir.glob("*.gold.json"))
    }

    validation = validate_phase05(trajectories, golds)
    phase0_score = score_baseline(trajectories, golds, "phase0_current")
    flat_rag_score = score_baseline(trajectories, golds, "flat_rag")
    tradeoff = alias_strategy_tradeoff(trajectories, golds)

    score_report = {
        "validation": validation,
        "baselines": {
            "phase0_current": phase0_score,
            "flat_rag": flat_rag_score,
        },
        "alias_strategy_tradeoff": tradeoff,
    }

    tag_failures = summarize_tag_failures(trajectories, score_report)
    score_report["tag_failures"] = tag_failures

    coverage_matrix = render_coverage_matrix(trajectories)
    gap_register = render_gap_register(validation, score_report, tag_failures)
    summary_md = render_summary(score_report)
    seal_report_md = render_seal_report(score_report)
    completion_lines_md = render_completion_lines(score_report)

    (project_dir / "coverage_matrix.md").write_text(coverage_matrix, encoding="utf-8")
    (project_dir / "gap_register.md").write_text(gap_register, encoding="utf-8")
    (reports_dir / "phase05_score_summary.md").write_text(summary_md, encoding="utf-8")
    (reports_dir / "phase05_seal_report.md").write_text(seal_report_md, encoding="utf-8")
    (reports_dir / "phase05_completion_lines.md").write_text(completion_lines_md, encoding="utf-8")
    write_json(reports_dir / "phase05_score_report.json", score_report)

    print(f"Wrote coverage matrix: {project_dir / 'coverage_matrix.md'}")
    print(f"Wrote gap register: {project_dir / 'gap_register.md'}")
    print(f"Wrote score report: {reports_dir / 'phase05_score_report.json'}")
    print(f"Wrote score summary: {reports_dir / 'phase05_score_summary.md'}")
    print(f"Wrote seal report: {reports_dir / 'phase05_seal_report.md'}")
    print(f"Wrote completion lines: {reports_dir / 'phase05_completion_lines.md'}")
    return 0 if validation["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
