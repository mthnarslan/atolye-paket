---
tur: kaynak
aciklama: Arastirma araclari: 22 aday tarandi, 3 soruda olculdu; kalan: Kanallar/ortak/arastir.py (6 sn, 9 kaynak paralel) + arastir_derin.py (GPT-Researcher+gemweb)
kaynak: C:/Users/meteh/testbench/arastirma_1119/RAPOR.md
olusturma: 2026-11-19
guncel: 2026-11-19
yazan: arastirma
onay: 
etiket: ortak
---
# arastirma-araclari-1119

19 Kas 2026. KULLANIM: (1) hizli: python C:/Users/meteh/Kanallar/ortak/arastir.py "english query" [--kaynak gh,hf,hfp,arxiv,oa,s2,hn,reddit,searx,so] [--n 8] [--json x.json] -> GitHub+HF(model/dataset/space)+HF papers+arXiv+OpenAlex+SemanticScholar+HN+Reddit(pullpush)+SearXNG VDS tekillestirilmis tarihli link; sorgu Ingilizce; 6 sn. Olcum A/B/C: 89/70/95 link, 24-34 farkli alan, WebSearch tabaninda olmayan 86/67/92 link (23/22/30 yeni alan), 1-3 olu sayfa, uydurma yok. Gurultu: HN/SO/HF dataset harfi harfine arar; ilgili olan HF papers+OpenAlex+arXiv+SearXNG. GitHub anahtarsiz 60 istek/saat (GITHUB_TOKEN env varsa kullanir), Semantic Scholar 429 (2/3), pullpush Reddit 521 (kapali olabilir). (2) derin: python Kanallar/ortak/arastir_derin.py "english soru" --cikti rapor.md -> GPT-Researcher (venv testbench/arastirma_1119/v_gptr, 1,2 GB) + gemweb_adaptor.py (:8791 OpenAI uyumlu -> gemweb, hash embedding); 126/149/397 sn, 40/25/22 kaynak, 5 gemweb istegi/soru, rapor atiflari kaynak listesinde (31/31), 10-15 yeni alan; rapordaki sayilari yine link_denetle ile denetle. (3) sayfa->metin: testbench/arastirma_1119/v_traf/Scripts/python -m trafilatura -u URL (14/18 sayfa metin, ort 3,3 sn) ya da curl https://r.jina.ai/URL (anahtarsiz, 1,2 sn). paperswithcode.com artik huggingface.co/papers/trending'e yonleniyor. Denenmedi: STORM (1 yil commit yok), smolagents/LangChain open_deep_research (LLM cagrisi cok / arsivli), Perplexica (Docker), paper-qa (PDF+embedding), youtube-transcript-api (yt_gate kurali).
