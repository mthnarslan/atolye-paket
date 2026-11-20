---
tur: ders
aciklama: Belgesel S1 ses hakemi+factcheck 9router'a gidiyordu (503): ses denetimi UNVERIFIED -> film S3'e gecmez; gemweb yamasi testbench/doc_gemweb_s1_1118
kaynak: testbench/doc_gemweb_s1_1118/RAPOR.md
olusturma: 2026-11-18
guncel: 2026-11-18
yazan: claude
onay: 
etiket: ortak
---
# belgesel-s1-9router-kirik-1118

11-18: documentary_voice_gateway.json 9router :20128 503 veriyor. documentary_voice_gemini_review.py 503'te UNVERIFIED -> voice_audit next_step_allowed False -> runner.py:5757/6227 ValueError, film durur. factcheck hatayi yutar. Yama (gemweb hydrogen high, _gemweb_heard_guard: hydrogen sessiz wav'a PASS verip istemden alinti uyduruyor, guard alintilari ASR ile karsilastirir) testbench/doc_gemweb_s1_1118/patched; prod'a A/B sonrasi. Ayrica voice_engine.py:266 model_receipt MODEL_ALIASES gemweb adini reddedebilir.
