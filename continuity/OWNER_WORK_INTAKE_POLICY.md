# Owner Work Intake Policy

Status: ACTIVE

Every new Owner request that represents work must become a canonical Work Item unless it is purely conversational.

Intake pipeline:
1. normalize the request
2. compute stable fingerprint
3. compare against Project Registry / Work Queue / Module Registry / Knowledge Graph
4. classify as NEW / RELATED / MERGE_CANDIDATE / DUPLICATE
5. if duplicate, link to the existing Work Item instead of creating another
6. if related, attach dependency/relation
7. assign project, priority and prerequisites
8. insert into the canonical Work Queue
9. replicate the execution-relevant slice to Windows Operator
10. continue automatically when prerequisites are satisfied

Owner can reprioritize at any time.

Default execution policy:
- deterministic/local Operator work first
- provider use only when semantic reasoning is actually needed
- do not spend provider tokens on build/test/hash/copy/download/inventory/retry/status work
- checkpoint after meaningful progress
- keep evidence
- never claim DONE without acceptance evidence

The queue survives chat/provider/session changes.
