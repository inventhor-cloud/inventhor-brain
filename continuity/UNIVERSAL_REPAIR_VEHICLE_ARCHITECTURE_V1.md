# INVENTHOR Main — Evrensel Tamir, Servis ve Araç Teşhis Mimarisi V1

**Durum: SOURCE_ONLY / OWNER IDEA / NOT DEPLOYED.** Bu, mevcut `INVENTHOR_MAIN` ve tek Organizer'ın altında yeni bir **tamir ve teşhis alanıdır**; ikinci AI beyni, ikinci modül katalogu veya ayrı aile hafızası oluşturmaz. Ürün vizyonu her şeyi birden yapmaya *açık*, aktivasyon ise gerçek cihaz ve güvenilir test kanıtına bağlıdır.

## Ürün hedefi

INVENTHOR, bir tamir sorusunda yalnız “parçayı değiştir” demeyecek:

1. **Cihazı tanıyacak:** marka, model, varyant, revizyon/yıl ve kullanıcının gözlediği semptom; eksikse net isteyecek. Bilmediğini uydurmayacak.
2. **Ön tanı ve güvenlik:** elektrik/yüksek gerilim, lityum batarya, basınç, gaz, dönen/kaldırılmış makina, otomobil fren/direksiyon/SRS/ADAS/HV gibi sistemleri sınıflandıracak; yüksek riskte profesyonel prosedür ve teknik yetkinlik gerektiren işlemleri ayrı ele alacak.
3. **Kaynak bulacak:** kullanıcının fotoğrafı, doğrulanmış servis kılavuzu, kablo/akış şeması, uygun üretici dokümanı, geçmiş servis kaydı; kaynak/provenans ve uyumluluk değişkenlerini gösterecek.
4. **Kanıt toplayacak:** görsel, ses, semptom tarihi, uygun bağlantı cihazının desteklediği hata kodu ve sensör verileri; bunları kesin arıza ile karıştırmayacak.
5. **Arıza olasılıklarını yönetecek:** birkaç alternatif neden, ayırt edici güvenli ölçüm/test, elde edilen sonuç ve bir sonraki adım; rastgele parça değişimini azaltacak.
6. **Görsel yönlendirecek:** gerçek fotoğrafı *izinli kopya üzerinde* işaretle, doğru revizyonun doğrulanmış şemasını göster, mevcut uygun görseli yeniden kullan; **yalnız genel konuyu anlatmada gerçekten fayda varsa** “temsili” ibareli çizim üret. Pin numarası/bağlantı/ölçüm noktası/torque gibi değerler görsel modelin hayal gücünden üretilemez.
7. **Tamir sonuçlarını sınayacak:** önce/sonra kanıtları, uygulanan parça ve iş, hata tekrar testi, güvenlik ve çalışma sonucu. “Teşhis edildi”, “onarım tamamlandı” ve “doğrulanmadı” ayrı statüler.
8. **Geçmişi tutacak:** ilgili cihaz ve yetkili kullanıcı profiline özgü, izinli ve özel; gerçekte yapılmayan işlem yapılmış diye kaydedilmez.

Kapsam: otomobil, motosiklet, ticari araç, bisiklet/e-bisiklet, telefon/tablet, PC, beyaz eşya, ses sistemleri, elektrikli aletler, HVAC, tesisat, ev elektriği, endüstriyel ekipman ve gelecekte yeni konu paketleri. Her şeyin her cihazda çalışacağı vaadi verilmez; **uyumluluk keşfi ve modüler adaptör** zorunludur.

## Tek mimari, konu paketleri ve araç bağlantısı

```text
Kullanıcı / mevcut chat+görsel arayüz
  ↓
INVENTHOR Main [kimlik, izin, cihaz profili, onay, Organizer, kayıt otoritesi]
  ├─ Universal Repair Triage (domain/risk/source/evidence decision)
  ├─ Existing Repair Visual Decision (gerektikçe fotoğraf/şema/temsili çizim)
  ├─ Manufacturer / Verified Source Resolver
  ├─ Repair Plan & Evidence / Quality Factory
  └─ Mevcut Windows Operator veya uygun onaylı yerel cihaz adapter'i
       ├─ OBD-II generic / SAE J1979 & J1979-2 (OBDonUDS)
       ├─ UDS on CAN / DoIP (ISO 14229 / ISO 13400, desteklendikçe)
       ├─ SAE J2534 Pass-Thru ve üretici yazılımı
       ├─ J1939 ticari araçlar, OEM diagnostic ve başka transport plugin'leri
       ├─ USB / BLE / Wi-Fi / serial / MIDI* / ölçü aleti* / kamera*
       └─ Gelecekte yeni marka/cihaz adaptörleri
```

`*` = cihaz ve fonksiyona göre ayrı gerçek implementasyon/izin gerekir; bu aşamada **bağlanmış değildir**. Genel tamir yönetiminin Main'de olması, geçmişteki `education/repair_visual_policy.py` salt-okunur görsel seçicisinin *yeniden kullanılmasına* engel değil. Birden çok “repair brain” kopyalanmayacak.

**Araç eşlemesi:** otomobil kimliği, motor/şanzıman/ECU varyantı, araç elektroniği ve seçenekleri doğrulanmadan başka araca ait modül verisi kullanılmaz. Varsayılan OBD okuyucu **her ECU'ya erişiyor diye** etiketlenmez. Hata kodu semptomdur; parçanın kesin bozulduğu anlamına gelmez.

## Araçta fonksiyon katmanları — mimari geniş, uygulama kontrollü

| Aşama | Fonksiyon | Gerçek kabul kapısı |
| --- | --- | --- |
| Keşif / temel okuma | OBD bağlantısı, araç kimliği, genel DTC, freeze frame, desteklenen PID ve canlı veriler | Kullanıcı bağlantı izni, güvenilir adaptör, eşleşen araç/arayüz, desteklenen hizmet |
| Gelişmiş teşhis | OEM/UDS ECU kimlikleri, üretici kodları, desteklenen veri akışları, servis bilgi kaynakları | OEM lisansı/güvenlik erişimi ve doğrulanmış teknik protokol |
| Servis işlemleri | Kod silme, servis reset, adaptasyon, kalibrasyon, çift yönlü aktüatör testi | *Tam olarak hangi işlem* için Owner onayı, araç güvenli durumda, doğru servis prosedürü |
| Profesyonel programlama | ECU coding, flash/update, bazı güvenlik sistemleri, ADAS ayarı, J2534/DoIP/OEM süreçleri | Gerçek OEM yetkilendirmesi, gerekli profesyonel bilgi, cihaz/güç/geri dönüş güvencesi, araç kimlik ve prosedür doğruluğu |

**“Kısıtlama olmadan” = modüler özellik mimarisinde marka/işlev tavanı yok.** Buna rağmen otomobilin fren, direksiyon, hava yastığı, tahrik ve yüksek gerilim sistemlerini veya ECU programlamasını rastgele AI metin çıktısına bırakmak, eksiksiz çalışma anlamına gelmez. Kullanıcı sahipliği, üretici erişimi, cihaz uyumu ve profesyonel çalışma koşulları olmadan **ECU write / raw bus / test actuator** otomatik olarak gönderilmez. İleri işlevler **tasarımda var**, gerçek donanım ve Main onay zinciri kurulunca ilgili paketlerle açılır.

Avrupa'da bağımsız tamir operatörlerinin araç OBD ve onarım bilgi erişimi için temel çerçeve: Regulation (EU) 2018/858 Article 61: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex:32018R0858 ; erişim, belirli bir araca veya güvenlik işlevine otomatik/ücretsiz/izinsiz hak verildiği anlamına gelmez.

Başvurulacak teknik standartlar (belirli araç/ağ arayüzüne göre, lisanslı tam metne erişim gerektirebilir):

- ISO 14229-1:2026 UDS application layer: https://www.iso.org/standard/87962.html
- SAE J1979-2 OBDonUDS: https://saemobilus.sae.org/standards/j1979-2_202104-e-e-diagnostic-test-modes-obdonuds (2026 revizyon bilgisi ayrıca doğrulanmalı)
- SAE J2534 pass-thru: https://saemobilus.sae.org/standards/j2534_201907-recommended-practice-pass-thru-vehicle-programming
- Her üreticiye ait değişen sistem fonksiyonları için **üreticinin yetkili güncel kılavuzu** bağlanmadan genel standarttan bir servis prosedürü tahmin edilmez.

## Modül üretim sözleşmesi ve kalite fabrikası

Yeni bir `vehicle.` ya da `repair.` adapter'i ayrı beyin değildir; mevcut Operator `MODULE_INTEGRATION_STANDARD_V1.md` ile `module.json` + `integration.json`, yetenek/aksiyonların %100 eşleşmesi, dependency, sürüm uyumu, sağlık testi, input/output/error şeması ve bağımlı modül/izin denetimleriyle üretilir.

Adapter'ler yalnız **destekledikleri** hizmetleri ilan eder. Kullandığı cihazın ve bağlı aracın gerçek destek listesini Main'e iletir. Genel OBD adaptörü ECU programlama özelliğine sahipmiş gibi etiketlenmez. Desteklenmeyen araç/protokol görüldüğünde açıkça “bu bağlantıda desteklenmiyor” bildirimi verir ve uygun adaptör arar; mevcut adapter güvenliği gevşetilmez.

Gerekli Quality Factory senaryoları: yanlış araç revizyonu; başka kullanıcıya ait VIN/veri; yanlış baud/protokol; çift modül yetenek çakışması; şişmiş batarya/HV; fren-SRS; bağlantı koptuğunda fallback ve hiç yazılmayan veri; otomobil hareketsizliği; şarj gücü/flash recovery; DTC'nin yanlış kesin teşhisi; uydurma şema; görseldeki işaretlerin gerçek kaynakla uyumu; canlı Main izin/lease ve oturum sonu veri kapatma; rollback; arayüz ve ekran okuyucu.

## Sürüm gerçeği / kaynak dosyaları

- `repair/triage.py` — Main-owned ve **SOURCE_ONLY** evrensel triyaj/güvenlik/kanıt kararları.
- `repair/vehicle_policy.py` — OBD/UDS/J2534/J1939/OEM bağlantı ve gelişmiş fonksiyon planlayıcısı. **Hiçbir gerçek ECU komutu göndermez.**
- `education/repair_visual_policy.py` — mevcut temsili görsel / gerçek fotoğraf tercih sistemi, tamir alanları için tekrar kullanılıyor. Kamera/görsel üretim veya cihaz bağlantısını çalıştırmaz.
- `tests/test_universal_repair.py` ve `tests/test_repair_visual_policy.py` — senaryo doğrulama; gerçek fiziksel tamir, görüntü analizi veya araç erişimi kanıtı değil.
- Bu tasarım `continuity/idea_pool.json` içinde aynı Main projesine bağlı **ayrı çalışma fikri** olarak tutulur; yeni repo ve paralel Organizer açılmaz.

**Canlı entegrasyon, USB/BLE/OBD bağlantısı, üretici API kimlik bilgileri, gerçek cihazda ölçüm, servis verisi ve saha testleri henüz yok.** Kanıt olmadan `ACTIVE` ya da `FULLY_INTEGRATED` gösterilmez.

## Multi-platform internet araştırması ve ekran içi medya

Owner gereksinimi: INVENTHOR bir arızayı sadece kendi model bilgisiyle yanıtlamayacak; gerektiğinde **YouTube, Google, Yandex, üretici kaynakları, forumlar ve izinli diğer platformlarda** arama yapabilmeli. Video, görsel ve şemayı mevcut INVENTHOR ekranında, tamir adımlarının yanında, kaynak bağlantısıyla birlikte sunabilmeli. Uygun video gömülebilir değilse kaynak sayfayı açabilmeli. Başka bir beyin/Organizer/sahte video proxy sistemi kurulmaz.

**Kaynak sözleşme:** `continuity/RESEARCH_MEDIA_CENTER_V1.md`; `repair/research_media.py` ortak provider planı ve medya kartları sunar. Kaynak türü, eşleşen cihaz revizyonu, araştırma/kullanım izni, güven seviyesi ve video oynatma hakkı ayrı doğrulanır. Google eski Custom Search JSON API'sine zorunlu bağlılık yok (yeni müşteri erişimi kapalı); Yandex için güncel Search API erişimi ve ücretsiz/ücretli kota host üzerinde doğrulanır. YouTube içi oynatma resmî IFrame/uygun gömme şartlarıyla sınırlıdır.

**Tamire entegrasyon:** fotoğrafta gerçek bileşen konumu; sembol, kısaltma ve ölçümlerde doğrulanmış datasheet, OEM kılavuzu, bilinen referans aralıkları; video ile kaynak karşılaştırması; kanıt olmayan adım için açık belirsizlik. Hiçbir YouTube videosu tek başına fren, yüksek gerilim veya ECU işleminin güvenilir uygulama kanıtı değildir. `SOURCE_CARDS_ONLY` ≠ canlı web araması ≠ INVENTHOR ekranına gerçek oynatma. Gerçek platform adapter'leri ve kullanıcı arayüzü henüz bağlı değildir.

## Gerçek bağlantı olmadan çok platformlu bağlantı ve OBD çözümleme

- `repair/platform_link_policy.py`: Platformlar **Android, iOS, Windows, Linux ve macOS**. Kablosuz `BLUETOOTH_LE`, `BLUETOOTH_CLASSIC`, `WIFI`, `WIFI_DIRECT`; kablolu `USB_SERIAL`, `USB_VENDOR`, `J2534_USB`, `ETHERNET`. Kullanıcı tercihi AUTO/WIRED/WIRELESS. Platformun ve adaptörün gerçek destek/entitlement/protokol/driver/izin durumu *yerel host tarafından doğrulanmadan* bağlantı uygun sayılmaz. **iOS USB ve Classic BT** için ayrıca doğru aksesuar/API izinleri gerekir. Sonuç yalnız `SOURCE_PLAN_ONLY`; mevcut kaynak kod Bluetooth eşleştirme/USB açma yapmaz.
- `repair/obd_metrics.py`: Daha önce alınmış saf Mode 01 pozitif yanıt byte'larını `0x41 05` sıcaklık, `0x41 0C` motor devri, `0x41 0D` hız ve `0x41 11` gaz kelebeği yüzde değerleri olarak **hesaplar**. Kaynak/protokol/araç kimliği kalibrasyonu burada doğrulanmaz; `SOURCE_DECODE_ONLY` sonucunu gerçek ECU verisiymiş veya kesin arızaymış gibi göstermeyin. Negatif yanıt, bilinmeyen PID, hatalı uzunluk ve ham ELM/CAN yazısı reddedilir. **Hiçbir sorgu veya araç komutu göndermez.**
- `tests/test_obd_and_platform_links.py` temel matematik, tüm platformlar, izin, aksesuar uygunluğu, link tercihleri, uyumsuzluk ve yalan bağlantı iddialarının önlenmesini kontrol eder. Gerçek test için yetkili, uyumlu OBD donanımı ve araç fiziksel erişimi şarttır.
