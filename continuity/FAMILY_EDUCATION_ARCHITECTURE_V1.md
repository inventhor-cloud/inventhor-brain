# INVENTHOR Main — Aile Eğitim ve Sohbet İçi Öğrenim Mimarisi V1

**Durum: SOURCE_ONLY / OWNER IDEA.** Aynı fikir kaydı: `continuity/idea_pool.json#IDEA-INVENTHOR-FAMILY-EDUCATION`. Bu belge gerçek Main kurulumunu, canlı sohbet eklentisini veya çocuk hesabı entegrasyonunu ispatlamaz. INVENTHOR Main tek otoritedir; ikinci bir beyin veya Organizer açılmaz.

## Ana ürün hedefi: öğretim, yalnız çeviri değil

**Owner kararı (2026-10-17): INVENTHOR Family Education'ın birincil amacı her öğrenciye gerçekten bir şey öğretmek, anlamayı ve hatırlamayı geliştirmektir.** Çeviri, sözlük, kelime işaretleme, tamamlama ve sohbet araçları bu amaca hizmet eder; yalnız mesaj çevirmek veya doğru cevabı söylemek öğretimin tamamlandığı anlamına gelmez.

- **Ders modu:** Ön bilgi/seviye belirle → tek küçük konuyu açıkla ve göster → öğrenciye uygulattır → hatayı gerekçesiyle düzelt → benzer yeni soruyla bağımsız anlamayı ölç → sonraki günlerde aralıklı tekrar et → ilerleme kaydını yalnız doğrulanmış öğrenci profiline yaz.
- **Sohbet modu:** Normal sohbet varsayılan olarak sohbet kalır. Öğrenci kendi seçtiğinde veya aktif eğitim oturumunda açılan kelime açıklaması, kısa quiz, eksik harf/kelime, çeviri, telaffuz ve anlık ipuçları ders hedefiyle ilişkilendirilir. Arkadaş/aile mesajı öğrencinin çalışması için değiştirilmez.
- **Uyarlanabilir öğretmen:** Seviye, yaş/sınıf, hedef dil/ders, cevap geçmişi ve sık hata türüne göre anlatım biçimini, ipucu düzeyini ve soru zorluğunu ayarlar. Çocuklar için anlaşılır, yaşa uygun, destekleyici anlatım tercih edilir.
- **Öğrenme ölçüsü:** Tek doğru cevap “öğrendi” değildir. Farklı örneklerde bağımsız doğru yapma ve aralıklı tekrar başarısı gerekir; emin olunmayan konular tekrar kuyruğuna gider. Otomatik çeviri başarı puanı sayılmaz.
- **Doğruluk ve izin:** Main'in doğruladığı öğretim içeriği/sağlayıcı kullanılır; yanlış veya belirsiz açıklama doğrulanmış ders kaynağına yönlendirilir. Çocuk hesabı, aile erişimi ve kişisel ilerleme yetkileri host tarafında kontrol edilir.

**Ürün kabul kriteri:** “Öğrenci doğru cevabı gördü” değil, “öğrenci daha önce anlamadığı konuyu rehberlikle öğrendi ve sonraki bağımsız ölçmede gösterebildi” olmalıdır. Bu pedagojik davranış henüz canlı uygulamada doğrulanmadı.

## Kapsam: aileye göre öğretim

- **Hedef yabancı diller V1:** Almanca ve İngilizce; Türkçe başlangıçta açıklama/arayüz ve çift yönlü çeviri dili. Diğer diller ihtiyaç halinde doğrulanmış dil paketleriyle açılır.
- **Yetişkin:** Almanca A1/A2/B1+, konuşma, dinleme, kelime, dil bilgisi, okuma, yazma, eksik konuyu tekrar etme.
- **Çocuklar:** İngilizce/Almanca, matematik, fen ve gerektiğinde okulun diğer dersleri; seviyeyi yaş, sınıf, yetkili okul müfredatı ve öğrenci yanıtları belirler. Yanlış bilgi şüphesi kontrol edilmeli; öğrenci yerine bütün ödevi otomatik bitirmek yerine adım adım rehberlik sunulmalı.
- **Bireysellik:** Ailede her kişinin kimlikli profili, çalışma hedefleri, kazanımları, ders geçmişi ve gizli kelime listesi ayrıdır. Akrabalık üzerinden özel sohbet veya anı erişimi otomatik verilmez.

## Sohbette çeviri ve Viktorija benzeri opsiyonel çalışma

Bu özellik, **mevcut chat ve Language Brain** içinde isteğe bağlı bir moddur; Viktorija'nın kodu, ikonu, bağımsız arayüzü veya öğrenci hafızasını kopyalamaz.

- Çeviri yönleri: **Almanca ↔ Türkçe, Almanca ↔ İngilizce**, ayrıca Türkçe ↔ İngilizce. Gelen mesajda dokunarak/anında çeviri ve giden mesajda **göndermeden önce önizleme**; özgün mesaj korunur ve otomatik gönderim yoktur.
- `study_mode=OFF` varsayılan. Açılınca Main'den alınan öğrenciye özel bilinmeyen kelimeler **kırmızı**, bizzat çalışmak için işaretledikleri **yeşil** görünür.
- Kelimeye dokununca küçük alt panelde kısa anlam; gerektiğinde geniş panelde bağlama göre çeviri, telaffuz, Almanca artikel/hal/fiil çekimi, örnek ve çalışmak istiyorum/öğrendim/unuttum kontrolleri. Dilsel ayrıntılar sözlük/sağlayıcı doğrulaması olmadan güvenilir sayılmaz.
- Mevcut cümle üzerinden **kelime boşluğu doldurma** ve **harf tamamlama** egzersizleri; yalnız seçilmiş kelime gizlenir, sohbet metni ve karşı tarafın gördüğü mesaj değişmez. Tek doğru yanıt “ezberlendi” sonucu doğurmaz; tekrar/sınama Main kişisel hafızasında ayrı doğrulanır.
- Sonraki aşamalarda aralıklı tekrar, kısa canlı konuşma, sesle cevap, OCR ile ders/ödev, öğretmen/grup öğrenme görünümü eklenebilir; izin verilmedikçe kamera/mikrofon çalışmaz.

## Kanonik sahiplik

| Mevcut alan | Sorumluluk |
| --- | --- |
| INVENTHOR Main + Organizer | Öğrenci kimliği ve veli politikası; hedef ders, eğitim oturumu, yetkili veri erişimi, aktif sohbet mesajının sürümü, görev planı ve kanıt |
| Language Brain (`inventhor-brain-language`) | Dil meta verisi ve TR/DE/EN çeviri isteği/önizleme sözleşmesi; `dialogue_quality/chat_learning.py` ile kelime işaretleri ve seçili mesajda tek egzersiz |
| Personal Memory Brain | Öğrenciye ayrılmış kelime, tekrar/öğrenme geçmişi; şifreli/izinli saklama ve kontrollü ilerleme özeti |
| Existing chat UI | Mesajı değiştirmeyen işaretleme katmanı, açılır kelime paneli, çeviri görünümü, egzersiz kartı ve kullanıcı kontrolleri |
| Existing provider gateway | Çeviri/gramer açıklama üretimi ancak doğrulanmış sağlayıcı ve mahremiyet izniyle |
| Quality Factory | Dil doğruluğu, çocuk uygunluğu, öğretim kalitesi, aile profili yalıtımı, gönderim/izin, performans, UI ve uçtan uca kabul |

## Mahremiyet ve doğrulama

- Çocukların ses kayıtları, ödev görüntüleri, mesajları, öğrenim düzeyleri ve kişisel kelime listeleri GitHub'a, ortak reklam/analitik servisine veya başka öğrenci profiline gönderilmez. Aile hesabı kontrolü, veli izinleri ve veri saklama/silme politikası Main tarafından uygulanır.
- Kaynak dosyalarındaki `learner_profile_authorized` benzeri bayraklar **host tarafından doldurulan referans alanlardır**; yalnız Python koduna `true` göndermek kimlik doğrulaması değildir.
- Çeviri adapter'ı çeviri üretmez; Main'de henüz bağlanmamış sağlayıcının çalıştığını iddia edemez. Kelime öğrenim adapter'ı kullanıcı mesajını değiştirmez, işi bitirmez, kelime bilgisini kalıcı olarak kaydetmez.
- `SOURCE_TESTED` ≠ `INSTALLED` ≠ `END_TO_END_VERIFIED`. Geçiş için gerçek mesaj kimliği/sürüm, çocuk veli izni, sözlük/çeviri doğruluğu, WPF/mobil arayüz testleri ve gerçek kullanıcı kabulü gereklidir.

## Önceliklendirme

1. V1 Main auth/aile profilleri ve chat-host bağlantısı.
2. Almanca/Türkçe/İngilizce sohbet çevirisinin gerçek sağlayıcıyla doğrulanması.
3. Sohbet öğrenimi opt-in UI: kırmızı/yeşil işaretler, kelime paneli, boşluk ve harf tamamlama.
4. Öğrenci hafızası, aralıklı tekrar, gelişim raporu; çocuklar için okul derslerine genişleme.

**Mevcut kaynak referansı:** `inventhor-cloud/inventhor-brain-language:docs/OPTIONAL_CHAT_WORD_LEARNING_V1.md`. İçerik kullanılabilir kaynak/plan olarak kayıtlıdır, çalışır ürün olarak değil.
