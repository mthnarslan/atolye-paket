"""Cok kaynakli paralel arastirma: tek komut, tekil + tarihli link listesi (LLM yok, anahtar yok).
Kullanim: python arastir.py "english query" [--kaynak gh,hf,hfp,arxiv,oa,s2,hn,reddit,searx,so] [--n 8] [--json cikti.json]
Her satir: [kaynak] tarih | baslik | url | not. Kaynak hata verirse '# kaynak: ... hata' stderr'e yazilir, digerleri surer.
Sorguyu Ingilizce yaz (arXiv/GitHub/HF Ingilizce indekslidir). GitHub anahtarsiz 60 istek/saat (403 = limit).
Ucretsiz/anahtarsiz: GitHub, HuggingFace (model/dataset/space/paper), arXiv, OpenAlex, SemanticScholar (429 olabilir),
HN algolia, Reddit pullpush, SearXNG VDS, StackOverflow (so, kodlama sorusu degilse gurultu: varsayilan kapali)."""
import os, sys, json, re, time, argparse, urllib.parse as up, urllib.request as ur
from concurrent.futures import ThreadPoolExecutor
import xml.etree.ElementTree as ET
UA = {"User-Agent": "arastir/1.0 (research script)"}
SEARX = "http://100.104.78.117:8888"


def get(url, t=25, js=True):
    h = dict(UA)
    if "api.github.com" in url and os.environ.get("GITHUB_TOKEN"): h["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    d = ur.urlopen(ur.Request(url, headers=h), timeout=t).read().decode("utf-8", "replace")
    return json.loads(d) if js else d


def gh(q, n):
    r = get("https://api.github.com/search/repositories?" + up.urlencode({"q": q + " pushed:>2025-06-01", "sort": "stars", "order": "desc", "per_page": n}))
    return [("gh", i["pushed_at"][:10], i["full_name"], i["html_url"], f"{i['stargazers_count']}* {(i.get('license') or {}).get('spdx_id')} {(i.get('description') or '')[:90]}") for i in r["items"]]


def hf(q, n):
    out = []
    for kind in ("models", "datasets", "spaces"):
        r = get(f"https://huggingface.co/api/{kind}?" + up.urlencode({"search": q, "sort": "downloads" if kind == "datasets" else "likes", "direction": -1, "limit": n}))
        for i in r:
            out.append(("hf-" + kind[:-1], (i.get("lastModified") or i.get("createdAt") or "")[:10], i["id"], f"https://huggingface.co/{'' if kind == 'models' else kind + '/'}{i['id']}", f"dl={i.get('downloads', '-')} likes={i.get('likes', '-')}"))
    return out


def hfp(q, n):
    r = get("https://huggingface.co/api/papers/search?" + up.urlencode({"q": q, "limit": n}))
    return [("hf-paper", (i["paper"].get("publishedAt") or "")[:10], i["paper"]["title"], "https://huggingface.co/papers/" + i["paper"]["id"], f"up={i['paper'].get('upvotes', '-')}") for i in r]


def arxiv(q, n):
    t = get("https://export.arxiv.org/api/query?" + up.urlencode({"search_query": "all:" + q, "max_results": n, "sortBy": "relevance"}), js=False)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    return [("arxiv", e.find("a:published", ns).text[:10], " ".join(e.find("a:title", ns).text.split()), e.find("a:id", ns).text, "") for e in ET.fromstring(t).findall("a:entry", ns)]


def oa(q, n):
    r = get("https://api.openalex.org/works?" + up.urlencode({"search": q, "per-page": n, "filter": "from_publication_date:2023-01-01"}))
    return [("openalex", i.get("publication_date") or "", i["title"] or "", (i.get("primary_location") or {}).get("landing_page_url") or i["id"], f"cited={i['cited_by_count']}") for i in r["results"]]


def s2(q, n):
    r = get("https://api.semanticscholar.org/graph/v1/paper/search?" + up.urlencode({"query": q, "limit": n, "fields": "title,year,url,citationCount,publicationDate"}))
    return [("s2", i.get("publicationDate") or str(i.get("year")), i["title"], i["url"], f"cited={i['citationCount']}") for i in r.get("data", [])]


def hn(q, n):
    r = get("https://hn.algolia.com/api/v1/search?" + up.urlencode({"query": q, "tags": "story", "hitsPerPage": n}))
    return [("hn", i["created_at"][:10], i["title"] or "", i.get("url") or f"https://news.ycombinator.com/item?id={i['objectID']}", f"pts={i.get('points')} hn={i['objectID']}") for i in r["hits"]]


def reddit(q, n):
    r = get("https://api.pullpush.io/reddit/search/submission/?" + up.urlencode({"q": q, "size": n, "sort_type": "score", "sort": "desc"}))
    return [("reddit", time.strftime("%Y-%m-%d", time.gmtime(i["created_utc"])), i["title"], "https://reddit.com" + i["permalink"], f"r/{i['subreddit']} score={i['score']}") for i in r["data"]]


def searx(q, n):
    r = get(f"{SEARX}/search?" + up.urlencode({"q": q, "format": "json"}), t=40)
    return [("searx", (i.get("publishedDate") or "")[:10], i["title"], i["url"], i.get("engine", "")) for i in r["results"] if i["url"].startswith("http") and "/go/v1/" not in i["url"]][:n * 3]


def so(q, n):
    r = get("https://api.stackexchange.com/2.3/search/advanced?" + up.urlencode({"q": q, "site": "stackoverflow", "order": "desc", "sort": "relevance", "pagesize": n}))
    return [("stackoverflow", time.strftime("%Y-%m-%d", time.gmtime(i["creation_date"])), i["title"], i["link"], f"score={i['score']}") for i in r["items"]]


STOP = set("a an the of for in on to and or with by from is are best open model models method methods using use how what which".split())


def varyant(q):
    """gh/hf/hn/so anlamsal degil harfi harfine arar: tam sorgu 0 donerse bitisik 2'li kelime gruplarini dener."""
    t = [w for w in re.findall(r"[\w.-]+", q) if w.lower() not in STOP]
    return [q] + [" ".join(t[i:i + 2]) for i in range(max(len(t) - 1, 0))][:4] + (t[:1] if len(t) > 2 else [])


def coklu(fn):
    def w(q, n):
        out, seen = [], set()
        for v in varyant(q):
            try: rows = fn(v, n)
            except Exception:
                if not out and v == q: raise
                rows = []
            for r in rows:
                if r[3] not in seen: seen.add(r[3]); out.append(r)
            if len(out) >= n: break
        return out
    return w


for _f in ("gh", "hf", "hn", "so"): globals()[_f] = coklu(globals()[_f])
SRC = dict(gh=gh, hf=hf, hfp=hfp, arxiv=arxiv, oa=oa, s2=s2, hn=hn, reddit=reddit, searx=searx, so=so)


def norm(u):
    u = re.sub(r"^https?://(www\.)?", "", u.lower()).split("#")[0].rstrip("/")
    return re.sub(r"(arxiv\.org/)(abs|pdf|html)/(\d+\.\d+)(v\d+)?(\.pdf)?", r"\1abs/\3", u)


def calis(q, kaynaklar, n=8):
    def run(k):
        t = time.time(); err = None
        for _ in (0, 1):
            try: return k, SRC[k](q, n), time.time() - t, None
            except Exception as e: err = f"{type(e).__name__}: {str(e)[:80]}"; time.sleep(2)
        return k, [], time.time() - t, err
    with ThreadPoolExecutor(len(kaynaklar)) as ex: res = list(ex.map(run, kaynaklar))
    seen, out = set(), []
    for k, rows, dt, err in res:
        for r in rows:
            if norm(r[3]) in seen: continue
            seen.add(norm(r[3])); out.append(r)
    return out, [(k, len(rows), round(dt, 1), err) for k, rows, dt, err in res]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("q"); ap.add_argument("--kaynak", default="gh,hf,hfp,arxiv,oa,s2,hn,reddit,searx"); ap.add_argument("--n", type=int, default=8); ap.add_argument("--json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    out, st = calis(a.q, a.kaynak.split(","), a.n)
    for r in out: print("[%s] %s | %s | %s | %s" % r)
    for k, c, dt, err in st: print(f"# {k}: {c} sonuc {dt}s {err or ''}", file=sys.stderr)
    if a.json: json.dump(out, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
