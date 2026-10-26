# SAHİP SON TALİMATI — GEREKSİZ MODÜLLERİN TAMAMEN SÖKÜLMESİ

**Tarih:** 26 Ekim 2026 — önceki hedeflerden daha güncel sahip talimatı.
**Durum:** `OWNER_INTENT_RECORDED_IN_GITHUB_MIRROR`; Windows'taki kanonik Organizer'da uygulanıp tamamlandığı **DOĞRULANMADI**.
**Önemli:** Bu belge mevcut göreve verilen talimatın bir referansıdır; **yeni Organizer, yeni görev, yeni yazma yetkisi, yerel bilgisayarda söküm, kurulum veya QA kanıtı oluşturmaz**.

## 1. SON HEDEF — baştan başlayan her yeni yapay zekâ buradan başlar

Yalnızca **BEŞ** tekil, birbirine bağlı işlevsel sistem:

1. **INVENTHOR:** karar, plan, kullanıcıyla gerçek metin/ses iletişimi ve iş akışı yönetimi.
2. **OPERATOR:** INVENTHOR'un yetkili işlemlerini gerçekleştiren tek uygulayıcı; doğrulanmış sonuç/ACK, durdurma/geri alma.
3. **ORGANIZER:** aynı mevcut kanonik görev, proje, fikir, checkpoint, lease ve delil defteri. INVENTHOR içinden görünse de ikinci kayıt sistemi kurulmaz.
4. **STUDIO_DESIGN:** gerçek uygulama tasarımı, düzenleme, birebir canlı etkileşimli görüntüleme, derleme/çalıştırma ve değişiklik.
5. **QA_FACTORY:** **tek mevcut Kalite Fabrikası (QA ile aynı şey)**; derleme, gerçek davranış/UI/güvenlik/regresyon, hata kanıtı, Studio'da düzeltme, aynı Fabrika'da yeni revizyonla tekrar test.

**Çalışma hattı:** kullanıcı fikri → Organizer mevcut gerçek görev → INVENTHOR plan → Operator uygular → Studio gerçek uygulamayı üretir/gösterir/çalıştırır → aynı QA Fabrikası tam build/hash'i test eder → hata varsa Studio+Operator düzeltir → aynı Fabrika yeni sürümü tekrar test eder → geri alma ve ayrı gerekli onaylardan sonra güncelleme/teslim.

## 2. MODÜL SÖKÜMÜNÜN KESİN ANLAMI

**Sahip kararı:** Beş sistem dışındaki **bütün eski bağımsız ürün/özellik modülleri artık INVENTHOR içinde varmış gibi davranmayacak**. Yalnızca beklemeye alma, yan menüde gizleme veya servis durdurma yeterli **DEĞİL**. Tam sökümün kabulü, beş çekirdeğin canlı çalışmasına bu eski modül sistemlerinden hiçbir zorunlu bağımlılık, kayıt veya kırık bağlantı kalmamasıdır.

Her gerçek **non-core eski modül** için native envanter ve ters-bağımlılık haritası alınacak; ardından kontrollü şekilde:
- Modülün canlı kayıt/katalog/servis-keşif/startup/autoload/uygulama menüsü/ikon/komut yönlendirmesi/UI sekmesi/özellik manifesti ve DI referansları kaldırılacak.
- Eklenti DLL/paketleri ve yalnızca o modüle ait servisler, Windows Scheduled Tasks, arka plan işçileri, IPC/transport abonelikleri, konfigürasyon kancaları ve installer/update hedefleri kaldırılacak; kendiliğinden yeniden yüklenmeyecek.
- Beş çekirdeğin kodu, servisleri, yetkileri, build/import/SDK/packaging, kurulum bağımlılıkları, konfigürasyonu, derleme/test/CI ve QA süreçlerindeki eski modül referansları **sıfırlanacak**. Bir referans hâlâ zorunluysa ya kanıtlı olarak çekirdeğin içine **iç yetenek** olarak taşınacak ya da çekirdek işlevi bozulmadan daha temiz bir bağımsız çekirdek API ile değiştirilecek; eski plugin'e gizli bağımlılık **KALMAYACAK**.
- Modül kullanıcının aktardığı verileri içeriyorsa yanlışlıkla silmeyeceğiz; kullanıcı verisi ve yetki/kanıt kayıtları ayrı ele alınacak. Aktif runtime'dan çıkarılmış modülün **güvenli geri alma yedeği ve tarihsel kanıtı**, canlı çalışma klasörlerinden/uygulama menüsünden ayrı korumalı arşivde kalabilir. "**Hiç yapılmamış gibi**" ifadesi **canlı işlev, görünüm ve bağımlılık haritasına** uygulanır; gerçek geçmiş kayıtlarını sahteleştirme talimatı değildir.
- Kaldırılan modülü yeni bağımsız program olarak geliştirmek, onun yerine benzerini kurmak veya paralel modül/Studio/Organizer/Factory oluşturmak yasak aktif kapsam.

**Çekirdeğin zorunlu iç altyapısını isim yüzünden silme:** Operator'un gerçek dosya/uygulama değişikliği, yetkili komut, Organizer handoff, bildirim, QA build/test, güvenli iletişim ve geri alma için gerekli alt yetenekler korunur; eski `windows.*` veya `transport.*` modül kimliği bunlara hizmet ediyorsa yetenek **mevcut beş sistemin iç uygulamasına taşınır**, sonra eski **modül kaydı** sökülür. Böylelikle canlı beşli sistem bozulmaz ve eski plugin'in zorunlu dependency grafı sıfıra iner. Bu taşıma yeni alt ürün anlamına gelmez.

### Kaynaktan görünen adaylar — KURULU olduğu kanıtlanmadı

`inventhor-operator-core` kaynak revizyonu `37ff1010aa5f55240a4324eafe5b3d5d45270e49` içinde **16 ayrı module.json dizini** görüldü: `windows.adb`, `windows.cleanup`, `windows.continuity-guard`, `windows.control`, `windows.desktop-control`, `windows.filesystem`, `windows.git`, `windows.performance`, `windows.powershell`, `windows.process-control`, `windows.service-control`, `windows.software-factory`, `windows.telemetry`, `windows.transfer`, `transport.direct-brain`, `transport.inventhor`.

Bunlar **"16 modülün hepsini kör sil" listesi DEĞİLDİR**. Kaynak manifesti kurulu Windows kanıtı değildir. Özellikle `windows.software-factory` gerçek QA/Studio build işlevinin, `transport.*` ve dosya/işlem/hizmet yetenekleri ise zorunlu Operator iç iletişiminin parçası olabilir. Bu durumlarda eski modül kabuğu kaldırılırken gerekli fonksiyon **beşli çekirdek içinde** güvenli biçimde sürdürülür. Yerelde mevcut başka tüm eski modüller de taranır; bu kaynak listesi eksiksiz kabul edilmez.

## 3. SIFIRLANAN AI / CODEX / OPERATOR İÇİN EMİR SIRASI

**A — YENİDEN BAŞLAMA:** Önce `system_constitution/ACTIVE_PRODUCT_ARCHITECTURE_20261026.json` ve bu talimatı oku; eski "dört çekirdek", "modülleri tek tek programa dönüştür" veya Eylül/Ekim eski iş hedeflerini aktif emir olarak kullanma.

**B — TEK KANONİK DEFTER:** Mevcut Windows **Organizer** üzerinde `operator_work_handoff(taskId)` veya kurulu Organizer Tool'un **exact task** handoff'u ile güncel `TASK_ID`, `PROJECT_ID`, revizyon, worker/lease, gerçek checkpoint, tamamlanan/kalan işler, kanıtlar, blokajlar ve dependency durumlarını oku. Başka worker sahipliyse lease'i çalma; yeni task/proje oluşturma; sonlandırılmış işi yeniden oynatma. İzin varsa **aynı gerçek görevin** hedef/kabul kriterlerini bu güncel talimata göre uzlaştır.

**C — OKU / ENVANTER:** Yerel disk, kurulu paketler/DLL, manifest/registry, Main/Operator/Organizer/Studio/QA host, servisler, schedule, startup, menü ve ekranlar, git bağımlılıkları, güncelleme/kurulum, CI testleri ve runtime IPC bağlantıları üzerinde **tam read-only envanter** çıkar. Her kayıt: gerçek module ID/kurulu sürüm/dosya yolu, çekirdeğin ona ihtiyacı, ters-bağımlılık, current owner, silinirse etkilenecek işlev, kaynak yedeği ve rollback. Kaynaktaki eski 16 modu yalnızca aday say.

**D — SINIFLANDIR:** `CORE_SYSTEM` (korunacak 5), `CORE_REQUIRED_INTERNAL_CAPABILITY` (beş sistem içine alınıp eski plugin kimliği çözülecek), `NONCORE_REMOVE` (tam canlı söküm), `UNRESOLVED_DEPENDENCY` (blokaj; asla kör söküm). Codex'in mevcut 17-file PR#3 çakışması ve yerelde kaldırılmış `Cleanup` bilgisi varsa **güncel yerel gözlemle doğrula**, deleted Cleanup'ı restore etme ve PR#3'e kör merge yapma.

**E — GERÇEK SÖKÜM / KONTROLLÜ GERİ ALMA:** Test edilen native owner/lease + yedek ve planla, servis/modül değişikliklerini **küçük, geri alınabilir partiler** halinde yap. Her partiden sonra beş sistem smoke + gerçek Studio edit→Operator sonuç/ACK→Fabrika test preflight kontrolü. Windows onay isteyen işlemlerde UAC/OS güvenlik kapısını atlama. **Kullanıcıya ait veriler/geri alınamaz kalıcı arşiv silmeleri için ayrı somut doğrulama/izin olmadan hard-delete yapma.**

**F — SIFIR BAĞIMLILIK TESTİ:** Beş sistemin aktif servis/registries/UI/shortcut/IPC/dependency grafından kaldırılan modüle giden **0 aktif referans** olmalı. Reboot/startup sonrası yeniden yüklenme olmamalı; orphan service/job/menu/link/installer/update/CI dependency kalmamalı. Her kaldırılan modül için önce/sonra kurulu paket envanteri + imzalı hash + dependency grep/dynamic binding + açılış/çalışma testi + QA regressions + rollback evidence kaydet. Eksik kanıt varsa `BLOCKED` yaz, `DONE` yazma.

**G — ASIL HEDEFTE DEVAM:** Tam söküm kanıtlandıktan sonra veya bağımsız güvenli iş hattında, tek üretim zincirini bitir: INVENTHOR plan → Organizer tek task → Operator gerçek eylem → Design Studio gerçek uygulama → AYNI QA Fabrikası fail→fix→retest. Ses/metin/fare müdahalesi, Stop/Undo ve güncelleme teslimi native olarak test edilir. Yeni yan modül yapımı YOK.

**H — GERÇEK CHECKPOINT:** Var olan Organizer görevinde `COMPLETED`, `REMAINING`, `BLOCKERS`, `EVIDENCE`, `NEXT_SMALLEST_FINITE_STEP`, gerçek native revizyon ve lease/handoff durumunu kaydet. Bir sonraki AI bunu **okuyarak** devam eder; bu GitHub metnini canlı durum sanmaz.

## 4. TAMAMLANDI SAYILMASI İÇİN

- `ACTIVE_ARCHITECTURE=INVENTHOR,OPERATOR,ORGANIZER,STUDIO_DESIGN,QA_FACTORY` (**QA=Fabrika**).
- `ACTIVE_NONCORE_MODULE_COUNT=0` native doğrulanmış.
- `ACTIVE_NONCORE_DEPENDENCY_EDGE_COUNT=0` native doğrulanmış.
- `ORPHAN_NONCORE_SERVICE/STARTUP/MENU/JOB/UPDATER_COUNT=0` native doğrulanmış.
- `REQUIRED_CORE_CAPABILITIES_FUNCTIONAL=TRUE` (zaten çekirdeğin içine taşınmış gerekiyorsa).
- `FIVE_SYSTEM_SMOKE_AND_REAL_STUDIO_OPERATOR_FACTORY_QA=PASS` bağımsız gerçek kurulu tanık/kanıtlı.
- `LIVE_ORGANIZER_CHECKPOINT=WRITTEN_AND_READ_BACK` gerçek lease ile.
- `STANDALONE_NEW_PROGRAM_OR_MODULAR_FEATURE_STARTED=FALSE`.

**Bugünkü doğrulanmış durum:** GitHub'da sahip talimatı kaynak referansı kaydedilebilir, ancak INVENTHOR PC Desktop Commander bağlantısı OFFLINE. Buradan `ACTIVE_NONCORE_MODULE_COUNT=0` veya native Organizer checkpoint'i `DONE` gösterme; gerçek söküm henüz bu sohbet üzerinden yapılmadı.

## Sahip son açıklama (26 Ekim 2026): programlar ayrı olacak

Eski gereksiz modüller INVENTHOR'un aktif çalışmasından **şimdi tamamen kaldırılacak**. İleride uygun görülen işlevler **ayrı normal programlar** şeklinde yapılabilir; şimdi bunları üretmeye başlamıyoruz.

Bu bağımsız programların INVENTHOR içerisine modül olarak eklenmesi gerekli değildir. INVENTHOR, **tek mevcut Operator** aracılığıyla, işletim sisteminin ve uygulamaların izin verdiği denetlenebilir bağlantılar üzerinden cihazlarda ve programlarda işlem yapabilecek. Bu hedef gerçek erişimin kurulduğu anlamına gelmez; uygulama desteği, kullanıcının verdiği izinler, gerçek eylem sonucu ve geri alma sınırları korunacak.

Beş sistem (INVENTHOR, OPERATOR, ORGANIZER, STUDIO_DESIGN, QA_FACTORY) değişmez. Eski modülün canlı sisteme bağımlılığı sıfır olmalı, geçmiş kaynaklar ve kullanıcı verileri güvenli biçimde korunmalıdır. Bu açıklama önceki bağımsız programları **hemen geliştirme** yönündeki görevlerin yerini alır. Kaynak sözleşmesi 1.2.0, yerel Organizer güncellemesi ve gerçek söküm henüz doğrulanmadı.
