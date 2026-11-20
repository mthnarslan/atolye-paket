"""Yazim sonrasi metin denetimi (tum kanallar). Hakem degil, ALARM: cikan her uyari elle bakilir.
Kullanim:
  python ortak/metin_denetle.py metin.md [--dil en|tr|de|es|pt|fr|ja|ko] [--bilgi bilgi.md] [--json out.json]
  - metin: "**VO:**" satirlari varsa yalniz onlar okunur, yoksa tum metin.
  - --onceki a.md b.md c.md: kanalin onceki bolumleriyle sablon tekrari (ortak 4'lu kalip, ayni acilis/kapanis/cumle basi); insan 8 dil 0-2, LimitClock ep04/05 19-23.
  - --bilgi: bilgi/iddia tablosu; verilirse gemweb (hydrogen low) tabloda olmayan iddia ADAYLARINI listeler.
  - --dilbilgisi: gemweb artikel/hal/sayi/ceviri hatasi adaylari (18 Kas: DE cinsiyet 2/2, TR 'nokta' 2/2 yakaladi; 'das Koppel' 0/2; ES/PT/FR/JA/KO 5 bilinen hatanin 10 denemesinde 4, KO kod okunusu onerileri uydurma).
Olculenler (esikler testbench/metin_kural_1118/rapor.md + dil_test/):
  ritim CV < CV_ESIK[dil], ayni acilis kelimesi >%20 (insan en cok %19, YZ %21-26), klise/dolgu kaliplari (dile gore),
  mekanik ozet kapanis (8 dil), soylenen ondalik (TR nokta, ES punto, PT ponto, FR point), DE/PT/FR '2.9' ondalik,
  EN disi dillerde Ingilizce kelime sizintisi, JA/KO kibar/duz cumle sonu karismasi.
  TTS riski (rakam, kisaltma, sembol, kod, TR buyuk I) yalniz not, cikis kodunu etkilemez.
Cikis: 0 = uyari yok, 1 = uyari var (bakilacak), 2 = girdi hatasi.
"""
import argparse, collections as C, json, re, statistics as st, sys
from pathlib import Path

KLISE = {
    "en": [r"\bdelv(e|es|ing)\b", r"\btapestry\b", r"\btestament\b", r"\bcrucial\b", r"\bpivotal\b", r"\brealm\b",
           r"\bgame-changer\b", r"\bmoreover\b", r"\bfurthermore\b", r"\bbuckle up\b", r"\blet that sink in\b",
           r"\bhere's the thing\b", r"\bhere's where it gets interesting\b", r"\bquietly\b", r"\bamid\b", r"\bnestled\b",
           r"\btoolkit\b", r"\blandscape\b", r"\bnavigat(e|es|ing)\b", r"\bunlock(s|ing)?\b", r"\bseamless(ly)?\b",
           r"\boverarching\b", r"\band that matters\b", r"\bthat's the point\b", r"\btells? a clear story\b",
           r"(?:^|(?<=[.!?]\s))(Honestly|The catch|The result|The twist|The kicker|Spoiler)\?",
           r"\b(it's|it is|this is|that's) not\b[^.!?]{1,40}[,;—-]\s*(it's|it is|this is|that's)\b",
           r"\bnot just\b[^.!?]{1,40}\bbut\b", r"\bthroughout history\b", r"\bhave you ever wondered\b", r"^imagine\b"],
    "tr": [r"\bpeki ama\b", r"\bi[sş]te tam burada\b", r"\bson derece\b", r"\bb[uü]y[uü]leyici\b", r"\bdikkat [cç]ekici\b",
           r"\bgelin birlikte\b", r"\bunutmamak gerekir ki\b", r"\bunutmay[ıi]n ki\b", r"\bsadece\b[^.!?]{1,40}\bde[gğ]il,? ayn[ıi] zamanda\b",
           r"\b[oö]te yandan\b", r"\boldukça\b", r"\b(sadece|yaln[ıi]zca)\b[^.!?]{1,40}\bkalma[zy]",r"\bk[ıi]sacas[ıi]\b", r"\bsonu[cç] olarak\b", r"\ba[cç][ıi]k konu[sş]ay[ıi]m\b",
           r"\bkritik bir rol\b", r"\b[oö]nemli bir rol oynamaktad[ıi]r\b", r"\bke[sş]fedelim\b", r"\bderinlemesine\b",
           r"\btarih boyunca\b", r"\bhi[cç] merak ettiniz mi\b", r"^hayal edin\b"],
    "de": [r"\beintauchen\b", r"\btauchen wir\b", r"\bfacettenreich\w*\b", r"\bes ist wichtig zu beachten\b",
           r"\bin der heutigen schnelllebigen welt\b", r"\bnicht nur\b[^.!?]{1,50}\bsondern auch\b", r"\bzusammenfassend\b",
           r"\bspannende reise\b", r"\bim folgenden\b", r"\bletztendlich\b", r"\bentscheidende rolle\b",
           r"\bim laufe der geschichte\b", r"\bhaben sie sich (jemals|schon einmal) gefragt\b", r"^stell(en sie)? sich vor\b"],
    # ES/PT/FR/JA: olcumsuz listeler (blog/README, testbench/metin_kural_1118/dil_arastirma2.md) + 18 Kas uretim testi; yalniz uyari.
    # KO: patina lift tablosu (2026-07-02) olculu; 핵심/생태계/패러다임 dusuk lift -> listede yok.
    "es": [r"\bno (es|son) (solo|s[oó]lo|solamente)\b[^.!?]{1,50}\bsino\b", r"\badem[aá]s\b", r"\bpor otro lado\b",
           r"\bes importante (destacar|se[nñ]alar|mencionar|tener en cuenta)\b", r"\ba lo largo de la historia\b",
           r"\bjuega un papel (crucial|fundamental|clave)\b", r"\bsumerg[a-z]+\b", r"\b[¿]?alguna vez te has preguntado\b", r"^imagina\b"],
    "pt": [r"\bn[aã]o (é|s[aã]o) (s[oó]|apenas|somente)\b[^.!?]{1,50}\b(mas|e sim)\b", r"\bal[eé]m disso\b", r"\bpor outro lado\b",
           r"\b[eé] importante (destacar|ressaltar|notar|lembrar)\b", r"\bao longo da hist[oó]ria\b",
           r"\bdesempenha um papel (crucial|fundamental)\b", r"\bmergulh[a-z]+\b", r"\bj[aá] se perguntou\b", r"^imagine\b"],
    "fr": [r"\bnon seulement\b[^.!?]{1,50}\bmais (aussi|[eé]galement)\b", r"\bde plus\b", r"\bpar ailleurs\b",
           r"\bil est important de (noter|souligner)\b", r"\bau fil de l'histoire\b", r"\bjoue un r[oô]le (crucial|cl[eé]|essentiel)\b",
           r"\bplong[a-z]+ dans\b", r"\bvoici ce qu", r"\bvous [eê]tes-vous d[eé]j[aà] demand[eé]\b", r"^imaginez\b"],
    "ja": [r"まとめると", r"結論として", r"要するに", r"重要なのは", r"注目すべきは", r"特筆すべきは", r"と言えるでしょう",
           r"が求められます", r"することが重要です", r"重要な役割を果たし", r"単なる.{1,12}ではなく", r"欠かせない存在"],
    "ko": [r"결론적으로", r"이를 통해", r"^또한,", r"중요한 역할을", r"더 나아가", r"필요가 있습니다", r"라고 할 수 있습니다",
           r"영향을 미칩니다", r"가능성이 큽니다", r"있으며, 이는", r"\S+[이가] 아니라 \S+"],
}
KANCA = {  # son 4 cumlede sonraki-bolum kancasi (testbench/benzerlik_1114/arac/ag.py KANCA)
    "en": r"\bnext (time|on|week|episode|video)\b|\bin the next (video|episode|part)\b|\bnext,? we\b",
    "es": r"\bpr[oó]xim[oa] (vez|episodio|video|cap[ií]tulo)\b|\ben el pr[oó]ximo\b",
    "pt": r"\bpr[oó]xim[oa] (vez|epis[oó]dio|v[ií]deo)\b|\bno pr[oó]ximo\b",
    "fr": r"\bla prochaine fois\b|\bprochain (épisode|episode|vid[ée]o)\b",
    "de": r"\bn[aä]chstes mal\b|\bn[aä]chste[nr]? (folge|episode|video)\b",
    "tr": r"\bbir sonraki (b[oö]l[uü]m|video)\b|\bgelecek (b[oö]l[uü]m|hafta)\b|\bsonraki b[oö]l[uü]mde\b",
}
KAPANIS = {
    "en": r"^(in the end|ultimately|in summary|to sum up|in conclusion|put (the two|them|it all) side by side|so,? in short|at the end of the day)\b|\bthe trade-offs are\b",
    "tr": r"^(sonu[cç] olarak|k[ıi]sacas[ıi]|[oö]zetle|velhas[ıi]l|g[oö]r[uü]ld[uü][gğ][uü] gibi)\b|\btam olarak (bu|budur)\b",
    "de": r"^(zusammenfassend|letztendlich|abschlie[sß]end|alles in allem|kurz gesagt|fazit|unterm strich)\b",
    # ES/PT/FR/JA/KO: 18 Kas uretim testinde 10 metnin 9'u bunlarla kapandi (dil_test/SONUC.md)
    "es": r"^(al final|en definitiva|en resumen|en conclusi[oó]n|en pocas palabras|as[ií])\b",
    "pt": r"^(no fim( das contas)?|em resumo|em suma|resumindo|colocando tudo lado a lado|enfim)\b|\bmostrando como\b",
    "fr": r"^(au final|en fin de compte|en r[ée]sum[ée]|en somme|bref|finalement|entre .{3,60}, chaque)\b|^deux \w+, deux\b",
    "ja": r"^(このように|以上のように|まとめると|結局|つまり)",
    "ko": r"^(결국|요컨대|정리하면|이처럼|이렇게)|(단적으로|분명하게|여실히) 보여[줍주]|드러납니다\.?$",
}
# ritim esigi dile gore (insan Kurzgesagt EN 0,55-0,61 / DE ceviri 0,52-0,84 / TR ceviri 0,46-0,64;
# YZ EN 0,41-0,53, DE 0,33-0,47, TR 0,41-0,43). TR esigi az veriyle: n=4 insan, 2 YZ.
# 18 Kas trend dilleri (yalniz noktalamasi duzgun insan altyazisi): PT insan 0,48 / YZ 0,27-0,31; FR insan 0,56-1,02 / YZ 0,42-0,43;
# JA insan 0,64 (n=1) / YZ 0,42-0,43; KO insan 0,49-0,62 / YZ 0,44-0,50; ES insan 0,50 (n=1) / YZ 0,48-0,53 -> ayrismiyor, esik yok.
CV_ESIK = {"en": 0.50, "de": 0.50, "tr": 0.45, "pt": 0.40, "fr": 0.50, "ja": 0.50, "ko": 0.47, "es": 0.0}
# Ingilizce islev kelimeleri DE/TR metinde gorunurse dil karismasi
EN_SIZINTI = r"\b(the|and|of|with|which|is|are|this|that|for|from|but|just|actually|however)\b"
SAYI_TR = r"\b(s[ıi]f[ıi]r|bir|iki|[uü][cç]|d[oö]rt|be[sş]|alt[ıi]|yedi|sekiz|dokuz|on)\s+nokta\s+\w+"
DILBILGISI_ISTEM = (
    "Asagidaki {dil} seslendirme metnini anadili {dil} olan bir editor gibi oku. YALNIZ kesin dil hatalarini bul: "
    "isim cinsiyeti/artikel, hal eki, cekim, uyum, yanlis ondalik/sayi soyleyisi, Ingilizceden birebir ceviri kokan ve "
    "anadilde kimsenin kurmayacagi ifade, baska dilden sizan kelime. Uslup, ritim, icerik dogrulugu hata DEGILDIR. "
    "Emin degilsen yazma. Yalniz JSON: {{\"hatalar\":[{{\"alinti\":\"<metinden birebir>\",\"tur\":\"...\",\"duzeltme\":\"...\"}}]}}. "
    "Yoksa bos liste.\n\nMETIN:\n{metin}")
DIL_ADI = {"en": "English", "de": "Deutsch", "tr": "Turkce", "es": "Espanol", "pt": "Portugues (Brasil)",
           "fr": "Francais", "ja": "Japanese (日本語)", "ko": "Korean (한국어)"}
# ondalik: bu dillerde virgul; sesli yazimda 'punto/ponto/point' Ingilizce kalibi
_ES = r"(cero|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez)"
_PT = r"(zero|um|uma|dois|duas|tr[eê]s|quatro|cinco|seis|sete|oito|nove|dez)"
_FR = r"(z[eé]ro|un|une|deux|trois|quatre|cinq|six|sept|huit|neuf|dix)"
ONDALIK_SOZ = {"es": rf"\b{_ES} punto {_ES}\b", "pt": rf"\b{_PT} ponto {_PT}\b", "fr": rf"\b{_FR} point {_FR}\b"}
# JA/KO hitap duzeyi (cumle sonu). Insan: JA Kurzgesagt da/dearu 68/85, desu-masu 2; KO hamnida ~%68 + yo/jyo ~%28 dogal, duz -da ~%4.
USLUP = {"ja": [("kibar", r"(です|ます|ました|でした|ません|でしょう|ください|ましょう)(か|ね|よ)?$"),
                ("duz", r"(だ|である|だろう|だった|ない|なかった|た|る|う|い)(か|ね|よ|の)?$")],
         "ko": [("kibar", r"(니다|니까|요|죠)$"), ("duz", r"(?<!니)다$")]}
# sirali gecis (ilk/sonra/son olarak): 18 Kas insan 33 metin <=3.6/100 cumle, YZ v1 ES/PT/FR/JA/KO 3.8-14.3
SIRA = {"en": r"^(first(ly)?|first up|next|then|finally|lastly|let's start|to begin|moving on)",
        "tr": r"^(önce|ilk olarak|öncelikle|ardından|son olarak|şimdi de|gelelim)",
        "de": r"^(zuerst|zunächst|als nächstes|danach|schließlich|zum schluss|beginnen wir|kommen wir)",
        "es": r"^(empecemos|empezamos|primero|en primer lugar|a continuación|por último|finalmente|si pasamos|pasemos)",
        "pt": r"^(começando|comecemos|primeiro|em primeiro lugar|em seguida|por fim|finalmente|passando)",
        "fr": r"^(commençons|d'abord|tout d'abord|ensuite|enfin|passons|regardons d'abord)",
        "ja": r"^(まず|次に|続いて|最後に)", "ko": r"^(먼저|다음은|다음으로|이어서|마지막으로|우선)"}
HARF =r"[^\W\d_]+(?:['’-][^\W\d_]+)*|\d+(?:[.,]\d+)*"


def vo_satirlari(t):
    L = [m.group(1).replace("**", "") for m in re.finditer(r"^\*\*VO:\*\*\s*(.*)$", t, re.M) if not m.group(1).startswith("(")]
    return L if L else [p for p in re.split(r"\n\s*\n", t) if p.strip() and not p.lstrip().startswith("#")]


def cumleler(t):
    t = re.sub(r"(\.\.\.|…)\s*(\.\.\.|…)", " ", t)  # altyazi devam isareti "... ..." cumle sonu degil
    t = re.sub(r"\b(U\.S\.|z\.B\.|d\.h\.|bzw\.|vs\.|örn\.|vb\.)", lambda m: m.group(0).replace(".", ""), t)
    return [s.strip() for s in re.split(r"(?<=[.!?…])\s+|(?<=[。！？])\s*", t) if s.strip()]


def kelimeler(s):
    return re.findall(HARF, s)


def uzunluk(s, dil):
    """cumle uzunlugu: JA bosluksuz yazilir -> harf (kana/kanji/latin) sayisi; diger diller kelime."""
    return len(re.findall(r"[\w]", s)) if dil == "ja" else len(kelimeler(s))


def uydurma_adaylari(S, bilgi):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import gemweb
    num = "\n".join(f"{i+1}. {s}" for i, s in enumerate(S))
    istem = ("Asagida bir BILGI TABLOSU ve numarali METIN cumleleri var. Gorev: tabloda DAYANAGI OLMAYAN olgu iddiasi "
             "(sayi, tarih, isim, yetenek, sebep, karsilastirma, tarihsel bilgi) iceren cumleleri bul. Benzetme, his, soru, "
             "izleyiciye hitap ve tablodaki bilginin yeniden soylenmesi iddia DEGILDIR; tablodan dogrudan cikan basit hesap da degildir. "
             "Yalniz JSON dondur: {\"adaylar\":[{\"no\":<cumle no>,\"iddia\":\"<tabloda olmayan kisim, birebir>\"}]}. Yoksa bos liste.\n\n"
             f"BILGI TABLOSU:\n{bilgi}\n\nMETIN:\n{num}")
    r = gemweb.sor_json(istem, zaman=300, deneme=2)
    return r.get("adaylar", []) if isinstance(r, dict) else []


def denetle(t, dil, bilgi=None, dilbilgisi=False, onceki=None):
    vo = vo_satirlari(t)
    S = [s for v in vo for s in cumleler(v)]
    if not S:
        raise ValueError("metinde cumle yok")
    L = [uzunluk(s, dil) for s in S]
    toplam = sum(L)
    out = {"dil": dil, "cumle": len(S), "kelime": toplam, "uyarilar": []}
    U = out["uyarilar"]
    cv = st.pstdev(L) / st.mean(L)
    out["ritim"] = {"cv": round(cv, 2), "kisa_<=4_yuzde": round(100 * sum(x <= 4 for x in L) / len(L)),
                    "ort": round(st.mean(L), 1), "en_uzun": max(L)}
    if len(S) < 15:
        out["ritim"]["not"] = "15 cumleden az: CV guvenilmez, alarm verilmedi"
    elif cv < CV_ESIK.get(dil, 0.50):
        U.append(f"RITIM: CV {cv:.2f} < {CV_ESIK.get(dil, 0.50)} (cumle uzunluklari cok esit). Dusunceye gore kisa/uzun cumle kur; bos kisa cumle ekleme.")
    ac = C.Counter(kelimeler(s)[0].lower() for s in S if kelimeler(s))
    k, v = ac.most_common(1)[0]
    out["ritim"]["en_sik_acilis"] = f"{k} %{round(100 * v / len(S))}"
    if dil != "ja" and len(S) >= 10 and v / len(S) > 0.20:  # JA bosluksuz: ilk 'kelime' butun cumle
        U.append(f"ACILIS: cumlelerin %{round(100 * v / len(S))}'i '{k}' ile basliyor (>%20).")
    kl = []
    for pat in KLISE.get(dil, []):
        for s in S:
            for m in re.finditer(pat, s, re.I | re.M):
                kl.append((m.group(0), s[:90]))
    out["klise"] = [{"kalip": a, "cumle": b} for a, b in kl]
    farkli = len({a.lower() for a, _ in kl})
    if farkli >= 3 or (toplam and 1000 * len(kl) / toplam >= 6):
        U.append(f"KLISE: {len(kl)} eslesme, {farkli} farkli kalip. Tek kelime kanit degil; bir aradaysa o cumleleri sade fiille yeniden yaz.")
    sr = [x[:40] for x in S if re.search(SIRA.get(dil, "$^"), x.strip(" «“\"'"), re.I)]
    if len(sr) >= 2 and 100 * len(sr) / len(S) >= 5:
        U.append(f"SIRALAMA: {len(sr)} cumle 'once/sonra/son olarak' diye aciliyor (insan <=3.6/100): {sr[:3]}. "
                 "Metin bilgi listesini sirayla okuyor; yapiyi soru/olay uzerine kur, liste gecisini sil.")
    son = cumleler(vo[-1]) if vo else []
    kap = [s for s in son if re.search(KAPANIS.get(dil, "$^"), s, re.I)]
    if kap:
        U.append(f"KAPANIS: son bolumde mekanik ozet kalibi: '{kap[0][:80]}'. Ozet yerine son yeni bilgi ya da acik soru.")
    kn = [s for s in S[-4:] if re.search(KANCA.get(dil, "$^"), s, re.I)]
    if kn:  # 11-19 benzerlik: bizde 15/31 video, 5/9 kanal; insanda 0/22 (ag izi)
        U.append(f"KANCA: kapanista 'next time/sonraki bolum' kancasi: '{kn[0][:80]}'. Kanallar arasi ortak sablon izi; filmi kendi olayiyla bitir.")
    if dil == "tr":
        nk = [m.group(0) for s in S for m in re.finditer(SAYI_TR, s, re.I)]
        if nk:
            U.append(f"SAYI: Turkcede ondalik 'virgul' okunur; 'nokta' Ingilizce kalibi: {', '.join(nk[:5])}")
    if dil == "de":
        nk = [m.group(0) for s in S for m in re.finditer(r"\b\d+\.\d{1,2}\b", s)]
        if nk:
            U.append(f"SAYI: Almancada ondalik virgul (2,9); nokta binlik ayiricidir: {', '.join(nk[:5])}")
    if dil in ("es", "pt", "fr"):
        # ES'de RAE noktayi da kabul eder (Meksika vb.) -> yalniz PT/FR rakam kontrolu
        nk = [m.group(0) for s in S for m in re.finditer(r"\b\d+\.\d{1,2}\b", s)] if dil != "es" else []
        nk += [m.group(0) for s in S for m in re.finditer(ONDALIK_SOZ[dil], s, re.I)]
        if nk:
            U.append(f"SAYI: {dil} ondalik virgulle (2,9 / 'coma, virgula, virgule'): {', '.join(nk[:5])}")
    if dil in USLUP:
        c = C.Counter()
        for s in S:
            s2 = re.sub(r"[\s。！？.!?…」』）)]+$", "", s)
            c[next((ad for ad, p in USLUP[dil] if re.search(p, s2)), "diger")] += 1
        out["uslup"] = dict(c)
        az = min(c["kibar"], c["duz"])
        if az >= 2 and az / len(S) > 0.10:
            U.append(f"USLUP: kibar ({c['kibar']}) ve duz ({c['duz']}) cumle sonu karisik. Kanal profilindeki tek duzeyi kullan.")
    if dil != "en":  # yerli kelimeyle cakisan: FR 'but' (hedef), PT 'for' (se for)
        yerli = {"fr": {"but"}, "pt": {"for"}}.get(dil, set())
        sz = [m.group(0) for s in S for m in re.finditer(EN_SIZINTI, s, re.I) if m.group(0).lower() not in yerli]
        if len(sz) >= 2:
            U.append(f"KARISMA: {dil} metinde Ingilizce kelime: {', '.join(sorted({x.lower() for x in sz})[:8])}")
    tts = C.OrderedDict()
    for s in S:
        for m in re.finditer(r"\d+(?:[.,]\d+)*", s): tts.setdefault("rakam", []).append(m.group(0))
        for m in re.finditer(r"\b[A-ZÄÖÜÇĞİŞ]{2,}\b", s): tts.setdefault("kisaltma", []).append(m.group(0))
        for m in re.finditer(r"[%$€£&/§°]", s): tts.setdefault("sembol", []).append(m.group(0))
        for m in re.finditer(r"\b\w*\d\w*-\w+|\b[A-Z]+-\d+\w*", s): tts.setdefault("kod", []).append(m.group(0))
    out["tts"] = {k: sorted(set(v)) for k, v in tts.items()}
    out["notlar"] = []
    if dil == "tr" and re.search(r"\b(?=[A-ZÇĞİÖŞÜ]{2,}\b)[A-ZÇĞİÖŞÜ]*I|(?<!\w)I (?=[A-Z]\b)", " ".join(S)):
        out["notlar"].append("TTS-TR: buyuk 'I' Turkce seste 'ı' okunabilir (IHPS -> 'ıhps'); kisaltmayi okunusla yaz (ay-eyc-pi-es).")
    if tts:
        out["notlar"].append("TTS: " + "; ".join(f"{k}: {', '.join(sorted(set(v))[:8])}" for k, v in tts.items())
                 + ". Sesin nasil okudugunu gercek TTS ile dinle; gerekirse yaziyla yaz.")
    if dilbilgisi:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        import gemweb
        r = gemweb.sor_json(DILBILGISI_ISTEM.format(dil=DIL_ADI.get(dil, dil), metin="\n".join(vo)), zaman=300, deneme=2)
        out["dilbilgisi"] = r.get("hatalar", []) if isinstance(r, dict) else []
        for h in out["dilbilgisi"]:
            U.append(f"DILBILGISI ADAYI (elle bak): '{h.get('alinti', '')}' -> '{h.get('duzeltme', '')}' ({h.get('tur', '')})")
    if bilgi:
        ad = uydurma_adaylari(S, bilgi)
        out["uydurma_adaylari"] = ad
        for a in ad:
            n = a.get("no")
            cum = S[n - 1][:100] if isinstance(n, int) and 0 < n <= len(S) else "?"
            U.append(f"UYDURMA ADAYI (elle bak): #{n} '{a.get('iddia', '')}' <- {cum}")
    if onceki:
        k = onceki_kiyas(t, dil, onceki); out["onceki"] = k
        # 18 Kas kalibrasyon (onceki 3 bolum): insan 8 dil x 4 video ngram<=2, cumle basi 0, acilis/kapanis 0;
        # LimitClock ep04/05 ngram 19-23, cumle basi 6, kapanis 2-3
        if k["ortak_ngram_n"] >= 5 or len(k["tekrar_cumle_basi"]) >= 3 or k["ayni_acilis"] or k["ayni_kapanis"] or k["soru_kapanis_tekrar"]:
            U.append(f"SABLON: onceki {k['onceki_n']} bolumle ortak kalip {k['ortak_ngram_n']} (insan <=2), tekrar cumle basi "
                     f"{len(k['tekrar_cumle_basi'])} {k['tekrar_cumle_basi'][:4]}, ayni acilis {len(k['ayni_acilis'])}, ayni kapanis {len(k['ayni_kapanis'])}, soru kapanisi tekrar {k['soru_kapanis_tekrar']}. "
                     f"Ornek: {k['ortak_ngram'][:4]}. Acilis/kapanis/gecisleri bu bolumun icerigine gore yeniden kur.")
    return out


def onceki_oku(p):
    """onceki bolum: .json (lines / segments[].text) ya da VO/duz metin"""
    t = Path(p).read_text(encoding="utf-8")
    if p.endswith(".json"):
        d = json.loads(t)
        L = d.get("lines") or [s.get("text", "") for s in d.get("segments", [])] if isinstance(d, dict) else d
        return "\n\n".join(x for x in L if isinstance(x, str))
    return re.sub(r"^# sure.*\n", "", t)


def _ngram(S, dil, n=4):
    if dil == "ja":  # bosluksuz: 6 harflik dizi
        z = "".join(re.findall(r"\w", "".join(S)))
        return {z[i:i + 6] for i in range(len(z) - 5) if not re.search(r"\d", z[i:i + 6])}
    w = [x.lower() for s in S for x in kelimeler(s)]
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1) if not any(re.search(r"\d", x) for x in w[i:i + n])}


def _bas(s, dil, k=3):
    return "".join(re.findall(r"\w", s))[:6] if dil == "ja" else " ".join(x.lower() for x in kelimeler(s)[:k])


def onceki_kiyas(t, dil, onceki):
    """yeni metin <-> kanalin onceki metinleri: ayni acilis/kapanis basi, bolum acilislari, ortak n-gram (>=esik bolumde)"""
    def yapi(x):
        S = [s for v in vo_satirlari(x) for s in cumleler(v)]
        return S, S
    S, B = yapi(t); P = [yapi(x) for x in onceki]; n = len(P)
    esik = 2 if n <= 3 else max(2, round(n * 0.6))
    ng = C.Counter(g for ps, _ in P for g in _ngram(ps, dil))
    ortak = sorted(g for g in _ngram(S, dil) if ng[g] >= esik)
    ac = [i for i, (ps, _) in enumerate(P) if ps and _bas(ps[0], dil) == _bas(S[0], dil)]
    kp = [i for i, (ps, _) in enumerate(P) if ps and _bas(ps[-1], dil) == _bas(S[-1], dil)]
    soru = lambda x: bool(x) and bool(re.search(r"[?？]\s*$", x[-1]))
    ks = soru(S) and sum(soru(ps) for ps, _ in P) >= esik  # 18 Kas: 'ozet yerine soru' talimati 10 metnin 7'sini soruyla bitirdi
    bo = C.Counter(b for _, pb in P for b in {_bas(x, dil, 3) for x in pb})  # 3 kelimelik cumle basi
    bt = [b for b in {_bas(x, dil, 3) for x in B} if bo[b] >= esik]
    return {"onceki_n": n, "esik_bolum": esik, "ortak_ngram_n": len(ortak), "ortak_ngram": ortak[:20],
            "ayni_acilis": ac, "ayni_kapanis": kp, "soru_kapanis_tekrar": ks, "tekrar_cumle_basi": sorted(bt)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metin"); ap.add_argument("--dil", default="en", choices=sorted(KLISE))
    ap.add_argument("--bilgi"); ap.add_argument("--json")
    ap.add_argument("--onceki", nargs="+", help="kanalin onceki bolum metinleri (.md/.txt VO ya da script.json); sablon tekrari")
    ap.add_argument("--dilbilgisi", action="store_true", help="gemweb ile artikel/cinsiyet/hal/sayi/ceviri hatasi adaylari (EN disi diller; aday listesi, hakem degil)")
    a = ap.parse_args()
    try:
        t = Path(a.metin).read_text(encoding="utf-8")
        b = Path(a.bilgi).read_text(encoding="utf-8") if a.bilgi else None
        r = denetle(t, a.dil, b, a.dilbilgisi, [onceki_oku(x) for x in a.onceki or []])
    except (OSError, ValueError) as e:
        print("HATA:", e); return 2
    print(f"{a.metin}: {r['cumle']} cumle, {r['kelime']} kelime | CV {r['ritim']['cv']} | kisa %{r['ritim']['kisa_<=4_yuzde']} | acilis {r['ritim']['en_sik_acilis']}")
    if "not" in r["ritim"]: print("  not:", r["ritim"]["not"])
    for u in r["uyarilar"]: print("  -", u)
    if not r["uyarilar"]: print("  uyari yok")
    for n in r["notlar"]: print("  not:", n)
    if a.json: Path(a.json).write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    return 1 if r["uyarilar"] else 0


if __name__ == "__main__":
    sys.exit(main())
