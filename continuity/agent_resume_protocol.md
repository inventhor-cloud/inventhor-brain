# Agent Resume Protocol

Every new chat/provider/session must treat INVENTHOR continuity as the canonical state source.

## On start

Read the continuity manifest, then all ACTIVE/P0 project state records.

Build a compact internal resume packet containing only:
- architecture decisions
- completed/verified facts
- implemented-but-not-verified facts
- blockers
- current next task
- acceptance criteria
- relevant evidence/source references
- idea pool items only when they affect the current task

Do not ask the user to repeat information already present in canonical continuity.

## On execution

Choose one finite next task whose prerequisites are satisfied.
Prefer Operator/local execution for builds, tests, scans, packaging, file operations and repetitive work.
Use expensive AI/provider reasoning only for decisions, architecture, review or problems that Operator cannot solve deterministically.

## On handoff

Before ending a meaningful work session, write a handoff record containing:
- project_id
- from_agent/provider
- current state
- what changed
- evidence references
- blockers
- exact next task
- do_not_repeat
- unresolved decisions

The next provider continues from that handoff rather than replaying the full history.

## Truth rules

REQUESTED is not DONE.
SOURCE_IMPLEMENTED is not RUNTIME_VERIFIED.
CI_PASS is not LOCAL_DEPLOYED.
LOCAL_DEPLOYED is not END_TO_END_CONNECTED.
DONE requires project-specific evidence.

## Live-state safety and current scope (2026-10-22)

This public repository is a **reference snapshot**, not current task ownership or runtime readiness evidence. Before *any* execution, every agent (currently GPT, Codex or INVENTHOR) must obtain the exact canonical task ID and live task-scoped handoff directly from the owner-authorized Main/Organizer interface. A missing live handoff, missing write lease, unresolved dependency or stale epoch denies mutation, not just completion reporting. See [LIVE_SOURCE_FRESHNESS_GATE.md](LIVE_SOURCE_FRESHNESS_GATE.md).

At handoff, persist separately: verified completed steps, still-open steps, evidence refs and verified hashes, task target and active owner, blocker, exact next safe step; planned handoff releases the lease and next agent rereads current state. If the execution result is uncertain, reconcile rather than blind retry.

New owner ideas are collected/deduplicated in the canonical idea pool by default, **without preempting the current QA Factory goal**. New provider integrations and adaptive task distribution are future backlog; only GPT/Codex/INVENTHOR coordination is in the immediate scope. Live implementation and tests are required before any claim that this protocol automatically runs.

## Odak koruyan kaynak karar katmanı (2026-10-23)

Var olan native Organizer'dan görev okunması için pinned `OrganizerCliReader` ve sınırlı `TaskResumeView` geliştirme dalında mevcut. Bunlar salt-okunurdur, `START` veya `WRITE` izni vermez.

Beyin, mevcut owner-approved ACTIVE plan kapsamındaki en küçük izinli hazır görevi önerirken `continuity/focus_adviser.py` kullanabilir. Böyle bir öneri yalnızca tam eşleşen `plan_id`, `plan_revision`, proje/hedef/üst iş, `authorized_work_ids`, `allowed_capabilities` ve **pozitif kalan dispatch bütçesi** üzerinden üretilir. Bağımlılık kayıtlarında çelişen DONE işaretleri veya başka çalışan varsa görev hazır değildir; COMPLETED/PAUSED plan yeniden oynatılmaz. Yeni fikirler otomatik iş planı sayılmaz.

`continuity/decision_trace.py` her öneri için belirli bir JSON görünümü ve SHA-256 parmak izi üretir. Bu parmak izi **denetim/dedup içindir, imza veya Native ACK değildir**. Yürütme yine mevcut Main/Organizer üzerinde taze sahiplik, kilit ve preflight doğrulaması ister. Tamamlanan/kalan/kanıt ayrı checkpoint alanlarına girilip serbest bırakıldıktan sonra sıradaki ajan verileri tekrar okur.

İlk kaynak doğrulaması GitHub Python testlerindedir; çalışan PC'ye bağlama, imzalı kurulum ve gerçek QA acceptance hâlâ ayrı açık işlerdir. Yetkisiz terminal görev replay, taslak QA'yı READY yapma veya kaynak testinden CANLI kurulum çıkarma yasaktır.

## Ajan kimliğini insan kimliğinden ayırma (2026-10-23)

Hangi oturumda, hangi `TASK_ID` için, kimin yazdığı native host tarafından doğrulanmadan bir model yanıtı **Owner/insan mesajı** veya gerçek yürütme kanıtı sayılmaz. `continuity/agent_action_origin.py` kaynak düzeyindeki iç görev önerilerini `AUTOMATED_AGENT` etiketiyle hazırlar; ChatGPT kullanıcı sohbeti, e-posta ve diğer dış mesaj hedeflerini reddeder. `continuity/AGENT_ACTION_ORIGIN_POLICY.md` bu sınırı ayrıntılı tanımlar. Bu kod tek başına canlı yetki, mesaj gönderimi, native olay kaydı veya bir sohbet mesajının asıl yazarını kanıtlamaz.
