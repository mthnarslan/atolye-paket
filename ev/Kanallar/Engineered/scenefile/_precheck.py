import sys
sys.path.insert(0, r'C:\Users\meteh\Kanallar\Engineered\casefile')
from cf_common import load_film, check_rows
from pathlib import Path
for f in sys.argv[1:]:
    F = load_film(f); w = Path(__file__).parent / 'work' / f
    check_rows(F['rows'], w / 'clipcheck'); print(f, 'done', flush=True)
