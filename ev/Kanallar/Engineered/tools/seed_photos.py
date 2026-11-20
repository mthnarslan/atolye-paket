"""Add real photographs to a film's archive photo pool with extra search queries.

python seed_photos.py <film 03_materials folder> "query 1" "query 2" ...

Stage 3 searches archive photos once, with the film's topic title. For an
explainer title ("The Enhanced Fujita Scale ...") every hit was a chart, the
classifier filed them as 2D, and the PHOTO/CARD mix had one photograph
(EP05, 2026-10-30). This keeps the manifest's query (so stage 3 takes the
pool from cache), appends photos found by the extra queries through the same
SearXNG search and the same row builder, and removes catalog.json so the
next stage-3 run classifies the new pool. Mix ratios and QA are unchanged.
"""
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, r"C:\Users\meteh\.gemini\scripts")
import requests
from documentary_materials import sources

out, queries = Path(sys.argv[1]), sys.argv[2:]
manifest_path = out / "photos" / "archive_manifest.json"
manifest = sources.load(manifest_path)
rows = [r for r in manifest["rows"] if Path(r["path"]).is_file()]
seen = {r["image_url"] for r in rows}
directory = out / "photos" / "archive"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def get(result):
    try:
        response = requests.get(result.get("img_src") or result.get("thumbnail"), timeout=20, headers=headers)
        response.raise_for_status()
        return response.content
    except Exception:
        return None


for query in queries:
    found = [r for r in sources.searxng_images(query, out, limit=40)
             if (r.get("img_src") or r.get("thumbnail")) and (r.get("img_src") or r.get("thumbnail")) not in seen]
    added = 0
    with ThreadPoolExecutor(8) as pool:
        for result, blob in zip(found, pool.map(get, found)):
            if added >= 10:
                break
            row = sources._archive_photo(result, blob, directory, len(rows)) if blob else None
            if row:
                rows.append(row)
                seen.add(row["image_url"])
                added += 1
    print(f"{query!r}: +{added}")

sources.save(manifest_path, {"query": manifest["query"], "rows": rows})
(out / "catalog.json").unlink(missing_ok=True)
print(f"pool {len(rows)} photos; catalog.json removed")
