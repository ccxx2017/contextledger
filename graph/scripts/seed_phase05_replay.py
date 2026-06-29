#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
from pathlib import Path


def claim(claim_id: str, dimension: str, value: str, importance: str) -> dict:
    return {
        "claim_id": claim_id,
        "dimension": dimension,
        "value": value,
        "importance": importance,
    }


def obs(
    obs_id: str,
    mentions: list[str],
    statement: str,
    claims: list[dict],
    source_channel: str,
    provenance: str,
    observed_at: str | None,
    valid_from: str,
    valid_to: str | None = None,
) -> dict:
    return {
        "obs_id": obs_id,
        "observed_at": observed_at,
        "valid_from": valid_from,
        "valid_to": valid_to,
        "source": {
            "channel": source_channel,
            "provenance": provenance,
        },
        "mentions": mentions,
        "payload": {
            "statement": statement,
            "claim_bundle": claims,
        },
    }


def inval(
    source_obs_id: str,
    target_obs_id: str,
    kind: str,
    dropped: list[str],
    replacement: list[str] | None = None,
    kept: list[str] | None = None,
    carve_out: str | None = None,
) -> dict:
    item = {
        "source_obs_id": source_obs_id,
        "target_obs_id": target_obs_id,
        "kind": kind,
        "dropped_claims": dropped,
    }
    if replacement is not None:
        item["replacement_claims"] = replacement
    if kept is not None:
        item["kept_claims"] = kept
    if carve_out is not None:
        item["carve_out"] = carve_out
    return item


def cluster(cluster_id: str, mentions: list[str]) -> dict:
    return {
        "cluster_id": cluster_id,
        "mentions": mentions,
    }


def step(
    after_obs_id: str,
    active: list[str],
    invalidations: list[dict],
    clusters: list[dict],
    must_include: list[str],
    adjudications: list[dict] | None = None,
) -> dict:
    return {
        "after_obs_id": after_obs_id,
        "expected_active_set": active,
        "expected_invalidations": invalidations,
        "entity_clusters": clusters,
        "must_include": must_include,
        "valid_time_adjudication": {
            "adjudication_targets": adjudications or [],
        },
    }


def make_records() -> list[dict]:
    records: list[dict] = []

    records.append(
        {
            "trajectory": {
                "trajectory_id": "tr01_full_leverage_flip",
                "title": "整体风险口径翻转",
                "coverage_tags": ["full"],
                "observations": [
                    obs(
                        "tr01_obs01",
                        ["Risk Engine"],
                        "Risk Engine caps leverage at 2x and forbids overnight positions.",
                        [
                            claim("tr01.leverage_cap.2x", "leverage_cap", "2x", "critical"),
                            claim("tr01.overnight.forbidden", "overnight_rule", "forbidden", "critical"),
                        ],
                        "ops_chat",
                        "ops_chat#001",
                        "2026-06-01T09:00:00Z",
                        "2026-06-01T09:00:00Z",
                    ),
                    obs(
                        "tr01_obs02",
                        ["Risk Engine"],
                        "Risk Engine now caps leverage at 4x and allows overnight positions only for hedged books.",
                        [
                            claim("tr01.leverage_cap.4x", "leverage_cap", "4x", "critical"),
                            claim("tr01.overnight.hedged_only", "overnight_rule", "hedged_only", "critical"),
                        ],
                        "ops_chat",
                        "ops_chat#002",
                        "2026-06-01T11:00:00Z",
                        "2026-06-01T11:00:00Z",
                    ),
                ],
            },
            "gold": {
                "trajectory_id": "tr01_full_leverage_flip",
                "schema_neutral": True,
                "steps": [
                    step(
                        "tr01_obs01",
                        ["tr01.leverage_cap.2x", "tr01.overnight.forbidden"],
                        [],
                        [cluster("tr01_entity", ["Risk Engine"])],
                        ["tr01.leverage_cap.2x", "tr01.overnight.forbidden"],
                    ),
                    step(
                        "tr01_obs02",
                        ["tr01.leverage_cap.4x", "tr01.overnight.hedged_only"],
                        [
                            inval(
                                "tr01_obs02",
                                "tr01_obs01",
                                "full",
                                ["tr01.leverage_cap.2x", "tr01.overnight.forbidden"],
                                ["tr01.leverage_cap.4x", "tr01.overnight.hedged_only"],
                            )
                        ],
                        [cluster("tr01_entity", ["Risk Engine"])],
                        ["tr01.leverage_cap.4x", "tr01.overnight.hedged_only"],
                    ),
                ],
            },
        }
    )

    records.append(
        {
            "trajectory": {
                "trajectory_id": "tr02_full_vendor_switch",
                "title": "执行总线整体替换",
                "coverage_tags": ["full"],
                "observations": [
                    obs(
                        "tr02_obs01",
                        ["Execution bus"],
                        "Execution bus runs on Kafka.",
                        [claim("tr02.bus.kafka", "bus_choice", "kafka", "critical")],
                        "design_note",
                        "design_note#001",
                        "2026-06-02T08:00:00Z",
                        "2026-06-02T08:00:00Z",
                    ),
                    obs(
                        "tr02_obs02",
                        ["Execution bus"],
                        "Execution bus moves to Redis Streams.",
                        [claim("tr02.bus.redis_streams", "bus_choice", "redis_streams", "critical")],
                        "design_note",
                        "design_note#002",
                        "2026-06-02T12:00:00Z",
                        "2026-06-02T12:00:00Z",
                    ),
                ],
            },
            "gold": {
                "trajectory_id": "tr02_full_vendor_switch",
                "schema_neutral": True,
                "steps": [
                    step(
                        "tr02_obs01",
                        ["tr02.bus.kafka"],
                        [],
                        [cluster("tr02_entity", ["Execution bus"])],
                        ["tr02.bus.kafka"],
                    ),
                    step(
                        "tr02_obs02",
                        ["tr02.bus.redis_streams"],
                        [inval("tr02_obs02", "tr02_obs01", "full", ["tr02.bus.kafka"], ["tr02.bus.redis_streams"])],
                        [cluster("tr02_entity", ["Execution bus"])],
                        ["tr02.bus.redis_streams"],
                    ),
                ],
            },
        }
    )

    records.append(
        {
            "trajectory": {
                "trajectory_id": "tr03_partial_policy_clause",
                "title": "规则包只改其中一条子句",
                "coverage_tags": ["partial"],
                "observations": [
                    obs(
                        "tr03_obs01",
                        ["Order gateway policy"],
                        "Order gateway policy sets timeout to 30s, retries to 2, and keeps audit logging mandatory.",
                        [
                            claim("tr03.timeout.30s", "timeout", "30s", "critical"),
                            claim("tr03.retries.2", "retries", "2", "critical"),
                            claim("tr03.audit.required", "audit_logging", "required", "supporting"),
                        ],
                        "policy_doc",
                        "policy_doc#001",
                        "2026-06-03T09:00:00Z",
                        "2026-06-03T09:00:00Z",
                    ),
                    obs(
                        "tr03_obs02",
                        ["Order gateway policy"],
                        "Only the retry count changes from 2 to 4.",
                        [claim("tr03.retries.4", "retries", "4", "critical")],
                        "policy_doc",
                        "policy_doc#002",
                        "2026-06-03T10:30:00Z",
                        "2026-06-03T10:30:00Z",
                    ),
                ],
            },
            "gold": {
                "trajectory_id": "tr03_partial_policy_clause",
                "schema_neutral": True,
                "steps": [
                    step(
                        "tr03_obs01",
                        ["tr03.timeout.30s", "tr03.retries.2", "tr03.audit.required"],
                        [],
                        [cluster("tr03_entity", ["Order gateway policy"])],
                        ["tr03.timeout.30s", "tr03.retries.2"],
                    ),
                    step(
                        "tr03_obs02",
                        ["tr03.timeout.30s", "tr03.retries.4", "tr03.audit.required"],
                        [
                            inval(
                                "tr03_obs02",
                                "tr03_obs01",
                                "partial",
                                ["tr03.retries.2"],
                                ["tr03.retries.4"],
                                ["tr03.timeout.30s", "tr03.audit.required"],
                            )
                        ],
                        [cluster("tr03_entity", ["Order gateway policy"])],
                        ["tr03.timeout.30s", "tr03.retries.4"],
                    ),
                ],
            },
        }
    )

    records.append(
        {
            "trajectory": {
                "trajectory_id": "tr04_partial_checklist_clause",
                "title": "检查单删掉一个子项",
                "coverage_tags": ["partial"],
                "observations": [
                    obs(
                        "tr04_obs01",
                        ["Replay checklist"],
                        "Replay checklist requires backtest, paper trade, and slippage report.",
                        [
                            claim("tr04.backtest.required", "backtest", "required", "critical"),
                            claim("tr04.paper_trade.required", "paper_trade", "required", "critical"),
                            claim("tr04.slippage_report.required", "slippage_report", "required", "supporting"),
                        ],
                        "ops_runbook",
                        "ops_runbook#010",
                        "2026-06-04T09:00:00Z",
                        "2026-06-04T09:00:00Z",
                    ),
                    obs(
                        "tr04_obs02",
                        ["Replay checklist"],
                        "The slippage report item is no longer required for this checklist.",
                        [claim("tr04.slippage_report.not_required", "slippage_report", "not_required", "supporting")],
                        "ops_runbook",
                        "ops_runbook#011",
                        "2026-06-04T09:20:00Z",
                        "2026-06-04T09:20:00Z",
                    ),
                ],
            },
            "gold": {
                "trajectory_id": "tr04_partial_checklist_clause",
                "schema_neutral": True,
                "steps": [
                    step(
                        "tr04_obs01",
                        ["tr04.backtest.required", "tr04.paper_trade.required", "tr04.slippage_report.required"],
                        [],
                        [cluster("tr04_entity", ["Replay checklist"])],
                        ["tr04.backtest.required", "tr04.paper_trade.required"],
                    ),
                    step(
                        "tr04_obs02",
                        ["tr04.backtest.required", "tr04.paper_trade.required", "tr04.slippage_report.not_required"],
                        [
                            inval(
                                "tr04_obs02",
                                "tr04_obs01",
                                "partial",
                                ["tr04.slippage_report.required"],
                                ["tr04.slippage_report.not_required"],
                                ["tr04.backtest.required", "tr04.paper_trade.required"],
                            )
                        ],
                        [cluster("tr04_entity", ["Replay checklist"])],
                        ["tr04.backtest.required", "tr04.paper_trade.required"],
                    ),
                ],
            },
        }
    )

    records.append(
        {
            "trajectory": {
                "trajectory_id": "tr05_conditional_region_exception",
                "title": "全局禁令加区域例外",
                "coverage_tags": ["conditional"],
                "observations": [
                    obs(
                        "tr05_obs01",
                        ["Deployment rule"],
                        "Trading is blocked for every region.",
                        [claim("tr05.trading.blocked.global", "trade_permission", "blocked_global", "critical")],
                        "risk_memo",
                        "risk_memo#001",
                        "2026-06-05T08:00:00Z",
                        "2026-06-05T08:00:00Z",
                    ),
                    obs(
                        "tr05_obs02",
                        ["Deployment rule"],
                        "Tokyo desk may trade when running in simulation mode.",
                        [claim("tr05.trading.allowed.tokyo_sim", "trade_permission_exception", "tokyo_simulation_allowed", "critical")],
                        "risk_memo",
                        "risk_memo#002",
                        "2026-06-05T08:30:00Z",
                        "2026-06-05T08:30:00Z",
                    ),
                ],
            },
            "gold": {
                "trajectory_id": "tr05_conditional_region_exception",
                "schema_neutral": True,
                "steps": [
                    step(
                        "tr05_obs01",
                        ["tr05.trading.blocked.global"],
                        [],
                        [cluster("tr05_entity", ["Deployment rule"])],
                        ["tr05.trading.blocked.global"],
                    ),
                    step(
                        "tr05_obs02",
                        ["tr05.trading.blocked.global", "tr05.trading.allowed.tokyo_sim"],
                        [
                            inval(
                                "tr05_obs02",
                                "tr05_obs01",
                                "conditional",
                                [],
                                ["tr05.trading.allowed.tokyo_sim"],
                                ["tr05.trading.blocked.global"],
                                "desk=Tokyo AND mode=simulation",
                            )
                        ],
                        [cluster("tr05_entity", ["Deployment rule"])],
                        ["tr05.trading.blocked.global", "tr05.trading.allowed.tokyo_sim"],
                    ),
                ],
            },
        }
    )

    records.append(
        {
            "trajectory": {
                "trajectory_id": "tr06_conditional_window_exception",
                "title": "全天封锁加时间窗例外",
                "coverage_tags": ["conditional"],
                "observations": [
                    obs(
                        "tr06_obs01",
                        ["Risk gate"],
                        "Rebalances are blocked for the whole day.",
                        [claim("tr06.rebalance.blocked.all_day", "rebalance_window", "blocked_all_day", "critical")],
                        "risk_note",
                        "risk_note#020",
                        "2026-06-06T08:00:00Z",
                        "2026-06-06T08:00:00Z",
                    ),
                    obs(
                        "tr06_obs02",
                        ["Risk gate"],
                        "Rebalances may run during the 15:00-15:30 close auction window.",
                        [claim("tr06.rebalance.allowed.close_auction", "rebalance_window_exception", "close_auction_allowed", "critical")],
                        "risk_note",
                        "risk_note#021",
                        "2026-06-06T08:40:00Z",
                        "2026-06-06T08:40:00Z",
                    ),
                ],
            },
            "gold": {
                "trajectory_id": "tr06_conditional_window_exception",
                "schema_neutral": True,
                "steps": [
                    step(
                        "tr06_obs01",
                        ["tr06.rebalance.blocked.all_day"],
                        [],
                        [cluster("tr06_entity", ["Risk gate"])],
                        ["tr06.rebalance.blocked.all_day"],
                    ),
                    step(
                        "tr06_obs02",
                        ["tr06.rebalance.blocked.all_day", "tr06.rebalance.allowed.close_auction"],
                        [
                            inval(
                                "tr06_obs02",
                                "tr06_obs01",
                                "conditional",
                                [],
                                ["tr06.rebalance.allowed.close_auction"],
                                ["tr06.rebalance.blocked.all_day"],
                                "time_window=15:00-15:30",
                            )
                        ],
                        [cluster("tr06_entity", ["Risk gate"])],
                        ["tr06.rebalance.blocked.all_day", "tr06.rebalance.allowed.close_auction"],
                    ),
                ],
            },
        }
    )

    records.append(
        {
            "trajectory": {
                "trajectory_id": "tr07_revival_feature_flag",
                "title": "关闭后再次启用功能",
                "coverage_tags": ["revival"],
                "observations": [
                    obs(
                        "tr07_obs01",
                        ["Alpha feature"],
                        "Alpha feature is enabled.",
                        [claim("tr07.feature.enabled.v1", "feature_flag", "enabled", "critical")],
                        "release_note",
                        "release_note#001",
                        "2026-06-07T08:00:00Z",
                        "2026-06-07T08:00:00Z",
                    ),
                    obs(
                        "tr07_obs02",
                        ["Alpha feature"],
                        "Alpha feature is disabled because of instability.",
                        [claim("tr07.feature.disabled", "feature_flag", "disabled", "critical")],
                        "incident_note",
                        "incident_note#003",
                        "2026-06-07T09:00:00Z",
                        "2026-06-07T09:00:00Z",
                    ),
                    obs(
                        "tr07_obs03",
                        ["Alpha feature"],
                        "Alpha feature is enabled again after rollback fixes.",
                        [claim("tr07.feature.enabled.v2", "feature_flag", "enabled_again", "critical")],
                        "release_note",
                        "release_note#004",
                        "2026-06-07T13:00:00Z",
                        "2026-06-07T13:00:00Z",
                    ),
                ],
            },
            "gold": {
                "trajectory_id": "tr07_revival_feature_flag",
                "schema_neutral": True,
                "steps": [
                    step(
                        "tr07_obs01",
                        ["tr07.feature.enabled.v1"],
                        [],
                        [cluster("tr07_entity", ["Alpha feature"])],
                        ["tr07.feature.enabled.v1"],
                    ),
                    step(
                        "tr07_obs02",
                        ["tr07.feature.disabled"],
                        [inval("tr07_obs02", "tr07_obs01", "full", ["tr07.feature.enabled.v1"], ["tr07.feature.disabled"])],
                        [cluster("tr07_entity", ["Alpha feature"])],
                        ["tr07.feature.disabled"],
                    ),
                    step(
                        "tr07_obs03",
                        ["tr07.feature.enabled.v2"],
                        [inval("tr07_obs03", "tr07_obs02", "revival", ["tr07.feature.disabled"], ["tr07.feature.enabled.v2"])],
                        [cluster("tr07_entity", ["Alpha feature"])],
                        ["tr07.feature.enabled.v2"],
                    ),
                ],
            },
        }
    )

    records.append(
        {
            "trajectory": {
                "trajectory_id": "tr08_revival_research_stream",
                "title": "暂停后恢复研究流",
                "coverage_tags": ["revival"],
                "observations": [
                    obs(
                        "tr08_obs01",
                        ["Research stream"],
                        "Research stream is active.",
                        [claim("tr08.stream.active.v1", "stream_state", "active", "critical")],
                        "program_board",
                        "program_board#011",
                        "2026-06-08T08:00:00Z",
                        "2026-06-08T08:00:00Z",
                    ),
                    obs(
                        "tr08_obs02",
                        ["Research stream"],
                        "Research stream is paused to save budget.",
                        [claim("tr08.stream.paused", "stream_state", "paused", "critical")],
                        "program_board",
                        "program_board#012",
                        "2026-06-08T11:00:00Z",
                        "2026-06-08T11:00:00Z",
                    ),
                    obs(
                        "tr08_obs03",
                        ["Research stream"],
                        "Research stream resumes after budget is restored.",
                        [claim("tr08.stream.active.v2", "stream_state", "active_again", "critical")],
                        "program_board",
                        "program_board#013",
                        "2026-06-08T15:00:00Z",
                        "2026-06-08T15:00:00Z",
                    ),
                ],
            },
            "gold": {
                "trajectory_id": "tr08_revival_research_stream",
                "schema_neutral": True,
                "steps": [
                    step(
                        "tr08_obs01",
                        ["tr08.stream.active.v1"],
                        [],
                        [cluster("tr08_entity", ["Research stream"])],
                        ["tr08.stream.active.v1"],
                    ),
                    step(
                        "tr08_obs02",
                        ["tr08.stream.paused"],
                        [inval("tr08_obs02", "tr08_obs01", "full", ["tr08.stream.active.v1"], ["tr08.stream.paused"])],
                        [cluster("tr08_entity", ["Research stream"])],
                        ["tr08.stream.paused"],
                    ),
                    step(
                        "tr08_obs03",
                        ["tr08.stream.active.v2"],
                        [inval("tr08_obs03", "tr08_obs02", "revival", ["tr08.stream.paused"], ["tr08.stream.active.v2"])],
                        [cluster("tr08_entity", ["Research stream"])],
                        ["tr08.stream.active.v2"],
                    ),
                ],
            },
        }
    )

    records.append(
        {
            "trajectory": {
                "trajectory_id": "tr09_alias_same_service",
                "title": "同一服务的别名写法",
                "coverage_tags": ["alias_trap"],
                "observations": [
                    obs(
                        "tr09_obs01",
                        ["Mercury feed"],
                        "Mercury feed keeps latency guard enabled.",
                        [claim("tr09.latency_guard.on", "latency_guard", "on", "critical")],
                        "service_note",
                        "service_note#001",
                        "2026-06-09T08:00:00Z",
                        "2026-06-09T08:00:00Z",
                    ),
                    obs(
                        "tr09_obs02",
                        ["mercury-feed"],
                        "mercury-feed is owned by market data.",
                        [claim("tr09.owner.market_data", "owner", "market_data", "supporting")],
                        "service_note",
                        "service_note#002",
                        "2026-06-09T08:20:00Z",
                        "2026-06-09T08:20:00Z",
                    ),
                ],
            },
            "gold": {
                "trajectory_id": "tr09_alias_same_service",
                "schema_neutral": True,
                "steps": [
                    step(
                        "tr09_obs01",
                        ["tr09.latency_guard.on"],
                        [],
                        [cluster("tr09_entity", ["Mercury feed"])],
                        ["tr09.latency_guard.on"],
                    ),
                    step(
                        "tr09_obs02",
                        ["tr09.latency_guard.on", "tr09.owner.market_data"],
                        [],
                        [cluster("tr09_entity", ["Mercury feed", "mercury-feed"])],
                        ["tr09.latency_guard.on"],
                    ),
                ],
            },
        }
    )

    records.append(
        {
            "trajectory": {
                "trajectory_id": "tr10_alias_same_person",
                "title": "同一人的不同表面形式",
                "coverage_tags": ["alias_trap"],
                "observations": [
                    obs(
                        "tr10_obs01",
                        ["M. Chen"],
                        "M. Chen must review final changes.",
                        [claim("tr10.reviewer.required", "review_gate", "required", "critical")],
                        "staff_note",
                        "staff_note#001",
                        "2026-06-10T08:00:00Z",
                        "2026-06-10T08:00:00Z",
                    ),
                    obs(
                        "tr10_obs02",
                        ["Mei Chen"],
                        "Mei Chen works in UTC+8.",
                        [claim("tr10.timezone.utc_plus_8", "timezone", "UTC+8", "supporting")],
                        "staff_note",
                        "staff_note#002",
                        "2026-06-10T08:10:00Z",
                        "2026-06-10T08:10:00Z",
                    ),
                ],
            },
            "gold": {
                "trajectory_id": "tr10_alias_same_person",
                "schema_neutral": True,
                "steps": [
                    step(
                        "tr10_obs01",
                        ["tr10.reviewer.required"],
                        [],
                        [cluster("tr10_person", ["M. Chen"])],
                        ["tr10.reviewer.required"],
                    ),
                    step(
                        "tr10_obs02",
                        ["tr10.reviewer.required", "tr10.timezone.utc_plus_8"],
                        [],
                        [cluster("tr10_person", ["M. Chen", "Mei Chen"])],
                        ["tr10.reviewer.required"],
                    ),
                ],
            },
        }
    )

    records.append(
        {
            "trajectory": {
                "trajectory_id": "tr11_provenance_conflict",
                "title": "高可信探针与低可信口述冲突",
                "coverage_tags": ["provenance_conflict"],
                "observations": [
                    obs(
                        "tr11_obs01",
                        ["Broker adapter"],
                        "Probe says broker adapter is not ready for production.",
                        [claim("tr11.prod_ready.false", "prod_readiness", "false", "critical")],
                        "probe_log",
                        "probe_log#771",
                        "2026-06-11T08:00:00Z",
                        "2026-06-11T08:00:00Z",
                    ),
                    obs(
                        "tr11_obs02",
                        ["Broker adapter"],
                        "A user note says broker adapter should be considered production ready.",
                        [claim("tr11.prod_ready.true", "prod_readiness", "true", "critical")],
                        "user_note",
                        "user_note#771",
                        "2026-06-11T08:30:00Z",
                        "2026-06-11T08:30:00Z",
                    ),
                ],
            },
            "gold": {
                "trajectory_id": "tr11_provenance_conflict",
                "schema_neutral": True,
                "steps": [
                    step(
                        "tr11_obs01",
                        ["tr11.prod_ready.false"],
                        [],
                        [cluster("tr11_entity", ["Broker adapter"])],
                        ["tr11.prod_ready.false"],
                    ),
                    step(
                        "tr11_obs02",
                        ["tr11.prod_ready.false"],
                        [],
                        [cluster("tr11_entity", ["Broker adapter"])],
                        ["tr11.prod_ready.false"],
                    ),
                ],
            },
        }
    )

    records.append(
        {
            "trajectory": {
                "trajectory_id": "tr12_non_invalidation_parallel_targets",
                "title": "同主题不同目标并存",
                "coverage_tags": ["non_invalidation_decoy"],
                "observations": [
                    obs(
                        "tr12_obs01",
                        ["Deployment allow-list"],
                        "Staging is allowed as a deployment target.",
                        [claim("tr12.target.staging.allowed", "allowed_targets", "staging", "critical")],
                        "release_sheet",
                        "release_sheet#001",
                        "2026-06-12T08:00:00Z",
                        "2026-06-12T08:00:00Z",
                    ),
                    obs(
                        "tr12_obs02",
                        ["Deployment allow-list"],
                        "Canary is also allowed as a deployment target.",
                        [claim("tr12.target.canary.allowed", "allowed_targets", "canary", "critical")],
                        "release_sheet",
                        "release_sheet#002",
                        "2026-06-12T08:05:00Z",
                        "2026-06-12T08:05:00Z",
                    ),
                ],
            },
            "gold": {
                "trajectory_id": "tr12_non_invalidation_parallel_targets",
                "schema_neutral": True,
                "steps": [
                    step(
                        "tr12_obs01",
                        ["tr12.target.staging.allowed"],
                        [],
                        [cluster("tr12_entity", ["Deployment allow-list"])],
                        ["tr12.target.staging.allowed"],
                    ),
                    step(
                        "tr12_obs02",
                        ["tr12.target.staging.allowed", "tr12.target.canary.allowed"],
                        [],
                        [cluster("tr12_entity", ["Deployment allow-list"])],
                        ["tr12.target.staging.allowed", "tr12.target.canary.allowed"],
                    ),
                ],
            },
        }
    )

    records.append(
        {
            "trajectory": {
                "trajectory_id": "tr13_non_invalidation_parallel_modes",
                "title": "同一栏位的多值并列",
                "coverage_tags": ["non_invalidation_decoy"],
                "observations": [
                    obs(
                        "tr13_obs01",
                        ["Allowed modes"],
                        "Paper mode is allowed.",
                        [claim("tr13.mode.paper.allowed", "allowed_modes", "paper", "critical")],
                        "mode_sheet",
                        "mode_sheet#001",
                        "2026-06-13T08:00:00Z",
                        "2026-06-13T08:00:00Z",
                    ),
                    obs(
                        "tr13_obs02",
                        ["Allowed modes"],
                        "Simulation mode is allowed as well.",
                        [claim("tr13.mode.simulation.allowed", "allowed_modes", "simulation", "critical")],
                        "mode_sheet",
                        "mode_sheet#002",
                        "2026-06-13T08:05:00Z",
                        "2026-06-13T08:05:00Z",
                    ),
                ],
            },
            "gold": {
                "trajectory_id": "tr13_non_invalidation_parallel_modes",
                "schema_neutral": True,
                "steps": [
                    step(
                        "tr13_obs01",
                        ["tr13.mode.paper.allowed"],
                        [],
                        [cluster("tr13_entity", ["Allowed modes"])],
                        ["tr13.mode.paper.allowed"],
                    ),
                    step(
                        "tr13_obs02",
                        ["tr13.mode.paper.allowed", "tr13.mode.simulation.allowed"],
                        [],
                        [cluster("tr13_entity", ["Allowed modes"])],
                        ["tr13.mode.paper.allowed", "tr13.mode.simulation.allowed"],
                    ),
                ],
            },
        }
    )

    records.append(
        {
            "trajectory": {
                "trajectory_id": "tr14_out_of_order_with_observed_at",
                "title": "迟到旧观测不应反杀新观测",
                "coverage_tags": ["out_of_order_late"],
                "observations": [
                    obs(
                        "tr14_obs01",
                        ["Inventory snapshot"],
                        "Inventory is 10 units.",
                        [claim("tr14.inventory.10", "inventory", "10", "critical")],
                        "warehouse_feed",
                        "warehouse_feed#1005",
                        "2026-06-14T10:05:00Z",
                        "2026-06-14T10:05:00Z",
                    ),
                    obs(
                        "tr14_obs02",
                        ["Inventory snapshot"],
                        "Inventory is 0 units.",
                        [claim("tr14.inventory.0", "inventory", "0", "critical")],
                        "warehouse_feed",
                        "warehouse_feed#1000_late",
                        "2026-06-14T10:00:00Z",
                        "2026-06-14T10:00:00Z",
                    ),
                ],
            },
            "gold": {
                "trajectory_id": "tr14_out_of_order_with_observed_at",
                "schema_neutral": True,
                "steps": [
                    step(
                        "tr14_obs01",
                        ["tr14.inventory.10"],
                        [],
                        [cluster("tr14_entity", ["Inventory snapshot"])],
                        ["tr14.inventory.10"],
                        [{"entity_cluster_id": "tr14_entity", "dimension": "inventory", "winner_obs_id": "tr14_obs01", "fallback_used": False}],
                    ),
                    step(
                        "tr14_obs02",
                        ["tr14.inventory.10"],
                        [],
                        [cluster("tr14_entity", ["Inventory snapshot"])],
                        ["tr14.inventory.10"],
                        [{"entity_cluster_id": "tr14_entity", "dimension": "inventory", "winner_obs_id": "tr14_obs01", "fallback_used": False}],
                    ),
                ],
            },
        }
    )

    records.append(
        {
            "trajectory": {
                "trajectory_id": "tr15_missing_observed_at_fallback",
                "title": "缺少 observed_at 时退回到达序",
                "coverage_tags": ["full", "out_of_order_late"],
                "observations": [
                    obs(
                        "tr15_obs01",
                        ["Queue depth"],
                        "Queue depth is 8.",
                        [claim("tr15.queue_depth.8", "queue_depth", "8", "critical")],
                        "queue_board",
                        "queue_board#001",
                        None,
                        "2026-06-15T08:00:00Z",
                    ),
                    obs(
                        "tr15_obs02",
                        ["Queue depth"],
                        "Queue depth is 20.",
                        [claim("tr15.queue_depth.20", "queue_depth", "20", "critical")],
                        "queue_board",
                        "queue_board#002",
                        None,
                        "2026-06-15T08:01:00Z",
                    ),
                ],
            },
            "gold": {
                "trajectory_id": "tr15_missing_observed_at_fallback",
                "schema_neutral": True,
                "steps": [
                    step(
                        "tr15_obs01",
                        ["tr15.queue_depth.8"],
                        [],
                        [cluster("tr15_entity", ["Queue depth"])],
                        ["tr15.queue_depth.8"],
                        [{"entity_cluster_id": "tr15_entity", "dimension": "queue_depth", "winner_obs_id": "tr15_obs01", "fallback_used": True}],
                    ),
                    step(
                        "tr15_obs02",
                        ["tr15.queue_depth.20"],
                        [inval("tr15_obs02", "tr15_obs01", "full", ["tr15.queue_depth.8"], ["tr15.queue_depth.20"])],
                        [cluster("tr15_entity", ["Queue depth"])],
                        ["tr15.queue_depth.20"],
                        [{"entity_cluster_id": "tr15_entity", "dimension": "queue_depth", "winner_obs_id": "tr15_obs02", "fallback_used": True}],
                    ),
                ],
            },
        }
    )

    records.append(
        {
            "trajectory": {
                "trajectory_id": "tr16_alias_false_merge_trap",
                "title": "别名合并的误杀陷阱",
                "coverage_tags": ["alias_trap", "non_invalidation_decoy"],
                "observations": [
                    obs(
                        "tr16_obs01",
                        ["Phoenix"],
                        "Phoenix is owned by infra on-call.",
                        [claim("tr16.phoenix_infra.owner", "owner", "infra_on_call", "critical")],
                        "naming_sheet",
                        "naming_sheet#001",
                        "2026-06-16T08:00:00Z",
                        "2026-06-16T08:00:00Z",
                    ),
                    obs(
                        "tr16_obs02",
                        ["Phoenix desk"],
                        "Phoenix desk is led by the APAC desk lead.",
                        [claim("tr16.phoenix_desk.owner", "owner", "apac_desk_lead", "supporting")],
                        "naming_sheet",
                        "naming_sheet#002",
                        "2026-06-16T08:05:00Z",
                        "2026-06-16T08:05:00Z",
                    ),
                ],
            },
            "gold": {
                "trajectory_id": "tr16_alias_false_merge_trap",
                "schema_neutral": True,
                "steps": [
                    step(
                        "tr16_obs01",
                        ["tr16.phoenix_infra.owner"],
                        [],
                        [cluster("tr16_entity_a", ["Phoenix"])],
                        ["tr16.phoenix_infra.owner"],
                    ),
                    step(
                        "tr16_obs02",
                        ["tr16.phoenix_infra.owner", "tr16.phoenix_desk.owner"],
                        [],
                        [cluster("tr16_entity_a", ["Phoenix"]), cluster("tr16_entity_b", ["Phoenix desk"])],
                        ["tr16.phoenix_infra.owner"],
                    ),
                ],
            },
        }
    )

    records.append(
        {
            "trajectory": {
                "trajectory_id": "tr17_provenance_conflict_probe_wins",
                "title": "探针压过口述",
                "coverage_tags": ["provenance_conflict"],
                "observations": [
                    obs(
                        "tr17_obs01",
                        ["Risk snapshot"],
                        "Probe shows circuit breaker is armed.",
                        [claim("tr17.circuit_breaker.armed", "circuit_breaker", "armed", "critical")],
                        "probe_log",
                        "probe_log#880",
                        "2026-06-17T08:00:00Z",
                        "2026-06-17T08:00:00Z",
                    ),
                    obs(
                        "tr17_obs02",
                        ["Risk snapshot"],
                        "A user note says circuit breaker should be considered disarmed.",
                        [claim("tr17.circuit_breaker.disarmed", "circuit_breaker", "disarmed", "critical")],
                        "user_note",
                        "user_note#880",
                        "2026-06-17T08:05:00Z",
                        "2026-06-17T08:05:00Z",
                    ),
                ],
            },
            "gold": {
                "trajectory_id": "tr17_provenance_conflict_probe_wins",
                "schema_neutral": True,
                "steps": [
                    step(
                        "tr17_obs01",
                        ["tr17.circuit_breaker.armed"],
                        [],
                        [cluster("tr17_entity", ["Risk snapshot"])],
                        ["tr17.circuit_breaker.armed"],
                    ),
                    step(
                        "tr17_obs02",
                        ["tr17.circuit_breaker.armed"],
                        [],
                        [cluster("tr17_entity", ["Risk snapshot"])],
                        ["tr17.circuit_breaker.armed"],
                    ),
                ],
            },
        }
    )

    records.append(
        {
            "trajectory": {
                "trajectory_id": "tr18_provenance_conflict_policy_wins",
                "title": "规范压过随手备注",
                "coverage_tags": ["provenance_conflict"],
                "observations": [
                    obs(
                        "tr18_obs01",
                        ["Broker adapter retries"],
                        "Official policy says broker adapter retries are capped at 2.",
                        [claim("tr18.retries.2", "retry_cap", "2", "critical")],
                        "policy_doc",
                        "policy_doc#880",
                        "2026-06-18T08:00:00Z",
                        "2026-06-18T08:00:00Z",
                    ),
                    obs(
                        "tr18_obs02",
                        ["Broker adapter retries"],
                        "A user note says retries can be treated as 4 during the incident.",
                        [claim("tr18.retries.4", "retry_cap", "4", "critical")],
                        "user_note",
                        "user_note#881",
                        "2026-06-18T08:03:00Z",
                        "2026-06-18T08:03:00Z",
                    ),
                ],
            },
            "gold": {
                "trajectory_id": "tr18_provenance_conflict_policy_wins",
                "schema_neutral": True,
                "steps": [
                    step(
                        "tr18_obs01",
                        ["tr18.retries.2"],
                        [],
                        [cluster("tr18_entity", ["Broker adapter retries"])],
                        ["tr18.retries.2"],
                    ),
                    step(
                        "tr18_obs02",
                        ["tr18.retries.2"],
                        [],
                        [cluster("tr18_entity", ["Broker adapter retries"])],
                        ["tr18.retries.2"],
                    ),
                ],
            },
        }
    )

    records.append(
        {
            "trajectory": {
                "trajectory_id": "tr19_alias_abbreviation_split_trap",
                "title": "缩写与全称的别名陷阱",
                "coverage_tags": ["alias_trap"],
                "observations": [
                    obs(
                        "tr19_obs01",
                        ["OMS"],
                        "OMS owns the final routing approval.",
                        [claim("tr19.routing_approval.owner", "routing_approval_owner", "oms", "critical")],
                        "naming_sheet",
                        "naming_sheet#101",
                        "2026-06-19T08:00:00Z",
                        "2026-06-19T08:00:00Z",
                    ),
                    obs(
                        "tr19_obs02",
                        ["order manager"],
                        "order manager runs on the same ownership lane.",
                        [claim("tr19.runtime.owner", "runtime_owner", "oms", "supporting")],
                        "naming_sheet",
                        "naming_sheet#102",
                        "2026-06-19T08:02:00Z",
                        "2026-06-19T08:02:00Z",
                    ),
                ],
            },
            "gold": {
                "trajectory_id": "tr19_alias_abbreviation_split_trap",
                "schema_neutral": True,
                "steps": [
                    step(
                        "tr19_obs01",
                        ["tr19.routing_approval.owner"],
                        [],
                        [cluster("tr19_entity", ["OMS"])],
                        ["tr19.routing_approval.owner"],
                    ),
                    step(
                        "tr19_obs02",
                        ["tr19.routing_approval.owner", "tr19.runtime.owner"],
                        [],
                        [cluster("tr19_entity", ["OMS", "order manager"])],
                        ["tr19.routing_approval.owner"],
                    ),
                ],
            },
        }
    )

    records.append(
        {
            "trajectory": {
                "trajectory_id": "tr20_alias_false_merge_shared_token",
                "title": "共享词导致误合并",
                "coverage_tags": ["alias_trap"],
                "observations": [
                    obs(
                        "tr20_obs01",
                        ["Atlas"],
                        "Atlas is owned by infra scheduling.",
                        [claim("tr20.atlas.owner", "owner", "infra_scheduling", "critical")],
                        "naming_sheet",
                        "naming_sheet#201",
                        "2026-06-20T08:00:00Z",
                        "2026-06-20T08:00:00Z",
                    ),
                    obs(
                        "tr20_obs02",
                        ["Atlas desk"],
                        "Atlas desk is run by the APAC desk lead.",
                        [claim("tr20.atlas_desk.owner", "owner", "apac_desk_lead", "supporting")],
                        "naming_sheet",
                        "naming_sheet#202",
                        "2026-06-20T08:03:00Z",
                        "2026-06-20T08:03:00Z",
                    ),
                ],
            },
            "gold": {
                "trajectory_id": "tr20_alias_false_merge_shared_token",
                "schema_neutral": True,
                "steps": [
                    step(
                        "tr20_obs01",
                        ["tr20.atlas.owner"],
                        [],
                        [cluster("tr20_entity_a", ["Atlas"])],
                        ["tr20.atlas.owner"],
                    ),
                    step(
                        "tr20_obs02",
                        ["tr20.atlas.owner", "tr20.atlas_desk.owner"],
                        [],
                        [cluster("tr20_entity_a", ["Atlas"]), cluster("tr20_entity_b", ["Atlas desk"])],
                        ["tr20.atlas.owner"],
                    ),
                ],
            },
        }
    )

    records.append(
        {
            "trajectory": {
                "trajectory_id": "tr21_alias_mixed_cost_profile",
                "title": "别名 split 与 merge 代价混合案例",
                "coverage_tags": ["alias_trap", "non_invalidation_decoy"],
                "observations": [
                    obs(
                        "tr21_obs01",
                        ["OMS"],
                        "OMS owns the release gate.",
                        [claim("tr21.release_gate.owner", "release_gate_owner", "oms", "critical")],
                        "naming_sheet",
                        "naming_sheet#301",
                        "2026-06-21T08:00:00Z",
                        "2026-06-21T08:00:00Z",
                    ),
                    obs(
                        "tr21_obs02",
                        ["order manager"],
                        "order manager is the same platform behind the release gate.",
                        [claim("tr21.platform.identity", "platform_identity", "oms_platform", "supporting")],
                        "naming_sheet",
                        "naming_sheet#302",
                        "2026-06-21T08:02:00Z",
                        "2026-06-21T08:02:00Z",
                    ),
                    obs(
                        "tr21_obs03",
                        ["OMS desk"],
                        "OMS desk is staffed by the APAC trading lead.",
                        [claim("tr21.oms_desk.owner", "desk_owner", "apac_trading_lead", "supporting")],
                        "naming_sheet",
                        "naming_sheet#303",
                        "2026-06-21T08:04:00Z",
                        "2026-06-21T08:04:00Z",
                    ),
                ],
            },
            "gold": {
                "trajectory_id": "tr21_alias_mixed_cost_profile",
                "schema_neutral": True,
                "steps": [
                    step(
                        "tr21_obs01",
                        ["tr21.release_gate.owner"],
                        [],
                        [cluster("tr21_entity_a", ["OMS"])],
                        ["tr21.release_gate.owner"],
                    ),
                    step(
                        "tr21_obs02",
                        ["tr21.release_gate.owner", "tr21.platform.identity"],
                        [],
                        [cluster("tr21_entity_a", ["OMS", "order manager"])],
                        ["tr21.release_gate.owner"],
                    ),
                    step(
                        "tr21_obs03",
                        ["tr21.release_gate.owner", "tr21.platform.identity", "tr21.oms_desk.owner"],
                        [],
                        [cluster("tr21_entity_a", ["OMS", "order manager"]), cluster("tr21_entity_b", ["OMS desk"])],
                        ["tr21.release_gate.owner"],
                    ),
                ],
            },
        }
    )

    records.append(
        {
            "trajectory": {
                "trajectory_id": "tr22_out_of_order_price_band_present",
                "title": "迟到旧价带不应覆盖新价带",
                "coverage_tags": ["out_of_order_late"],
                "observations": [
                    obs(
                        "tr22_obs01",
                        ["Price band"],
                        "Price band is set to wide.",
                        [claim("tr22.price_band.wide", "price_band", "wide", "critical")],
                        "warehouse_feed",
                        "warehouse_feed#2205",
                        "2026-06-22T10:05:00Z",
                        "2026-06-22T10:05:00Z",
                    ),
                    obs(
                        "tr22_obs02",
                        ["Price band"],
                        "Price band is set to narrow.",
                        [claim("tr22.price_band.narrow", "price_band", "narrow", "critical")],
                        "warehouse_feed",
                        "warehouse_feed#2201_late",
                        "2026-06-22T10:01:00Z",
                        "2026-06-22T10:01:00Z",
                    ),
                ],
            },
            "gold": {
                "trajectory_id": "tr22_out_of_order_price_band_present",
                "schema_neutral": True,
                "steps": [
                    step(
                        "tr22_obs01",
                        ["tr22.price_band.wide"],
                        [],
                        [cluster("tr22_entity", ["Price band"])],
                        ["tr22.price_band.wide"],
                        [{"entity_cluster_id": "tr22_entity", "dimension": "price_band", "winner_obs_id": "tr22_obs01", "fallback_used": False}],
                    ),
                    step(
                        "tr22_obs02",
                        ["tr22.price_band.wide"],
                        [],
                        [cluster("tr22_entity", ["Price band"])],
                        ["tr22.price_band.wide"],
                        [{"entity_cluster_id": "tr22_entity", "dimension": "price_band", "winner_obs_id": "tr22_obs01", "fallback_used": False}],
                    ),
                ],
            },
        }
    )

    records.append(
        {
            "trajectory": {
                "trajectory_id": "tr23_missing_observed_at_latency_fallback",
                "title": "缺少 observed_at 时按到达序保留最新延迟阈值",
                "coverage_tags": ["full", "out_of_order_late"],
                "observations": [
                    obs(
                        "tr23_obs01",
                        ["Latency threshold"],
                        "Latency threshold is 50ms.",
                        [claim("tr23.latency_threshold.50", "latency_threshold", "50ms", "critical")],
                        "queue_board",
                        "queue_board#2301",
                        None,
                        "2026-06-23T08:00:00Z",
                    ),
                    obs(
                        "tr23_obs02",
                        ["Latency threshold"],
                        "Latency threshold is 80ms.",
                        [claim("tr23.latency_threshold.80", "latency_threshold", "80ms", "critical")],
                        "queue_board",
                        "queue_board#2302",
                        None,
                        "2026-06-23T08:01:00Z",
                    ),
                ],
            },
            "gold": {
                "trajectory_id": "tr23_missing_observed_at_latency_fallback",
                "schema_neutral": True,
                "steps": [
                    step(
                        "tr23_obs01",
                        ["tr23.latency_threshold.50"],
                        [],
                        [cluster("tr23_entity", ["Latency threshold"])],
                        ["tr23.latency_threshold.50"],
                        [{"entity_cluster_id": "tr23_entity", "dimension": "latency_threshold", "winner_obs_id": "tr23_obs01", "fallback_used": True}],
                    ),
                    step(
                        "tr23_obs02",
                        ["tr23.latency_threshold.80"],
                        [inval("tr23_obs02", "tr23_obs01", "full", ["tr23.latency_threshold.50"], ["tr23.latency_threshold.80"])],
                        [cluster("tr23_entity", ["Latency threshold"])],
                        ["tr23.latency_threshold.80"],
                        [{"entity_cluster_id": "tr23_entity", "dimension": "latency_threshold", "winner_obs_id": "tr23_obs02", "fallback_used": True}],
                    ),
                ],
            },
        }
    )

    return records


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    root = repo_root()
    base = root / "graph" / "projects" / "abu_modern" / "phase05_replay"
    trajectories_dir = base / "trajectories"
    gold_dir = base / "gold"
    reports_dir = base / "reports"

    for path in (trajectories_dir, gold_dir, reports_dir):
        path.mkdir(parents=True, exist_ok=True)

    readme = """# abu_modern · phase05_replay

这是 `abu_modern` 的 `Phase 0.5` 失效回放基准沙箱。

目的：
- 在任何新管线代码之前，先构建一套与当前 schema/脚本实现脱钩的 gold 基准
- 用独立观测流暴露 `partial / conditional / revival / alias / provenance / valid-time` 的真实缺口
- 交付“哪里塌了”的地图，而不是“全部通过”的报告

目录约定：
- `trajectories/`：有序观测流，每条观测携带 `obs_id / observed_at / valid_from / valid_to / source / mentions / payload`
- `gold/`：逐步金标，包含 `expected_active_set / expected_invalidations / entity_clusters / must_include / valid_time_adjudication`
- `reports/`：评分结果与摘要
- `coverage_matrix.md`：8 类形态覆盖矩阵
- `gap_register.md`：现有 schema 与基线的失败地图

纪律：
- gold 使用“事实上应该发生什么”的语言，不复用 `status / state / supersede / OpenTask` 词汇
- `partial / conditional / revival / valid-time` 预期会暴露缺口，不能为了通过率把它们改写成现有字段可表达的形状
- 乱序与迟到场景以文件内到达顺序为 transaction order，以 `observed_at` 为额外裁决键；若缺失则显式退回到达序
"""
    (base / "README.md").write_text(readme, encoding="utf-8")

    records = make_records()
    for item in records:
        trajectory = item["trajectory"]
        gold = item["gold"]
        trajectory_id = trajectory["trajectory_id"]
        write_json(trajectories_dir / f"{trajectory_id}.json", trajectory)
        write_json(gold_dir / f"{trajectory_id}.gold.json", gold)

    print(f"Wrote {len(records)} trajectories and {len(records)} gold files under {base}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
