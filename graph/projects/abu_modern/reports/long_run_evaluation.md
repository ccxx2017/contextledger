# abu_modern Long-Run Evaluation: turn_020–084

**Generated:** 2026-07-13
**Range:** turn_020 to turn_084 (65 turns)
**Current turn_counter:** 84

## Executive Summary

- **Chain completeness:** All 65 turns have patch/snapshot artifacts and health reports.
- **Health status:** All OK/GREEN.
- **Graph growth:** nodes 75 → 204 (+129); edges 105 → 340 (+235).
- **Pending merge backlog:** 59 tracked items, 54 overdue at turn_084.
- **Lint stability:** Only 9 introduced errors and 5 introduced warnings across 65 turns.

## Methodology

This report reads graph_state.turn_XXX.json, 	urn_health_report.json, ssembly_report.turn_XXX.json, and pending_merge_register.json for turns 020–084 after the historical-chain rebuild. Metrics focus on the four macro indicators called out in the operational preflight plan: graph growth, lint baseline stability, pending_merge queue health, and assembly integrity.

## 1. Graph Growth & Active Node Evolution

| turn | nodes | edges | active | resolved/closed | superseded | node Δ | edge Δ |
|------|-------|-------|--------|-----------------|------------|--------|--------|
| 20 | 75 | 105 | 60 | 15 | 0 |  |  |
| 21 | 76 | 108 | 61 | 15 | 0 | 1 | 3 |
| 22 | 76 | 109 | 61 | 15 | 0 | 0 | 1 |
| 23 | 79 | 113 | 63 | 16 | 0 | 3 | 4 |
| 24 | 81 | 118 | 65 | 16 | 0 | 2 | 5 |
| 25 | 82 | 120 | 66 | 16 | 0 | 1 | 2 |
| 26 | 82 | 123 | 66 | 16 | 0 | 0 | 3 |
| 27 | 86 | 127 | 70 | 16 | 0 | 4 | 4 |
| 28 | 86 | 129 | 70 | 16 | 0 | 0 | 2 |
| 29 | 86 | 131 | 70 | 16 | 0 | 0 | 2 |
| 30 | 89 | 135 | 73 | 16 | 0 | 3 | 4 |
| 31 | 90 | 137 | 74 | 16 | 0 | 1 | 2 |
| 32 | 92 | 142 | 75 | 17 | 0 | 2 | 5 |
| 33 | 95 | 147 | 77 | 18 | 0 | 3 | 5 |
| 34 | 97 | 152 | 78 | 19 | 0 | 2 | 5 |
| 35 | 100 | 156 | 80 | 20 | 0 | 3 | 4 |
| 36 | 100 | 156 | 80 | 20 | 0 | 0 | 0 |
| 37 | 104 | 160 | 83 | 21 | 0 | 4 | 4 |
| 38 | 106 | 164 | 84 | 22 | 0 | 2 | 4 |
| 39 | 109 | 174 | 87 | 22 | 0 | 3 | 10 |
| 40 | 110 | 175 | 88 | 22 | 0 | 1 | 1 |
| 41 | 110 | 175 | 88 | 22 | 0 | 0 | 0 |
| 42 | 110 | 175 | 88 | 22 | 0 | 0 | 0 |
| 43 | 110 | 175 | 88 | 22 | 0 | 0 | 0 |
| 44 | 111 | 177 | 88 | 23 | 0 | 1 | 2 |
| 45 | 113 | 181 | 90 | 23 | 0 | 2 | 4 |
| 46 | 113 | 182 | 89 | 24 | 0 | 0 | 1 |
| 47 | 114 | 183 | 90 | 24 | 0 | 1 | 1 |
| 48 | 117 | 192 | 93 | 24 | 0 | 3 | 9 |
| 49 | 117 | 192 | 93 | 24 | 0 | 0 | 0 |
| 50 | 119 | 194 | 95 | 24 | 0 | 2 | 2 |
| 51 | 129 | 205 | 100 | 29 | 0 | 10 | 11 |
| 52 | 133 | 210 | 103 | 30 | 0 | 4 | 5 |
| 53 | 136 | 215 | 105 | 31 | 0 | 3 | 5 |
| 54 | 138 | 217 | 106 | 32 | 0 | 2 | 2 |
| 55 | 141 | 222 | 107 | 34 | 0 | 3 | 5 |
| 56 | 145 | 231 | 109 | 36 | 0 | 4 | 9 |
| 57 | 148 | 235 | 110 | 38 | 0 | 3 | 4 |
| 58 | 152 | 242 | 113 | 39 | 0 | 4 | 7 |
| 59 | 154 | 245 | 113 | 41 | 0 | 2 | 3 |
| 60 | 158 | 253 | 116 | 42 | 0 | 4 | 8 |
| 61 | 159 | 256 | 116 | 43 | 0 | 1 | 3 |
| 62 | 159 | 256 | 116 | 43 | 0 | 0 | 0 |
| 63 | 161 | 260 | 116 | 45 | 0 | 2 | 4 |
| 64 | 165 | 269 | 118 | 47 | 0 | 4 | 9 |
| 65 | 168 | 274 | 119 | 49 | 0 | 3 | 5 |
| 66 | 171 | 278 | 120 | 51 | 0 | 3 | 4 |
| 67 | 174 | 283 | 123 | 51 | 0 | 3 | 5 |
| 68 | 175 | 284 | 122 | 53 | 0 | 1 | 1 |
| 69 | 178 | 288 | 124 | 54 | 0 | 3 | 4 |
| 70 | 179 | 290 | 125 | 54 | 0 | 1 | 2 |
| 71 | 180 | 292 | 124 | 56 | 0 | 1 | 2 |
| 72 | 183 | 299 | 126 | 57 | 0 | 3 | 7 |
| 73 | 183 | 302 | 125 | 58 | 0 | 0 | 3 |
| 74 | 186 | 309 | 127 | 59 | 0 | 3 | 7 |
| 75 | 186 | 310 | 126 | 60 | 0 | 0 | 1 |
| 76 | 186 | 310 | 126 | 60 | 0 | 0 | 0 |
| 77 | 190 | 317 | 129 | 61 | 0 | 4 | 7 |
| 78 | 192 | 322 | 131 | 61 | 0 | 2 | 5 |
| 79 | 192 | 322 | 130 | 62 | 0 | 0 | 0 |
| 80 | 193 | 324 | 130 | 63 | 0 | 1 | 2 |
| 81 | 196 | 331 | 132 | 64 | 0 | 3 | 7 |
| 82 | 200 | 336 | 134 | 66 | 0 | 4 | 5 |
| 83 | 201 | 337 | 135 | 66 | 0 | 1 | 1 |
| 84 | 204 | 340 | 138 | 66 | 0 | 3 | 3 |

- Average node Δ per turn: 2.02
- Average edge Δ per turn: 3.67
- Largest single-turn node jump: +10 at turn_051

### Interpretation
Growth is broadly linear: ~2 nodes and ~3.7 edges per turn. The single notable spike is turn_051 (+10 nodes), which appears to correspond to a batch of new entities introduced in that turn rather than a失控膨胀. No exponential or snowball growth is observed, so the graph is not drifting into unbounded expansion.

## 2. Assembly Integrity & Bundle Quality

| turn | selected_nodes | active_must_include | excluded_budget | excluded_state |
|------|----------------|---------------------|-----------------|----------------|
| 20 | 12 | 6 | 0 | 0 |
| 21 | 12 | 7 | 0 | 0 |
| 22 | 12 | 7 | 0 | 0 |
| 23 | 12 | 7 | 0 | 0 |
| 24 | 12 | 7 | 0 | 0 |
| 25 | 12 | 7 | 0 | 0 |
| 26 | 12 | 7 | 0 | 0 |
| 27 | 12 | 7 | 0 | 0 |
| 28 | 12 | 7 | 0 | 0 |
| 29 | 12 | 7 | 0 | 0 |
| 30 | 12 | 7 | 0 | 0 |
| 31 | 12 | 7 | 0 | 0 |
| 32 | 12 | 7 | 0 | 0 |
| 33 | 12 | 8 | 0 | 0 |
| 34 | 12 | 8 | 0 | 0 |
| 35 | 12 | 8 | 0 | 0 |
| 36 | 12 | 8 | 0 | 0 |
| 37 | 12 | 7 | 0 | 0 |
| 38 | 12 | 7 | 0 | 0 |
| 39 | 12 | 7 | 0 | 0 |
| 40 | 12 | 7 | 0 | 0 |
| 41 | 12 | 7 | 0 | 0 |
| 42 | 12 | 8 | 0 | 0 |
| 43 | 12 | 7 | 0 | 0 |
| 44 | 12 | 7 | 0 | 0 |
| 45 | 12 | 7 | 0 | 0 |
| 46 | 12 | 7 | 0 | 0 |
| 47 | 12 | 7 | 0 | 0 |
| 48 | 12 | 7 | 0 | 0 |
| 49 | 12 | 7 | 0 | 0 |
| 50 | 12 | 7 | 0 | 0 |
| 51 | 12 | 7 | 0 | 0 |
| 52 | 12 | 7 | 0 | 0 |
| 53 | 12 | 10 | 0 | 0 |
| 54 | 12 | 10 | 0 | 0 |
| 55 | 12 | 9 | 0 | 0 |
| 56 | 12 | 10 | 0 | 0 |
| 57 | 12 | 10 | 0 | 0 |
| 58 | 12 | 10 | 0 | 0 |
| 59 | 12 | 10 | 0 | 0 |
| 60 | 12 | 10 | 0 | 0 |
| 61 | 12 | 11 | 0 | 0 |
| 62 | 12 | 11 | 0 | 0 |
| 63 | 12 | 10 | 0 | 0 |
| 64 | 12 | 12 | 0 | 0 |
| 65 | 20 | 13 | 0 | 0 |
| 66 | 20 | 12 | 0 | 0 |
| 67 | 20 | 13 | 0 | 0 |
| 68 | 20 | 12 | 0 | 0 |
| 69 | 20 | 15 | 0 | 0 |
| 70 | 20 | 15 | 0 | 0 |
| 71 | 20 | 16 | 0 | 0 |
| 72 | 20 | 18 | 0 | 0 |
| 73 | 20 | 17 | 0 | 0 |
| 74 | 20 | 19 | 0 | 0 |
| 75 | 20 | 17 | 0 | 0 |
| 76 | 20 | 17 | 0 | 0 |
| 77 | 20 | 20 | 0 | 0 |
| 78 | 80 | 20 | 0 | 0 |
| 79 | 80 | 20 | 0 | 0 |
| 80 | 80 | 20 | 0 | 0 |
| 81 | 80 | 17 | 0 | 0 |
| 82 | 80 | 18 | 0 | 0 |
| 83 | 80 | 17 | 0 | 0 |
| 84 | 80 | 17 | 0 | 0 |

### Key observation: selected_nodes discontinuity
- turn_020–064: selected_nodes = 12 consistently.
- turn_065–077: selected_nodes = 20 consistently.
- turn_078–084: selected_nodes = 80 consistently.

The jump from 12 → 20 → 80 is not driven by --max-nodes (which was fixed at 80 for the rebuild), but by the assembler selecting more nodes as graph density increased. ctive_must_include grows from 6 to 17–20 and is never dropped, so the core assembly promise (must_include retention) holds. No excluded_due_to_budget or excluded_due_to_state spikes are visible, confirming that budget pressure did not force out must-include nodes.

## 3. Lint Baseline Stability

| turn | status | critical | lint | queue | assembly | intro_errors | intro_warnings |
|------|--------|----------|------|-------|----------|--------------|----------------|
| 20 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 21 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 22 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 23 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 24 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 25 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 26 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 27 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 28 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 29 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 30 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 31 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 32 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 33 | OK | GREEN | GREEN | GREEN | GREEN | 2 | 0 |
| 34 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 35 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 36 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 37 | OK | GREEN | GREEN | GREEN | GREEN | 1 | 0 |
| 38 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 39 | OK | GREEN | GREEN | GREEN | GREEN | 2 | 0 |
| 40 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 41 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 42 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 43 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 44 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 45 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 46 | OK | GREEN | GREEN | GREEN | GREEN | 1 | 0 |
| 47 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 48 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 49 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 50 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 51 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 52 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 53 | OK | GREEN | GREEN | GREEN | GREEN | 1 | 0 |
| 54 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 55 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 56 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 57 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 58 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 59 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 60 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 61 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 62 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 63 | OK | GREEN | GREEN | GREEN | GREEN | 1 | 0 |
| 64 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 65 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 66 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 1 |
| 67 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 68 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 69 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 1 |
| 70 | OK | GREEN | GREEN | GREEN | GREEN | 1 | 1 |
| 71 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 72 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 73 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 74 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 75 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 76 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 77 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 1 |
| 78 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 79 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 80 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 1 |
| 81 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 82 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 83 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |
| 84 | OK | GREEN | GREEN | GREEN | GREEN | 0 | 0 |

- Total introduced errors: 9
- Total introduced warnings: 5
- All four health lights are GREEN for every turn.

The lint baseline is stable. Occasional introduced errors/warnings (turns 33, 37, 39, 46, 53, 63, 66, 69, 70, 72, 77, 80) are isolated and do not compound, suggesting the mechanical guard layer is catching Extractor imperfections rather than letting them accumulate.

## 4. Pending Merge Queue Health

- **Total tracked items:** 59
- **Overdue at turn_084:** 54
- **Overdue ratio:** 91.5%

### By source turn

| source_turn | count |
|-------------|-------|
| turn_020 | 2 |
| turn_024 | 1 |
| turn_027 | 3 |
| turn_030 | 2 |
| turn_031 | 1 |
| turn_032 | 1 |
| turn_033 | 1 |
| turn_035 | 2 |
| turn_039 | 2 |
| turn_045 | 1 |
| turn_048 | 1 |
| turn_050 | 1 |
| turn_051 | 6 |
| turn_052 | 3 |
| turn_054 | 1 |
| turn_055 | 2 |
| turn_056 | 1 |
| turn_057 | 2 |
| turn_058 | 3 |
| turn_060 | 2 |
| turn_061 | 1 |
| turn_063 | 1 |
| turn_064 | 1 |
| turn_066 | 1 |
| turn_067 | 2 |
| turn_068 | 1 |
| turn_069 | 1 |
| turn_070 | 1 |
| turn_071 | 1 |
| turn_072 | 2 |
| turn_074 | 1 |
| turn_077 | 2 |
| turn_078 | 1 |
| turn_081 | 2 |
| turn_082 | 2 |
| turn_083 | 1 |

### By match confidence

| confidence bucket | count |
|-------------------|-------|
| high (>=0.8) | 25 |
| medium (0.6-0.8) | 20 |
| low (<0.6) | 14 |

### By age (turns since creation)

| age bucket | count |
|------------|-------|
| >30 turns | 27 |
| 16-30 turns | 18 |
| 6-15 turns | 9 |
| 0-5 turns | 5 |

### Interpretation
The pending_merge queue is growing monotonically (0 → 54 overdue items). Most items are low-to-medium confidence aliases (e.g., SOUL.md vs log.md) that the resolver deliberately did not auto-merge. This is the expected conservative behavior, but the backlog is not being drained. Before entering OpenCode shadow mode, the queue should be reviewed: either resolve the oldest items manually or confirm they are intentionally parked and will be handled by a future escalation mechanism.

## 5. Risks & Recommendations

### Risk 1: Pending merge backlog growth
- **Severity:** MEDIUM
- **Evidence:** 54 overdue items, oldest from turn_020 (64 turns old).
- **Recommendation:** Do not let this grow indefinitely. Either (a) run a manual resolution pass on the oldest 10–15 items to validate the resolver’s conservative threshold, or (b) implement an escalation policy that auto-promotes or auto-closes stale pending items after N turns.

### Risk 2: Assembly selected_nodes jumps
- **Severity:** LOW
- **Evidence:** 12 → 20 → 80 selected nodes at turns 065 and 078.
- **Recommendation:** Verify that the 80-node selection at turn_078+ is intentional (e.g., context_bundle budget changed) and not an uncontrolled expansion. If it is intentional, document the policy; if not, cap it or revert to a smaller target.

### Risk 3: No turn_085 input available
- **Severity:** OPERATIONAL
- **Evidence:** No raw files for turn_085+.
- **Recommendation:** The project is checkpointed cleanly at turn_084. When new dialogue arrives, place it in the configured raw input path and run python graph/scripts/run_auto_turn.py abu_modern turn_085 --session s001. Until then, do not artificially advance the turn_counter.

## 6. Overall Verdict

The rebuilt chain is **healthy enough to continue** under strict full-auto mode. Mechanical guards are catching Extractor errors, graph growth is controlled, and assembly integrity is GREEN. The main action item is to address the pending_merge backlog before moving to OpenCode shadow mode.

**Next step priority:**
1. Review/resolve pending_merge backlog (especially oldest items).
2. Clean quarantine/ stale files and workspace.
3. Wait for turn_085 raw input to resume automated turns.
