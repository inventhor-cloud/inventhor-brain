# Deduplication and Merge-Candidate Pipeline

Purpose: stop repeated work, repeated modules, repeated knowledge and repeated downloads before they consume provider quota or machine resources.

## Layered filter

### L0 — Stable identity / idempotency
Check stable IDs, TASK_ID + EPOCH, module_id, artifact IDs and known aliases.

### L1 — Exact fingerprint
Normalize deterministic content and compare SHA-256 fingerprints.

### L2 — Structural fingerprint
Compare normalized names, paths, dependency sets, module capabilities, schemas and artifact metadata.

### L3 — Local lexical similarity
Windows Operator may calculate deterministic token/Jaccard similarity locally. This costs no AI tokens.

Suggested thresholds:
- 1.00 exact duplicate
- >= 0.90 likely duplicate
- >= 0.70 related/merge candidate
- below 0.70 usually new

Thresholds are hints, not semantic truth.

### L4 — Knowledge Graph neighborhood
Check whether equivalent entities/facts already exist through aliases, SAME_AS, SUPERSEDES, IMPLEMENTS, DEPENDS_ON or MERGED_INTO relations.

### L5 — AI semantic review
Only ambiguous candidates are sent to the Brain/provider.

Possible Brain decisions:
- REUSE_EXISTING
- LINK_EXISTING
- MERGE_RECORDS
- SUPERSEDE_OLD
- CREATE_NEW
- NEEDS_REVIEW

## Boundary

Operator performs cheap deterministic filtering and reports candidates.
INVENTHOR Brain performs semantic merge/reuse decisions.
Operator must not silently merge canonical records.

## Audit

Every prevented duplicate or merge decision records:
- candidate IDs
- fingerprints
- similarity score
- decision
- decision owner
- provenance
- timestamp/revision
