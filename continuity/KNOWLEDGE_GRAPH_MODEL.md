# INVENTHOR Knowledge Graph Model

The knowledge layer is a revisioned, provenance-aware **Knowledge Graph**.

## Node types

- SYSTEM
- PROJECT
- MODULE
- CAPABILITY
- WORK_ITEM
- ARTIFACT
- EVIDENCE
- DECISION
- REQUIREMENT
- PROVIDER
- DEVICE
- ERROR
- FIX
- IDEA
- CONCEPT

## Edge types

- DEPENDS_ON
- IMPLEMENTS
- PRODUCES
- VERIFIED_BY
- BLOCKED_BY
- SUPERSEDES
- MERGED_INTO
- SAME_AS
- RELATED_TO
- CAUSED_BY
- FIXED_BY
- DECIDED_BY
- EXECUTED_BY
- OWNED_BY
- REQUIRES
- DERIVED_FROM

## Every fact/edge requires

- stable ID
- source/provenance
- revision
- created_at
- validity/status
- confidence when inferred
- namespace/project scope

## Integrity rules

- no dangling edges
- no promoted fact without provenance
- no silent overwrite of conflicting facts
- aliases resolve to one canonical entity or remain explicitly ambiguous
- superseded records stay traceable
- deleted local cache does not erase canonical audit history
- graph validation runs before promotion
- secrets are references, never knowledge-graph payloads

## Completeness model

The system cannot guarantee that all real-world knowledge is complete. It can guarantee internal structural checks:
- referential integrity
- schema validity
- provenance coverage
- conflict visibility
- orphan detection
- unresolved-link queue
- duplicate-candidate queue

The unresolved-link queue is the explicit list of “puzzle gaps” still needing evidence or a decision.
