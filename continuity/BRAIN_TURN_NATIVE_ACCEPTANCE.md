# INVENTHOR Brain — tek native entegrasyon girişi

Durum: SOURCE_TESTED_ONLY. Bu PR çalışan Main/Organizer veya Operator'da kurulu değildir. Tarih: 2026-10-23.

## Görev akışı

Kaynak dosyası: continuity/brain_turn_integration.py (prepare_brain_turn).

- Mevcut Inventhor.WorkOrganizer.Tool.exe handoff komutu ile tek kanonik görev okunur. Tool executable sahibin onayladığı SHA256 ile yürütmeden önce ve sonra doğrulanır. Bu kontrol Authenticode, Windows ACL ve TOCTOU koruması yerine geçmez.
- Bağımsız native Main/Organizer host aynı görev için kesin task ID, project ID, target, gerçek revision, native timestamp, state, completed/remaining ve evidence bilgisini getirir. Host verify_read_provenance çağrısı gerçek native veritabanı, görev sürümü ve kanonik olay geçmişine dayanır, bir sohbet modeli veya JSON trusted alanı bunu sağlayamaz.
- Native CLI ile native host görev kimliği, durum, tamamlanan/kalan, varsa hedef/proje/aşama ve sonraki işlem verilerinde çelişiyorsa FAIL CLOSED; kaynaklar arasında atomik aynı epoch garantisi ayrıca yerel host kontrolüne muhtaçtır.
- CLI sürümü `revision` veya `canonical_revision` alanını gösteriyorsa bunlar native Main görev revizyonuyla **tam ve tür güvenli** eşleşmelidir; `True`, `"9"`, `None` gibi taklitler veya çelişen değerler reddedilir. Eski CLI hiç revizyon sunmuyorsa değer uydurulmaz; native host revizyonunun ayrı kontrolü zorunlu kalır.
- Beyin odak planı ve ajan kökenini hazırladıktan sonra aynı native görevi **ikinci kez bağımsız provenance doğrulamasıyla** salt-okunur okur. Başlangıç ve final gözlemlerinde görev/proje/hedef/revizyon/durum/aktif çalışan değişirse öneri reddedilir; ardından aynı native focus/plan kanıtı da yeniden doğrulanır. Bu kontrol yarış penceresini daraltır ancak gerçek atomik Organizer lease ve execution-time preflight yerine geçmez.
- Native host read_focus_snapshot ile owner tarafından onaylı güncel ACTIVE planı, pozitif dispatch bütçesini, tek odak, izinli TASK_ID ve capability setini sağlar. verify_focus_snapshot(attachment, focus, tasks) bu planın aynı kanonik ledger epoch'unda olduğunu, sahibinin izin verdiğini ve görev sahipliği/lease durumunu bağımsız doğrular.
- Provider'a gösterilen özet, kaynak karşılaştırması tamamlandıktan sonra yerel mutlak dosya yollarını, UNC/file bağlantılarını ve sorgu parametreli URL'leri gizler. Kanonik kanıt ve path değerleri Organizer tarafında aynen kalır.
- DONE/ARCHIVED odak görevi için yeni tavsiye üretilmez; aktif sahibi olmayan DOING odak görevi native uzlaştırma yapılmadan ilerletilmez. Bu kaynak koruması gerçek native epoch/lease doğrulamasının yerine geçmez.
- focus_adviser yalnızca sonlu bir TODO için tek iş önerir; DOING task, COMPLETED/PAUSED plan, tükenmiş bütçe ve çelişkili dependency tekrar yürütülmez. Bütün öneriler ADVISORY, asla native claim veya dispatch değil.
- Native read_actor_context ve verify_actor_context üzerinden gerçek GPT/Codex/INVENTHOR worker ve session atfı yapılır. İnsan Owner kimliğine bürünülmez. ChatGPT kullanıcı mesajı ve dışa mesaj gönderme eylemi bu kaynak kapısında kapalıdır.

Çıktı BrainTurnPreparation: BrainReadOnlyAttachment, Advisory, AdvisoryTrace ve ActionOriginProposal. may_claim, may_send_message, may_install ve native_runtime_installed_verified alanlarının hepsi false. Kaynak trace SHA256 gerçek native imza, yetki veya Fabrika QA kabulü değildir.

## Tek mevcut native host'a bağlama

Mevcut .NET Main/Organizer içine, başka bir Beyin/servis/kuyruk üretmeden TrustedMainContextPort ile eşleşen güvenilir adapter uygulanmalı. Atomik native kaydı ve epoch doğrulaması Main'de yapılmalı. Yerel host kodu bilinmeden veya doğrulanmadan port sahte revizyon ve timestamp değerleriyle doldurulamaz.

Bu okuma akışını gerçek görev çalıştırmaya çevirmek ayrı adım gerektirir: mevcut Organizer kilidi altında exact preflight-show/ack/verify, native claim_if_unchanged, yetkili capability kontrolü, gerçek uygulama kanıtı, checkpoint --completed-json --remaining-json ve release. Kesintide sonucu belirsiz işi otomatik yeniden oynatma; uzlaştırma gerekir. İmza, kurulu QA 0.7 tanığı, UAC ve geri alma kapıları ayrı kalır. Codex QA/Studio dosyalarına veya açık native lease'lerine dokunulmaz.

## Yerel kabul protokolü — henüz gerçekleştirilmedi

1. DC bağlantısı elverişli olduğunda bir açık Brain canonical task ve gerçek installed Organizer sürümü/dosyası okunur; QA işi çakışması olmadığından emin olunur.
2. Sahibinin kayıtlı Tool.exe hash, gerçek Authenticode signer, kurulu dosya izinleri ve gerçek Organizer kökü doğrulanır.
3. Native Main host görev kaydını ve onaylı planı aynı güncel epoch'ta doğrular. CLI ile çelişki yoksa READ_ONLY BrainTurnPreparation hazırlanır.
4. Stale tool/revision, değişmiş durum/ilerleme, sahte proje/target, aktif başka worker, orphan DOING, duplicate terminal job, COMPLETED plan, bütçe sıfır, eski oturum, sahte Owner ve dış mesaj denemeleri negatif testten geçer.
5. Sadece yetkili bir finite işte Native preflight, tek claim, gerçek kanıtlı checkpoint, release ve yeniden okuma uygulanır.
6. Canlı Main/Operator ve gerçek QA Factory tanığı onaylanmadan RUNTIME_VERIFIED veya SIGNED_RELEASED bildirilmez.

## Source verification

Run: python3 tools/verify_reference_freshness.py
Run: python3 -m unittest discover -s tests -v

Testler FAKE port ve FAKE CLI sonuçları kullanır, kurulu Windows UI veya canlı dispatch başarısını kanıtlamaz. Değişiklikler PR #6 içinde review-only durumundadır; owner approval ve güvenilir native kurulum olmadan birleştirme veya yayın yapılmamalı.


## 2026-11-02 native kaynak incelemesi — revizyon kimliği ve kesintisiz gözlem

Bilgisayardaki **kurulu ve imzası geçerli** `Inventhor.WorkOrganizer.Tool.exe` üzerinden, sahibi mevcut `work-organizer` kökünde yalnız `handoff --root=... --task=...` komutu ile salt-okunur görev kontrol edildi. Handoff `source=CANONICAL_WORK_ITEMS_AND_EVENTS_READ_ONLY`, `task_count=1` ve `task_id`, `state`, `owner`, `target_id`, `completed`, `remaining`, `dependencies`, `checkpoint_stage` döndürüyor; **`revision` ve `observed_at` alanları bu kurulu CLI sürümünde YOK**. Eksik alanlara yapay revision/timestamp koymak yasak. Kaynak testleri anonim/sentetik görev verisi kullanır; gerçek kimlik, gizli token veya yerel yol kaynak koduna yüklenmez.

Yerel Main'in `Inventhor.Main.Brain/BrainWorkCenter.cs` kaynağı bir `SnapshotId` türetiyor; özet, kayıtların `id|state|updated_at` metninin SHA-256 değeridir. Bu değer **atomik Organizer görev revizyonu değildir**; worker, lease, kanıt, bağımlılık ve checkpoint değiştiğinde güncel kalacağı garanti değildir. `CoreBrainReview.native_revision` ve güvenilir Main portundaki `read_exact().revision` yalnız gerçekten yetkili native Organizer epoch/lease kaydından gelmelidir; Main görünüm özeti ile değiştirilemez.

Source-only Brain portu iki salt-okunur native gözlem arasında `task_id`, `project_id`, `target_id`, `revision`, `state` ve aktif çalışanı tekrar doğrular. Ek olarak `native_task_state_sha256` ile güvenilir native portun **ham** `stage`, `completed`, `remaining`, `evidence_refs`, `blocker`, `next_action` ve doğrulanmış `dependency_states` değerleri karşılaştırılır; sağlayıcıya yansıyan gizlenmiş/metin maskelenmiş alanlar bu kontrolün yerine kullanılamaz. Final gözlem zamanının ilk gözlemden eski olması reddedilir. Bu hash **imza veya yetki değildir**, gerçek Main'in atomik işlem öncesi revizyon ve lease karşılaştırması yine zorunludur.

Canlı kabul için mevcut Main/.NET adapter şu sırayı kendi native Organizer kilidi içinde kanıtlamalı: tam görev/proje/target ve revizyon okuma → owner/worker/lease karşılaştırma → bağımlılıkların güncel DONE kanıtı → preflight-show/ack/verify → atomik claim → gerçek Operator sonuç ACK + kanıt → checkpoint ve release. Bu koşullar olmadan GitHub'daki başarılı kaynak CI, kurulmuş beyin, canlı Fabrika veya temizlik tamamlandı iddiası değildir. Codex ile çakışan mevcut PC source dosyaları, çalışan servisler ve kurulu modüller bu source turunda değiştirilmemiştir.


## Native eşzamanlılık sınırı: Organizer TaskSnapshotHash ≠ revizyon

Bilgisayardaki **mevcut** `Inventhor/work-organizer/runtime/ScriptlessPreflight.cs` kaynak kodu, `TaskSnapshotHash` için yalnızca şu alanları kullanıyor: `id, state, target_id, acceptance, next_action, summary, depends_on, updated_at`. Bu içerik özeti, `owner`, `active_worker`, `active_session`, `lease_expires_at`, sonuç kanıtları ve tüm Fabrika checkpoint zincirini kapsamaz. Öte yandan Main `BrainWorkCenter.SnapshotId` ise yalnız `id|state|updated_at` özetidir. Bu iki hash **görev revizyonu, yetki belgesi veya atomik ledger epoch değildir**. Bunları `NativeEpochScope.task_revision` ya da tek başına `verify_canonical_epoch=True` kanıtı olarak kabul etmek yasaktır.

Beyin'in bu PR'deki `TrustedMainContextPort.verify_canonical_epoch(CanonicalEpochScope)` yöntemi mevcut kurulu Main'de henüz uygulanmadı. Kaynak davranışı: yöntem yoksa/istisna verirse veya gerçek `True` döndürmezse görev tavsiyesi **fail-closed** olur. `CanonicalEpochScope` tam TASK_ID, project, target, görevin native revizyonu, ham kanonik kayıt özeti, plan ID+revizyon, çalışan ID ve gerçek ajan oturumu kimliğini aynı doğrulamaya taşır. Bu veri **istek** niteliğindedir; bilgisayardan doğrulama yapılmadan kabul makbuzu değildir.

Main için uygulanacak tek güvenilir yol: orijinal `OrganizerStore.Locked` kilidinde, **güncel** `WORK_ITEMS.jsonl` + `EVENTS.jsonl` ve kanonik owner plan/lease/session kayıtlarından tüm scope'u tek tutarlı işlem içinde karşılaştırmak. `ScriptlessPreflight.RequireActiveLease` ve `preflight-show/ack/verify` kuralları gerçek yazma ve native sonuç kabul aşamasında ayrıca korunmalı. Eğer orijinal Organizer **monotonik revizyon** tutmuyorsa `updated_at` veya hash'e revizyon adı vermek yerine, gerçek Organizer kaynağına sürümlü ve atomik kayıt desteği tasarlanmalı, migrasyon/rollback gerçek yerel Fabrika testinden geçmeli. Bu işi farklı bir Main, paralel kuyruk veya ikinci Organizer oluşturmakla çözmeyin.

İlk salt-okunur kimlik köprüsünde native `owner` **görev atamasıdır**, `active_worker` ise **yürütme lease sahibidir**. Aynı değere zorla eşitlenmezler. CLI `owner` alanı sağlıyorsa Main'in bağımsız okumasındaki `owner` ile çelişki **reddedilir**; her iki native gözlem arasında atama değişirse ham kayıt SHA-256 denetimi hata verir. İsim ve özel kaynak dizeleri sağlayıcıya açık JSON'a kopyalanmaz, yalnız atomik host karşılaştırmasında tutulur.

**Yerel kurulum durumu:** Buradaki tüm Python kontrolleri SOURCE_ONLY. İmzalı native `Tool.exe` ile read-only `handoff` yapılabilmesi, Main için gerekli atomik task-plan-worker epoch doğrulamasının kurulduğu anlamına gelmez. Codex'in özgün PC dosyaları, çalışan hizmetler, kanonik görev ve kurulu QA değiştirilmedi.
