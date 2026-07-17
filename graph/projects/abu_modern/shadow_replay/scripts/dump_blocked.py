import json, os

base = os.path.abspath('.')
path = os.path.join(base, 'graph/projects/abu_modern/shadow_replay/runs/stage04a_latest_summary.json')
data = json.load(open(path))
output_lines = []
for s in data['summaries']:
    if s['gate_decision'] == 'BLOCK':
        rd = os.path.join(base, s['run_dir'])
        dr = os.path.join(rd, 'diff_report.json')
        diff = json.load(open(dr))
        cps = diff.get('checkpoints', [])
        output_lines.append('FIXTURE: ' + s['fixture_id'] + ' CPs: ' + str(len(cps)))
        for cp in cps:
            diffs = cp.get('diffs', [])
            output_lines.append('  CP ' + cp['checkpoint_id'] + ' diffs: ' + str(len(diffs)))
            for dd in diffs:
                output_lines.append('    ' + str(dd.get('kind')) + ' ' + str(dd.get('claim_id')) + ' -> ' + str(dd.get('classification')))

with open('D:/CCXXLESSON/contextledger/reports/blocking_fixture_details.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))
print('WROTE', len(output_lines), 'lines')
