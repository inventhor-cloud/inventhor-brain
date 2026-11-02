# Operator: İsteğe bağlı modüllere çekirdek bağımlılığı — doğrulanan kaynak mimari kusuru

**Sahip kuralı:** Beş çekirdek (INVENTHOR, OPERATOR, ORGANIZER, STUDIO_DESIGN, QA_FACTORY) tüm zorunlu işler ve iletişim için tarihsel opsiyonel modüllerden **bağımsız** olmalıdır. Bir modülün çıkarılması temel çekirdeği bozuyorsa bu **mimari kusurdur**; eski modülü çekirdeğin içinde zorunlu tutmak çözüm değildir.

**İnceleme kaynağı:** `inventhor-cloud/inventhor-operator-core`, taslak Operator PR #3, SHA `37ff1010aa5f55240a4324eafe5b3d5d45270e49`. Bu yalnızca GitHub kaynak revizyonudur. Yerel Codex dosyaları ve bilgisayarın kurulu sürümü aynı olmayabilir; bunlar yeniden doğrulanmadan native değiştirilmez.

## Somut kaynak bulguları

| Yer | Kaynakta görülen davranış | Etki |
|---|---|---|
| `windows/src/Inventhor.Operator.Service/OperatorWorker.cs` | `pluginCatalog.Load(modulesRoot)`, ardından yürütücüler `p.Executor` ve iletişim kanalları `p.Transport` üzerinden geliyor | Operatör servisinin iş yürütme ve Inventhor'a erişim yolu eski plugin kataloglarına çalışma zamanında bağlanmış |
| `windows/src/Inventhor.Operator.Service/Program.cs` | `AddSingleton<PluginCatalog>()` | Plugin keşfi ana Windows hizmetine kaydedilmiş |
| `windows/src/Inventhor.Operator.Core/TaskEngine.cs` | Yürütücülerden eşleşme yoksa `CAPABILITY_UNAVAILABLE` | Modüller kaldırılırken temel eylemler sağlayıcı kalmayabilir; 'servis çalışıyor' tek başına yeterli değil |
| `windows/bootstrap/Build-Deploy-V2_1.ps1` | 16 modül/transport projesini derleyip paketliyor; `modules.Count -lt 16` ve `capabilities.Count -lt 41` ile kurulum kabulünü engelliyor | Eski modülleri kaldırmak yanlışlıkla kurulumun başarısız olmasına yol açar |
| `windows/src/Inventhor.Operator.Desktop/MainWindow.Modules.cs` | Modül merkezi ve `operator:modules` rotası korunuyor | Görünümde eski modül mimarisine bağlı ekranlar kalır |

**Yorum:** Kaynakta çekirdek–isteğe bağlı modül bağının bulunduğu doğrulandı. Her modülün gerçek Windows makinesinde kurulu olduğunu veya zaten sökülmüş olduğunu iddia etmiyoruz. `PluginCatalog` ve kaynak modüllerinin varlığı tek başına güvenlik açığı anlamına gelmez; sorun **zorunlu çekirdek işlevinin yalnızca eski eklenti kanalı üzerinden sağlanmasıdır**.

## Sıfırlanan AI/Codex için düzeltme sırası (yeni görev açma!)

1. Mevcut **kanonik Organizer exact TASK_ID/PROJECT_ID/lease/owner/revision** ile yerel Codex çalışma ağacını oku. PR #3 ve eski `Cleanup` kaynağına ilişkin bildirilen çakışmaları yerel 3-way diff ve gerçek envanterle doğrula. Başka çalışanın aktif işinin üzerine yazma.
2. Beş çekirdeğin sahip olduğu **yerleşik ve açık API/servis sınırlarını** tanımla: Operator temel yetkili görev yürütme, Main/Inventhor'a güvenli bağlantı, yerel Organizer'dan handoff, Studio build/run, mevcut QA. Bu işlevler eski takılabilir `module.json`/DLL kataloglarından **bağımsız** uygulanmalı. Mevcut kod yeniden kullanılacaksa **modül kimliğine/runtime loader'a bağımlı olmadan** mevcut çekirdek servis içine refaktör edilmelidir. Yeni alt ürün veya ikinci Operator yaratma.
3. Önce kontrollü testte **boş legacy module klasörüyle** Operator başlasın; Inventhor ile doğrulanmış bağlantı, doğru izinlerle en az bir gerçek eylem/ACK, Organizer exact handoff, Studio tasarım/build/gerçek çalıştırma ve aynı QA Fabrikası fail→fix→retest akışı çalışsın. Mock/source CI buna eşit değildir.
4. Çekirdek işlevleri bağımsızlaştıktan sonra eski `PluginCatalog` runtime bağımlılığını, 16-module derleme adımlarını/sayı eşiklerini, legacy UI menülerini, eski modul service/startup/config/installer/update/CI referanslarını güvenli, geri alınabilir biçimde sök.
5. Hem kaynak hem native envanterde eski noncore modül ID'lerine **sıfır zorunlu dependency edge**, reboot sonrası sıfır yükleme, yetkili QA smoke ve rollback kanıtı olmadan `DONE` yazma. Kişisel verileri/tek geri alma kopyasını kör silme.
6. Mevcut Organizer görevine gerçek `COMPLETED / REMAINING / BLOCKERS / EVIDENCE / NEXT` checkpoint'ini kaydet; GitHub aynası native sonucu kanıtlamaz.

**Kaynak denetim aracı:** `tools/audit_operator_core_modularity.py <operator_checkout>`. Yalnızca okur, bir JSON raporu üretir; mimari bağımlılık işaretleri varsa sıfır olmayan çıkış kodu döndürür. Testleri `tests/test_audit_operator_core_modularity.py` içindedir. Bu araç **tam semantik bağımlılık analizi değil**, yerel kurulu sistem denetimi hiç değildir.

**Geçerli durum:** `SOURCE_ARCHITECTURE_DEFECT_CONFIRMED` (incelenen PR #3 SHA için); `NATIVE_OPERATOR_DEPENDENCY_STATUS=UNVERIFIED`; `REAL_MODULE_DETACHMENT=UNVERIFIED`; `EMPTY_PLUGIN_NATIVE_CORE_BOOT=NOT_VERIFIED`.

## 26 Ekim 2026 — Gerçek kaynak refaktör ilerlemesi

**Operator taslak PR #5:** https://github.com/inventhor-cloud/inventhor-operator-core/pull/5

Ayrı dal `brain/core-transport-without-legacy-plugins-20261026`, önceki Operator PR #3 kaynak HEAD'i temel alınarak açıldı; Codex'in mevcut yerel dosyaları, başka çalışanın native Organizer lease'i veya kurulu PC **değiştirilmedi**. PR #5 **taslak ve birleştirilmedi**.

Bu kod değişiklikleri artık mevcut:
- `Operator.Service` proje referansı, eski `Inventhor.Transport.Inventhor` ve `Inventhor.Transport.DirectBrain` iletişim kodlarını **doğrudan derlenmiş çekirdek servis bağımlılığı** olarak içeriyor. `CoreTransportFactory` ikisini `module.json` olmadan oluşturuyor ve başlatıyor.
- `PluginCatalog.Load(..., includeTransports: false)`, iki iletişim kanalının eski `transport.*` eklentisi olarak tekrar yüklenmesini önlüyor.
- `CoreStatusExecutor` hiçbir eski modül kurulu olmadan `STATUS/READ_CORE_STATUS` komutuna, izin kontrolü altında salt-okunur ve hiçbir gerçek QA/bağlantı kanıtı iddiası taşımayan yanıt verebiliyor.
- Windows PR CI artık derlenmiş servis paketinin iki iletişim DLL'sini içerdiğini ve içinde eski `modules` klasörü oluşturmadığını doğruluyor.

**Doğrulanmış kaynak kanıtı:** [Operator Windows kaynak CI #40404820824](https://github.com/inventhor-cloud/inventhor-operator-core/actions/runs/40404820824), **150/150 test PASS**, Windows Operator servisi kaynak publish PASS, WPF masaüstü derleme PASS, Windows read-only predeploy/source drift/compare regresyonları PASS.

**Açık ve hâlâ gerçek eksikler:** Eski isteğe bağlı *executor* eklentileri geçici olarak kalıyor; `OperatorWorker` onları `PluginCatalog` ile keşfediyor. Eski 16-modül deployment betiği, `config/modules` taşıma gereksinimi, Module Center/registry/startup izleri, gerçek Studio edit/build/run ve Fabrika QA döngüsü tamamlanmış değil. Kaynak çekirdek STATUS sonucu yetkili bir gerçek program değişikliğiyle karıştırılamaz. Yerel Organizer son görev/lease, imzalı bağlanma ACK, gerçek modülsüz Windows kurulum testi ve QA rollback **DOĞRULANMADI**.

**Bir sonraki mevcut native görev alt adımı:** Codex'in güncel Organizer lease'i ve kaynak diff'i doğrulaması ardından PR #5'teki modül-bağımsız çekirdek haberleşme kodunu kontrollü biçimde incelemesi; gerçek uygulama oluşturma/run/QA işlevlerini tek Operator çekirdeğine taşıması; eski script/menü/dizin/servis bağlantılarını geri alınabilir etaplarda sıfırlaması; modül klasörü boşken gerçek beşli sistem testi ve aynı Fabrika FAIL→FIX→RETEST onayı alması. Kör PR merge veya Cleanup yeniden kurma yok.
