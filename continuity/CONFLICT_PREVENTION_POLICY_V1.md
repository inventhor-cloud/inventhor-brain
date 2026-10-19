# INVENTHOR Main / Operator — Kalıcı Çakışma Önleme Sözleşmesi V1

**18 Ekim 2026 · Kaynak sözleşmesi / NOT DEPLOYED.** Mevcut Main, Organizer, Operator, GitHub PR ve Quality Factory üzerine uygulanır. İkinci görev yöneticisi, ikinci beyin veya ayrı geçici kaynak otoritesi yaratılmaz. İki farklı ajan aynı dosyayı değiştiriyorsa sessiz birleştirme yapılmaz.

## Neden bu olay yaşandı?

Gözlenen durum: Codex, Main'in yerel çalışma klasörünün bir Git deposu olmadığını, eski görev sahipliğini yalnız ilgili görevde TODO'ya döndürdüğünü ve Operator'ın 16 yerel dosyası ile PR değişikliklerini karşılaştırırken tekrar eden engeller yaşadığını raporladı. **Kesin yerel hata çıktıları ve gerçek 16 dosya içeriği henüz görülmedi.** GitHub'da doğrulanabilen teknik etkenler:

1. Operator GitHub `main` dalı mevcut Windows masaüstü tabanı değildir. Doğru PR #3 tabanı `pc-desktop-live-ui-v1`, örnek sabit commit `0245010cbf15cee516b985c0acafce648ebaefc7`. `main` ve desktop tabanı arasında 152 commit, taban ile PR #3 arasındaysa başlangıçta 83 commit vardı. Yanlış karşılaştırma tabanı gereksiz büyük fark listesi üretir.
2. Yerel çalışma klasörü `.git` barındırmıyorsa commit atalığı otomatik belirlenemez. SHA-256 üç-yönlü veri karşılaştırması yapılabilir, fakat yerel dosyanın hangi commit'ten türediği **yalnız eşit hash ile kanıtlanamaz**.
3. Main/Organizer'ın GitHub kaynak politikası `TODO` kayıtlarına doğrudan yazma lease'i vermez. Aynı TODO'ya dönüşü defalarca tekrarlamak doğru host izni oluşturmaz.
4. Eski `assess_takeover` kontrolünde bir görevin eski lease'i aynı projedeki **farklı, çakışmayan scope'u** da engelleyebiliyordu. Kaynak düzeyinde bu aşırı kilitlenme daraltıldı; aynı görev, aynı/üst-alt klasör, modül–yol belirsizliği, eksik kapsam veya gerçek çakışma hâlâ bloke.
5. Kod aynı anda Codex ve başka ajan tarafından GitHub veya yerelde güncellenirse ilk diff raporu eskiyebilir. Başka ajan tarafından edinilmiş/expired scope ile yeni yerel kaynağı karşılaştırmak tek başına yazma izni değildir.

## Tek otoriteli görev ve dosya sahipliği

Her değişiklikten önce Main host tarafından **gerçek ve güncel** kayıttan doğrulanmalı:

- Sabit `PROJECT_ID`, `TASK_ID`, `revision`, `epoch`, `owner_agent_id`, `scope_keys`, `expires_at`.
- Windows yollarında büyük/küçük harf, dizin üst–alt kapsamı ve symlink/junction gerçek yolu normalize edilerek kapsam çakışması kontrolü.
- Modül→dosya eşlemesi güvenilir Inventory tarafından kesinleştirilemiyorsa **çakışmasız olduğu varsayılmaz**.
- Yalnız bir **yazan ajan** aynı kapsamı tutabilir. Başka ajanlar, erişim izni varsa, dosyayı **salt-okunur** karşılaştırabilir; bu işlem task lease devri değildir.
- Gerçek mutasyon öncesi host tarafında atomik compare-and-swap ile güncel epoch/revision doğrulaması; heartbeat/expiry doğrulaması ve kaynak hash son kontrolü.
- Expired/stale lease aynı görev veya çakışan dosya/modüle aitse eski ajan devri netleşene kadar yazma durur. **İlgisiz başka kapsamın** eski lease'i bütün projeyi dondurmaz.
- Terminal BS/BF/DONE tekrar çalıştırılmaz. Başarısızlık tespitinde zaten var olan görev ve evidence'a bağlı aynı hata üzerinden ilerlenir.

**Yetki gerçeği:** `shared_organizer/board.py`, `shared_organizer/conflict_prevention.py` ve `repair/` altındaki kaynak modeller **host yetkisi vermez**. Bu sözleşmeyi canlıya almak için yüklü Main host üzerinde gerçek kimlik, lease CAS, scope Inventory, olay günlüğü ve Operator entegrasyon testleri gerekir. Bu aşamada bunlar kurulmuş/kanıtlanmış değildir.

## Standart güncelleme hattı

| Aşama | Kontrol | Başarısızsa |
|---|---|---|
| 1. Kapsam alımı | Canlı görev ID, gerçek sahiplik/lease, kullanıcı projesi, değişecek dosya listesi, yeniden yürütme kontrolü | Başka yetkili görevde devam et; scope'u gasp etme |
| 2. Sürüm sabitleme | Repo + base ref + **40 karakter commit** + PR head SHA, kaynak klasör kimliği, dosya hashleri | Yanlış taban veya değişen PR için önce yeni salt-okunur envanter |
| 3. Çakışma taraması | Local/Base/PR üçlü SHA-256 sınıflandırması; dosya ekleme/silme dahil | İkili değişen dosyaları ayrı incele, normal yeni dosyayı yanlışlıkla hata yapma |
| 4. Tekrar doğrulama | İşlemden hemen önce aynı üç kaynağın hashlerini yeniden oku, mevcut PR head ile pinned SHA'yı karşılaştır | PR/head veya yerel dosya değiştiyse eski plana göre yazma |
| 5. Kontrollü uzlaştırma | Tek seferde 1–4 ayrık dosya; diğer ajan aynı scope'ta yazmıyor; gerçek Main lease CAS | Aşırı büyük/çift taraflı dosyada uzman incelemesi ve ayrı geçici çalışma ağacı |
| 6. Kalite fabrikası | .NET/Python kaynak testi, WPF derleme, Main rota ve gerçek UI/servis testleri, backup/restore | Kurulum bloke; etkin çalışan sürüm korunur |
| 7. Dağıtım | SHA-256 doğrulanmış ve **bağımsız birimde** yedek, kurulum kaydı, rollback denemesi, gerçek host health | Eski çalışan sürümü koru veya doğrulanmış geri dönüşü uygula |

### Tekrar-deneme sınırı

Aynı `task_id + kaynak revision + işlem + hata kodu + kapsam hash` kombinasyonu aynı sonucu verdiyse Codex/Operator **aynı komutu tekrar etmez**. `HOLD_REPEATED_FAILURE` kararı raporlanır; farklı güvenli yol seçilir veya bloke olarak bırakılır. Bir otomatik döngü, `TODO` ↔ `READY` arasında tekrar tekrar geçiş yapamaz. Hata ve doğrulama kanıtı geçmişi korunur. Kaynak düzeyindeki fingerprint uyarısı kendi başına bir kalıcı retry kayıt defteri değildir; canlı Main host bunu atomik hata günlüğüne bağlamalıdır.

## Mevcut uygulama dosyaları

- `shared_organizer/board.py::assess_takeover`: scope/durum/lease advisory; ilgisiz eski lease tüm projeyi dondurmaz.
- `shared_organizer/board.py::advise_read_only_source_comparison`: görev durumunu değiştirmeden kaynak incelemesini önerir, dosya okuma/yazma izni **vermez**.
- `shared_organizer/conflict_prevention.py::classify_reconciliation`: tam sayılı dosya listesi, pinned commit head, 3-way sınıflandırma, recheck hash ve tekil başarısızlık fingerprint güvenlik denetimi. **PURE / no I/O / no execution**.
- Operator PR #3 `windows/bootstrap/Compare-SourceTriplet.ps1`: Git olmayan yerel klasörde salt-okunur üçlü hash.
- Operator PR #3 `windows/bootstrap/Review-SourceDrift.ps1`: aynı raporu hostta yeniden hesaplayıp değişen yerel/PR/taban dosyasını bloke etme; kendisi Git commit kimliğini doğrulamaz, **host** ayrıca pinned snapshotu doğrulamalı.
- `.github/workflows/operator-source-pr.yml`: mevcut Operator PR #3 için doğru taban dal denetimi ve Windows PowerShell + .NET/WPF testleri.
- `windows/SOURCE_RECONCILIATION_RUNBOOK.md`: Codex'e uygulanacak mevcut yedek, karşılaştırma, çözüm, geri dönüş prosedürü.

## Tekrar yaşanmaması için henüz gerçek ortamda doğrulanacaklar

**Açık uygulama/kabul maddeleri:** bilgisayarın/Operator'ın canlı bağlantısı; yerel 16 dosya ve Codex hata günlüğü; mevcut yedeklerin SHA-256 manifesti; Main'de gerçek CAS lease owner ve Inventory; installed Windows Operator adaptörünün test sözleşmesini kullanması; eski ve yeni Main ile GUI testleri; eşzamanlı iki ajanın aynı dosyayı değiştirememesi; başka scope'a izin verilmesi; başlatma, kapatma, ağ kopması, provider limit dolması, rollback senaryoları.

GitHub CI **SOURCE_TESTED**, bilgisayar kurulumu **LOCAL_DEPLOYED** değildir. Bu nedenle korunma sözleşmesi üretilmiş olsa da gerçek cihazda çalışan kalıcı çakışma önleme mekanizmasının tamamlandığı iddia edilmez.
