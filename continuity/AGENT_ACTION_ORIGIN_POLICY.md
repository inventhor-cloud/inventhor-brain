# INVENTHOR ajan eylem kaynağı ve kullanıcı mesajı sınırı

**Durum:** KAYNAK + GitHub testleri. Çalışan Main/Operator'a kurulu değil. Bu dosya canlı oturum geçmişinin geriye dönük kanıtı değildir.

## Neden

Bir kullanıcı tarafından yazıldığı iddia edilen metin ile GPT/Codex/INVENTHOR'un **otomatik ürettiği** bir işlem birbirine karışmamalıdır. Görev bağlamı, sağlayıcı yanıtı, GitHub issue yorumu veya model çıktısı, kullanıcı adına ChatGPT arayüzüne mesaj gönderme yetkisi oluşturmaz.

Geçmiş sohbetlerde kimin mesaj oluşturduğu yalnız ChatGPT hesabının/platformunun denetlenebilir oturum kayıtlarıyla belirlenebilir. Bu kaynak katmanı geçmiş sohbet mesajlarını inceleyemez, kimlik tespiti yapmaz ve bir insanın yazıp yazmadığını iddia etmez.

## Kaynak işlevi

`continuity/agent_action_origin.py` yalnız bir **eylem önerisi** oluşturur ve onu kesin biçimde `AUTOMATED_AGENT` olarak işaretler. Ajan kümesi ilk aşamada yalnız `GPT`, `CODEX`, `INVENTHOR`. Eylemler yalnız `TASK_CONTEXT_READ`, `TASK_ADVICE`, `CHECKPOINT_DRAFT`; hedef yalnız `INTERNAL_ORGANIZER`.

Kabul öncesi gerekenler: gerçek kanonik görev kimliği, owner plan kimliği ve sürümü, gerçek çalışan/oturum, zaman sınırı içinde native gözlem, native kanıt referansı ve bağımsız olarak sağlanan güvenilir host doğrulayıcısı. Yerel native `preflight`, `lease`, `checkpoint` ve `release` yetkileri ayrıca gerekir.

GitHub/Python uygulamasının döndürdüğü `fingerprint` tekrarları ayırt etmek için SHA-256 özetidir; imza, kimlik doğrulama veya native ACK değildir. Öneri her zaman `impersonates_owner=false`, `is_executed=false`, `may_send_chat_message=false`, `is_native_receipt=false` durumundadır.

Dış hedefler, `CHATGPT_USER_MESSAGE`, `CHATGPT_WEB_UI`, `EMAIL`, `WEBHOOK`, `PROVIDER_API`, ödeme, kurulum ve imza bu izinli kümede **yoktur**. Yetkili ürün API entegrasyonu ileride ayrı, açık ve sınırları tanımlı native sözleşmeyle yapılabilir. ChatGPT aboneliği/kullanım limitlerini atlamaya veya kullanıcı kimliğine bürünmeye yönelik arayüz otomasyonu tasarlanmaz.

## Yerel kabul planı

1. Gerçek Main/Organizer host, yalnız owner yetkili görev kayıtlarından NativeActorContext üretir; sahte/AI yazılmış nesneye güvenmez.
2. Native host içinde aktör ve görev/session bağımsız kanıtı doğrulanır. Ajan cevabı bir `verified=true` bayrağına dayanarak kabul edilmez.
3. Görev tavsiyeleri ve devirler ajan/oturum/task/plan sürümüyle etiketlenir; veri gizliliğine aykırı sohbet içeriği, token veya kişisel bilgi kaydedilmez.
4. Sahte oturum, farklı görev, geç kalan onay, taklit edilen owner kimliği, başka hedefe gönderim ve eşzamanlı görev sahipliği **negatif testle** reddedilir.
5. Native Organizer checkpoint/devir denemesi ve kurulu Operator testi tamamlanmadan `INSTALLED` veya `LIVE_VERIFIED` denmez.

Bu değişiklik Codex'in QA Fabrikası geliştirmesinin yerine geçmez, onun dosyalarını değiştirmez ve yeni bir görev kuyruğu oluşturmaz.
