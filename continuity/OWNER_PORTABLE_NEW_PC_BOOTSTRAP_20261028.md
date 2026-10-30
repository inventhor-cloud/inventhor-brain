# INVENTHOR — BAŞKA BİLGİSAYARA TAŞINABİLİRLİK VE OTOMATİK KURULUM

**Sahip kesin isteği: 28 Ekim 2026.** Beş sistemli INVENTHOR yalnızca geliştirildiği PC'de çalışamaz; yeni bir Windows bilgisayara kopyalanabilir ve güvenli biçimde otomatik kurulabilir olmalıdır. Bu yetenek aynı beş çekirdeğin **P0 kabul kriteridir**, yeni modül, alt ürün, ikinci Organizer/Operator veya yeni Fabrika değildir.

**Mevcut gerçek durum:** GitHub'da Operator için Windows kurulum betikleri vardır ama temiz bilgisayarda beşli sisteme yönelik **imzalı, tek paketli, otomatik kurulum ve portable açılış doğrulanmamıştır**. `Build-Deploy-V2_1.ps1` Windows admin + yerel .NET SDK + 16 eski modül gerektiriyor; bu hâli yeni PC'ye yönelik nihai kullanıcı kurulum betiği olamaz. `Pair-Inventhor.ps1` yerel anahtarı konsola basar; sıfırdan müşteri/cihaz kurulumunda güvenli pairing bu eski yöntemden farklı olacak. Mevcut PR #5 kaynak derlemesi gerçek kurulum/portable kabulü değildir.

## İki ayrı ama ortak çekirdekli kullanım modu

1. **PORTABLE_USER_MODE:** Tek dizin/USB/yerel kopya olarak taşınabilecek, desteklenen kullanıcı düzeyi INVENTHOR arayüzü ve kullanıcı düzeyi Operator işlevlerini çalıştırabilecek bir sürüm. Yönetici hakkı, servis sürücüsü, erişilebilirlik izinleri veya Windows hizmeti isteyen eylemler kullanılabilir değilse açıkça `NEEDS_INSTALL_OR_PERMISSION` dene. Portable demek sınırsız sistem denetimi değildir.
2. **ONE_CLICK_LOCAL_INSTALL:** Yeni desteklenen Windows PC üzerinde bir paket veya doğrulanmış indirici başlatılır; işletim sistemi/mimari/özellikler/sürüm/boş alan doğrulanır, yayın imzası ve her dosya hash'i kontrol edilir, gerekli Windows UAC onayı istenir, yalnızca mevcut 5 çekirdek kurulur, veri/konfig/kimlik ayrılır, işletim sistemiyle gerekli servis bağlantıları kurulur, eşleştirme yapılır ve gerçek kabul testleri çalışır. Kurulum/sürüm yükseltme/onarım/geri alma/veriyi koruyan kaldırma ayrı kanıtlanır.

**Portatif paket, otomatik kurulumun kendisi değildir:** İmzasız ZIP, `dotnet publish` veya çalışan build/test sonucu yalnızca kaynak/artefakt önkontrolüdür; clean-PC acceptance sağlamaz. Windows WPF ve Windows Services kısıtları nedeniyle ilk tam hedef Windows; başka işletim sistemleri destek kapsamına sonradan alınır ve kanıtsız ilan edilmez.

## Yeni cihaz ve veri izolasyonu zorunluluğu

- `app/` salt okunur sürümlenmiş program; `data/`, `config/`, `logs/` ve `security/` yeni cihaza **ayrı** hazırlanır. Eski PC'den mutlak yol/hesap adı/registry/state/kullanıcı profili **gömülmez**.
- Yeni cihazın kendi benzersiz ve güvenli `device_id` ve bağlantı anahtarları üretilir; mevcut PC'nin pairing key'i, kullanıcı gizli bilgileri, Organizer olayları, proje dosyaları, hesap token'ları ve cloud credential'ları yeni kişiye **asla kopyalanmaz**.
- Kullanıcının mevcut projelerini taşıma **seçmeli**, bütünlük/şema sürümü kontrolünden ve mahremiyet onayından sonra gerçekleşir. Kurulumda eski Organizer'ın ham verisi otomatik yeniden yayınlanmaz. Aynı cihazın restore/rollback'i ile yeni kişiye fresh install farklı işlemlerdir.
- Yeni kullanıcının kendi cloud hesabını bağlaması gerekiyorsa güvenli giriş/yetki akışı gerekir; şifre, token, cihaz secret'ı GitHub'a veya debug loguna yazılmaz. Salt kaynak repoyu klonlamak erişim yetkisi veya kimlik kopyalama anlamına gelmez.
- Opsiyonel eski modüller kuruluma girmez; **beş çekirdeğin sıfır legacy dependency** hedefi portable paket için de geçerlidir.

## Tek kabul dizisi

`SIGNED_RELEASE_PACKAGE → FRESH_SUPPORTED_WINDOWS_VM → VERIFIED_ARCHITECTURE_AND_HASH → PORTABLE_USER_MODE_SMOKE → USER_APPROVED_ONE_CLICK_INSTALL → FRESH_ORGANIZER_AND_PAIRING → INVENTHOR_OPERATOR_AUTHENTICATED_ACK → STUDIO_REAL_EDIT/BUILD/RUN → SAME_QA_FACTORY_REAL_FAIL/FIX/RETEST → RESTART_SMOKE → SAFE_ROLLBACK → DATA_PRESERVING_UNINSTALL`

Bağımsız iki kurulum koşusu: (a) temiz sistemde sıfırdan kullanıcı, (b) farklı Windows kullanıcı profili/yolu/cihaz kimliği. Eski geliştirici PC'si, developer `.NET SDK` veya 16 modül varlığı kurulumun gizli ön koşulu olmayacak. Self-contained paket veya doğrulanmış çalışma zamanı bootstrap seçilip test edilmeden `NO_DOTNET_PREINSTALLED` durumu kabul edilmiş sayılmaz. Kurulum onayı gereken eylemler otomatik güvenlik atlaması yapmaz.

## Reset AI/Codex için uygulama ve durum sınırı

Önce **mevcut** native Organizer `TASK_ID/PROJECT_ID/revision/lease` ve kaynak diff; yeni paralel task/queue yok. `system_constitution/ACTIVE_PRODUCT_ARCHITECTURE_20261026.json` içinde `portable_new_computer_installation` P0 kuralını oku; mevcut Operator PR #5'in compiled transport ve modülsüz Studio workspace kaynaklarını kullan. Sökülebilir modülleri çekirdek bağımlılığından ayırma ve portable packaging birbirine bağlı kabul aşamalarıdır; eski 16 modül paketleyen script'i bitmiş portable installer sayma.

**Bu kaydın yazılması = portable ürünün tamamlandığı anlamına GELMEZ.** Tek gerçek durum: `SOURCE_REQUIREMENT_RECORDED`, `FRESH_PC_PORTABLE_RUN=NOT_VERIFIED`, `CLEAN_PC_AUTO_INSTALL=NOT_VERIFIED`, `SIGNED_RELEASE=NOT_VERIFIED`, `NATIVE_ORGANIZER_SYNC=NOT_VERIFIED`.
