---
tur: ders
aciklama: Forumlarda/makalelerde AI arastirma dogrulugu yontemleri: ham metin + birebir alinti, link/alinti denetleyici betik, ucgenleme (>=2 bagimsiz kok), karsi-kanit turu, bulamamaya izin, engelli site yollari; olcum: cok arac cagrisi dogrulugu dusurur
kaynak: https://www.anthropic.com/engineering/multi-agent-research-system ; https://arxiv.org/abs/2604.03173 ; https://arxiv.org/abs/2605.06635 ; https://arxiv.org/abs/2508.07999 ; reddit r/ClaudeAI 1vim8b7
olusturma: 2026-11-17
guncel: 2026-11-17
yazan: claude
onay: 
etiket: ortak,arastirma
---
# arastirma-yontemleri-1117

Kaynaklar 11-17 alt ajan raporu; 3 kritik iddia elle dogrulandi. 1) r/ClaudeAI 1vim8b7 (981 puan, 8 Agu 2026, pullpush ile dogrulandi): WebFetch sayfayi kucuk modelle ozetler, ~30 makalede 17 hata; kritik sayfayi curl/trafilatura ile ham oku, alt ajana 'yalniz alinti + yer, yoksa NOT PRESENT' dedir. 2) Alinti-once kaynak: alinti getirilen sayfada birebir yoksa atif yok; her sayi alintiya bagli (sami-mag07/claude-skill-research-agent, gpt-researcher #1572). 3) URL denetimi: canlilik + Wayback ile uydurma/curume ayrimi (arXiv 2604.03173: 53k URL'de %3-13 uydurma; urlhealth ile cozulmeyen atif <%1). 4) arXiv 2605.06635: link gecerli >=%94 ama olgusal dogruluk %39-77; arac cagrisi 2->150 cikinca dogruluk ~%42 dustu -> daha cok arama != daha dogru. 5) AI-Q 2608.24306: rapor hatalarinin %84.7'si orkestratorde -> ana oturum sentezi de denetlenmeli. 6) WideSearch 2508.07999: tam liste basarisi en iyi sistemde %5 -> liste/kapsam islerinde once kapsama plani (resmi liste, alt kumeler), sonra madde basi tablo, ikinci bagimsiz tarama. 7) Ucgenleme: >=2 bagimsiz kok (ayni basin bulteninin kopyalari = 1 kaynak); 2 turda yeni kaynak cikmazsa dur, 'acik sorular' yaz. 8) Karsi-kanit turu: cevabi curuten en guclu kaynagi ara. 9) Sayi siniri koyma ('top 5' 4 varsa 5.'yi uydurur). 10) Engelli: Reddit api.pullpush.io (yeni threadler gecikmeli), HN Algolia API, GitHub API/raw, arXiv abs/html; reddit.sentinel-team.org ayna DEGIL (tehdit panosu), r.jina.ai ve old.reddit .json 403. Sonraki adim adaylari (yapilmadi): link/alinti denetleyici betik, kaynaklar.json cikti sozlesmesi, bagimsiz dogrulayici ajan.
