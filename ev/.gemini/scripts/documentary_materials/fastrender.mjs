// usage: node fastrender.mjs --fmt jpeg|png --enc x264|nvenc --dedup 0|1 --frames N proj1::out1.mp4 proj2::out2.mp4 ...
// Fast card/motion renderer used by cards.render_project (HyperFrames is the fallback). Needs the installed hyperframes package (puppeteer-core, chrome-headless-shell, Montserrat).
// One chrome-headless-shell for all jobs, frames piped straight into ONE ffmpeg per job (final encode, no second pass).
import { createRequire } from 'module'; import { spawn } from 'child_process'; import path from 'path'; import os from 'os'; import { pathToFileURL } from 'url';
const require = createRequire(process.env.HYPERFRAMES_ROOT ? path.join(process.env.HYPERFRAMES_ROOT, 'package.json') : path.join(process.env.APPDATA || '', 'npm/node_modules/hyperframes/package.json'));
const puppeteer = require('puppeteer-core');
const a = process.argv.slice(2); const opt = { fmt: 'jpeg', enc: 'x264', dedup: '1', frames: '0', q: '95', par: '1' }; const jobs = [];
for (let i = 0; i < a.length; i++) { if (a[i].startsWith('--')) opt[a[i].slice(2)] = a[++i]; else jobs.push(a[i].split('::')); }
const CACHE = path.join(os.homedir(), '.cache/hyperframes'); const fs = await import('fs'); const shellDir = path.join(CACHE, 'chrome/chrome-headless-shell');
const chrome = path.join(shellDir, fs.readdirSync(shellDir)[0], 'chrome-headless-shell-win64/chrome-headless-shell.exe');
const FONT = pathToFileURL(path.join(CACHE, 'fonts/montserrat', fs.readdirSync(path.join(CACHE, 'fonts/montserrat')).find(f => f.endsWith('.woff2')))).href;
const browser = await puppeteer.launch({ executablePath: chrome, headless: 'shell', args: ['--no-sandbox', '--disable-gpu', '--allow-file-access-from-files', '--force-color-profile=srgb', '--hide-scrollbars'] });
const FPS = 25;
async function runJob([proj, out]) {
  const page = await browser.newPage(); await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
  await page.goto(pathToFileURL(path.resolve(proj, 'index.html')).href, { waitUntil: 'load' });
  await page.addStyleTag({ content: `@font-face{font-family:"Montserrat";font-weight:100 900;font-style:normal;src:url(${FONT}) format("woff2")}` });
  await page.evaluate(() => document.fonts.ready); await new Promise(r => setTimeout(r, 150));
  const info = await page.evaluate(() => { const tl = window.__timelines.main; tl.pause();
    const iv = tl.getChildren(true, true, true, 0).map(c => [c.startTime(), c.startTime() + c.totalDuration()]);
    return { dur: +document.getElementById('root').dataset.duration, iv }; });
  const n = +opt.frames || Math.round(info.dur * FPS);
  const enc = opt.enc === 'nvenc' ? ['-c:v', 'h264_nvenc', '-preset', 'p5', '-rc', 'vbr', '-cq', '19', '-b:v', '0'] : ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', '-threads', '2'];
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', '25', '-c:v', opt.fmt === 'png' ? 'png' : 'mjpeg', '-i', '-', '-vf', 'setsar=1', '-frames:v', String(n), ...enc, '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise(r => ff.on('close', r));
  let prev = null, shots = 0;
  for (let i = 0; i < n; i++) {
    const t = i / FPS;
    // dedup: frame is static when no tween covers (t-1/FPS .. t]; reuse previous bytes
    const moving = info.iv.some(([s, e]) => t >= s - 1e-6 - 1 / FPS && t <= e + 1 / FPS);
    if (opt.dedup !== '1' || prev === null || moving) {
      await page.evaluate(t => { window.__timelines.main.time(t, false); }, t);
      prev = await page.screenshot(opt.fmt === 'png' ? { type: 'png' } : { type: 'jpeg', quality: +opt.q }); shots++;
    }
    if (!ff.stdin.write(prev)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await done; await page.close(); console.error(`${proj}: ${n} frames, ${shots} screenshots`);
}
const par = +opt.par; const q = [...jobs]; await Promise.all(Array.from({ length: par }, async () => { while (q.length) await runJob(q.shift()); }));
await browser.close();
