import json, os
base = os.path.abspath('.')
path = os.path.join(base, 'graph/projects/abu_modern/shadow_replay/runs/stage04b/development/stage04b_20260715T092526_development/tr_syn_revival_feature_flag/diff_report.json')
data = json.load(open(path))
out = []
for cp in data.get('checkpoints', []):
    out.append('CP: ' + cp['checkpoint_id'])
    out.append('  graph_state_hash: ' + cp.get('graph_state_hash', ''))
    for d in cp.get('diffs', []):
        out.append('  ' + str(d))
out.append('gate: ' + data.get('gate_decision', ''))
out.append('aggregate: ' + str(data.get('aggregate', {})))
with open('D:/CCXXLESSON/contextledger/reports/dev_revival_after_fix.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('DONE')
