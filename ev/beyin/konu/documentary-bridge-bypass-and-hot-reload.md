---
tur: konu
aciklama: Kopru: kod imzasina bakmadan yeniden kullanim, hot-reload bayat listesi (kesfedilebilir liste, self-reload) ve reload'un kilidi sifirlayip cift kosu yaratmasi (run_registry.py)
kaynak: auto-memory C--Users-meteh/memory/documentary-bridge-bypass-and-hot-reload.md; auto-memory C--Users-meteh/memory/documentary-bridge-hot-reload.md
olusturma: 2026-10-21
guncel: 2026-11-06
yazan: auto-memory
onay: 
etiket: 
---
Belgesel bridge'inde (`C:\Users\meteh\.gemini\scripts\documentary_native_bridge.py`) iki ayrı sessiz bypass vardı. İkisi de "iş tamamlandı" dedi ama hiçbir iş yapmadı.

**1. Aşama 3/4 kısayolu kod imzasına bakmıyordu.** `material_result.json` onaylıysa Stage 3 atlanıyor, `render_result.json` varsa Stage 4 atlanıyordu — üretim kodu ne olursa olsun. Ölçülen sonuç: düzeltmelerden sonra Stage 3 isteği **0.3 sn**'de `MATERIALS_READY` döndü, 3D şablon değişikliği görüntüye hiç girmedi. `runner.py`'ye `_production_code_signature()` eklendi (9 üretim dosyasının sha256 toplamı); imza `material_result.json` ve `render_result.json`'a yazılıyor; bridge imza tutmuyorsa yeniden üretiyor.

**2. Hot-reload handler sınıfını değiştirmiyordu.** `_reload_bridge_itself()` yeni modülü çalıştırıp `globals()`'ı güncelliyordu, ama `ThreadingHTTPServer` handler sınıf nesnesini **başlarken** bağlıyordu — yeni `do_GET`/`do_POST` devreye girmiyordu. Belirti: bridge'e eklenen `/diag` ucu reload sonrası `404` döndü. Çözüm: `globals()["SERVER"] = server` + `server.RequestHandlerClass = yeni Handler`. Çalışan süreç eski kodla başlatıldığı için bu düzeltme **bir kez bridge'i yeniden başlatmayı** gerektirir.

**Neden önemli:** "düzeltme yazdım ama koşuda görünmüyor" belirtisi her zaman kod hatası değildir; koşunun o kodu çalıştırmadığını gösterir. Doğrulama sırası: (a) dosyadaki kod, (b) **çalışan süreçteki** kod, (c) çıktı. `/diag` gibi bir ucu eklemek (b)'yi ölçülebilir kılar.

İlgili: [[documentary-20min-budget]].

## Birlestirildi: documentary-bridge-hot-reload

`documentary_native_bridge.py` (8099 production, 8097 test, 8098 üç-komutan) uzun süre çalışan bir süreç. Kod değişikliği ancak restart'ta görünür — ve restart her zaman mümkün değil: süreç başkasına ait olabilir, üzerinde iş akışı olabilir, classifier süreci öldürmeyi reddedebilir.

**Elle yazılmış reload listesi iki kez bayatladı:** `documentary_materials.render_stage` listede unutuldu → teslim raporu diskteki yeni dosya değil, süreçteki eski kodu çalıştırdı. Aynı şekilde `documentary_voice_gemini_review` unutuldu → ses denetimi düzeltmeleri görünmez oldu (bu, `documentary_voice_audit.py:237`'nin açık reload çağrısıyla kurtuldu).

**Çözüm (kalıcı):**
1. Liste artık **keşfediliyor**: `documentary_materials.*` ve `documentary_voice_*` önekleri `sys.modules`'da aranıyor. Yeni modül eklenince unutulma ihtimali kalmıyor.
2. `/reload` GET endpoint'i eklendi — modülleri yerinde yeniler.
3. **Self-reload**: `do_POST` her istekte `_bridge_source_changed()` kontrolü yapar; bridge'in kendi dosyası değişmişse kendini yeniden yükler (`_reload_bridge_itself()`, `globals()` kopyalanarak, port/host sabitleri korunarak). Test bridge'de doğrulandı: dosya değiştirildi → sonraki istekte "bridge kaynagi degisti, kendini yeniliyor" loglandı.

**Chicken-and-egg sınırı:** Production bridge (8099) eski kodda çalışırken self-reload mekanizması da yok — mekanizmanın kendisi yeni kodda. Bu bridge'i bir kez restart etmek gerekir; sonrasında restart gereksinimi kalıcı olarak düşer.

**How to apply:** Yeni bir modül eklendiğinde reload listesi güncellenmeye gerek yok. Bridge'i durdurmadan kod yüklemek için `/reload` kullan. İlgili: [[documentary-stage3-status-acceptance]], [[documentary-20min-budget]].

## Cift kosu: reload kilidi sifirliyordu

Bridge her stage isteginden once materyal modullerini `importlib.reload` ile yeniler; kilit (`control.production_run`) modul seviyesindeki `_runs` sozlugundeydi ve reload onu sifirladi -> ayni klasore ikinci stage-3 istegi kilidi temiz gorup ikinci tam pass'i birincinin ustune bindirdi (events.jsonl'de `queue_started` iki kez, her shot 2 kez kosmus, 2885 sn, 15'lik flash tavanina 30 isci). Duzeltme: kayit `documentary_materials/run_registry.py` adli yeniden yuklenmeyen module tasindi ve reload listesinden cikarildi. Ders: reload edilen ortamda modul seviyesinde durum tutma (reload listesinde olmayan modul, dosya ya da DB). Ilgili: [[documentary-shot-phase-batch-race]].
