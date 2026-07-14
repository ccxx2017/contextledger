# Stage04-C Evidence Hash Policy v1

## Canonical Hash Definition

**Policy ID:** canonical_lf_v1
**Applicable to:** All evidence files in reports/ used for benchmark evaluation gates.
**Definition:**

`
evidence_canonical_hash = SHA256(UTF-8 bytes after CRLF/CR -> LF normalization)
`

### Algorithm

For any evidence file F:
1. Read raw UTF-8 bytes from F
2. Normalize line endings: replace all \\r\\n -> \\n, then replace all remaining \\r -> \\n
3. Compute SHA256 of the normalized byte sequence
4. This is the canonical hash

### Why

Cross-platform git workflows cause CRLF/LF line-ending differences that change raw byte SHA256
without changing semantic content. The canonical hash strips line-ending differences to provide
a platform-independent integrity check.

### When to Use

- Primary: evidence integrity verification across Windows/Linux/Mac environments
- Diagnostic: raw_byte_sha256_at_generation is retained alongside canonical hash for forensic comparison
- The original stage04b2_regression_ready_evidence_index.json remains as-is (historical record)

### Verification Command

`
python graph/scripts/verify_canonical_evidence_hashes.py --policy canonical_lf_v1
`
