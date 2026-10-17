# INVENTHOR Main — Araştırma Merkezi / Video, Görsel ve Teknik Kaynak Sunumu V1

**Durum: SOURCE_ONLY, ÇALIŞAN ARAMA VE OYNATICI DEĞİL.** Mevcut INVENTHOR Main + Organizer'ın yetkili sağlayıcı gateway'i ve mevcut sohbet/tamir ekranı kullanılır. İkinci arama beyni, ikinci tarayıcı, yeni hesap/veri havuzu ya da kopya modül kurma.

## Beklenen davranış

Kullanıcı "Mercedes W... P... arızası", "mosfet nedir", "elektronik şema", "cihazı nasıl sökerim" veya "Almanca telaffuz videosu" istediğinde:

1. Önce cihazın doğrulanmış modeli ve varyantı, arıza kodu veya belirtiler, araştırmanın kapsamı belirlenir. VIN, seri numarası, plaka, adres, çocuk adı, özel fotoğraf gibi mahrem bilgiler açık onay ve gerçek gereklilik olmadan harici arama terimine yazılmaz.
2. Mevcut provider gateway üzerinden uygun çoklu arama adaptörleri seçilir: YouTube, mevcut desteklenen Google erişim yolu, Yandex Search API, OEM dokümanları ve diğer izinli web/forum kaynakları. Kullanıcı belirli platformları kapatabilir; başarısız sağlayıcı diğer kaynakları durdurmaz.
3. Kaynaklar **VIDEO / IMAGE / DOCUMENT / WEBPAGE** tipiyle ortak listeye alınır; kaynak adı, doğrudan bağlantı, sağlayıcı, doğrulanmış/yayın tarihi (varsa), araç/kart revizyonu uyumu, fiyat/kota politikası ve kaynağın güven derecesi belirgin olur.
4. Sonuçlar çoğaltılmaz; kullanım izinleri ve saklama/telif kontrol edilir. Video/yorum **fabrika doğrulaması** değildir. Gerçek servis kılavuzu ve datasheet, ancak doğru cihaz revizyonu ve host kaynak doğrulamasıyla öncelikli kabul edilir.
5. Tamir ekranında ana adım **solda**, kaynak kitaplığı **sağda veya mobilde altta** görünür. Sekmeler: **Videolar, Görseller, Şemalar/Belgeler, Web**. Bir videoya dokununca izin veriliyorsa resmî oynatıcı, yoksa **Kaynağı aç**; görsel için güvenli kaynaklı önizleme ve büyütme; PDF ve şema için lisans/erişim uygun ise sandbox doküman gösterici.
6. Kullanıcı kendi fotoğrafını izinle eklerse resmin orijinalini değiştirmeden işaretlenmiş kopyası gösterilir. Temsili görsel **yalnız gerçekten gerekli olduğunda** üretilir; pin/bağlantı numarası ve ölçüm konumu uydurulmaz.
7. Kaynaklar bulununca "videoda geçen yöntem doğrudur" varsayılmaz. Servis adımı, teknik semboller ve voltaj/direnç ölçüm referansları bağımsız üretici verileri ve güvenli gözlemlerle kontrol edilir. Sonuçla gerçek teşhis ayrı tutulur.
8. Araştırma ve sunum her platforma uyumlu UI bileşenlerince sağlanır: Android, iOS, Windows, Linux (uygunsa macOS). Aynı Main metadata, farklı sistem oynatıcı/WebView izin ve yeteneklerini kullanır.

## Gerçek API ve lisans seçimi

- **YouTube:** Resmî YouTube Data API `search.list` video araması; `type=video` ve uygun olduğunda `videoEmbeddable=true` / veri erişim politikası. Resmî IFrame oynatıcısı uygulama WebView/host içinde çalışabilir; platformun `Referer`, API, bölgesel erişim, yaş ve embed şartları ayrıca doğrulanır. Video indirme veya kalıcı medya kopyası otomatik yapılmaz. Resmî kaynak: https://developers.google.com/youtube/v3/docs/search/list , https://developers.google.com/youtube/iframe_api_reference , https://developers.google.com/youtube/terms/required-minimum-functionality
- **Google:** Google Custom Search JSON API **yeni müşterilere kapalı**; mevcut kullanıcılar için 1 Ocak 2027 sonlandırma tarihi verilmiş. Bu yüzden yeni INVENTHOR mimarisi bunu **zorunlu bağımlılık** yapmaz. Güncel Google destekli ürün, lisanslı web sağlayıcısı veya erişilebilir kaynak-bağlantı yöntemi kullanılabilir; sağlayıcının yeteneği/ücreti önceden doğrulanmalı. Resmî kaynak: https://developers.google.com/custom-search/v1/overview
- **Yandex:** Yandex Cloud Search API ancak uygun hesap, kota, güncel izin ve yetkilendirmelerle kullanılabilir; Yandex Query/SQL API, Yandex web araması ile karıştırılmaz. Hizmet/erişim planı uygulamaya bağlanmadan live `YANDEX_CONNECTED` yazılmaz. Örn. https://yandex.cloud/en/docs/iam/roles-reference
- **Diğer kaynaklar:** OEM, eğitim platformları, forumlar, yasal/veri-lisanslı arama sağlayıcıları. "Tüm platformlar" **bağlanabilir adapter standardı** demektir; giriş gerektiren, kapalı veya çekilmesine izin verilmeyen içerikleri otomatik kopyalama garantisi değildir.
- **Free-tier önce:** önbellek kısa süreli ve izinli metadata düzeyinde; kota ve maliyet tavanı Main'de; yalnız arama gerektiğinde provider çağrılır; aynı arıza için sonuçlar ve kaynaklar gereksiz tekrarlanmaz. API anahtarları uygulama koduna/PR'a girmez.

## Kaynak kod sözleşmesi ve görüntüleme sınırı

- `repair/research_media.py::plan_research` yalnız araştırma planını hazırlar; **ağ isteği yapmaz**. Main oturumu, araştırma izni, medya türü, kullanıcı verisi sızıntısı ve sağlayıcı seçimi kontrollüdür.
- `repair/research_media.py::prepare_media_cards` daha önce host tarafından alınmış `MediaCandidate` listelerini kontrol edip kullanıcı arayüzü için tekil `MediaCard` nesnelerine dönüştürür. Yerel/özel IP, güvensiz URL, yetkisiz görsel ve sahte YouTube URL'leri kabul edilmez.
- `preview_url` sadece doğrulanmış YouTube video ID'si ve host'un **embeddable** bilgisi sağlandığında hazırlanır; bu hazır videonun gerçekten oynatıldığı anlamına gelmez. Oynatıcının gerçek hak/URL/redirect/iframe güvenliği işletim sistemi WebView'i tarafından ayrıca denetlenir.
- `IMAGE` / `DOCUMENT` kaynağı dışarıdan alınan url olarak kullanıcıya gösterilebilir; boyut/içerik türü/indirilen dosya güvenliği ve origin politikası, güvenilir host download/proxy ve sandbox tarafından uygulanmak zorundadır. Kaynak kartının olması host'a URL'yi sunucu tarafında fetch etme izni değildir.
- `SOURCE_CARDS_ONLY` ile `LIVE_SEARCHED`, `PREVIEW_RENDERED`, `VERIFIED_REPAIR`, `END_TO_END_ACCEPTED` açıkça ayrı seviyelerdir. Bu aşamada **ilk seviye** dışında gerçek ekran veya web uygulaması yapılandırılmadı.

## Tam entegre olmak için QA kabul listesi

Yetkili Main host/provider bağlantısı; sağlayıcı API bağlantı hataları/kota; YouTube oynatıcının resmî embed ve referer davranışı; Android/iOS/Windows/Linux WebView gösterimi; kaynağın lisans/erişimi; HTML/PDF/görsel zararlı içerik ve boyut kontrolleri; linkten kullanıcıya ait ağ/yerel adres erişimi/SSRF engeli; aile profili izolasyonu; gerçek cihaz revizyonu eşleşmesi; eksik/yasak içerikte kullanıcıya düzgün hata; video açma seçimi; tablet/PC ekranında kesintisiz çalışma; maliyet politikası; gerçek USB/OBD görüntüleme kanıtı.

Mevcut durum: **arama/medya görünümü için kaynak sözleşmesi hazır**. Gerçek YouTube/Google/Yandex araması ya da video oynatma devrede değildir.
