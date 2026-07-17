import json, os
base = os.path.abspath('.')
path = os.path.join(base, 'graph/projects/abu_modern/shadow_replay/runs/stage04b/development/stage04b_20260715T094617_development/split_summary.json')
data = json.load(open(path))
out = []
for case in data.get('cases', []):
    out.append('CASE: ' + case['trajectory_id'])
    out.append('  gate: ' + case['gate_decision'])
    out.append('  aggregate: ' + str(case.get('aggregate', {})))
    for cp in case.get('checkpoints', []):
        dc = cp.get('diff_counts', {})
        if dc.get('regression', 0) > 0 or dc.get('blocker', 0) > 0:
            out.append('  CP ' + cp['checkpoint_id'] + ' reg=' + str(dc.get('regression',0)) + ' blk=' + str(dc.get('blocker',0)) + ' total=' + str(dc.get('total',0)))
            for d in cp.get('diffs', []):
                if d.get('classification') in ('regression', 'blocker'):
                    out.append('    ' + str(d.get('kind')) + ': ' + str(d.get('claim_id')) + ' -> ' + str(d.get('classification')))
with open('D:/CCXXLESSON/contextledger/reports/cp123_dev_summary.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('DONE')
