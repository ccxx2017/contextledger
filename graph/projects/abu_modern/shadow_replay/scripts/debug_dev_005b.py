import json, os
base = os.path.abspath('.')
path = os.path.join(base, 'graph/projects/abu_modern/shadow_replay/runs/stage04b/development/stage04b_20260715T092526_development/tr_full_tkt_005b/diff_report.json')
data = json.load(open(path))
out = []
for cp in data.get('checkpoints', []):
    out.append('CP: ' + cp['checkpoint_id'])
    for d in cp.get('diffs', []):
        out.append('  ' + str(d.get('kind')) + ': ' + str(d.get('claim_id')) + ' -> ' + str(d.get('classification')))
    out.append('  diff_counts: ' + str(cp.get('diff_counts', {})))
with open('D:/CCXXLESSON/contextledger/reports/dev_005b_after_fix.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('DONE')
