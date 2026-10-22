# Owner Work Intake Policy

Status: ACTIVE

Every new Owner request that represents work must enter the canonical **idea/backlog intake** unless it is purely conversational. Intake is not permission to start, and an existing active job is not implicitly preempted. Only an explicit owner priority-change instruction can override the current target, subject to existing authorization and safety checks.

Intake pipeline:
1. normalize the request
2. compute stable fingerprint
3. compare against Project Registry / Work Queue / Module Registry / Knowledge Graph
4. classify as NEW / RELATED / MERGE_CANDIDATE / DUPLICATE
5. if duplicate, link to the existing Work Item instead of creating another
6. if related, attach dependency/relation
7. assign project, priority and prerequisites
8. insert into the canonical Idea Pool or Work Item backlog; mark non-urgent/new feature requests as PLANNED and do not automatically make them executable
9. when authorized and eligible, promote the canonical Work Item and replicate only the execution-relevant slice to Windows Operator
10. continue automatically **only if** explicit work-plan authorization, ownership/lease and prerequisites are satisfied; unrelated ideas never interrupt in-flight work

Owner can reprioritize at any time.

Default execution policy:
- deterministic/local Operator work first
- provider use only when semantic reasoning is actually needed
- do not spend provider tokens on build/test/hash/copy/download/inventory/retry/status work
- checkpoint after meaningful progress
- keep evidence
- never claim DONE without acceptance evidence

The queue survives chat/provider/session changes.

## Operator / Brain scope boundary

GPT/Codex/INVENTHOR collaboration and the QA Factory are the immediate owner priority. Brain cleanup may proceed concurrently in non-overlapping files/targets. Additional provider integrations belong in the backlog until the owner changes priorities. This file is public reference policy, not an executable work authorization or a replacement for live canonical Organizer records. See [LIVE_SOURCE_FRESHNESS_GATE.md](LIVE_SOURCE_FRESHNESS_GATE.md).
