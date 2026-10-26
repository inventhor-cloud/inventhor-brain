# INVENTHOR Beyin — Kaynak Temizlik ve Eksik İş Denetimi

**Denetim tarihi:** 2026-10-26.
**Kapsam:** `inventhor-cloud/inventhor-brain` taslak PR #6, mevcut kaynak ağacı ve GitHub Actions üzerinden doğrulanabilen kaynak kontrolleri.
**Yetki:** SOURCE_REFERENCE_ONLY; yerel Windows dosyaları, gerçek Organizer kayıtları, kurulu uygulamalar, canlı QA ve imzalı sürüm **bu raporda denetlenmiş değildir**.
**Sahip üst kuralı:** `system_constitution/ACTIVE_PRODUCT_ARCHITECTURE_20261026.json` — tam olarak INVENTHOR, OPERATOR, ORGANIZER, STUDIO_DESIGN, QA_FACTORY; QA/Fabrika tektir.

## Kapsam ve dikkatli değerlendirme

Kaynaktaki 104 Git ağacı girdisi (dizinler dâhil) tarandı; merkezi Python görev devri/advisory kodları, kayıt/referans belgeleri, CI iş akışı, anayasa, kataloglar ve testleri incelendi. Eski planları veya kodu silmek, özellikle yetkili yerel Codex/Operator çalışması sürerken yanlış olabilir. Bu yüzden tarihsel verilerin orijinalliği korunarak **güncel kural en üste taşındı** ve otomatik çelişki/durum denetimi eklendi.

### Bu denetimde düzeltilen sorunlar

| Bulgu | Düzenleme | Sonuç |
|---|---|---|
| Eski 4-bileşenli hedefler ve 25 Ekim modülleri ayrı programa dönüştürme kararı, 26 Ekim'in 5-bileşenli nihai kuralıyla çelişiyordu | Güncel beşli mimari makine-sözleşmesi varsayılan girişte korundu; `README.md`, `CONTINUE_HERE.md`, `continuity/README.md`, `OWNER_WORK_INTAKE_POLICY.md` ve `LIVE_SOURCE_FRESHNESS_GATE.md` üst önceliğe göre düzeltildi; 25 Ekim planı tarihsel olarak etiketlendi | **SOURCE FIXED** |
| Yeni AI, Eylül'den kalan `continuity_manifest.json` ve `work_queue.json` verisini canlı iş listesi sanabilirdi | İlk okuma sırası **beşli sözleşme → gerçek yerel Organizer görev/lease → son checkpoint → tarihsel snapshot** biçimine getirildi | **SOURCE FIXED; NATIVE RECHECK ALWAYS REQUIRED** |
| PR CI yalnızca belirli `continuity/**` dosyaları değişince tetikleniyordu; temel `system_constitution/**` ve kök kurallar otomatik dışında kalabiliyordu | GitHub Actions bütün PR değişikliklerinde source hygiene, eski kaynak freshness, Python compileall ve bütün unittest'leri çalıştırıyor | **SOURCE FIXED** |
| Beş ana sistemden birinin eksikliği belirgin tutarlılık kontrolleriyle korunmalı | `tools/audit_brain_source.py` beş kanonik ID, QA=Fabrika eşanlamlıları, lease/no-replay, gerçek kaynak QA ayırımı, stale queue bayraklarını denetliyor | **SOURCE FIXED** |
| `continuity/core_brain_review.py` açıklamasında 4-core ifadesi kalmıştı | Açıklama 5-system olarak güncellendi; gerçek API'nin read-only davranışı değiştirilmedi | **SOURCE FIXED** |
| Yerel Organizer binary hash denetimi tüm programı `f.read()` ile belleğe alıyordu | `organizer_cli_reader.py` SHA-256 kontrolünü en fazla 1 MiB parçalarda yürütüyor; ikinci post-run hash kontrolü korunuyor | **SOURCE FIXED + LARGE FIXTURE TEST** |
| İlk yeni lint kuralı anayasa Markdown göreli bağlantısını yanlış yorumlayarak hata verdi | Bağlantı yolu kontrolü düzeltildi, başarılı CI ile yeniden doğrulandı | **SOURCE FIXED** |

### Kaynakta korunmuş fakat *aktif olmayan* alanlar

- `module_catalog.json`, `module_memory/module_catalog.json` ve `logic_registry.json` eski modüler fikir/katalog referanslarıdır; **bunların varlığı yeni modül/ürün geliştirme yetkisi DEĞİLDİR**. Kataloglar farklı amaçlıdır; sırf iki katalog var diye kayıtlar birleştirilmez.
- `continuity/DEFERRED_PROGRAM_CANDIDATES_20261025.json`, `continuity/program_control_gate.py`, `continuity/portable_module_admission.py` kaynakları mevcut; yeni bağımsız program/modül üretme görevi **PAUSED**, kaynakları koru.
- `provider_independence/free_provider_candidates_20261024.json` ileride kullanılabilecek sağlayıcı araştırmasıdır; yeni provider entegrasyonu hedefte yok. Ücretsiz abonelik başka bir API erişimi kanıtlamaz.
- `continuity/active_projects/WINDOWS_OPERATOR_P0_UNATTENDED.json` ve benzer eski P0 taslakları tarihsel kaynaklardır, bugün etkin Organizer hedefinin yerine geçmez.
- Federation/domain Brain katalogları ileride ayrı uzman kaynak depoları olarak referans kalabilir; beş ana ürünün yerine geçen yeni çalışma kuyruğu veya modül değildir.

### Doğrulama yapılmadan kapanmayacak gerçek işler

1. **NATIVE ORGANIZER — OPEN BLOCKER.** Windows bilgisayarındaki gerçek mevcut task ID, project ID, revizyon, Codex/Operator sahibi, lease, checkpoint, bağımlılık, önceki emir ve güncel hedef yeniden okunmalıdır. Kaynaktaki `role: canonical_resume_index` gibi tarihsel alanları gerçek yetki sanmak yasaktır. Son 26 Ekim beşli hedef, orijinal Organizer'la native olarak uzlaştırılmadan **MIGRATED** denemez.
2. **OPERATOR — OPEN BLOCKER.** Daha önce 17 yerel dosyanın Operator PR #3 ile çakıştığı ve Cleanup'ın yerelde silindiği bildirilmişti. Bu sayı ve durum da güncel yerel okumayla doğrulanmalı. Kör PR merge veya Cleanup restore yapılmamalı; kalan çekirdek için 3-way conflict çözümü, gerçek ACK, güvenli geri alma ve yetki kanıtı gerekli.
3. **STUDIO DESIGN — OPEN BLOCKER.** Gerçek dosya/proje oluşturma, düzenlenebilir arayüz, gerçek render/preview, çalıştırılan app, manuel fare müdahalesi, tek Inventhor asistanı ve ses işlevi ancak cihazda doğrulanabilir. Kaynak sözleşmesi/CI render kanıtı değildir.
4. **KALİTE FABRİKASI — OPEN BLOCKER.** Daha önce QA 0.5 kurulu/0.7 taslak bildirildi; hangi sürümün şimdi kurulu olduğu yeniden doğrulanmalı. Gerçek app derleme/run, bağımsız UI witness, gerçek fail → Studio fix → **aynı** Factory retest, artifact revision/hash, imza/UAC ve rollback yoksa LIVE_ACCEPTANCE beyanı YOK.
5. **SOURCE DRAFT PROMOTION — REVIEW PENDING.** PR #6 açık taslak olarak tutuluyor; yalnızca yazılı kaynak testlerinin geçmesi kurulu uygulama veya Main entegrasyonu anlamına gelmez. Birleştirme/kurulum/iş devri için mevcut native owner/lease/release kontrolleri gerekir.
6. **RUNTIME CONNECTION — OPEN BLOCKER.** Desktop Commander bu turdaki gözlemde INVENTHOR cihazını **Offline** gösterdi. Bu, Brain'in yerelde çalışmadığının kanıtı değildir; yalnızca ChatGPT'nin o kanal üzerinden canlı test yapamadığı anlamına gelir.

### Beşli hedefe göre kalan en küçük gerçek kabul dizisi

`REAL_ORGANIZER_TASK_READ → EXACT_OWNER_LEASE → STUDIO_EDITABLE_PROJECT → OPERATOR_BUILD_AND_RUN_WITH_ACK → QA_TEST_SAME_BUILD → DEFECT_EVIDENCE → STUDIO_REPAIR_NEW_REVISION → SAME_QA_RETEST → NATIVE_ROLLBACK/OWNER_RELEASE_GATES`

**SONUÇ:** Kaynak temizlik katmanı ve otomatik linter iyileştirildi. Beşli kural için kaynak testleri başarıyla çalışıyor. **Sistem bütünüyle temiz/kurulu/aktif olarak doğrulanmadı.** Kalıcı silme, canlı çalışma taşıma ve QA kabulü yapılmadı.

**İş sınırı:** Codex native görevini ve aktif lease'ini devralma; başka görev oluşturma; 25 Ekim bağımsız program planını yeniden etkinleştirme; eylem ve test sonucu üretme veya uydurma; terminal işi yeniden oynatma.

## Aynı gün — Studio → QA hata zinciri ek düzeltme

`continuity/studio_factory_handoff.py` kaynak denetimi daha sıkı hâle getirildi. Studio düzenleme aşaması eski build/QA çalıştırma kanıtını taşıyamaz. Gerçek hatadan sonra yeni sürümün QA'ya geri gönderilmesi için **önceki başarısız build hash'i, önceki Fabrika çalıştırma ID'si, hata kanıtı, daha yüksek Studio revizyonu ve değişmiş build hash'i** tutarlı olmalıdır. Yeniden QA'nın ID'si önceki başarısız QA ID'si olamaz. Önceki başarısız test yoksa `REPAIRED_RUNNING` adı kullanılmaz. İlk denemede başarılı QA, ilgisiz tarihsel hata kanıtı taşıyamaz. Hiçbiri native Factory PASS, imzalı çıktı veya PC'de kurulu çalışma kanıtı üretmez.

Bu ek kaynak korumaları `tests/test_studio_factory_handoff.py` içinde negatif ve pozitif durumlarla denetlenir. **Doğrulama sonucu GitHub Actions'ın en son commit bazlı sonucu okunmadan başarı sayılmayacaktır**. Yerel Organizer/Operator/Studio/Factory entegrasyonu hâlâ ayrı ve engellidir.
