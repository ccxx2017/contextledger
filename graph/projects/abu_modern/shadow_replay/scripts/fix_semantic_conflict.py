# Fix semantic conflict detection to also check 'state' field
path = r'D:\CCXXLESSON\contextledger\graph\projects\abu_modern\shadow_replay\scripts\shadow_lifecycle_adjudicator.py'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

old_code = '''        # Step 3: Semantic conflict? (same time window, mutually exclusive values)
        semantic_conflict = False
        if time_progression is False and same_entity and same_adjudication_key:
            new_val = (payload.get("value") or "").strip().lower()
            prev_val = (prev.get("state") or "").strip().lower()
            if new_val and prev_val and new_val != prev_val:
                semantic_conflict = True'''

new_code = '''        # Step 3: Semantic conflict? (same time window, mutually exclusive values)
        semantic_conflict = False
        if time_progression is False and same_entity and same_adjudication_key:
            # Check both 'value' and 'state' fields for conflict
            new_val = (payload.get("value") or payload.get("state") or "").strip().lower()
            prev_val = (prev.get("state") or "").strip().lower()
            if new_val and prev_val and new_val != prev_val:
                semantic_conflict = True'''

if old_code in content:
    content = content.replace(old_code, new_code)
    with open(path, 'w', encoding='utf-8-sig') as f:
        f.write(content)
    print("SUCCESS: Fixed semantic conflict detection")
else:
    print("ERROR: Pattern not found")
