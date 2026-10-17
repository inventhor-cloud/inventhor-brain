# INVENTHOR Main — Kaynak, Modül, Uygulama ve Güncelleme Depolama Sözleşmesi V1

**Durum: SOURCE_REFERENCE_ONLY / NOT DEPLOYED / NO FILES MOVED.** Mevcut INVENTHOR Main / Organizer'ın Artifact Registry **meta veri** alanını genişletir; ikinci Organizer, ikinci modül kataloğu, ikinci beyin veya bağımsız depolama servisi yaratmaz. Ana kayıt Main'dedir. GitHub yalnız sürümlü kaynak ve kod inceleme kanalıdır; Windows Operator yerelde paket doğrulama / staging / geri alma işleri yapar.

## Üç ayrı varlık

| Tür | Kanonik sorumluluk | Amaç |
| --- | --- | --- |
| Kod / Git geçmişi | Var olan GitHub proje depoları (`inventhor-cloud/inventhor-...`) | Kaynak, sürüm etiketleri, branch/PR, test tanımı ve küçük imzalı metadata; gerçek kullanıcı verisi değil |
| Paket ve arşiv dosyaları | Yetkili Windows Operator yerel artefakt alanı; **önerilen** hedef D: | Derlenmiş uygulama, modül, checksum, release, offline paket, rollback snapshot; boş yere repo şişirmez |
| Sistem kaydı | **Mevcut** INVENTHOR Main > Organizer / Artifact Registry | PROJECT_ID/MODULE_ID, sürüm, source commit, paket hash, kabul kapısı, kanıt, kurulu sürüm, test sonrası geri alma referansı |

Depo durumunu canlı uygulama gibi göstermeyin: gerçek D: diski yolu, içerikleri ve başarılı import henüz uzaktan doğrulanmadı. 2 TB D: sahibi tarafından önceden amaç olarak belirtilmiştir; klasörleri **kaynakta planlamak**, bilgisayarda oluşturmaya eşit değildir.

## Önerilen yerel fiziksel düzen (kurulumdan önce sürücü, izin ve boş alanı doğrula)

```text
D:\INVENTHOR\
  SOURCE\              # Kaynak çalışma kopyaları / Git worktrees
  BUILD_CACHE\         # Silinebilir ara derleme verileri
  ARTIFACTS\
    apps\              # PRODUCT_ID / VERSION / immutable files
    modules\           # MODULE_ID / VERSION / package + manifest
    source_snapshots\  # Kaynağın doğrulanabilir sürümlü yedeği
    manifests\         # content hash + release metadata
  RELEASES\             # QA/kabul sonrasında yayımlanan sabit paketler
  BACKUPS\
    originals\          # Eldeki orijinal çalışma/backup; elle onay olmadan değişmez
    verified\           # checksum doğrulanmış ayrı yedekler
    rollback\           # Güncelleme öncesi çalışan sürüm snapshot'ı
  EVIDENCE\             # build/test/integration/UI kabul kanıtı
  QUARANTINE\           # Belirsiz veya onaysız paket; çalıştırılmaz
  TEMP\                 # Yalnız süre/kanunlu temizlik
```

**Önemli:** Windows çalışma zamanı C: üzerinde kalmak zorundaysa Main/Operator'ın gerçek uygulama ve servis konumu otomatik değiştirilmez. D: burada büyük çalışma depolaması, paket/rollback arşivi içindir. Var olan Desktop/INVENTHOR ve gerçek D: içeriği önce salt okunur envanter + SHA-256 ile uzlaştırılır, sonra onaylı migration uygulanır; formatlama/silme/taşıma **bu kaynak sözleşmesiyle yapılmaz**.

## Katalog kuralları ve güncelleme disiplini

1. Var olan `module_catalog.json` modül kimlik/özellik yetkilisidir; her Artifact Registry girdisi bilinen PROJECT_ID ve MODULE_ID'ye bağlıdır. Yeni klasör/modül açılması gerekiyorsa önce mevcut kimliği kontrol et.
2. Her yayımlanabilir dosya için `artifact_id`, `project_id`, `module_id`, `version`, `kind`, `store`, `relative_path`, `sha256`, `channel`, `contains_secrets=false` gerekir. Bunlar gerçek dosyanın bağımsız kanıtı değildir.
3. Üç kayıt eşsiz tutulur: (project,module,kind,version), artifact_id, sha256; benzer ad/sürümle çifte kurulum engellenir. Sabit paketler yerinde değiştirilmez; yeni sürüm yeni pakettir.
4. Akış: SOURCE_CHANGE → BUILD → UNIT/INTEGRATION/UI/SECURITY CHECK → HASH → REVIEW → RELEASE_CANDIDATE → HOST-VERIFIED ACCEPTED RELEASE → STAGING → SNAPSHOT → INSTALL → HEALTH/UI ACCEPTANCE → ACTIVE. Başarısızsa doğrulanmış önceki sürüme kontrollü rollback; paket saklanır ve hata kanıtı Main'e döner.
5. Kullanıcıya gösterilen **güncelle** düğmesi yalnız gerçekten uygun, test edilmiş, imzalı/güvenilir, mevcut cihazla uyumlu ve Main Owner politikasıyla yetkili sürüm için etkin olur. GitHub commit/PR onayı, Windows'ta kuruldu demek değildir.
6. İndirilen binary ve modül paketleri için SHA-256 zorunlu, sağlayıcının kaynak ve imza/izin doğrulaması ayrıca gerekir. Gizli anahtar, token, aile sohbeti, çocuk öğrenim verisi ve kayıtlar **public veya private repo artefaktlarına bile açık ham dosya olarak** konmaz.
7. Backup en az iki doğrulanmış bağımsız kopya ve bir offline/çıkarılabilir hedef politikasıyla planlanmalı; **tek başına D: aynı bilgisayarda disk arızasına karşı yeterli yedek değildir**. Başarı ilanından önce restore testi gerekir.
8. Güncelleme küçük, geri alınabilir, bağımlılık-güvenli olmalı. Windows Service gibi kesintili işlemler UAC/owner onayı olmadan değiştirilmez. Terminal BS/BF ve onaylanmış eski iş yeniden oynatılmaz.

## Mevcut kod bağlantıları ve doğrulama sınırı

- `continuity/artifact_registry.source.json`: boş, dürüst başlangıç katalog kaydı; gerçek artefakt varmış gibi veri eklenmedi.
- `shared_organizer/artifacts.py`: mevcut Main/Organizer bağlamında salt-okunur metadata incelemesi. Kimlik, sürüm, özel yol ve SHA-256 durumunu kontrol eder; dosyaları açmaz ve doğrulamaz, hiçbir şeyi yüklemez veya silmez.
- Windows Operator'daki `windows/TRANSFER_MODULE.md`: mevcut FILE_DOWNLOAD ve ARTIFACT_STAGE kaynak tasarımı; gerçek PC'de kurulduğu/teslim edildiği ayrıca test edilmeli.
- `release_packages/release_package_policy.md`: mevcut “kısa değişiklik günlüğü + tek güncelle butonu” hedefi sürüyor; bu kurallarla uyumlu hale getirilmeli.
- Main'in gerçek Artifact Registry uygulaması ve bilgisayardaki kaynakların salt-okunur envanteri kurulmadan/okunmadan kaynak kataloğu Main'in canlı kaydının yerine geçemez.

## Gerekli PC kabul kapıları

- Gerçek sürücü harfi, kapasite, dosya sistemi, NTFS izinleri, kritik masaüstü veri dizini, yedek listesi salt okunur tespit.
- Dosya hash/size manifesti ve proje/modül eşleme; duplicated files raporlanır fakat **otomatik silinmez**.
- Bir küçük test modülünde eski sürüm→yeni sürüm, hizmet yeniden başlangıcı, kanıt gönderimi, geri dönüş testi.
- Silmeden ve taşımadan önce kullanıcı erişimi/D: backup stratejisi; Owner izni ve doğrulanmış backup.
- UI'daki Katalog: Projeler / Uygulamalar / Modüller / Güncellemeler / Yedekler / Kanıtlar; gerçek çalışır sürümler yalnız host tarafından doğrulandığında ACTIVE gösterilir.

Bu bir mimari + test edilebilir kaynak sözleşmesidir; gerçek dosya taşıma, kurulum ve canlı INVENTHOR arşivi henüz **yapılmadı**.

## Üretilecek modül standardı — tam entegrasyon

**Owner kararı (2026-10-17):** Kullanıcı kendi veya üçüncü taraf modüllerini kurma özgürlüğüne sahiptir. Modüller keyfi marka/önek sınırlamasına değil, **ortak mimari ve Quality Factory kabulüne** tabidir. Bir modül sadece DLL olarak kurulunca veya bir fonksiyonu çalışınca **%100 entegre** sayılamaz.

Var olan Operator kaynağı `inventhor-cloud/inventhor-operator-core:windows/MODULE_INTEGRATION_STANDARD_V1.md` sözleşmesine göre yeni modüllerde `module.json` + `integration.json` birlikte kontrol edilir: gerçek PROJECT_ID/MODULE_ID, sürüm, host API uyumu, bütün capabilities/actions, giriş/çıkış/hata protokolü, Main yetki politikası, bağımlılıklar, health check ve rollback. **Eksik fonksiyon, dependency, yetki veya duplicate capability** kabulü engeller; yanlış modüle sessiz yönlendirme yapılmaz.

**Main / Organizer sorumluluğu:** Proje/kimlik, izin-scope, dependency/değişiklik onayı, sürüm kabulü ve merkezi Artifact Registry metadata. **Operator sorumluluğu:** Modül yükleme, gerçek handler/capability eşleşmesi, hatasız yürütme ve evidence. **Quality Factory sorumluluğu:** Bütün fonksiyonların logic/UI/e2e testleri, kalite metrikleri, rollback ve son `QUALITY_ACCEPTED_FULLY_INTEGRATED` durumu. Sadece Main runtime tarafından doğrulanmış sonuçlar kullanıcıya `ACTIVE` olarak sunulabilir.

**Kaynak durumu:** Mevcut Operator'un eski yerleşik modülleri henüz yeni sözleşmeye otomatik geçirilmedi; yeni modül kaynak denetleyicisi gerçekte kurulum veya uçtan uca test yapmaz. Eski modüller izinsiz silinmez, kopyalanmaz; geçişte birer birer test edilip uzlaştırılır. Çalışır modül garantisi yalnız Main bağlantısı + cihazda Quality Factory kabul kanıtıyla sağlanabilir.

### 2026-10-17 Modül işlevlerinin gerçek yetki eşleşmesi — kaynak denetim notu

Kod denetiminde yeni modül sözleşmesinin yanında var olan bazı eski modüllerin **komut adı ile capability adını birebir eşleştirmediği** görüldü. Operator kaynak dalında `ControlModule`, `GitModule`, `AdbModule`, `ProcessControlModule`, `ServiceControlModule`, `PerformanceModule` ve `TelemetryModule` için komut/yetki denetimleri ekleniyor. Bir modülün var olması veya DLL yüklenmesi bunların Main üzerinden izinli ve doğru çalıştığını **kanıtlamaz**.

Main tarafı özellikle her `capability+action` kombinasyonunu ilgili biricik modüle bağlamalı, etkin uygulama izin/scope/lease kontrolü ve host tarafından yürütülmüş kalite kanıtı olmadan `ACTIVE/FULLY_INTEGRATED` etiketi vermemeli. Sistem sahibi FULL izinle bile yanlış capability altında başka eylem çalıştırmaz; yerel sahip onayı gereken kalıcı silme ve erişim seviyesi değiştirme işlemleri yalnız doğrulanmış yerel akıştan yapılır. Kaynak kodda gerçekleştirilen korumalar gerçek cihazdaki kurulu sürüm ve kullanıcının verileri için kurulum kanıtı değildir.
