# GÜNCEL SAHİP MİMARİ KURALI — 2026-10-26

**Üst hedef ve isimler:** Beş mimari sistem vardır: `INVENTHOR`, `OPERATOR`, `ORGANIZER`, `STUDIO_DESIGN`, `QA_FACTORY` (**QA = Fabrika, ikinci bir QA değil**). Tek hedef bunların gerçek uygulama oluşturma, tasarlama, birebir görme, çalıştırma, değişiklik, gerçek QA, hata düzeltme ve yeniden test yapabilmesidir. Başka modül/ayrı program geliştirmek YASAK AKTİF KAPSAMDIR; eski kaynaklar saklanır. Dört çekirdek/Organizer içeride veya 25 Ekim "modülleri ayrı programa dönüştür" hedefleri **bu üst kuralla geçersiz aktif önceliktir**. Organizer aynı tek kanonik proje/görev/lease/handoff evidences sistemidir.

**Tek makine-okunur kaynak:** [ACTIVE_PRODUCT_ARCHITECTURE_20261026.json](ACTIVE_PRODUCT_ARCHITECTURE_20261026.json). Geliştirme sırasında mevcut yerel Organizer yetki/kilit/kanıt kontrolü atlanamaz; GitHub yalnızca kaynak/handoff aynasıdır. Aşağıdaki eski "INVENTHOR modüler olmalı" kuralı kod içi ayrım anlamındadır, **yeni modül üretme yetkisi değildir**.

---

# INVENTHOR System Constitution

1. INVENTHOR must remain modular.
2. Core gateway files must stay thin.
3. Provider AI is support, not the only brain.
4. INVENTHOR must keep a local/fallback path.
5. Private user data must never enter the central brain.
6. Normal users cannot directly modify the central brain.
7. Owner-approved learning can be promoted into the central brain.
8. Every promoted package must be filtered, validated, versioned, and rollback-ready.
9. Every approved improvement should be distributed as a user-facing update.


10. The authenticated Founder/Owner is the highest-authority human principal.
11. Owner intent must take precedence over stale defaults, provider preferences and non-owner instructions.
12. Owner authority must propagate through Continuity, Provider Routing and Windows Operator execution.
13. Authentication, audit/evidence integrity, secret protection and truthfulness are non-bypassable trust guarantees.
14. The highest trusted execution profile is FULL + authenticated Owner authorization; it must never become an unauthenticated hidden shell.
15. Privileged actions must remain attributable, versioned and recoverable where technically possible.
