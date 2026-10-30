# SON SAHİP SÖKÜM TALİMATI — 2026-10-26

> **EN SON SAHİP KARARI — 28 EKİM 2026 — İLK OKU:** **ŞİMDİ P0: GEREKSİZ MODÜLLERİ ÇEKİRDEKTEN TAMAMEN SÖK, 0 AKTİF BAĞIMLILIK KALDIR.** Sonra **P1:** mevcut tek Operator + Studio + QA Fabrikası gerçek uygulama yapıp test etsin. Bunlar tamamlanınca **P2:** formatlanmış/başka bilgisayara doğrulanmış bulut sürümünü indir, **aynı hesapla giriş yap, şifreli Organizer/proje yedeğini geri yükle**, yeni cihaz kimliği ve pairing key üret. Bulut geliştirmesi şu an sökümü geciktirmeyecek. Yeni modül/ayrı program/ikinci çekirdek yok. **İlk gerçek talimat:** [OWNER_PRIORITY_CLEAN_CORE_THEN_CLOUD_20261028.md](continuity/OWNER_PRIORITY_CLEAN_CORE_THEN_CLOUD_20261028.md); [tek makine sözleşmesi v1.5](system_constitution/ACTIVE_PRODUCT_ARCHITECTURE_20261026.json). Kaynak ilerlemesi yerel Organizer checkpoint veya Windows söküm kanıtı değildir.



> **ÇEKİRDEK-BAĞIMSIZLIK DENETİMİ:** Hiçbir opsiyonel/legacy modül Operator, Inventhor, Organizer, Studio, QA için temel gereklilik olamaz. Kaynakta OperatorWorker PluginCatalog üzerinden yürütücü/transport alıyor ve eski kurulum 16 modül istiyor; bu bir **kaynak mimari kusuru**, kaçınılmaz çekirdek bağımlılığı değildir. [Kanıt ve düzeltme sırası](validation_reports/OPERATOR_OPTIONAL_MODULE_COUPLING_20261026.md). Mevcut native task+lease ile önce bağımsız çekirdek işlevini ve boş plugin klasörü boot/QA'yı doğrula; sonra tam söküm. PC kurulu durumu doğrulanmadı.


**ÜST MİMARİ TALİMAT — 2026-10-26:** Yalnızca `INVENTHOR`, `OPERATOR`, `ORGANIZER`, `STUDIO_DESIGN`, `QA_FACTORY` kalacak. QA=Fabrika (tek servis). **TÜM non-core eski bağımsız modüller**, aktif servis/başlangıç/menü/registry/installer/CI/build/IPC ve ters-bağımlılıklarıyla **TAMAMEN canlı sistemden sökülecek**. Gizlemek veya durdurmak tamamlandı sayılmaz. Eski noncore kimliklerinden beş sisteme **0 aktif bağımlılık** kalmalı. Zorunlu çekirdek işlevleri beş sistemin **içinde** korunur/taşınır; gizli eski plugin bağımlılığı bırakılmaz. Yerel devre dışı bırakma/sökümün kendisi **henüz doğrulanmadı**.

**YENİ AI VE CODEX ÖNCE OKU:** [Tam söküm ve Organizer devam kuralı](continuity/OWNER_NONCORE_TOTAL_DETACH_HANDOFF_20261026.md), sonra [makine-okunur tek mimari sözleşme](system_constitution/ACTIVE_PRODUCT_ARCHITECTURE_20261026.json). Önce mevcut Windows Organizer exact TASK_ID + worker lease oku; yeni görev, ikinci Organizer/Studio/Fabrika/Operator kurma. Eski 25 Ekim "ayrı uygulama yapma", 26 Ekim "yalnızca arşivle/pasifleştir" yönleri **bu tam söküm emrine göre geçersiz aktif hedeftir**. Kaynak kayıtları ve kullanıcı verisi saklanabilir, fakat canlı üründe eski modül yokmuş gibi davranmak **testle kanıtlanmalıdır**.

---

# ÜST MİMARİ TALİMAT — 2026-10-26

**HEDEF = SADECE BEŞ İŞLEVSEL PARÇA:** INVENTHOR, OPERATOR, ORGANIZER, STUDIO DESIGN, KALİTE FABRİKASI (QA). **QA/Fabrika aynıdır.** Tek uygulama üretim zincirini bitir. Yeni modül, ürün, ayrı program, provider veya yan projede geliştirme yapma. Eski modülleri yalnızca sakla/gelecek havuzunda tut; ancak güvenli ve geri alınabilir temizliğini çekirdek bağlantıları koruyarak yap. Organizer ayrı yetkili tek kanonik kayıt, INVENTHOR arayüzü içinde görülebilir ama kopyalanamaz.

**Önce şunu oku:** [Machine contract](system_constitution/ACTIVE_PRODUCT_ARCHITECTURE_20261026.json) ve [Architecture owner contract](https://github.com/inventhor-cloud/inventhor-brain-architecture/blob/feat/advisory-architecture-guard-v1-20261015/constitution/OWNER_ACTIVE_PRODUCTION_ARCHITECTURE_20261026.md). Bunlar önceki 25 Ekim modül/program planlarını ve aşağıdaki dört çekirdek sözcüklerini **aktif öncelikte geçersiz kılar**. Kaynak CI başarıları kurulu program veya QA başarı beyanı değildir. Yerel mevcut Organizer TASK_ID/lease alınmadan görev yazılamaz.

---

# GÜNCEL ÖNCELİK — 2026-10-26

**SADECE UYGULAMA ÜRETEN ANA SİSTEM:** INVENTHOR (Brain/Main + mevcut Organizer), OPERATOR, STUDIO DESIGN, KALİTE FABRİKASI. Bu dört bileşen gerçek tasarım→birebir görüntü→çalıştırma→değiştirme→QA→onarım→yeniden QA akışında çalışacak. Başka modül/program geliştirme ve eski modülleri ayrı uygulamaya dönüştürme çalışması **DURDURULDU/GELECEK HAVUZUNDA**. Sadece gerekliyse yedekli, geri alınabilir, bağımlılık doğrulanmış non-core devre dışı bırakma.

**Son sahibi yönergesi ve Codex/Organizer taşınma sözleşmesi:** [OWNER_PRIORITY_PRODUCT_ENGINE_20261026.md](continuity/OWNER_PRIORITY_PRODUCT_ENGINE_20261026.md).
**Eski 25 Ekim 'ayrı program' bölümleri bugün için GEÇERSİZ ÖNCELİKTİR; kaynak arşividir.** Bu bulut belge/PR, kurulu Organizer yetkisi veya QA kabulü değildir. Yerel Codex mevcut orijinal TASK_ID/lease üzerine yeni hedefi işlemelidir.

---

# Historical source records / superseded priorities

**IMPORTANT (2026-10-22):** These are public cloud reference files, not live local work authority. The operator and Main may have newer installed state; see [live source/freshness gate](continuity/LIVE_SOURCE_FRESHNESS_GATE.md) and obtain exact task-scoped handoff from the owner-authorized canonical Organizer before any write, status claim or restart. The earlier project/next task noted below is historical, not the current priority. Default: new ideas go to intake without interrupting active QA or separately scoped Brain housekeeping. No new providers are in the immediate GPT/Codex/INVENTHOR roster.


STATUS=REFERENCE_ONLY_LIVE_TASK_RECHECK_REQUIRED
LAST_CLOUD_REFERENCE_VERIFIED=2026-09-22
CURRENT_RUNTIME_VERIFIED=NO

SYSTEM_OF_RECORD=INVENTHOR_MAIN
EXECUTION_REPLICA=WINDOWS_OPERATOR
CLOUD_ROLE=SYNCED_REPLICA
PROVIDER_CHAT_ROLE=NON_CANONICAL_CONTEXT

HISTORICAL_ACTIVE_PROJECT_20260922=WINDOWS_OPERATOR_P0_UNATTENDED
HISTORICAL_NEXT_TASK_20260922=Finish Windows Operator V2.3 CI/deploy path, then verify Session Agent and unattended execution on WINDOWS-INVENTHOR.

BOOTSTRAP_SOURCE=The current INVENTHOR Main System exists only in a Desktop backup package on WINDOWS-INVENTHOR. Inventory and hash it read-only before importing anything.

READ_FIRST:
1. continuity/continuity_manifest.json
2. continuity/STANDARD_TERMINOLOGY.md
3. continuity/SYSTEM_OF_RECORD_AND_REPLICATION.md
4. continuity/active_projects/WINDOWS_OPERATOR_P0_UNATTENDED.json
5. continuity/idea_pool.json
6. latest Handoff Packet / Checkpoint / Event Log references

DO_NOT_REPEAT:
- Android Operator development
- rebuilding project context from chat history
- treating CI_PASS as LOCAL_DEPLOYED
- treating provider conversation as canonical project truth

Any new AI/provider must resume from the System of Record and select exactly one finite eligible Work Item.

## OWNER CORE-ACTIVATION DIRECTION — 2026-10-25

ACTIVE_SCOPE=INVENTHOR_BRAIN,OPERATOR,ORGANIZER,QA_FACTORY
OTHER_MODULES=DEFERRED_FUTURE_SEPARATE_PROJECTS_NOT_AUTO_ACTIVATED
OWNER_EXPERIENCE=Actual program opens; single small movable INVENTHOR voice/text assistant in the program; authorized Operator edits the real program, user may take over; Organizer tracks work and QA Factory tests.
SOURCE_ACTIVATION_CHECK=continuity/core_activation_gate.py
SOURCE_ACTIVATION_TEST=tests/test_core_activation_gate.py
CURRENT_SOURCE_TEST=GitHub Actions 40223408469 success at commit 84cd3b0c6e2d7a4e259ed0071237e2d74458b5c7 (SOURCE ONLY)
ACTIVATION_LIMIT=This source-only gate cannot activate installed code, grant a native lease, sign a release, or attest live QA. Never claim activation from this mirror.
KNOWN_NATIVE_BLOCKERS=Last reported QA Factory 0.5.0 installed / 0.7 draft, 17 Operator PR#3 versus local conflicts with Cleanup locally deleted, Main/Operator native ACK not proven, signing/rollback witness pending. Native Organizer must be freshly read to verify whether these are still current.
NEXT_NATIVE_STEP=Trusted Main/Organizer owner/lease check, classify deployed core versus deferred modules, reconcile Operator conflict, verify exact signed artifacts/rollback/handshake and QA acceptance, then owner-gated progressive activation. No blind merge/deletion/restore or duplicate modules. DC low quota/offline is not a Brain runtime state.

## FOUR-CORE COMPOSED BRAIN REVIEW — 2026-10-25

SOURCE=continuity/core_brain_review.py
TEST=tests/test_core_brain_review.py
FUNCTION=prepare_core_brain_review
INPUT=Exact native Organizer handoff + independently trusted Main context host + one claimed CoreActivationSnapshot + exact task/revision/time.
OUTPUT=CoreBrainReview: current task and finite safe advisory + four-core activation blockers in one bounded read-only object.
SAFETY=Never dispatch/claim/install/delete. Even zero reported blockers => NATIVE_REVIEW_REQUIRED, not activated. Does not authenticate arbitrary caller's activation facts. Must not be used as a security ticket.
NATIVE_HOST_GAP=Real Main must collect, authenticate and reconcile same-epoch installed evidence for all four components; verify native owner/lease, signatures, artifact hashes, Operator result ACK, QA witness and rollback. Native Composer/real-program command execution is separately gated.
SCOPE=Four-core integration only; no new module, queue, factory, voice provider or app.

## 2026-10-25: owner-approved application creation end-to-end goal

OWNER_ACTIVE_PRODUCT_GOAL=single clean INVENTHOR using Brain/Main, Operator, Organizer, QA Factory to create actual programs from voice/text instructions; design, one-to-one render and run, update, human change-of-mind/mouse override, Factory test, evidence-linked repair, re-test, rollback and gated delivery.
AUTHORITATIVE_OWNER_MIRROR=continuity/OWNER_CORE_APPLICATION_FACTORY_GOAL_20261025.md
NATIVE_ORGANIZER_GOAL_MIGRATION=REQUIRED_NOT_VERIFIED
OWNER_COMMANDED_CODEX=YES_REPORTED_BY_OWNER; DO_NOT_DUPLICATE_WORK
ONLY_NATIVE_WORKER_WITH_VERIFIED_CURRENT_TASK_AND_LEASE_MAY_EDIT_ORGANIZER=TRUE
NONCORE_MODULES=DEFER_SEPARATE_PROJECTS_AND_SAFE_DETACH_AFTER_BACKUP_QA
SOURCE_HAS_NO_RUNTIME_ACTIVATION_AUTHORITY=TRUE

## SEPARATE PROGRAMS + CENTRAL INVENTHOR CONTROL — OWNER UPDATE 2026-10-25

SOURCE_OWNER_GOAL=continuity/OWNER_CORE_APPLICATION_FACTORY_GOAL_20261025.md
SOURCE_CANDIDATES=continuity/DEFERRED_PROGRAM_CANDIDATES_20261025.json
SOURCE_PROGRAM_CONTROL_GUARD=continuity/program_control_gate.py
SOURCE_TEST=tests/test_program_control_gate.py
POLICY=User-facing legacy feature modules become separate individually listed standalone programs in the future, not permanently embedded in INVENTHOR. The four core Brain/Main, Operator, Organizer and QA Factory stay singletons. Security, transport and necessary internal adapters remain internal when a verified core dependency.
PROGRAM_AI_CONTROL=Each real program can expose its full permission-scoped, versioned capabilities to the SAME Brain and Operator. The user controls via compact text/live-voice assistant, and may also use the program manually. No silent admin authority, duplicate AI, duplicate operator, fake edits or fake test results. Source program control gate is READ-ONLY and never grants native execution.
NATIVE_ORGANIZER_MIGRATION=REQUIRED_BY_CODEX_UNDER_VERIFIED_EXISTING_TASK_OWNER_LEASE_NOT_YET_VERIFIED_HERE
MIRROR_IS_NOT_INSTALLED=true

## SOURCE-ONLY KOD İLERLEMESİ — 26 EKİM 2026

> **26 EKİM — KOD İLERLEMESİ / CODEX DEVİR:** [Operator taslak PR #5](https://github.com/inventhor-cloud/inventhor-operator-core/pull/5) ile iki Beyin transportu doğrudan çekirdek derlemeye bağlandı, aynı transportun plugin olarak ikinci kez yüklenmesi engellendi ve çekirdek salt-okunur STATUS komutu modülsüz çalışabilir hâle getirildi. [Windows kaynak CI](https://github.com/inventhor-cloud/inventhor-operator-core/actions/runs/40419263111): **166/166 PASS**, servis publish, WPF derlemesi ve predeploy testleri başarılı. **TAM SÖKÜM veya NATIVE CANLI TEST DEĞİLDİR.** Codex mevcut Organizer TASK_ID/lease+yerel diff üzerinden doğrulamadan merge/install yapmasın. Kalan eski executor/plugin, 16-modül dağıtım betiği, Studio build/run ve Fabrika QA için [açık kaynak denetimi](validation_reports/OPERATOR_OPTIONAL_MODULE_COUPLING_20261026.md).

> **27 EKİM — STUDIO KAYNAK İLERLEMESİ:** Operator taslak PR#5 içinde `CoreStudioWorkspaceExecutor` gerçek proje dizinini ve manifestini `app/modules` olmadan oluşturabiliyor; eski Factory'nin bu yetkiyi tekrar sunmasını önleyen geçiş adaptörü ve negatif tests var. Kaynak CI **166/166 PASS**, kurulu Windows Studio/QA **HENÜZ DOĞRULANMADI**. [Ayrıntılı Codex ortak devam](https://github.com/inventhor-cloud/inventhor-operator-core/issues/4#issuecomment-6429751022).
