# INVENTHOR Main / Organizer — Ortak Çalışma ve Devir Alanı (v1 sözleşmesi)

**Durum: SOURCE_REFERENCE_ONLY.** Bu, mevcut `INVENTHOR Main > Organizer` için bir genişletmedir; ikinci bir Organizer, scheduler, görev kuyruğu, yürütücü veya yapay zekâ beyni oluşturmaz. GitHub deposu kaynak/replika/handoff referansıdır, gerçek zamanlı sistem kaydı değildir. Mevcut `continuity/work_queue.json` ve Main'deki kayıtlar esas alınır; hiçbir kopya sırf GitHub'da yazıyor diye canlı yürütme yetkisi vermez.

## Kullanıcı görünümü (proje proje)

Her proje tek bir proje kimliğine bağlıdır. Ana projeler, modüller ve alt modüller bir ağaçta gösterilir. Proje sayfası şu kısımları sunar:

1. **Amaç ve hedef sonuç:** Sahip talebi, nihai kabul koşulu, mevcut kilometre taşı.
2. **Mimari harita:** Onaylı constitution sürümü, mimari ADR'leri, Inventhor Main/Operator sorumluluk sınırları, modül/alt modül kimlikleri, bağımlılıkları, arayüz slotları, yetenekleri, mevcut ve hedef davranışları, gizlilik ve reklamsızlık kuralları.
3. **Çalışma durumu:** Fikirler, Yapılacaklar, Yarım Kalanlar, Kontrol Bekleyenler, Tamamlananlar; işler PROJECT_ID+TASK_ID ile eşlenir.
4. **Çalışan yapay zekâlar:** Aktif ajan ve rolü, kendi üstlendiği dosya/modül kapsamı, işi üstlenme zamanı, doğrulanmış lease son kullanımı, son canlı heartbeat, erişilebilirlik ve kota durumu. Bekleyen agent'in kendi yazdığı durum, doğrulanmış canlılık değildir.
5. **Kanıt ve değişiklik geçmişi:** Branch, commit, PR, değişen dosya listesi, test raporları, artifacts, kontroller, hata nedeni, kayıtlı olaylar ve geri dönüş planı.
6. **Devir kutusu:** Çalışmayı bırakan ajan, görevi devralabilecek ajan, yapılmış işler, kalınan checkpoint, bir sonraki **tek sonlu adım**, engeller, yeniden yapılmayacaklar, ilgili kapsam, bağımlılıklar ve kalite kontrolü devralacak rol.

Ana kart kısa ve anlaşılırdır. Detay ekranı tüm proje sözleşmesini, iş tarihçesini ve kanıt referanslarını açabilir; her ajana her seferinde uzun konuşma dökümü gönderilmez.

## Çalışma sahipliği, çakışma ve eş zamanlılık

- Main/Organizer System of Record olarak **tek yetkili iş ve lease otoritesidir**. Her görev `PROJECT_ID` + `TASK_ID` + `revision` + `epoch` + `scope_keys` + `owner_agent_id` + `expires_at` tutar; devralma compare-and-swap (CAS) ile atomik olur.
- Kapsam en az `module:<canonical_module_id>` veya `path:<canonical_relative_path>` gibi açık bir alan tanımlar. Aynı modül, aynı dosya veya üst-alt dizinleri paylaşan mutasyon sahiplikleri çakışır; `path:a/b` ile `path:a/bc` çakışmaz. Farklı/ayrık modüllerde işler paralel ilerleyebilir.
- Bir ajan sadece kendi **doğrulanmış lease'i** içindeki dosya/modülleri değiştirebilir. Başka ajanın alanı doluysa otomatik yönlenme / bekleme / salt-okunur inceleme önerilir. Yetkisiz ajan görev sahipliğini veya scope'u değiştiremez.
- Stale/expired/unknown lease, yetki aktarımı değildir. Main önce lease'i ve süren işi uzlaştırır; aktif agent olmadığı kanıtlanmadan devralma yapılmaz. **Mutlak sıfır çakışma garantisi** verilmez; kilit, CAS, versiyon, dosya revizyonu ve mutasyon öncesi doğrulama çakışma riskini sınırlar.
- Agentlerin kendini `DONE`, `BS` veya runtime-verified ilan etmesi yeterli değildir. Bağımsız Quality Factory / trusted host doğrulaması gerekir. Terminal iş tekrar edilmez, yalnız yeni açık takip işi Main tarafından açılabilir.
- Eş zamanlı inceleyici değişen kodu kilitsiz yeniden yazamaz. `REVIEW_PENDING` önceki uygulayıcının değişiklikleri üzerinde test/kanıt incelemesi içindir; düzeltme gerekiyorsa Main ayrı kapsam veya lease geçirir.
- Bir iş başka sağlayıcıya `WAITING_PROVIDER` / `CHECKPOINTED` olarak aktarılırken bir sonraki ajana **yalnız gerekli veri** verilir; sağlayıcı kota dolduğunda işler en ucuz uygun local/sağlayıcı üzerinde planlanabilir, limitler aşılmaz.

## AI/devralma protokolü

1. Main'den onaylı konstitüsyon kimliği ve proje mimari snapshot'ını oku.
2. Projenin mevcut modül envanterini, Work Queue, açık PR/branch, son checkpoint ve handoff'u oku.
3. Exact TASK_ID, sahip, epoch, aktif lease, blocker ve test/evidence durumunu doğrula.
4. Kendi rolünü belirle: `PLANNER`, `IMPLEMENTER`, `REVIEWER`, `TESTER`, `INTEGRATOR` veya `OPERATOR`.
5. Yalnız göreve ait kapsamı ve en küçük sonlu adımı host CAS ile edin. Çakışma varsa başka uygun işe yönlen veya Main'e bildirim gönder.
6. İşlem/checkpoint/patch kanıtını Event Log'a yaz, dosya revizyonu ve artifact hash'i bağla.
7. İkinci ajan kontrol edecekse işi `REVIEW_PENDING` durumuna geçir; hangi testi neden çalıştıracağını belirt.
8. Host gerçekte build/test/UI/integration/teslim doğrulamaları tamamlamadan `DONE` yazma. Başarılı terminal kaydı bir kez yapılır.
9. Kesilme, kota dolması veya kapanmada Handoff Packet ve Checkpoint yaz; yetkiyi kendiliğinden başka ajana atama.
10. Yeni ajan aynı work item'ı **yalnız hostun devralma kararı sonrası** devam ettirir.

## Örnek görünüm

`INVENTHOR_OPERATOR`: hedef = sürekli kullanılabilir Windows gövdesi; mimari = Main beyin / Windows Operator yürütücü. `P0-2` son kayıtlarda kurulumu bekliyor; `P0-3` servis testini bekliyor. GitHub dalındaki iş `SOURCE_IMPLEMENTED` ise bu `PC_DEPLOYED` değildir.

`INVENTHOR_ARCHITECTURE`: reklamsız ürün anayasası kaydı, ref: constitution section 13. Test/uygulama ayrı.

`INVENTHOR_SHARED_ORGANIZER`: bu kaynak referans sözleşmesi; Main canlı kurulumu, kilit atomikliği, mesajlaşma, UI ve çoklu ajan gerçek testi ayrıca gerekli.

## Zorunlu kanıt ve gizlilik

Private chat/history, aile ilişkileri, tokenlar, kişisel yollar, özel dosya içerikleri GitHub'a ham olarak eklenmez. Handoff Packet yalnız güvenli referansları ve yetkilendirilmiş proje kesitini taşır. Başka bir ajanın private veri erişimi otomatik olarak miras alınmaz.

UI ve bildirimler Organizer'ın mevcut durum ve event kanalından türetilir. Saat, agent-online, lease ve provider-quota durumları Main'in güvenilir kanalları tarafından rapor edilmedikçe **UNKNOWN** gösterilir.

**Kabul kapısı:** Gerçek Main/Operator, iki bağımsız ajanla aynı dosyaya çift yazmayı reddetmeli; ayrı modülleri paralel yürütmeli; ağ kopması/codex kotası sonrası checkpoint'i doğru devretmeli; reviewer'ın sonucun hangi testini çalıştıracağını otomatik gösterebilmeli; UI herhangi bir kaynak testini runtime çalışıyor gibi sunmamalıdır.

Komut/evidence sınıfları: `REQUESTED` ≠ `SOURCE_IMPLEMENTED` ≠ `SOURCE_TESTED` ≠ `LOCAL_DEPLOYED` ≠ `END_TO_END_VERIFIED`. 
