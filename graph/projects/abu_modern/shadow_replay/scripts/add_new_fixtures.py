# Add new fixtures to EXPECTED_NODE_SEMANTICS
path = r'D:\CCXXLESSON\contextledger\graph\projects\abu_modern\shadow_replay\scripts\fixture_replay_runner.py'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

old_end = '''    "lc_state_value_vs_real_scope_ambiguity": {
        "n_feature_x_enabled": {"entity_ref": "Feature-X", "lifecycle_ref": "lc_feature_x", "lifecycle_seq": 1, "state": "enabled", "claim_id": "feature.x.enabled"},
        "n_feature_x_staging": {"entity_ref": "Feature-X", "lifecycle_ref": "lc_feature_x", "lifecycle_seq": 2, "state": "deployed", "claim_id": "feature.x.staging"},
    },
}'''

new_end = '''    "lc_state_value_vs_real_scope_ambiguity": {
        "n_feature_x_enabled": {"entity_ref": "Feature-X", "lifecycle_ref": "lc_feature_x", "lifecycle_seq": 1, "state": "enabled", "claim_id": "feature.x.enabled"},
        "n_feature_x_staging": {"entity_ref": "Feature-X", "lifecycle_ref": "lc_feature_x", "lifecycle_seq": 2, "state": "deployed", "claim_id": "feature.x.staging"},
    },
    "lc_different_source_chronological_progression_supersedes": {
        "n_alpha_enabled_v1": {"entity_ref": "Alpha-feature", "lifecycle_ref": "lc_alpha_feature", "state": "enabled", "claim_id": "alpha.feature.enabled.v1"},
        "n_alpha_disabled": {"entity_ref": "Alpha-feature", "lifecycle_ref": "lc_alpha_feature", "state": "disabled", "claim_id": "alpha.feature.disabled"},
    },
    "lc_different_source_true_conflict_contests": {
        "n_engine_nominal": {"entity_ref": "Engine-001", "lifecycle_ref": "lc_engine_001_health", "state": "nominal", "claim_id": "engine.001.temp.nominal"},
        "n_engine_critical": {"entity_ref": "Engine-001", "lifecycle_ref": "lc_engine_001_health", "state": "critical", "claim_id": "engine.001.temp.critical"},
    },
    "lc_three_step_same_key_immediate_predecessor_only": {
        "n_order_initialized": {"entity_ref": "Order-Stream", "lifecycle_ref": "lc_order_processing", "state": "initialized", "claim_id": "order.stream.initialized"},
        "n_order_started": {"entity_ref": "Order-Stream", "lifecycle_ref": "lc_order_processing", "state": "started", "claim_id": "order.stream.started"},
        "n_order_completed": {"entity_ref": "Order-Stream", "lifecycle_ref": "lc_order_processing", "state": "completed", "claim_id": "order.stream.completed"},
    },
    "lc_multi_claim_stream_no_fanout_to_unrelated_predecessors": {
        "n_platform_operational": {"entity_ref": "Platform-X", "lifecycle_ref": "lc_platform_x_status", "state": "operational", "claim_id": "platform.x.operational"},
        "n_platform_degraded": {"entity_ref": "Platform-X", "lifecycle_ref": "lc_platform_x_status", "state": "degraded", "claim_id": "platform.x.degraded"},
        "n_platform_recovered": {"entity_ref": "Platform-X", "lifecycle_ref": "lc_platform_x_status", "state": "recovered", "claim_id": "platform.x.recovered"},
    },
}'''

if old_end in content:
    content = content.replace(old_end, new_end)
    with open(path, 'w', encoding='utf-8-sig') as f:
        f.write(content)
    print("SUCCESS: Added 4 new fixtures to EXPECTED_NODE_SEMANTICS")
else:
    print("ERROR: Pattern not found")
    idx = content.find('lc_state_value_vs_real_scope_ambiguity')
    if idx >= 0:
        print("Found at:", idx)
        print(repr(content[idx:idx+300]))
