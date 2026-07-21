# Add quarantine for CONTESTS relation
path = r'D:\CCXXLESSON\contextledger\graph\projects\abu_modern\shadow_replay\scripts\shadow_lifecycle_adjudicator.py'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

old_code = '''        if relation == "CONTESTS":
            target_id = prev_active[0]["node_id"]
            patch["new_edges"].append({
                "source": node_id,
                "target": target_id,
                "relation": "CONTESTS",
            })
            log.append({"event_id": event["event_id"], "action": "contest", "node_id": node_id, "target": target_id})'''

new_code = '''        if relation == "CONTESTS":
            target_id = prev_active[0]["node_id"]
            patch["new_edges"].append({
                "source": node_id,
                "target": target_id,
                "relation": "CONTESTS",
            })
            log.append({"event_id": event["event_id"], "action": "contest", "node_id": node_id, "target": target_id})
            quarantine.append({"event_id": event["event_id"], "reason": "temporal_overlap_mutual_exclusion_no_resolver"})'''

if old_code in content:
    content = content.replace(old_code, new_code)
    with open(path, 'w', encoding='utf-8-sig') as f:
        f.write(content)
    print("SUCCESS: Added quarantine for CONTESTS")
else:
    print("ERROR: Pattern not found")
