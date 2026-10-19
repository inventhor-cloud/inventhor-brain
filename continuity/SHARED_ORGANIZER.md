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

## Salt-okunur kaynak karşılaştırması, TODO döngüsünden bağımsızdır

**Codex kilitlenme düzeltmesi (2026-10-18):** Canlı Main görevi `TODO` durumuna döndüyse bu, başkasının sahipliğini devralma veya bir PR'ı kurma yetkisi değildir. Kaynak `assess_takeover` bunu genel başarısızlık yerine `HOST_MUST_ACTIVATE_TODO_BEFORE_WRITE_LEASE` nedeni ile bildirir. Ana Main host gerçek görev revision/epoch ve izin/scope doğrulamasını yapıp meşru şekilde `READY` durumuna geçirmedikçe **yazma/merge/deploy olmaz**.

Ancak var olan kullanıcının erişme yetkisi bulunan dosyalarının **salt-okunur SHA-256 karşılaştırması**, bir Work Item mutasyonu/lease devri değildir. `advise_read_only_source_comparison` bunun yalnızca kaynak önerisini verir: `may_read_private_files=false`, `may_mutate_files=false`, `may_take_ownership=false`; gerçek dosya okuma hakkını güvenilir yerel host ve kullanıcı izni denetler. Böylece sorunu teşhis etmek için aynı eski sahiplik kaydı art arda yazılmaz.

Yerel Main bir Git deposu değilse Operator PR #3 içindeki `windows/bootstrap/Compare-SourceTriplet.ps1` mevcut yetkili klasör, sabitlenmiş Operator tabanı ve sabitlenmiş PR başı arasında 3-yönlü salt-okunur hash envanteri üretir. Örnek kullanım ve çözüm tablosu `windows/SOURCE_RECONCILIATION_RUNBOOK.md` içinde. Referans: https://github.com/inventhor-cloud/inventhor-operator-core/pull/3 .

**Çakışma sözleşmesi:** Aynı hash = yeniden yapma; yalnız PR değişmiş = aday, yerel değişikliği koru; iki taraf değişmiş = insan/kod incelemesi ve yetkili geçici worktree; herhangi taban/kimlik belirsiz = fail closed. Kaynak aracı hiçbir dosyayı değiştirmez. Karşılaştırma başarmak canlı kurulum/eşitleme kanıtı değildir.


## Yeni fikir/konuşma girdisi için mevcut Main karar katmanı (19 Ekim 2026)

Kanonik Organizer kaydında P0 fikir IDEA_20261010190842_97D94F, mevcut görev TASK_20260923181752_A7FD3C ile ilişkilidir. Bu kayıtlar aynı fikir-hafızası amacını taşıdığından yeni bir ledger veya Organizer oluşturulmaz. shared_organizer.idea_review.advise_idea_intake yalnızca Main tarafından sağlanan proje kayıtları, zaman/revizyon damgalı mevcut Work Items ve ayrı IDEA havuzu ile TEK öneri başlığını karşılaştırır. Çıktı, mevcut IDEA veya TODO'yu gözden geçirmeyi, benzer amacın incelenmesini ya da Main'den yeni IDEA kaydı için yeniden onay alınmasını önerir. Proje kimliği açıkça verilmemişse tahmin yapılmaz; diğer projelerin fikirleri, iş kimlikleri veya içerikleri açığa çıkarılmaz.

Kaynak sınırlaması: mevcut kaynak GitHub dalında yalnızca salt-okunur karşılaştırma mevcuttur; sohbeti gizlice dinlemez, konuşmayı kendi başına yakalamaz, Main üzerinde kayıt yaratmaz veya otomatik TODO/DOING/DONE geçişi yapmaz. Aynı fikir birden çok kanonik kayda düşmüşse sessiz birleştirme yerine belirsizlik bildirir. Eksik IDEA endeksi, eski revizyon, belirsiz proje veya bozuk Work Item endeksi onay sayılmaz. Normalleştirilmiş başlık karşılaştırması gerçek semantik model değildir; benzer başlıklar yalnızca manuel/Main incelemesine gönderilir.

Sonraki entegrasyon adımı: güvenilir Main sohbet/voice ingress'i kullanıcı tarafından seçilmiş proje kimliğiyle tek mevcut Organizer gateway'ine bağlamak, ana depodaki fikir ve görev endekslerini tek revizyonda okumak, kaynak yetkisini denetlemek, revizyon kilitli kayıt/bağlama yapmak, mesaj/konuşma idempotency anahtarı ve çift kayıt/restart testleri eklemek. Yerel P0 görevlerin kaynak CI başarısı, Owner-PC üzerinde canlı fikir yakalama/kaydetme kanıtı değildir.


## Çoklu ajan için çakışmasız iş şeridi önerisi (19 Ekim 2026)

Kanonik P0 görevleri TASK_20260926120200_1F352D (Main Multi-AI Coordinator) ve TASK_20260926120233_104D25 (conflict-aware parallel lanes) aynı Brain alanında kalır. Mevcut shared_organizer.parallel_advice.advise_parallel_lanes bunlara yalnızca salt-okunur kaynak öneri katmanı sunar. Tek-iş advise_next_work denetimlerini her seçimde yeniden kullanır; aynı kaynak/modül yolları çakışan iki işi beraber önermez; ayrı proje kimlikleri altında bile aynı fiziksel yolun çift yazımını önlemeye çalışır. Kullanıcının mevcut Main ayarlarındaki günlük adım ve paralel iş sınırını aşmaz; eşleştirme veya ajan yetkisi üretmez.

Bu bir worker havuzu, gerçek ana scheduler, otomatik görev başlangıcı, maliyet doğuran model çağrısı veya güvenli atomik lease yerine geçmez. Her önerilen görev Main'in mevcut Organizer Work Item durumunda ayrı bir owner+revision+scope CAS lease, preflight, izin ve Quality Factory doğrulaması gerektirir. Devam et komutunda TODO otomatik DOING yapılmaz. Host entegrasyonunda aktif yetki, global dosya kapsamı/alias ve cihaz/provider bütçeleri güvenilir şekilde yeniden denetlenmelidir; GitHub kaynağının CI'sı canlı paralel test değildir.
