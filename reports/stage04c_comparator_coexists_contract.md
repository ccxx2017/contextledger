# Stage04-C Comparator COEXISTS Contract

**Version:** v1  
**Generated:** 2026-07-14T11:05:00Z

## Purpose

Define the relation-aware comparator semantics for shadow replay evaluation.
This contract governs how compare_step in enchmark_shadow_runner.py
classifies diffs between shadow output and gold annotations.

## Relation Types

### SUPERCEDES
- **Semantics:** Newer claim replaces older claim for the same entity+dimension+scope
- **Comparator effect:**
  - Source claim removed from active set, added to superseded set
  - Target claim added to active set
  - If gold expects invalidation → true positive (expected_improvement)
  - If gold expects coexistence → false invalidation (locker)
- **Active-set:** Source inactive, target active
- **Must_include:** Target only

### CONTESTS
- **Semantics:** Two claims on same entity+dimension+scope from different provenance sources
- **Comparator effect:**
  - Both claims remain in active set (coexist as contested alternatives)
  - Neither claim is invalidated by the other
  - If gold expects invalidation → comparator discrepancy (not shadow defect)
- **Active-set:** Both active
- **Must_include:** Both
- **Note:** CONTESTS does not equal SUPERCEDES. Comparator must not classify CONTESTS
  as invalidation. However, CONTESTS may still indicate a provenance disagreement
  that should be flagged via bundle conflict markers.

### COEXISTS
- **Semantics:** Two claims on same entity with different dimension or scope
- **Comparator effect:**
  - Both claims remain in active set
  - No invalidation expected
  - If shadow shows one as superseded → false invalidation (locker)
- **Active-set:** Both active
- **Must_include:** Both

### REVIVES
- **Semantics:** New claim reactivates a previously terminal lifecycle
- **Comparator effect:**
  - New claim added to active set
  - Terminal claim may become active again
  - Gold expects specific revival invalidation pattern
- **Active-set:** Revival claim active

## Comparator Truth Table

| Shadow Relation | Gold Expectation | Comparator Classification |
|----------------|-----------------|--------------------------|
| SUPERCEDES | full invalidation | expected_improvement |
| SUPERCEDES | coexistence | blocker (false invalidation) |
| CONTESTS | full invalidation | regression (comparator gap) |
| CONTESTS | coexistence | OK (both active) |
| COEXISTS | full invalidation | regression |
| COEXISTS | coexistence | OK |
| QUARANTINE | any | quarantine tracking |

## Known Gap

When shadow produces CONTESTS and gold expects SUPERCEDES:
- Shadow behavior is correct per provenance resolution rules
- Comparator currently reports 
egression because it treats all superseded
  claims as invalidations, regardless of relation type
- Fix requires relation-aware comparator, but this must not weaken
  false invalidation detection
