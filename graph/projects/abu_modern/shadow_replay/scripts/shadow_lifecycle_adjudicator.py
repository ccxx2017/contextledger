#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shadow lifecycle adjudication kernel.

This module implements a deterministic, side-track lifecycle adjudicator.
It does not write to the formal main graph.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class AdjudicationResult:
    patch: dict[str, Any]
    quarantine: list[dict[str, Any]] = field(default_factory=list)
    log: list[dict[str, Any]] = field(default_factory=list)


class ShadowLifecycleAdjudicator:
    """Heuristic lifecycle adjudicator for shadow replay.

    Rules implemented:
    - lifecycle_seq collisions -> quarantine
    - alias hint mismatch -> abstain/quarantine
    - same lifecycle progression -> supersede previous active
    - provenance conflict (same adj key, different source) -> CONTESTS
    - different lifecycle_ref for same entity -> COEXISTS
    - revival content/state -> REVIVES relation
    - legacy nodes (no lifecycle_ref) -> adjudication_key = entity_ref
    """

    # Lifecycle states that mark a node as terminal / non-active on arrival.
    # This set is intentionally narrow to avoid marking benchmark states like
    # "resolved" or "superseded" as terminal.
    TERMINAL_STATES = {"cancelled"}

    def __init__(self, project_id: str = "abu_modern") -> None:
        self.project_id = project_id
        self._node_counter = 0

    def adjudicate_event(self, event: dict[str, Any], graph_state: dict[str, Any]) -> AdjudicationResult:
        payload = event.get("payload", {})
        entity_ref = payload.get("entity_ref")
        lifecycle_ref = payload.get("lifecycle_ref")
        lifecycle_seq = payload.get("lifecycle_seq")
        adjudication_key = self._compute_adjudication_key(payload)
        alias_hints = payload.get("alias_hints") or []
        source = event.get("source", "unknown")
        state = (payload.get("state") or "").strip().lower()
        content = (payload.get("content") or "").strip()

        log: list[dict[str, Any]] = []
        quarantine: list[dict[str, Any]] = []

        # Alias hint resolution
        if alias_hints:
            matched = self._resolve_alias_hint(graph_state, entity_ref, alias_hints)
            if matched is None:
                reason = "resolver_abstain_alias_mismatch"
                quarantine.append({"event_id": event["event_id"], "reason": reason})
                log.append({"event_id": event["event_id"], "action": "abstain", "reason": reason})
                return AdjudicationResult(patch=self._empty_patch(event), quarantine=quarantine, log=log)
            if lifecycle_ref is None:
                lifecycle_ref = matched
                adjudication_key = lifecycle_ref or entity_ref

        # Lifecycle sequence collision check
        if lifecycle_ref is not None and lifecycle_seq is not None:
            existing_seqs = self._existing_seqs(graph_state, lifecycle_ref)
            if existing_seqs and lifecycle_seq <= max(existing_seqs):
                reason = "lifecycle_seq_collision"
                quarantine.append({"event_id": event["event_id"], "reason": reason})
                log.append({"event_id": event["event_id"], "action": "quarantine", "reason": reason})
                return AdjudicationResult(patch=self._empty_patch(event), quarantine=quarantine, log=log)

        # Build new node
        self._node_counter += 1
        node_id = self._generate_node_id(event, self._node_counter)
        new_node = {
            "node_id": node_id,
            "entity_ref": entity_ref,
            "lifecycle_ref": lifecycle_ref,
            "lifecycle_seq": lifecycle_seq,
            "lifecycle_stage": payload.get("lifecycle_stage"),
            "adjudication_key": adjudication_key,
            "observed_at": event.get("observed_at"),
            "effective_at": event.get("effective_at"),
            "node_type": payload.get("node_type", "Fact"),
            "content": content,
            "state": state or None,
            "claim_id": payload.get("claim_id"),
            "status": "active",
            "active": True,
            "source": source,
        }

        patch: dict[str, Any] = {
            "turn_id": event["event_id"],
            "new_nodes": [new_node],
            "updated_nodes": [],
            "superseded_nodes": [],
            "new_edges": [],
        }

        # COEXISTS: same entity, different lifecycle (including legacy vs new)
        same_entity_active = self._find_active_nodes_by_entity(graph_state, entity_ref)
        for other in same_entity_active:
            if other.get("lifecycle_ref") != lifecycle_ref:
                patch["new_edges"].append({
                    "source": other["node_id"],
                    "target": node_id,
                    "relation": "COEXISTS",
                })
                log.append({"event_id": event["event_id"], "action": "coexist", "node_id": node_id, "target": other["node_id"]})

        # Late-arrival check: same channel, effective_at before previous active
        # This must be checked BEFORE deciding SUPERCEDES/CONTESTS/REVIVES.
        if self._is_late_arrival(event, graph_state, adjudication_key):
            reason = "late_arrival_effective_at_before_previous"
            quarantine.append({"event_id": event["event_id"], "reason": reason})
            log.append({"event_id": event["event_id"], "action": "quarantine_late", "reason": reason})
            return AdjudicationResult(patch=self._empty_patch(event), quarantine=quarantine, log=log)

        # Find previous active node(s) with same adjudication_key
        prev_active = self._find_active_nodes(graph_state, adjudication_key)

        if not prev_active:
            # Cross-key revival: new lifecycle/adjudication key for an entity
            # that previously had a terminal node.
            if self._is_revival_signal(event, new_node, graph_state):
                self._apply_revival_edges(event, new_node, graph_state, patch, log)
                log.append({"event_id": event["event_id"], "action": "create", "node_id": node_id})
                return AdjudicationResult(patch=patch, quarantine=quarantine, log=log)
            log.append({"event_id": event["event_id"], "action": "create", "node_id": node_id})
            return AdjudicationResult(patch=patch, quarantine=quarantine, log=log)

        # Determine relationship
        relation = self._determine_relation(event, new_node, prev_active)

        if relation == "CONTESTS":
            target_id = prev_active[0]["node_id"]
            patch["new_edges"].append({
                "source": node_id,
                "target": target_id,
                "relation": "CONTESTS",
            })
            log.append({"event_id": event["event_id"], "action": "contest", "node_id": node_id, "target": target_id})
            quarantine.append({"event_id": event["event_id"], "reason": "temporal_overlap_mutual_exclusion_no_resolver"})
        elif relation == "REVIVES":
            target_id = prev_active[0]["node_id"]
            patch["superseded_nodes"].append(target_id)
            patch["new_edges"].append({"source": node_id, "target": target_id, "relation": "REVIVES"})
            log.append({"event_id": event["event_id"], "action": "revive", "node_id": node_id, "target": target_id})
        else:
            # Default: SUPERCEDES / normal progression / COEXISTS already handled
            # FIXED (C1.2.3): Only select the IMMEDIATE temporal predecessor,
            # not all prev_active (fan-out fix).
            is_terminal = state in self.TERMINAL_STATES

            # Predecessor selection: find the single most recent active node
            # with the same lifecycle_ref, ordered by observed_at/effective_at
            selected_prev = None
            candidate_ids = []
            for prev in prev_active:
                if prev.get("lifecycle_ref") == lifecycle_ref:
                    candidate_ids.append(prev.get("node_id"))
                    if selected_prev is None:
                        selected_prev = prev
                    else:
                        # Compare observed_at to pick the most recent
                        sel_obs = selected_prev.get("observed_at", "") or ""
                        prev_obs = prev.get("observed_at", "") or ""
                        if prev_obs > sel_obs:
                            selected_prev = prev

            if selected_prev is not None:
                patch["superseded_nodes"].append(selected_prev["node_id"])
                patch["new_edges"].append({
                    "source": node_id,
                    "target": selected_prev["node_id"],
                    "relation": "supersedes",
                    "edge_id": f"edge_{event['event_id']}_{selected_prev['node_id']}",
                    "predecessor_selection_rule_id": "immediate_temporal_predecessor",
                    "candidate_predecessor_ids": candidate_ids,
                    "selected_predecessor_id": selected_prev["node_id"],
                    "selection_evidence": f"observed_at: new={event.get('observed_at', 'N/A')} > target={selected_prev.get('observed_at', 'N/A')}",
                })
                log.append({"event_id": event["event_id"], "action": "supersede", "node_id": node_id, "target": selected_prev["node_id"]})
                # Other candidates remain active (COEXISTS, not superseded)
            else:
                # No matching predecessor with same lifecycle_ref — COEXISTS already handled above
                pass

            if is_terminal:
                patch["superseded_nodes"].append(node_id)
                log.append({"event_id": event["event_id"], "action": "terminal", "node_id": node_id})

        return AdjudicationResult(patch=patch, quarantine=quarantine, log=log)

    def _empty_patch(self, event: dict[str, Any]) -> dict[str, Any]:
        return {
            "turn_id": event["event_id"],
            "new_nodes": [],
            "updated_nodes": [],
            "superseded_nodes": [],
            "new_edges": [],
        }

    def _compute_adjudication_key(self, payload: dict[str, Any]) -> str | None:
        return payload.get("adjudication_key") or payload.get("lifecycle_ref") or payload.get("entity_ref")

    def _resolve_alias_hint(
        self,
        graph_state: dict[str, Any],
        entity_ref: Any,
        alias_hints: list[str],
    ) -> str | None:
        if not entity_ref:
            return None
        entity_lifecycles: set[str] = set()
        for node in graph_state.get("nodes", {}).values():
            if node.get("entity_ref") == entity_ref and node.get("lifecycle_ref"):
                entity_lifecycles.add(node["lifecycle_ref"])
        if not entity_lifecycles:
            return None
        for hint in alias_hints:
            for lc in entity_lifecycles:
                if hint.lower() in lc.lower() or lc.lower() in hint.lower():
                    return lc
        return None

    def _existing_seqs(self, graph_state: dict[str, Any], lifecycle_ref: str) -> list[int]:
        seqs: list[int] = []
        for node in graph_state.get("nodes", {}).values():
            if node.get("lifecycle_ref") == lifecycle_ref and node.get("lifecycle_seq") is not None:
                seqs.append(int(node["lifecycle_seq"]))
        return seqs

    def _find_active_nodes(self, graph_state: dict[str, Any], adjudication_key: str | None) -> list[dict[str, Any]]:
        if adjudication_key is None:
            return []
        result: list[dict[str, Any]] = []
        for node in graph_state.get("nodes", {}).values():
            if node.get("adjudication_key") == adjudication_key and node.get("status") == "active":
                result.append(node)
        return result

    def _find_active_nodes_by_entity(self, graph_state: dict[str, Any], entity_ref: Any) -> list[dict[str, Any]]:
        if not entity_ref:
            return []
        result: list[dict[str, Any]] = []
        for node in graph_state.get("nodes", {}).values():
            if node.get("entity_ref") == entity_ref and node.get("status") == "active":
                result.append(node)
        return result

    def _determine_relation(
        self,
        event: dict[str, Any],
        new_node: dict[str, Any],
        prev_active: list[dict[str, Any]],
    ) -> str:
        """Decision contract v2: six-step relation determination.

        Replaces the old 'different source -> CONTESTS' default assumption.
        """
        from datetime import datetime

        payload = event.get("payload", {})
        new_source = event.get("source", "unknown")
        new_state = (payload.get("state") or "").strip().lower()
        content = (payload.get("content") or "").lower()
        new_observed_at = event.get("observed_at", "")
        new_effective_at = event.get("effective_at", "")

        # Step 0: Revival signal check FIRST (before relation determination)
        if "reviv" in content or (new_state in ("in_progress", "open", "implemented", "deployed") and any(
            n.get("state") in ("cancelled", "superseded") for n in prev_active
        )):
            return "REVIVES"

        if not prev_active:
            return "SUPERCEDES"

        prev = prev_active[0]
        prev_source = prev.get("source", "unknown")
        prev_observed_at = prev.get("observed_at", "")
        prev_effective_at = prev.get("effective_at", "")

        # Step 1: Same atomic claim, same scope?
        same_adjudication_key = (
            prev.get("adjudication_key") == new_node.get("adjudication_key")
        )
        same_entity = prev.get("entity_ref") == new_node.get("entity_ref")

        # Step 2: Is there sufficient evidence for state progression?
        # New observed_at is unambiguously later than previous -> supports SUPERCEDES
        time_progression = False
        if new_observed_at and prev_observed_at:
            try:
                new_dt = datetime.fromisoformat(str(new_observed_at).replace("Z", "+00:00"))
                prev_dt = datetime.fromisoformat(str(prev_observed_at).replace("Z", "+00:00"))
                time_progression = new_dt > prev_dt
            except (ValueError, TypeError):
                pass

        # Step 3: Semantic conflict? (same time window, mutually exclusive values)
        semantic_conflict = False
        if time_progression is False and same_entity and same_adjudication_key:
            # Check both 'value' and 'state' fields for conflict
            new_val = (payload.get("value") or payload.get("state") or "").strip().lower()
            prev_val = (prev.get("state") or "").strip().lower()
            if new_val and prev_val and new_val != prev_val:
                semantic_conflict = True

        # Step 4: Source authority/trustworthiness insufficient to decide?
        source_authority_questionable = False
        if new_source != prev_source:
            # Different source does NOT automatically mean CONTESTS.
            # It only matters if there's a semantic conflict AND no clear time ordering.
            if semantic_conflict and time_progression is False:
                source_authority_questionable = True

        # Step 5: Unresolvable specific conflict?
        if source_authority_questionable and semantic_conflict and not time_progression:
            return "CONTESTS"

        # Step 6: Safe default -> time progression with different source = SUPERCEDES
        # The new claim supersedes the old one because it's temporally later
        # and represents state evolution, not a provenance conflict.
        if time_progression:
            return "SUPERCEDES"

        # No clear time ordering and no semantic conflict -> SUPERCEDES (progression)
        return "SUPERCEDES"

    def _generate_node_id(self, event: dict[str, Any], counter: int) -> str:
        payload = event.get("payload", {})
        entity = str(payload.get("entity_ref") or "unknown")[:20]
        lifecycle = str(payload.get("lifecycle_ref") or "legacy")[:20]
        seq = str(payload.get("lifecycle_seq") or "x")
        base = f"{entity}_{lifecycle}_{seq}_{counter}"
        return "n_" + hashlib.sha256(base.encode("utf-8")).hexdigest()[:12]

    def _is_revival_signal(
        self,
        event: dict[str, Any],
        new_node: dict[str, Any],
        graph_state: dict[str, Any],
    ) -> bool:
        content = (event.get("payload", {}).get("content") or "").lower()
        if "reviv" in content:
            return True
        new_state = new_node.get("state") or ""
        if new_state not in ("in_progress", "open", "implemented", "deployed"):
            return False
        for node in graph_state.get("nodes", {}).values():
            if node.get("entity_ref") == new_node.get("entity_ref") and node.get("state") in self.TERMINAL_STATES:
                return True
        return False

    def _is_late_arrival(
        self,
        event: dict[str, Any],
        graph_state: dict[str, Any],
        adjudication_key: str | None,
    ) -> bool:
        """Detect late-arrival: same channel, effective_at indicates back-dated event.

        A late arrival is when:
        1. There is already an active node with the same adjudication_key from the same source/channel.
        2. The new event's effective_at is before the existing active node's observed_at
           (i.e., the event is reporting something that happened earlier than what we already know).
        3. OR the new event's effective_at is missing/None (ambiguous timing).

        In these cases, the new event should NOT supersede the current active state.
        """
        if adjudication_key is None:
            return False

        new_source = event.get("source", "unknown")
        new_effective = event.get("effective_at")
        new_observed = event.get("observed_at")

        for node in graph_state.get("nodes", {}).values():
            if node.get("adjudication_key") != adjudication_key:
                continue
            if node.get("status") != "active":
                continue
            prev_source = node.get("source", "unknown")
            if new_source != prev_source:
                continue  # Different source = provenance conflict, not late arrival

            prev_effective = node.get("effective_at")
            prev_observed = node.get("observed_at")

            # Late arrival: missing effective_at (ambiguous timing)
            if new_effective is None or new_effective == "":
                return True

            # Late arrival: effective_at before previous observed_at
            if prev_effective and new_effective < prev_effective:
                return True
            if prev_observed and new_effective < prev_observed:
                return True

            return False

        return False

    def _apply_revival_edges(
        self,
        event: dict[str, Any],
        new_node: dict[str, Any],
        graph_state: dict[str, Any],
        patch: dict[str, Any],
        log: list[dict[str, Any]],
    ) -> None:
        entity_ref = new_node.get("entity_ref")
        lifecycle_ref = new_node.get("lifecycle_ref")
        node_id = new_node["node_id"]

        candidates = [
            n for n in graph_state.get("nodes", {}).values()
            if n.get("entity_ref") == entity_ref
            and (lifecycle_ref is None or n.get("lifecycle_ref") == lifecycle_ref)
        ]
        terminal_nodes = [n for n in candidates if n.get("state") in self.TERMINAL_STATES]
        origin_nodes = [n for n in candidates if n.get("state") not in self.TERMINAL_STATES]

        if terminal_nodes:
            terminal_nodes.sort(key=lambda n: (n.get("observed_at") or "", n.get("node_id") or ""))
            target_id = terminal_nodes[-1]["node_id"]
            patch["new_edges"].append({"source": node_id, "target": target_id, "relation": "REVIVES"})
            log.append({"event_id": event["event_id"], "action": "revive", "node_id": node_id, "target": target_id})

        if origin_nodes:
            origin_nodes.sort(key=lambda n: (n.get("observed_at") or "", n.get("node_id") or ""))
            origin_id = origin_nodes[-1]["node_id"]
            patch["new_edges"].append({"source": node_id, "target": origin_id, "relation": "derived_from"})
            log.append({"event_id": event["event_id"], "action": "derived_from", "node_id": node_id, "target": origin_id})

        for active in self._find_active_nodes_by_entity(graph_state, entity_ref):
            if active["node_id"] != node_id and (lifecycle_ref is None or active.get("lifecycle_ref") == lifecycle_ref):
                patch["superseded_nodes"].append(active["node_id"])
                log.append({"event_id": event["event_id"], "action": "supersede", "node_id": node_id, "target": active["node_id"]})
