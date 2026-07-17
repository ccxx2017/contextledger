#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shadow resolution adapter 鈥?separates observation_to_event from benchmark runner.

Transforms raw benchmark observations (with claim_bundle) into structured
resolution records and adjudicator-ready events, with explicit, versioned
normalization priorities (NOT relying on claim_id string position).

Schema: shadow_resolution_record_v1
Contract: shadow_resolution_adapter_contract.md
"""
from __future__ import annotations

# Versioned scope normalization mapping (loaded at runtime).
# See contracts/shadow_scope_normalization_mapping_v1.json for the authoritative rule definitions.
_SCOPE_MAPPING = None

def _load_scope_mapping():
    """Load the versioned scope normalization mapping from contract."""
    global _SCOPE_MAPPING
    if _SCOPE_MAPPING is None:
        import json
        from pathlib import Path
        mapping_path = Path(__file__).resolve().parent.parent / "contracts" / "shadow_scope_normalization_mapping_v1.json"
        if mapping_path.exists():
            with open(mapping_path, "r", encoding="utf-8") as f:
                _SCOPE_MAPPING = json.load(f)
        else:
            _SCOPE_MAPPING = []
    return _SCOPE_MAPPING


def _is_state_value_token(seg):
    """Check if a segment is a known state value via the versioned mapping."""
    mapping = _load_scope_mapping()
    for entry in mapping:
        if entry.get("token") == seg and entry.get("semantic_role") == "state_value":
            return True, entry.get("rule_id", "S000_mapped")
    return False, None

import hashlib
from typing import Any


def _extract_dimension_v2(claim):
    """Extract claim dimension with explicit versioned priority.

    Priority:
      1. claim.dimension (explicit field)
      2. claim type/predicate field (not yet in phase05_v3)
      3. Versioned legacy heuristic from claim_id second segment (v1, audit-trail only)
      4. abstain/quarantine if none
    """
    raw = claim.get("dimension")
    if raw:
        return str(raw), "claim.dimension", "R003_explicit", False

    cid = claim.get("claim_id", "")
    parts = [p for p in cid.split(".") if p]
    if len(parts) >= 2 and not parts[1].startswith("obs"):
        return parts[1], "claim_id.heuristic.second_segment.v1", "R003_legacy_v1", True

    return None, "nil", "R003_abstain", True


def _extract_scope_v2(claim, obs):
    """Extract scope with explicit versioned priority.

    Priority:
      1. claim.scope or obs.claim_scope (explicit)
      2. claim_id third segment 鈥?used as scope only when it looks semantic
         (multi-char, not purely numeric, not a timestamp, not version-like)
      3. _default_ 鈥?sequential progression scope
    """
    raw = claim.get("claim_scope") or obs.get("claim_scope")
    if raw:
        return str(raw), "claim.scope", "R006_explicit", False

    cid = claim.get("claim_id", "")
    parts = [p for p in cid.split(".") if p]
    if len(parts) >= 3:
        seg = parts[2]

        # State-value detection via versioned mapping (v1).
        # When the third segment is a known state-like value (past participle,
        # descriptive adjective, or matches claim.value), it is NOT a scope.
        # Uses the authoritative shadow_scope_normalization_mapping_v1.json.
        seg_is_state_value, _state_rule_id = _is_state_value_token(seg)
        # NOTE: We do NOT use seg == claim.value as a shortcut because claim.value
        # can legitimately equal the third segment when that segment IS a real scope
        # (e.g. tr12.target.staging.allowed where value=staging, seg=staging).
        # Only the versioned STATE_VALUE_TOKENS mapping is authoritative.
        pass  # exact-value match intentionally disabled (see above)

        if not seg_is_state_value:
            # Heuristic: numeric-like segments (digits, digits+s, version numbers)
            # are values not scopes. Semantic scopes are alphanumeric words.
            is_numeric = all(c.isdigit() or c in ".-" for c in seg)
            is_version_like = seg.replace(".","").isdigit() or (len(seg) <= 3 and seg.isdigit())
            is_value_like = is_numeric or is_version_like or seg.endswith("s")
            if not is_value_like and not seg.startswith("obs") and not seg.startswith("cp"):
                return seg, "claim_id.heuristic.third_segment.v1", "R006_legacy_v1", True

    return "_default_", "inferred_default", "R006_default", False


def observation_to_event(obs, seq):
    """Convert a benchmark observation to adjudication events via dimension/scope-aware resolver.

    Each claim in claim_bundle becomes one event with a composite adjudication_key
    derived from entity + claim_dimension + scope.
    Schema: shadow_resolution_record_v1
    """
    source = obs.get("source", {})
    source_str = source.get("channel") or source.get("provenance") or "unknown"
    source_str = source_str.split("#")[0] if "#" in source_str else source_str
    surface_entity = obs.get("mentions", [None])[0] or "unknown"
    claims = obs.get("payload", {}).get("claim_bundle", [])

    if not claims:
        return [{
            "event_id": obs["obs_id"],
            "observed_at": obs.get("observed_at"),
            "effective_at": obs.get("valid_from"),
            "source": source_str,
            "payload": {
                "entity_ref": surface_entity,
                "lifecycle_ref": surface_entity,
                "lifecycle_seq": seq,
                "adjudication_key": surface_entity,
                "node_type": "Fact",
                "content": obs.get("payload", {}).get("statement", ""),
                "state": None,
                "claim_id": None,
                "claim_dimension": None,
                "claim_scope": None,
                "alias_hints": None,
            },
            "resolution_record": {"claim_id": None, "abstain_reason": "no_claims"},
        }]

    events = []
    for claim in claims:
        claim_id = claim.get("claim_id", f"c{seq}")
        dimension, dim_source, dim_rule, dim_fallback = _extract_dimension_v2(claim)
        scope, scope_source, scope_rule, scope_fallback = _extract_scope_v2(claim, obs)

        lifecycle_ref = surface_entity + ":" + dimension if dimension else surface_entity
        adj_key = surface_entity + ":" + (dimension or "_nodim_") + ":" + (scope or "_default_")

        rec = {
            "claim_id": claim_id,
            "source_field_for_dimension": dim_source,
            "source_field_for_scope": scope_source,
            "normalization_rule_id": dim_rule if dim_fallback else scope_rule,
            "fallback_used": dim_fallback or scope_fallback,
            "abstain_reason": None,
            "entity_resolution_confidence": "medium" if dim_fallback else "high",
            "lifecycle_resolution_confidence": "medium" if scope_fallback else "high",
            "surface_entity": surface_entity,
            "canonical_entity": surface_entity,
            "claim_dimension": dimension,
            "scope": scope,
            "scope_raw_value": scope,
            "scope_normalization_rule_id": scope_rule,
            "state_value_token_match": scope_rule in {"S001_state_value_whitelist", "S002_dimension_state_value", "S003_lifecycle_state_value", "S004_terminal_state_value", "S005_review_state_value"},
            "mapping_version": "v1" if "S00" in (scope_rule or "") else None,
            "channel": source_str,
            "adjudication_key": adj_key,
            "lifecycle_ref": lifecycle_ref,
        }

        events.append({
            "event_id": obs["obs_id"] + "#" + claim_id,
            "observed_at": obs.get("observed_at"),
            "effective_at": obs.get("valid_from"),
            "source": source_str,
            "payload": {
                "entity_ref": surface_entity,
                "lifecycle_ref": lifecycle_ref,
                "lifecycle_seq": seq,
                "adjudication_key": adj_key,
                "node_type": "Fact",
                "content": obs.get("payload", {}).get("statement", ""),
                "state": claim.get("value"),
                "claim_id": claim_id,
                "claim_dimension": dimension,
                "claim_scope": scope,
                "alias_hints": None,
            },
            "resolution_record": rec,
        })
    return events



