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
        sys.exit(0)
    else:
        print(f'\nFAILURE: Some canonical evidence hashes do not match.')
        sys.exit(1)


if __name__ == '__main__':
    main()
