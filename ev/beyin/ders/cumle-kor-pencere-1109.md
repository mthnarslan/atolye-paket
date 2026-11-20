---
tur: ders
aciklama: Asama 3 cozulmeyen cekim koku: recovery dogru videoyu bulur ama pencereyi cumleye bakmadan secer (PINPOINT kapali, recovery.py:204 sentences vermez, bilinen video yeniden aranmaz). Cozum: storyboard+cumle Flash pinpoint (testbench sentence_finder.py)
kaynak: gaia_1108 oturumu 2026-11-09
olusturma: 2026-11-09
guncel: 2026-11-09
yazan: claude
onay: 
etiket: 
---
# cumle-kor-pencere-1109

Belirti: EP03 193 kopekbaligi cumlesi, basliginda shark olan videolardan dalgic/fok/penguen pencereleri; 5 filmde 4-42 cekim REVIEW_REQUIRED, asama 3 saatlerce tekrar turu. Kok: sources.fetch_source_windows cumle yoksa judge_storyboard (genel temiz B-roll) ya da plan_windows ile pencere koyar; PINPOINT=0 (9router YouTube izleyemez); recovery.fetch sentences gecmez; 'known' filtresi havuzdaki videoyu baska pencereden bir daha almaz; arama cekim basina bir kez. Cozum (testbench/gaia_1108/tools/sentence_finder.py): storyboard kareleri (_storyboard_frames/_storyboard_sheets) + cekim cumlesi + visual_goal Flash'a (resim 9router'dan gecer), 'konu gorunsun, aksiyon bonus' istemi; kare -> saniye, pinpoint_windows, _download_windows, pinpoint_check (pinpoint/<id> klasoru onceden acilmali yoksa sample sessizce duser), supplemental manifeste scene_ids ile. Olcum: EP03 193 tek video 10 sn dogru aralik (2:39-2:51); 6 video 43 sn 5 kopekbaligi penceresi; EP04 2 cekim 16 video 92 sn, 19 pencere. Ilk istem ('wanted picture' sart) bos dondu: katiligi gevset. Prod'a: recovery sentences gecsin + storyboard pinpoint PINPOINT yerine (parti bitince).
