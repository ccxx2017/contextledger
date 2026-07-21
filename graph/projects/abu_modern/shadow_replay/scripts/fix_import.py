# Add datetime import to top of file and remove inline import
path = r'D:\CCXXLESSON\contextledger\graph\projects\abu_modern\shadow_replay\scripts\shadow_lifecycle_adjudicator.py'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Add datetime import
content = content.replace(
    'import hashlib\nfrom dataclasses import dataclass, field\nfrom typing import Any',
    'import hashlib\nfrom dataclasses import dataclass, field\nfrom datetime import datetime\nfrom typing import Any'
)

# Remove inline import in _determine_relation
content = content.replace(
    '        """Decision contract v2: six-step relation determination.\n\n        Replaces the old \'different source -> CONTESTS\' default assumption.\n        """\n        from datetime datetime\n\n        payload',
    '        """Decision contract v2: six-step relation determination.\n\n        Replaces the old \'different source -> CONTESTS\' default assumption.\n        """\n\n        payload'
)

# Fix the inline import pattern
content = content.replace(
    'from datetime datetime\n\n        payload',
    '\n\n        payload'
)

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)
print("DONE")
