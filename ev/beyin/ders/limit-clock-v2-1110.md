---
tur: ders
aciklama: LIMIT CLOCK v2 ornek: referansi kontak sayfa + kare seridiyle incele; konusan maskot = ses RMS'inden agiz, gercek kesit = G-Labs foto + Omni Flash klip, gecis = sert kesim
kaynak: ZeroPulse limit_clock_ornek oturumu 2026-11-10
olusturma: 2026-11-10
guncel: 2026-11-10
yazan: claude
onay: 
etiket: 
---
# limit-clock-v2-1110

v1 reddedildi (maskot duruyor, gercek kesit yok, cizim tarzi ve gecisler zayif). Dogru analiz: videoyu 4 fps 6x4 kontak sayfalara + gecis anlarinda kare seritlerine bol, Flash (ag/gemini-3.8-flash-high, reasoning_effort low) ve kendin ayri oku. GPT gorsel cagrisi (gpt-6.1-sol, VDS 8765) 2 sayfayla bile 504 Gateway Timeout verdi; gorsel analizde Flash kullan. Bulgular: cizim ve gercek kesitlere SERT kesim, grafik ogeleri tek tek 0.25-0.5 sn yumusak belirir, wipe yok; cizimler tek renk mavi-yesil kara murekkep + surekli yavas itme; maskot sagdan yuruyerek girer, 1.5-3 sn'de bir poz degistirir, agzi her karede degisir. Cozumler: (1) agiz = anlatim RMS'i 12 fps 0-3 seviyeye -> lip.js, film zamanina gore agiz elipsi; (2) gercek gorunen kesit = G-Labs nano_banana_pro fotogercekci kare -> omni_flash start_image 4 sn klip (su bardagi temiz cikti), ffmpeg ile soguk ton + -g 1; (3) cizimde 'no text, full bleed' de: nano_banana beyaz panel cercevesi koyabiliyor, kirp; Omni Flash'in hucre klibi asiri zoom + sacma duman yapti, durgun kare + GSAP itme daha iyi; (4) HyperFrames: letterSpacing tween'i lint hatasi (gsap_non_transform_motion), scale kullan. Dosyalar: Kanallar/ZeroPulse/limit_clock_ornek/hf2, tools/gen.py, tools/sfx2.py.
