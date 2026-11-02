# INVENTHOR Beyin bağlantısı ve yalın çekirdek — doğrulanmış kaynak incelemesi
**Denetim tarihi:** 2026-11-02. **Gözlem türü:** Bağlı GitHub depoları ve PR dalları. **Kanonik çalışma durumu değildir.** Bu rapor kurulu PC'de işlem, native Organizer task/lease devralma, install, imza veya Fabrika QA başlatmaz.

## Kısa hüküm

**TAM BAĞLI / TAM TEMİZ: DOĞRULANMADI.** GitHub kaynaklarında *bağlantı protokolleri, güvenlik kapıları ve source tests* var; gerçek INVENTHOR Main / Organizer native host adapteri, onaylı Studio↔Operator↔QA uçtan uca çalışma ve eski modüllerden tam bağımsızlık için kanıt yok. Bilinmeyeni doğrudan "çalışmıyor" veya "bağlandı" diye sunma.

Kanonik beş ürün kimliği: **INVENTHOR · OPERATOR · ORGANIZER · STUDIO_DESIGN · QA_FACTORY** (QA=Fabrika). Yedi uzmanlık Beyni bu beşli dışında yeni aktif uygulama/servis değildir; aşağıdaki taslak kod depoları ancak mevcut ürünün gerek duyduğu onaylı kaynak referanslarıdır.

## Beş sistemin 10 zorunlu bağlantısı

Kaynak sözleşmesi: `continuity/core_activation_gate.py`. Tamamı için kurulu host tarafından doğrulanmış kimlik + taze sonuç ACK, ayrıca aynı Fabrika'nın canlı QA tanığı gerekir.

| Zorunlu bağlantı | Doğrulanmış kaynak durumu | Gerçek native bağlantı |
|---|---|---|
| BRAIN_OPERATOR | Operator PR #5 içinde derlenmiş `CoreTransportFactory`, HMAC DEVICE_HELLO ve DEVICE_ACCEPTED yanıt akışı mevcut; PR #6 eski CONNECTED görüntüsünü süreyle denetliyor | **UNVERIFIED** |
| BRAIN_ORGANIZER | Brain `LiveTaskPort`, `TrustedMainContextPort` arayüzleri ve salt-okunur `prepare_brain_turn` mevcut | **UNVERIFIED**; gerçek native Main adapteri okunamadı |
| OPERATOR_ORGANIZER | Task envelope / owner lease ve revision kontrolleri tanımlanmış | **UNVERIFIED** |
| OPERATOR_QA | Eski Factory executor geçiş yolu halen geçici `LegacyFactoryCapabilityAdapter` üzerinden ilerliyor | **UNVERIFIED** |
| QA_ORGANIZER | Tek Fabrika + aynı Organizer checkpoint/readback kullanıcı sözleşmesinde tanımlı | **UNVERIFIED** |
| PROGRAM_ACTION_BRIDGE | Operator görev ve sonuç ACK protokol kaynakları var | **UNVERIFIED** |
| INVENTHOR_STUDIO | Brain semantik düzenleme/advisory kaynakları ve native Studio dosya handoff'u var | **UNVERIFIED** |
| STUDIO_OPERATOR | Core workspace/archive executor kaynakları var; eski Factory build/run bağımlılığı devam ediyor | **UNVERIFIED** |
| STUDIO_QA | Studio→Factory devri kaynak sözleşmesi var | **UNVERIFIED** |
| STUDIO_REAL_RENDER | Native preview/render kabul kuralları var | **UNVERIFIED** |

### Uzmanlık Beyinlerinin tamamı

GitHub `main` referanslarının ötesindeki **DRAFT PR #1** kodları: [Architecture](https://github.com/inventhor-cloud/inventhor-brain-architecture/pull/1), [Design](https://github.com/inventhor-cloud/inventhor-brain-design/pull/1), [Visual](https://github.com/inventhor-cloud/inventhor-brain-visual/pull/1), [Social](https://github.com/inventhor-cloud/inventhor-brain-social/pull/1), [Language](https://github.com/inventhor-cloud/inventhor-brain-language/pull/1), [Automation](https://github.com/inventhor-cloud/inventhor-brain-automation/pull/1), [Memory](https://github.com/inventhor-cloud/inventhor-brain-memory/pull/1). Bunların hiçbiri için bu oturumda native çalışma/promotion kanıtı bulunmadı. Bugünkü P0 çekirdek temizliğini bölmek için sosyal veya ek provider modüllerini canlıya taşımak yasak; gelecekteki özellik geliştirmeyi yasaklamak değil, yanlış sırada ayrı çalışma sistemi açmamak hedefi.

## Bu oturumda kodla tamamlanan güvenilir düzeltme

- Operator [izole taslak PR #6](https://github.com/inventhor-cloud/inventhor-operator-core/pull/6), PR #5 üstüne: `CoreTransportStatusReader` artık `timestamp` yaşı 30 saniyeyi geçen, ileri tarihli, eksik veya bozuk `CONNECTED` durumunu `DEGRADED` olarak işaretliyor. Main bağlantısı yalnız `transport.inventhor` durumundan geliyor; eski `direct-brain` yalnız kendi geliştirme alanında görünüyor. Eşleşme, kimlik doğrulama veya iş yürütme güvenliğini gevşetmez.
- [Operator Windows CI](https://github.com/inventhor-cloud/inventhor-operator-core/actions/runs/41520397621): **195/195 .NET tests PASS**, derlenmiş core transport kütüphaneleri, **boş `app/modules` ile gerçek kaynak derlemesinden test servisi başlatma**, WPF build ve PS kaynak kontrolleri PASS. **Bu kullanıcı PC'sinde kurulum/gerçek Main pairing değildir.**
- Brain aynı izole taslak [PR #7](https://github.com/inventhor-cloud/inventhor-brain/pull/7): tüm yedi uzmanlık Beyni, beş mevcut sistem, 10 gereken native bağlantı ve devam eden legacy bağımlılıklar `validation_reports/BRAIN_CONNECTION_SOURCE_INVENTORY_20261102.json` dosyasında; regresyon testleri hepsinin runtime statüsünü **UNVERIFIED** tutuyor. [CI](https://github.com/inventhor-cloud/inventhor-brain/actions/runs/41520692164): **324/324 source tests PASS**.

## Gerçek tam bağlantı için kalan işin minimum güvenli sırası

1. Mevcut **tek** Organizer'dan güncel TASK_ID, PROJECT_ID, revision, worker/lease ve onaylı hedefi **native kaynakta** oku; yabancı/çakışan lease devralma. Codex beklenmeden başka bağımsız dosyada çalışılabilir, ancak onun kirli yerel dosyaları ezilemez.
2. INVENTHOR Main ve Operator'ın **kurulu yerel** dosya/imza/hash, servis, startup, installer, IPC, `app/modules`, kod ve bağımlılıklarını 3-yönlü karşılaştır. Kaynak GitHub aynasını gerçek makine sayma.
3. `PluginCatalog.Load(...includeTransports:false)`, `LegacyFactoryCapabilityAdapter`, eski `windows.software-factory` ve derleme/test/kurulum referanslarını tek tek çekirdek sahibi mevcut Gateway/Aggregator/Tree bağlantılarına **gerçek eşdeğerlikle** taşı. Önce eski davranışları kapsayan test, sonra tek geri alınabilir değişiklik, sonra test; boş modül klasörüyle yetenek kaybı olmamalı.
4. Var olan **native Main** hostuna `TrustedMainContextPort` gerçek adaptörünü bağla. Organizer revision, task, owner/lease epoch, kaynağın doğruluğu ve ACK ana host tarafından **bağımsız** onaylansın. Python advisory nesnesi canlı host yetkisi yerine geçmez.
5. `InventhorTransport` cihaz eşleşmesini gerçek Main ile doğrula: taze `DEVICE_ACCEPTED`, kimliği belli tek görev, imzalı gerçek sonuç ACK, bağlantı kopması/yeniden bağlanma ve tekrar oynatma reddi.
6. Aynı işi aynı beş sistemde **INVENTHOR→Organizer→Studio gerçek düzenleme/render→Operator build/run→aynı QA Fabrika FAIL/FIX/RETEST→Organizer checkpoint readback** boyunca gerçek uygulamayla yürüt.
7. Native `NATIVE_ACTIVE_NONCORE_MODULES=0`, `NATIVE_CORE_TO_NONCORE_DEPENDENCY_EDGES=0`, imza/rollback, kaynak tüketimi, kullanıcı yetkisi ve tekrar başlatma kanıtı olmadan **CLEAN/DONE** deme.

**Bu oturumda DC çağrısı: 0.** Kurulu kaynakların ve mevcut native görev kilidinin doğrulanmadığı aşamada Codex'i beklemek şart değil; ama sahte native yetki üretmek, dosya değiştirmek veya canlı bağlandı diye hüküm vermek de doğru değil.
