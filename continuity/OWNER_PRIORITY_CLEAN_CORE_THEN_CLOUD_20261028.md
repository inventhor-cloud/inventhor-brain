# SON SAHİP HEDEFİ — ÖNCE YALIN ÇEKİRDEK, SONRA BULUTTAN TAM GERİ KURULUM

**Sahip kararı: 28 Ekim 2026.**
**İlk okunacak kaynak, P0 yürütme sırasını belirler.** Bu kaynak bir GitHub iş devri aynasıdır; kurulu Windows Organizer'ın canlı görev kaydı ya da tamamlanmış söküm kanıtı değildir. **Eski task/project ID oluşturma; gerçek mevcut Organizer TASK_ID / PROJECT_ID / revision / worker lease kullan.**

## Bitirilecek TEK ana ürün

1. INVENTHOR — planlayan tek beyin.
2. OPERATOR — INVENTHOR'un güvenli ve izinli gerçek eylem organı, ayrı beyin değil.
3. ORGANIZER — tek kanonik görev, proje, iş geçmişi ve checkpoint defteri (UI içinde entegre görünür; mükerrer ürün kurulmaz).
4. STUDIO_DESIGN — var olan gerçek tasarım, gösterim, düzenleme ve uygulama çalışma alanı.
5. QA_FACTORY — **tek mevcut kalite fabrikası**; QA=Fabrika; gerçek uygulamayı denetler, hatayı Studio'ya geri yollar ve yeni build hash'iyle yeniden test eder.

## P0 AŞAMA 1 — HEPSİNDEN ÖNCE YALINLAŞTIR / TAM MODÜL SÖKÜMÜ

**Önce bu aşama, bitmeden yeni program ve büyük bulut geliştirmesine GEÇME.**

- Yerel mevcut Organizer task/lease'i ve güncel native çalışma ağacını oku, PR#3, PR#5 ve Codex yerel değişikliklerini 3-way diff ile karşılaştır; hiç kimsenin dosyasını ezme.
- Mevcut 5 ana sistemin gerçek runtime, servis, app modules, registry, manifest, startup, menü, IPC, installer/updater, build ve CI bağımlılık grafını çıkar. 16 `module.json` dizini kaynak adayıdır, kurulu PC kanıtı değildir.
- **Çekirdek hiçbir sökülebilir eski modüle bağımlı olamaz.** Bağımlıysa `ARCHITECTURE_DEFECT` olarak düzelt. Mevcut tek Operator'a ait temel iletişim, görev yürütme, Studio build/run yeteneğini eski `PluginCatalog` olmadan çekirdek sahibi API/servis şeklinde refaktör et. Aynı QA Fabrikası'nı koru, ikincisini kurma.
- Tüm noncore modülleri kaynak, kurulum, çalıştırma, UI ve aktifleştirme yollarından tamamen ayır: yalnızca kapatmak veya saklamak `DONE` değil. Kod ve tarihsel kayıtları güvenli runtime dışı arşive koru; kullanıcı verisini hard-delete etme.
- Yeniden başlatılmış gerçek Windows ortamında `app/modules` **boş veya bulunmuyor** iken 5 çekirdek çalışabilmeli; Inventhor↔Operator güvenli bağlantı/ACK, orijinal Organizer handoff, Studio'da gerçek uygulama edit/build/run, aynı Fabrika'da gerçek FAIL→FIX→RETEST ve rollback tanıkla doğrulanmalı. Artık 16 modül sayısı veya 41 yetenek sayısı dağıtım koşulu olamaz.
- Her küçük geri alınabilir partide önce/sonra inventory, source/runtime dependency edge count, servis/menü/startup/list ve core smoke kanıtı. Sıfır noncore aktif modül ve sıfır zorunlu bağımlılık olmadan tamamlandı yazma.

**P0 Aşama 1 tamamlanma şartı:** `NATIVE_ACTIVE_NONCORE_MODULES=0`, `NATIVE_CORE_TO_NONCORE_DEPENDENCY_EDGES=0`, eski module updater/installer/UI/startup/servis kalıntısı `0`; beş çekirdek gerçek Studio/Operator/QA smoke `PASS`; kanonik Organizer checkpoint yazıldı ve yeniden okundu. GitHub source CI tek başına bu iddiaların hiçbirini ispatlamaz.

## P1 AŞAMA 2 — TEMİZ SİSTEMİ GERÇEK UYGULAMA FABRİKASI OLARAK BİTİR

- Kullanıcıdan fikir/konuşma → aynı Organizer task → INVENTHOR plan → gerçek tek Operator eylemi/ACK → Studio gerçek tasarım, düzenleme, ekrandan görme ve çalıştırma → aynı QA Fabrikası build/artifact kimliğiyle test → hata varsa Studio düzeltme ve aynı Fabrika tekrar test → kullanıcı yetkisi, sürüm, geri alma ve güvenli teslim.
- Önce **bir gerçek örnek uygulama** ile uçtan uca tamamla. Diğer eski modülleri hemen yeni uygulamaya dönüştürme. Gelecekte gerekiyorsa ayrı sıradan programlar olabilir; INVENTHOR içine plugin olarak geri gömme.

## P2 AŞAMA 3 — BULUTTA HESAP + OTOMATİK YENİ BİLGİSAYAR KURULUMU

**Hedef yalnızca zip/portable dosya değildir:** Kullanıcı bilgisayarını **formatladığında**, orijinal PC hiç yokken desteklenen bulut sağlayıcısından INVENTHOR paketini indirip kurabilsin; kendi hesabına güvenli giriş yapınca eski projeleri/Organizer'ın kendi hesabına ait verilerini seçerek geri yükleyip aynı çalışma düzenini yeniden oluşturabilsin. Yeni/başka bilgisayar, aynı kullanıcı restorasyonu ile farklı kullanıcıya satılan sıfır kurulum ayrı akıştır.

- Bulut sağlayıcısına kilitlenmeyen **veri/nesne depolama arayüzü**; ilk sürümde belirli, doğrulanmış desteklenen sağlayıcı(lar), genel S3-uyumlu veya benzer backendler ileride adaptörle desteklenebilir. "Herhangi bir bulut" sözü evrensel, test edilmemiş otomatik destek vaadi değildir. Mümkünse ücretsiz katmanlar; gereksiz ücretli servis zorunlu değil.
- İmzalı sürüm + checksum + uygun OS/CPU kontrolü; installer ve portable kullanıcı modu; varsayılan veri korumalı kurulum/onarım/güncelleme/rollback/uninstall; sistem hizmetleri için gerektiğinde UAC.
- Kullanıcıya ait Organizer görevleri, Studio projeleri, kullanıcı tercihleri, çalışma düzeni ve yetkili checkpoint'ler **sürümlenmiş, bütünlük kontrolü yapılmış ve şifrelenmiş hesabına bağlı yedekten** geri gelebilmeli; her yeni cihaza kendi `device_id` ve **yeni** pairing anahtarı üretilmeli, orijinal PC'nin makine secret'ları, oturum tokenları ve cihaz kimliği **klonlanmamalı**. Kullanıcı kendi şifresini/hesabını sağlayacak, cihaz izinleri yeniden alınacak.
- **Format test kabulü:** A bilgisayarında gerçek iş/proje/checkpoint oluştur, şifreli desteklenen bulut yedeğini doğrula; A bilgisayarı yok kabul edip temiz B bilgisayarında uygulamayı indir ve kur; **aynı kullanıcı hesabıyla** giriş yap; veri ve ayarları geri yükle, yeni cihazda Operator/Organizer/Studio ve aynı QA Fabrikası doğrulansın. Farklı hesaba ait kullanıcı verisi asla görünmesin; yeni kullanıcı için fresh izole sistem açılır.
- Sökülen eski modüller bir daha paket veya restore edilmiş bağımlılık olarak dönmemeli. Eski tarihsel modül kaynakları bulut kullanıcı veri yedeğine zorla taşınmamalı.

**Aşama 3 kabulü:** `CLOUD_ACCOUNT_RESTORE_ON_FRESH_PC=LIVE_VERIFIED`, `CROSS_ACCOUNT_DATA_ISOLATION=PASS`, `NO_COPIED_DEVICE_SECRETS=PASS`, `SIGNED_INSTALLER_AND_ROLLBACK=PASS`. Bunlar şu an **NOT_VERIFIED**.

## Yürütme / öncelik koruma

`NOW=P0_REMOVE_NONCORE_AND_ZERO_CORE_DEPS` → `THEN=P1_ONE_REAL_APP_FACTORY` → `AFTER=P2_CLOUD_LOGIN_RESTORE_ANY_NEW_SUPPORTED_PC`. P0 devam ederken P2 **yalnızca sözleşme/backlog** düzeyinde; büyük bulut implementasyonu yapılmaz. Daha önce portable özelliğinin `P0_CORE_ACCEPTANCE_REQUIREMENT` diye anılması **nihai ürün için vazgeçilmez şart** anlamındadır; **yürütme sırası P2'ye taşınmıştır**.

Kaynak kontrol raporu: `validation_reports/OPERATOR_OPTIONAL_MODULE_COUPLING_20261026.md`. Operator ilk gerçek refaktör: [PR #5](https://github.com/inventhor-cloud/inventhor-operator-core/pull/5), kaynak Windows testleri 166/166; eski plugin executor, 16-modül install betiği ve gerçek kurulu QA hâlâ açık. Asıl kullanıcı PC bağlantısı OFFLINE görüldü, yalnızca GitHub aynası güncellenebilir.

## Sonraki en küçük gerçek iş

Mevcut Operator PR #5'in `PluginCatalog` yürütücü bağımlılığını, güncel Codex/native Organizer sahibiyle çatışmadan gider; temel gerçek Studio build/test/run, yetkili OS eylemi ve güvenli iletişim modül klasörü boşken çalışsın. Sonra eski modül paketleme/servis/UI/installer kalıntılarını gerçek yedek ve rollback ile sök; QA regresyonunda kanıtla. **Bu görevden ayrı yeni uygulama, ekstra Factory, ek Organizer, plugin veya yeni bulut servisi üretme.**

## Gerçek P0 kaynak ilerlemesi — 28 Ekim 2026

**Operator [PR #5](https://github.com/inventhor-cloud/inventhor-operator-core/pull/5), halen TASLAK, kurulu sisteme birleştirilmedi.** OperatorWorker ile mevcut Inventhor/DirectBrain transport kaynakları geçici **process-scope** `INVENTHOR_OPERATOR_ROOT` değerini kabul ediyor; gerçek makine/USER kayıt defterine yazmadan izole bir çalışma alanında çalıştırılabiliyor. [Windows GitHub Actions #40778714440](https://github.com/inventhor-cloud/inventhor-operator-core/actions/runs/40778714440) **166/166 test PASS**. Ayrıca çekirdek servisi gerçek Windows CI prosesinde yeni, boş temp kök ile başlatıldı; **`app/modules` klasörü hiç mevcut değilken**, servis heartbeat'i `modules=0`, `STATUS` ve `SOFTWARE_WORKSPACE_CREATE` çekirdek yetenekleriyle doğrulandı. Checkpoint: `OPERATOR_CORE_EMPTY_PLUGIN_BOOT_SOURCE_SMOKE_PASS`.

**Neyi kanıtlamaz:** Kurulu kullanıcı bilgisayarında modüllerin sökülmesi; tüm çekirdek eylemlerinin yetkisiz eski executor modülleri olmadan kullanılabilmesi; INVENTHOR'a imzalı gerçek bağlantı; Organizer native lease; uygulama Studio build/run; tek Fabrika QA; gerçek yeniden başlatma ve cloud restore. Diğer eski executor pluginleri, legacy 16-module yayın betiği ve UI/installer temizliği **hala P0 kalan işler**. Bu source smoke kuruluma dönüştürülmemeli veya DONE sayılmamalı. Codex mevcut yerel dosyaları ve gerçek Organizer task/lease'i önce okumalı.
