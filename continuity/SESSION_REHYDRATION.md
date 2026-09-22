# Session Rehydration and Provider Handoff

## Standard terms

The process of starting a new chat/provider from saved canonical state is **Session Rehydration**.

The minimal transferable state is a **Handoff Packet** created from a **Checkpoint** plus the current **Project State** and **Ready Queue**.

## Trigger conditions

A new provider/session may be started when:
- context budget approaches a configured threshold,
- provider quota/cooldown requires routing,
- the current provider fails or becomes unavailable,
- a user explicitly switches AI/provider,
- a task requires a different provider capability.

## Flow

1. Commit current state transition to the Event Log.
2. Create a Checkpoint.
3. Generate a compact Handoff Packet.
4. Persist it in the System of Record.
5. Select the next provider/session.
6. Rehydrate only the relevant project slice.
7. Continue the same Work Item / TASK_ID when ownership permits.
8. Never reconstruct canonical truth from chat transcript alone.

## UI fallback

Preferred path is provider API/app integration. Browser/UI automation through Windows Session Agent is only a fallback for providers that lack an integration.

If UI fallback is used, Operator may open/focus the target provider page and paste/submit the Handoff Packet, but INVENTHOR remains the owner of reasoning and task state.

## Token/quota control

Do not resend full history. A Handoff Packet should contain only:
- objective
- architecture decisions
- verified facts
- current work item
- blockers
- next action
- evidence references
- do-not-repeat set
- unresolved decisions

This is the default strategy for keeping provider usage low.
