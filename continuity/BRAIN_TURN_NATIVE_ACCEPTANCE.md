# INVENTHOR Brain — tek native entegrasyon girişi

Durum: SOURCE_TESTED_ONLY. Bu PR çalışan Main/Organizer veya Operator'da kurulu değildir. Tarih: 2026-10-23.

## Görev akışı

Kaynak dosyası: continuity/brain_turn_integration.py (prepare_brain_turn).

- Mevcut Inventhor.WorkOrganizer.Tool.exe handoff komutu ile tek kanonik görev okunur. Tool executable sahibin onayladığı SHA256 ile yürütmeden önce ve sonra doğrulanır. Bu kontrol Authenticode, Windows ACL ve TOCTOU koruması yerine geçmez.
- Bağımsız native Main/Organizer host aynı görev için kesin task ID, project ID, target, gerçek revision, native timestamp, state, completed/remaining ve evidence bilgisini getirir. Host verify_read_provenance çağrısı gerçek native veritabanı, görev sürümü ve kanonik olay geçmişine dayanır, bir sohbet modeli veya JSON trusted alanı bunu sağlayamaz.
- Native CLI ile native host görev kimliği, durum, tamamlanan/kalan, varsa hedef/proje/aşama ve sonraki işlem verilerinde çelişiyorsa FAIL CLOSED; kaynaklar arasında atomik aynı epoch garantisi ayrıca yerel host kontrolüne muhtaçtır.
- Native host read_focus_snapshot ile owner tarafından onaylı güncel ACTIVE planı, pozitif dispatch bütçesini, tek odak, izinli TASK_ID ve capability setini sağlar. verify_focus_snapshot(attachment, focus, tasks) bu planın aynı kanonik ledger epoch'unda olduğunu, sahibinin izin verdiğini ve görev sahipliği/lease durumunu bağımsız doğrular.
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
