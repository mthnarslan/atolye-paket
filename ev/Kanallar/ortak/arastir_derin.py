"""Derin arastirma: GPT-Researcher (venv) + gemweb hydrogen + SearXNG/OpenAlex/arXiv, kaynakli rapor uretir.
Kullanim: python arastir_derin.py "english soru" [--cikti rapor.md] [--kelime 600] [--tur 2]
Maliyet: ~5-6 gemweb istegi, 2-7 dk. Hizli tarama icin once arastir.py. Rapor atiflari kaynak listesindedir (uydurma link gorulmedi, 3 test);
yine de karar verdirecekse link_denetle.py'den gecir. Embedding yerine hash vektoru (LLM'siz) kullanilir: ilgi suzgeci kaba.
Venv: C:/Users/meteh/testbench/arastirma_1119/v_gptr (gpt-researcher, ~1.2 GB)."""
import os, sys, subprocess, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
VENV = r"C:/Users/meteh/testbench/arastirma_1119/v_gptr/Scripts/python.exe"
IC = r'''
import os, sys, asyncio, json
from gpt_researcher import GPTResearcher
async def main():
    r = GPTResearcher(query=sys.argv[1], report_type="research_report", verbose=False)
    await r.conduct_research(); urls = list(r.get_source_urls()); rep = await r.write_report()
    json.dump({"urls": urls, "rapor": rep}, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False)
asyncio.run(main())
'''
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("q"); ap.add_argument("--cikti", default="arastir_derin_rapor.md"); ap.add_argument("--kelime", default="600"); ap.add_argument("--tur", default="2")
    a = ap.parse_args()
    import gemweb_adaptor; gemweb_adaptor.baslat(8791)
    env = dict(os.environ, OPENAI_API_KEY="x", OPENAI_BASE_URL="http://127.0.0.1:8791/v1", FAST_LLM="openai:gemini-4-hydrogen", SMART_LLM="openai:gemini-4-hydrogen",
               STRATEGIC_LLM="openai:gemini-4-hydrogen", EMBEDDING="custom:hash", RETRIEVER="searx,openalex,arxiv", SEARX_URL="http://100.104.78.117:8888",
               MAX_ITERATIONS=a.tur, MAX_SEARCH_RESULTS_PER_QUERY="6", TOTAL_WORDS=a.kelime, MAX_SCRAPER_WORKERS="6", SCRAPER="bs", PYTHONIOENCODING="utf-8")
    tmp = a.cikti + ".json"
    p = subprocess.run([VENV, "-c", IC, a.q, tmp], env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode or not os.path.exists(tmp): sys.exit("HATA: " + p.stderr[-600:])
    d = json.load(open(tmp, encoding="utf-8")); os.remove(tmp)
    open(a.cikti, "w", encoding="utf-8").write(d["rapor"] + "\n\n## Gezilen kaynaklar\n" + "\n".join("- " + u for u in d["urls"]) + "\n")
    print(f"{a.cikti}: {len(d['urls'])} kaynak, {len(d['rapor'])} harf")
