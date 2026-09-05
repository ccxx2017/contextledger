#!/usr/bin/env python3
"""Verify canonical evidence hashes for cross-platform integrity checking.

Usage:
    python graph/scripts/verify_canonical_evidence_hashes.py
    python graph/scripts/verify_canonical_evidence_hashes.py --policy canonical_lf_v1

Returns exit code 0 if all canonical hashes match, 1 otherwise.
"""

import hashlib
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def canonical_hash(filepath: str) -> str:
    """Compute canonical SHA256 after CRLF/CR -> LF normalization."""
    with open(filepath, 'rb') as f:
        raw = f.read()
    normalized = raw.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
    return hashlib.sha256(normalized).hexdigest()


def main():
    policy = 'canonical_lf_v1'
    if '--policy' in sys.argv:
        idx = sys.argv.index('--policy')
        if idx + 1 < len(sys.argv):
            policy = sys.argv[idx + 1]

    index_path = os.path.join(REPO_ROOT, 'reports', 'stage04c_evidence_index_canonical_v1.json')
    if not os.path.exists(index_path):
        print(f'ERROR: Canonical evidence index not found: {index_path}')
        sys.exit(1)

    with open(index_path) as f:
        index = json.load(f)

    if index.get('hash_policy') != policy:
        print(f'ERROR: Policy mismatch: expected {policy}, found {index.get("hash_policy")}')
        sys.exit(1)

    all_match = True
    for entry in index['entries']:
        path = entry.get('path', '')
        expected_canon = entry.get('canonical_content_sha256', '')
        fp = os.path.join(REPO_ROOT, path)

        if not os.path.exists(fp):
            print(f'SKIP: {path} (file not found)')
            continue

        actual_canon = canonical_hash(fp)
        match = actual_canon == expected_canon
        status = 'PASS' if match else 'FAIL'
        if not match:
            all_match = False

        print(f'  [{status}] {path}')
        print(f'           expected canonical: {expected_canon[:16]}')
        print(f'           actual canonical:   {actual_canon[:16]}')

    if all_match:
        print(f'\nAll {len(index["entries"])} canonical evidence hashes match.')
    else:
        print(f'\nFAILURE: Some canonical evidence hashes do not match.')
        sys.exit(1)

    all_match = verify_evidence_chains()
    if all_match:
        print('All evidence chains verified.')
        sys.exit(0)
    else:
        print('FAILURE: Some evidence chain entries do not match.')
        sys.exit(1)


def collect_chain_entries(chain_path, chain):
    """Pull every {path, sha256} entry out of an evidence_chain.v1 document."""
    sections = [('hashes', chain.get('hashes', {})),
                ('component_versions', chain.get('component_versions', {})),
                ('contract_versions', chain.get('contract_versions', {}))]
    for section_name, section in sections:
        if not isinstance(section, dict):
            print(f'SKIP: {chain_path} .{section_name} (not an object)')
            continue
        for label, entry in section.items():
            if isinstance(entry, dict) and 'path' in entry and 'sha256' in entry:
                yield section_name, label, entry


def verify_evidence_chains():
    """Verify published evidence chains (graph/projects/*/run/evidence_chain.*.json).

    Every recorded hash must still match the referenced file; a mismatch means the
    artifact was modified after the chain was written (tamper or drift).
    """
    projects_dir = os.path.join(REPO_ROOT, 'graph', 'projects')
    chain_paths = []
    if os.path.isdir(projects_dir):
        for project in sorted(os.listdir(projects_dir)):
            run_dir = os.path.join(projects_dir, project, 'run')
            if not os.path.isdir(run_dir):
                continue
            for name in sorted(os.listdir(run_dir)):
                if name.startswith('evidence_chain.') and name.endswith('.json'):
                    chain_paths.append(os.path.join(run_dir, name))

    if not chain_paths:
        print('No published evidence chains found (nothing to verify).')
        return True

    all_match = True
    checked = 0
    for chain_path in chain_paths:
        rel_chain = os.path.relpath(chain_path, REPO_ROOT)
        try:
            with open(chain_path, encoding='utf-8') as f:
                chain = json.load(f)
        except Exception as exc:
            print(f'  [FAIL] {rel_chain}: unparseable ({exc})')
            all_match = False
            continue

        for section_name, label, entry in collect_chain_entries(rel_chain, chain):
            checked += 1
            artifact = os.path.join(REPO_ROOT, entry['path'])
            if not os.path.exists(artifact):
                print(f'  [FAIL] {rel_chain} .{section_name}.{label}: missing artifact {entry["path"]}')
                all_match = False
                continue
            actual = canonical_hash(artifact)
            if actual != entry['sha256']:
                print(f'  [FAIL] {rel_chain} .{section_name}.{label}: {entry["path"]}')
                print(f'           expected canonical: {entry["sha256"][:16]}')
                print(f'           actual canonical:   {actual[:16]}')
                all_match = False

    print(f'Verified {checked} hashed entries across {len(chain_paths)} evidence chain(s).')
    return all_match


if __name__ == '__main__':
    main()
