import json, os
base = os.path.abspath('.')
path = os.path.join(base, 'graph/projects/abu_modern/shadow_replay/runs/stage04b/development/stage04b_20260715T092526_development/tr_syn_revival_feature_flag/shadow_graph_state.json')
data = json.load(open(path, encoding='utf-8'))
out = []
out.append('NODES:')
for nid, n in sorted(data.get('nodes', {}).items()):
    cid = n.get('claim_id', '?')
    out.append('  ' + nid + ' claim=' + cid + ' status=' + str(n.get('status')) + ' source=' + str(n.get('source')))
out.append('EDGES:')
for e in data.get('edges', []):
    out.append('  ' + str(e.get('source','?')) + '->' + str(e.get('target','?')) + ' ' + str(e.get('relation','?')))
with open('D:/CCXXLESSON/contextledger/reports/dev_revival_graph_state.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('DONE')
