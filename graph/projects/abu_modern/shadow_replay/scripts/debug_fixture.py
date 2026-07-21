import json, os
base = os.path.abspath('.')
path = os.path.join(base, 'graph/projects/abu_modern/shadow_replay/runs/stage04a_latest_summary.json')
data = json.load(open(path))
for s in data['summaries']:
    if s['fixture_id'] == 'lc_diff_source_conflict':
        rd = os.path.join(base, s['run_dir'])
        gs = json.load(open(os.path.join(rd, 'shadow_graph_state.json')))
        out = []
        out.append('NODES:')
        for nid, n in gs.get('nodes', {}).items():
            out.append('  ' + nid + ' claim=' + str(n.get('claim_id')) + ' status=' + str(n.get('status')) + ' source=' + str(n.get('source')))
        out.append('EDGES:')
        for e in gs.get('edges', []):
            out.append('  ' + str(e.get('source')) + '->' + str(e.get('target')) + ' ' + str(e.get('relation')))
        out.append('QUARANTINE: ' + str(gs.get('quarantine', [])))
        with open('D:/CCXXLESSON/contextledger/reports/fixture_diff_source_debug.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(out))
        print('DONE')
