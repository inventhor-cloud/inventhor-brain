# Beyin–Organizer–Operator: gerçek görev devamı için bağlantı sözleşmesi

**Durum:** Kaynak kod ve sınamalar hazır; **çalışan Beyin/Operator'a kurulmuş değil**. Fabrika 0.7.0 ile Codex'in yaptığı işler değiştirilmedi.

## Amaç

GPT, Codex ve INVENTHOR aynı **canlı kanonik Organizer görevini** görecek. Birinin bitirdiği iş tekrarlanmayacak; sonraki ajan tamamlananları, kalanları, kanıtı, hedef dosya kimliğini ve görev sahibini okuyacak. Yeni fikirler öncelikli Fabrika işini kesmeyecek.

## Mevcut tek sisteme bağlama

`continuity/live_handoff_gate.py` bir kaynak **denetim katmanı**; yeni Beyin, yeni kuyruk veya arka plan hizmeti değil. Yerel, yetkili .NET Main/Organizer bağlayıcısı `LiveTaskPort` sözleşmesini mevcut kanonik olay/görev deposuna bağlamalı:

- `read_exact(TASK_ID)`: Yetkili Organizer'ın *güncel* TASK_ID kaydını okur; snapshot değil.
- `verify_read_provenance(record)`: Ana bilgisayar dönen kaydın bulut, sohbet, model cevabı veya önbellek olmadığını **bağımsız** doğrular. Kayıt içindeki bir `trusted=true` bayrağı asla yeterli değildir.
- `claim_if_unchanged(TASK_ID, target, revision, worker)`: Mevcut Organizer ile atomik revizyon/kilit kontrolü, görev sahipliği ve yerel `preflight-show/ack/verify` tamamlanmadan olumlu yanıt vermez.

Mevcut `Inventhor.WorkOrganizer.Tool.exe handoff` tamamlanan/kalan alanlarını okuyabiliyor. Fakat bu görünümün `revision`, `observed_at`, güncel bağımlılık listesi ve bağımsız kaynak doğrulamasını **tek başına** sunduğu henüz kanıtlanmadı. Yerel bağlayıcı bunları güncel kanonik kayıtlar üzerinden doğrulayarak sağlamalı; sabit veya tahminî alan kullanmamalı.

## Denetim ve devam

1. Ana ajan canlı TASK_ID ile giriş yapar. Eski `continuity/work_queue.json` veya sohbet geçmişi görev seçimi için yetki değildir.
2. Okuma salt-okunurdur. Yazma için görev TODO/DOING olmalı, bağımlılıklar DONE olmalı, başka çalışan bulunmamalı, kalan iş belirtilmiş olmalı ve **native kilit** başarıyla alınmalı.
3. Kesinti, bitmiş iş, eski revizyon, eski görev sahibi, sahte kanıt veya yanlış hedefte **yeniden oynatma yok**: kesin görev bazında uzlaştırma gerekir.
4. İş sonunda `draft_next_checkpoint` denetimli tamamlanan/kalan/kanıt/sonraki-adım taslağı verir; **kendisi kayıt yazmaz**. Mevcut Organizer'ın `checkpoint --completed-json ... --remaining-json ... --evidence ... --next ...` mekanizmasıyla çalışan sahibi yazar; ardından yeni kayıt okunup sahiplik `release` ile bırakılır.
5. Test: GPT → Codex → INVENTHOR tek gerçek küçük görev üzerinde sırayla ilerlemeli; bozulmuş kaynak, iki çalışan, yeniden başlatma, eskimiş kilit ve terminal tekrar çalıştırma sınamaları yapılmalı.
6. Son adım onaylı **yerel derleme, imza, güncelleme ve geri alma**. Fabrika'nın güvenilir canlı QA tanığı/ayrı imzalama gerekliliği bu sistemden bağımsız olarak devam eder.

## Kanıt ve sınırlar

Kaynak testleri: `python3 -m unittest discover -s tests -v`. Bu testsuite, **yerel Organizer değil sahte bir yetkili port** kullanır; gerçek UI veya yüklü uygulama başarısını kanıtlamaz. GitHub değişikliği görev dağıtımı başlatmaz. Gerçek başarı: kurulu Operator'da bir işin doğrulanmış kontrol noktası ile bir ajandan diğerine devri, aynı işin yeniden oynatılmaması ve güncel ACK/kanıtla sonuçlanmasıdır.

Codex QA Fabrikası üzerinde çalışırken bu Beyin değişiklikleri ayrı kolda kalır; mevcut PC'ye yazma yetkisi veya sınırsız provider kullanımı gerektirmez.
