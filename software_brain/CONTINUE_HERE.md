# Software Brain Continue Here

STATUS=SOFTWARE_BRAIN_FOUNDATION_IN_PROGRESS
VERSION=0.1.0
PRIORITY=1
OPERATOR_CONNECTION=AUTO_DISCOVER_USER_APPROVAL_AFTER_VALIDATION
NEXT_TASK=Validate manifest, capability registry, filter policy, continuation contract and connection gate.
AUTONOMOUS_CONTINUATION=SEQUENTIAL_FINITE
ADVANCE_AFTER=BS
STOP_AFTER=BF_OR_APPROVAL_OR_SECURITY_OR_DELIVERY_FAILURE

Rules:

- Read this file and the software-brain ledger before continuing.
- Use one finite task and one stable TASK_ID at a time.
- Never promote private data, credentials or raw conversations.
- Never report BS without evidence and result delivery.
- Discover Operator automatically, but require the user's Settings approval before activation.
- After approval, reconnect automatically on session start; revocation must disconnect immediately.
- If a next finite task exists, continue automatically after a real BS.
- Never invent a task to avoid an honest BF or approval pause.
