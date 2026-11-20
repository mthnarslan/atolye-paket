"""Render the existing scene-specific mesh contract through local Hyperframes/WebGL."""
import functools
import atexit
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time
import queue
import tempfile
from contextlib import contextmanager

from . import geometry
from .io import save

ROOT = Path(__file__).resolve().parent
# Five shot workers share three browser workers; avoid five independent 5-browser renders.
_POOL_LOCK = threading.Lock()
_WORKERS = []
_IDLE = queue.Queue()


def _governor():
    from adaptive_governor import get_governor
    return get_governor()


@contextmanager
def encoding_slot(force=None):
    """Encode on NVENC, waiting for a free session rather than spilling to CPU.

    A short clip encodes in 1-2 s on NVENC; spilled to libx264 it held a
    CPU for ~10 s, and with four films 47 of 241 renders spilled while the
    CPU sat at 100% (2026-10-27). DOCUMENTARY_NVENC_SPILL=1 restores the
    old non-blocking spill.
    """
    governor = _governor()
    nvenc = encoder_args()[1] == "h264_nvenc"
    if force == "nvenc" or (force is None and nvenc and os.environ.get("DOCUMENTARY_NVENC_SPILL", "0") != "1"):
        channel = "nvenc"
    else:
        channel = "nvenc" if force is None and nvenc and governor.try_acquire("nvenc") else (force or "cpu")
    held = force is None and channel == "nvenc" and os.environ.get("DOCUMENTARY_NVENC_SPILL", "0") == "1"
    if not held:
        governor.acquire(channel)
    started = time.perf_counter()
    success = False
    try:
        yield (["-c:v", "h264_nvenc", "-preset", "p1", "-rc", "vbr", "-cq", "19", "-b:v", "0"]
               if channel == "nvenc" else ["-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-threads", "2"])
        success = True
    finally:
        governor.release(channel)
        governor.observe(channel, time.perf_counter()-started, success)


_WARM_JS = r'''
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import readline from 'node:readline';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {pathToFileURL} from 'node:url';
const {default:puppeteer}=await import(pathToFileURL(process.env.DOCUMENTARY_PUPPETEER).href);
const pidFile=path.join(process.env.TEMP||process.env.TMPDIR||'.','documentary_browser_'+process.pid+'.pid');
fs.writeFileSync(pidFile,String(process.pid));
process.on('exit',()=>{try{fs.unlinkSync(pidFile);}catch{}});
const browser=await puppeteer.launch({executablePath:process.env.DOCUMENTARY_CHROME,headless:true,userDataDir:process.env.DOCUMENTARY_PROFILE,
  args:JSON.parse(process.env.DOCUMENTARY_CHROME_ARGS||'[]')});
const page=await browser.newPage();await page.setViewport({width:1920,height:1080,deviceScaleFactor:1});
const gpu=await page.evaluate(()=>{const gl=document.createElement('canvas').getContext('webgl2',{powerPreference:'high-performance'});if(!gl)throw Error('WebGL2 unavailable');const ext=gl.getExtension('WEBGL_debug_renderer_info');return {vendor:ext?gl.getParameter(ext.UNMASKED_VENDOR_WEBGL):null,renderer:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER)}});
if(!process.env.DOCUMENTARY_ALLOW_SOFTWARE_WEBGL && /swiftshader|llvmpipe|software/i.test(gpu.renderer))throw Error('Hardware WebGL required: '+gpu.renderer);
let root='';const server=http.createServer((req,res)=>{try {const p=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));if(!p.startsWith(root+path.sep)&&p!==root){res.writeHead(403);res.end();return;}const file=p===root?path.join(p,'index.html'):p;res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript':file.endsWith('.html')?'text/html':'application/octet-stream');fs.createReadStream(file).on('error',()=>{res.statusCode=404;res.end();}).pipe(res);}catch{res.writeHead(400);res.end();}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));const url='http://127.0.0.1:'+server.address().port+'/index.html';
console.log(JSON.stringify({ready:true,gpu}));
for await(const line of readline.createInterface({input:process.stdin,crlfDelay:Infinity})){
  let enc;try{const job=JSON.parse(line);root=path.resolve(job.project);const errors=[];page.removeAllListeners('pageerror');page.on('pageerror',e=>errors.push(String(e)));
    await page.goto(url+'?job='+Date.now(),{waitUntil:'networkidle0',timeout:30000});await page.waitForFunction(()=>!!window.__documentaryScene,{timeout:15000});
    enc=spawn('ffmpeg',['-v','error','-y','-f','image2pipe','-vcodec','mjpeg','-framerate','25','-i','pipe:0','-vf','scale=in_range=full:out_range=limited',...job.encoder,'-frames:v',String(job.count),'-r','25','-pix_fmt','yuv420p','-movflags','+faststart',job.output],{windowsHide:true});let stderr='';enc.stderr.on('data',d=>stderr+=d);const finished=new Promise((resolve,reject)=>{enc.on('error',reject);enc.on('close',code=>code===0?resolve():reject(Error(stderr||'FFmpeg exit '+code)))});
    for(let i=0;i<job.count;i++){await page.evaluate(t=>{window.__timelines.main.seek(t,false);window.dispatchEvent(new CustomEvent('hf-seek',{detail:{time:t}}));},i/25);const frame=await page.screenshot({type:'jpeg',quality:92});if(!enc.stdin.write(frame))await once(enc.stdin,'drain');}
    enc.stdin.end();await finished;if(errors.length)throw Error(errors.join(';'));console.log(JSON.stringify({ok:true,gpu,frames:job.count}));
  }catch(e){if(enc)enc.kill();console.log(JSON.stringify({ok:false,error:String(e)}));}
}
await browser.close();server.close();
'''


# The browser is opened WITHOUT the high performance GPU flag. Forcing
# that adapter is what took the desktop down: a parallel headless
# Chrome that grabs the high performance GPU drags the driver down with
# it and the screen goes black with it. The default adapter draws the
# same scene. If the machine cannot give a headless browser a working
# hardware WebGL at all, the software renderer draws it instead: the
# picture is the same and the driver is never touched.
_CHROME_ARGS = ("--no-first-run",
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
                "--disable-dev-shm-usage")

_SOFTWARE_CHROME_ARGS = _CHROME_ARGS + ("--use-gl=angle", "--use-angle=swiftshader")


def _chrome_args(software=False):
    return list(_SOFTWARE_CHROME_ARGS if software else _CHROME_ARGS)


class WarmBrowser:
    def __init__(self, software=False):
        _, puppeteer = runtime()
        chrome = Path(os.environ.get("DOCUMENTARY_CHROME", r"C:\Program Files\Google\Chrome\Application\chrome.exe"))
        if not chrome.is_file():
            raise RuntimeError("Installed Chromium executable missing")
        script = Path(tempfile.gettempdir()) / "documentary_warm_three.mjs"
        script.write_text(_WARM_JS, encoding="utf8")
        self.log_path = Path(tempfile.gettempdir()) / f"documentary_warm_three_{time.time_ns()}.log"
        self.log = self.log_path.open("w", encoding="utf8")
        self.broken = False
        # The profile is ours, not puppeteer's: close() kills the browser
        # tree, which skips puppeteer's own cleanup, and every 3D worker
        # left a ~110 MB profile in Temp (99 of them, 5.7 GB).
        self.profile = tempfile.mkdtemp(prefix="documentary_chrome_")
        self.proc = subprocess.Popen([shutil.which("node") or "node", str(script)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=self.log, text=True, encoding="utf8",
            env={**os.environ,"DOCUMENTARY_PUPPETEER":str(puppeteer),"DOCUMENTARY_CHROME":str(chrome),
                 "DOCUMENTARY_CHROME_ARGS":json.dumps(_chrome_args(software)),"DOCUMENTARY_PROFILE":self.profile,
                 "DOCUMENTARY_ALLOW_SOFTWARE_WEBGL":"1" if software else ""})
        self.lines=queue.Queue()
        threading.Thread(target=self._read,daemon=True).start()
        self.identity = self._next(40)
        if not self.identity.get("ready"):
            self.close(); raise RuntimeError("Warm Chromium did not become ready")

    def _read(self):
        for line in self.proc.stdout:
            self.lines.put(line)
        self.lines.put(None)

    def _next(self, timeout):
        try:
            line=self.lines.get(timeout=timeout)
        except queue.Empty:
            self.close(); raise TimeoutError("Warm browser operation timed out; worker terminated")
        if line is None:
            raise RuntimeError("Warm Chromium process exited; see worker stderr log")
        return json.loads(line)

    def render(self, project, count, output, encoder):
        try:
            self.proc.stdin.write(json.dumps({"project":str(project),"count":count,"output":str(Path(output).resolve()),"encoder":encoder})+"\n")
            self.proc.stdin.flush()
        except OSError as exc:
            # The browser is gone. Writing to its pipe is the first sign
            # of it, and the reason is in its log, not in this message.
            self.broken=True
            raise RuntimeError("The render browser stopped before the frame was drawn: %s | %s"
                               % (exc,self._log_tail()))
        result=self._next(max(180,count/25*15))
        if not result.get("ok"):
            self.broken=True
            raise RuntimeError("Warm WebGL render failed: "+result.get("error","unknown")+" | "+self._log_tail())
        return result

    def _log_tail(self, limit=1200):
        try:
            self.log.flush()
            return self.log_path.read_text(encoding="utf8",errors="replace")[-limit:].strip()
        except Exception:
            return ""

    def close(self):
        if self.proc.poll() is None:
            # Terminate the browser descendants as well; no detached rendering remains.
            subprocess.run(["taskkill","/PID",str(self.proc.pid),"/T","/F"],capture_output=True,timeout=15)
        self.log.close()
        shutil.rmtree(self.profile, ignore_errors=True)
        # A healthy worker's log says nothing; a broken one's is the evidence.
        if not self.broken:
            self.log_path.unlink(missing_ok=True)


def close_warm_workers():
    for worker in list(_WORKERS):
        worker.close()


atexit.register(close_warm_workers)


@functools.lru_cache(maxsize=1)
def encoder_args():
    result = subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=s=1920x1080:r=25", "-frames:v", "1", "-c:v", "h264_nvenc", "-f", "null", "-"], capture_output=True, timeout=20)
    if result.returncode == 0:
        return ["-c:v", "h264_nvenc", "-preset", "p1", "-rc", "vbr", "-cq", "19", "-b:v", "0"]
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-threads", "2"]


@functools.lru_cache(maxsize=1)
def runtime():
    """Locate the browser runtime the 3D render needs.

    The render itself does not use the Hyperframes CLI. It opens the
    scene in a headless Chromium through puppeteer-core, takes a
    screenshot per frame and pipes the frames into ffmpeg. So the only
    thing that has to exist is the puppeteer-core module.

    The CLI used to be the only place the module was looked for,
    through the node_modules folder of its npx cache entry, and that
    cache is cleaned by npm. When the cache was gone the render died
    with "Installed Hyperframes CLI not found" even though the module
    was installed somewhere else. So the module is searched for on its
    own now, and the CLI is only one of the places it can be.
    """
    override = os.environ.get("DOCUMENTARY_PUPPETEER")
    if override and Path(override).is_file():
        return Path(override), Path(override)
    roots = []
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        roots.append(Path(local) / "npm-cache" / "_npx")
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        roots.append(Path(appdata) / "npm" / "node_modules")
    roots.append(Path(os.environ.get("PROGRAMFILES", "")) / "nodejs" / "node_modules")
    # A puppeteer-core install is a node_modules folder that holds
    # puppeteer-core/lib/puppeteer/puppeteer-core.js.
    found = []
    for root in roots:
        if not root.is_dir():
            continue
        for module in root.glob("**/puppeteer-core/lib/puppeteer/puppeteer-core.js"):
            found.append(module)
    if not found:
        raise RuntimeError(
            "puppeteer-core not found. Install it with "
            "'npm install -g puppeteer-core', or point "
            "DOCUMENTARY_PUPPETEER at puppeteer-core.js")
    module = max(found, key=lambda p: p.stat().st_mtime)
    # The CLI is reported for the receipt, but it is not required.
    cli_candidates = []
    for root in roots:
        cli_candidates.extend(root.glob("**/hyperframes/bin/hyperframes.mjs"))
    cli = max(cli_candidates, key=lambda p: p.stat().st_mtime, default=None)
    return cli, module


def write_project(spec, count, work):
    geometry.validate(spec)
    yaw = spec.get("camera_yaw", -26)
    if type(yaw) not in (int, float) or not -180 <= yaw <= 180:
        raise ValueError("camera_yaw must be finite and within +/-180 degrees")
    project = Path(work) / "three_project"
    project.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "three_vendor", project / "vendor", dirs_exist_ok=True)
    if (ROOT / "hanger-elevation.png").exists():
        shutil.copy2(ROOT / "hanger-elevation.png", project / "hanger-elevation.png")
    meshes = {}
    for kind in {obj["type"] for obj in spec["objects"]}:
        vertices, faces = geometry.mesh(kind)
        positions = []
        for face in faces:
            for i in range(1, len(face) - 1):
                for index in (face[0], face[i], face[i + 1]):
                    positions.extend(vertices[index].tolist())
        meshes[kind] = {"positions": positions}
    source = (ROOT / "three_scene.html").read_text(encoding="utf8")
    title = spec.get("title") or ""
    source = source.replace("__DURATION__", str(count / 25)).replace("__TITLE__", title).replace("__SPEC__", json.dumps(spec, allow_nan=False).replace("<", "\\u003c")).replace("__MESHES__", json.dumps(meshes, separators=(",", ":")))
    (project / "index.html").write_text(source, encoding="utf8")
    save(project / "hyperframes.json", {"name": "Documentary scene", "entry": "index.html"})
    save(project / "mesh_spec.json", spec)
    return project


# The browser pool is bounded by a number, not by the governor's limit.
# The governor raises that limit when the renders come back fast, and
# thirty headless browsers, each with its own GPU process, is what
# took the machine down: they held three gigabytes and the screen went
# black with them. The pool is also narrowed when the memory is low.
_MAX_BROWSERS = 3


def _browser_limit():
    from . import resources
    # A browser is 472 MB on this machine and the encoder it pipes into
    # is another 312, so a browser costs about eight hundred.
    return resources.worker_count(_MAX_BROWSERS, per_worker_mb=800, minimum=1)


def _close_stale_browsers():
    """Close the browsers of a run that was killed before it could close them.

    A run that is killed takes its node process and its browser with
    it, but a run that is interrupted leaves them alive: they keep
    their memory, and they keep a GPU process on the display. This
    machine carried thirty of them after the runs that the memory
    guard had to stop. Every browser writes its process id down, so
    the leftovers can be found and closed.
    """
    temp = Path(tempfile.gettempdir())
    # The browsers of this run's own pool also have a pid file. Opening
    # a second browser used to kill the first one in the middle of a
    # frame ("Warm Chromium process exited", "Errno 22").
    live = {w.proc.pid for w in _WORKERS if w.proc.poll() is None}
    for pid_file in temp.glob("documentary_browser_*.pid"):
        try:
            pid = int(pid_file.read_text(encoding="utf8").strip())
        except Exception:
            pid_file.unlink(missing_ok=True)
            continue
        if pid in live:
            continue
        try:
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                           capture_output=True, timeout=20)
        except Exception:
            pass
        pid_file.unlink(missing_ok=True)


def _new_browser():
    """A browser that renders without taking the display driver down.

    The first attempt uses the machine's own adapter. If the machine
    cannot give a headless browser a working WebGL context at all, the
    second attempt asks for the software renderer: the picture is the
    same and no driver is involved, so a machine that cannot spare the
    GPU keeps working instead of going dark.
    """
    from . import resources
    if not resources.wait_for_room(resources.CRITICAL_MB, timeout=120):
        raise RuntimeError("Not enough free memory to open a render browser")
    _close_stale_browsers()
    try:
        return WarmBrowser()
    except Exception as first:
        try:
            return WarmBrowser(software=True)
        except Exception:
            raise first


def render_three(spec, count, output, work):
    if type(count) is not int or count <= 0:
        raise ValueError("3D needs a positive frame count")
    project = write_project(spec, count, work)
    started = time.perf_counter()
    governor = _governor()
    with governor.slot("hyperframes"):
        with _POOL_LOCK:
            if _IDLE.empty() and len(_WORKERS) < _browser_limit():
                worker=_new_browser();_WORKERS.append(worker);_IDLE.put(worker)
        worker = _IDLE.get()
        try:
            with encoding_slot() as encoder:
                result=worker.render(project,count,output,encoder)
            save(project / "gpu_identity.jsonl",result["gpu"])
        finally:
            # A browser that died in the middle of a frame is not put
            # back into the pool. It was measured on a live run: the
            # dead browser stayed in the idle queue, and the next two
            # shots wrote into its closed pipe and died with the same
            # error. A broken worker is thrown away, and the next shot
            # opens a new one.
            if worker.proc.poll() is None and not worker.broken:
                _IDLE.put(worker)
            else:
                worker.close()
                with _POOL_LOCK:
                    if worker in _WORKERS:
                        _WORKERS.remove(worker)
    save(project / "render_receipt.json", {"elapsed_seconds": round(time.perf_counter() - started, 3), "frame_count": count, "width": 1920, "height": 1080, "fps": 25, "implementation": "Three.js WebGL via installed Hyperframes Puppeteer runtime; persistent Chromium", "encoder":encoder[1], "nvenc_available": encoder_args()[1] == "h264_nvenc", "gpu_identity_receipt": str(project / "gpu_identity.jsonl")})
