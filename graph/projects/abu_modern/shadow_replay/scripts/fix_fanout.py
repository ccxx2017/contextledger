# Fix fan-out in shadow_lifecycle_adjudicator.py for Stage04-C1.2.3
# Replace the fan-out SUPERCEDES loop with single-immediate-predecessor logic

path = r'D:\CCXXLESSON\contextledger\graph\projects\abu_modern\shadow_replay\scripts\shadow_lifecycle_adjudicator.py'

with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

old_fanout = '''        else:
            # Default: SUPERCEDES / normal progression / COEXISTS already handled
            is_terminal = state in self.TERMINAL_STATES
            for prev in prev_active:
                if prev.get("lifecycle_ref") == lifecycle_ref:
                    patch["superseded_nodes"].append(prev["node_id"])
                    patch["new_edges"].append({"source": node_id, "target": prev["node_id"], "relation": "supersedes"})
                    log.append({"event_id": event["event_id"], "action": "supersede", "node_id": node_id, "target": prev["node_id"]})
            if is_terminal:
                patch["superseded_nodes"].append(node_id)
                log.append({"event_id": event["event_id"], "action": "terminal", "node_id": node_id})'''

new_single_pred = '''        else:
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
                    "selection_evidence": f"observed_at: new={new_observed_at or 'N/A'} > target={selected_prev.get('observed_at', 'N/A')}",
                })
                log.append({"event_id": event["event_id"], "action": "supersede", "node_id": node_id, "target": selected_prev["node_id"]})
                # Other candidates remain active (COEXISTS, not superseded)
            else:
                # No matching predecessor with same lifecycle_ref — COEXISTS already handled above
                pass

            if is_terminal:
                patch["superseded_nodes"].append(node_id)
                log.append({"event_id": event["event_id"], "action": "terminal", "node_id": node_id})'''

if old_fanout in content:
    content = content.replace(old_fanout, new_single_pred)
    with open(path, 'w', encoding='utf-8-sig') as f:
        f.write(content)
    print("SUCCESS: Fan-out replaced with single-predecessor logic")
else:
    print("ERROR: Old fan-out not found")
    # Debug
    idx = content.find('# Default: SUPERCEDES')
    if idx >= 0:
        print(f"Found at {idx}")
        print(repr(content[idx:idx+300]))
    else:
        print("Not found")
