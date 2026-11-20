"""11-19: 1095 oncesi 'queueing' durumu akista kacinci saniyede gorunuyor?"""
import sys, runpy, time
sys.argv = ["deney_temp_1119.py"] + sys.argv[1:]
from loguru import logger
T0 = [time.time()]
logger.remove()
logger.add(lambda m: print(f"[{time.strftime('%H:%M:%S')}] {m.record['message'][:110]}", flush=True), level="DEBUG",
           filter=lambda r: "HTTP" not in r["message"])
runpy.run_path("deney_temp_1119.py", run_name="__main__")
