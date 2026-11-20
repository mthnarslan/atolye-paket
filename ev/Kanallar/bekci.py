"""bekci: watch a job without waking the model. Silent until the job ends, fails, stalls or RAM runs low;
then prints one short package (reason, error lines, log tail) and exits. Start it with run_in_background: one wake per incident.

  python bekci.py --ad gaia -- python tools/gaia_finish.py EP03        # run a command and watch it
  python bekci.py --ad ep04 --log OUT/queue/EP04.log --pid 1234       # watch a job that already runs
  python bekci.py --ad pack --log x.log --done-file out/final.zip     # done when a file appears

Exit codes: 0 done, 1 failed, 2 stalled (log silent for --stall-min), 3 low RAM, 4 timeout, 5 bad arguments.
After a wake for 2/3/4 the job itself may still run: fix the cause, then start bekci again (--pid/--log form)."""
import argparse, ctypes, os, re, subprocess, sys, time
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(errors="replace")
    except Exception: pass

ERR = r'Traceback \(most recent|Error\b|\bFAIL(ED)?\b|\bFATAL\b|Exception|exit code [1-9]|Max Retries'
LOGDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bekci_log')
NAMES = ['BITTI', 'HATA', 'TAKILDI', 'RAM DUSUK', 'ZAMAN ASIMI']


def free_ram_gb():
    class M(ctypes.Structure):
        _fields_ = [('len', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [(n, ctypes.c_ulonglong) for n in
                   ('total', 'avail', 'tpf', 'apf', 'tv', 'av', 'aev')]
    m = M(); m.len = ctypes.sizeof(M)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.avail / 2**30


def pid_alive(pid):
    h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
    if not h: return False
    code = ctypes.c_ulong()
    ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code)); ctypes.windll.kernel32.CloseHandle(h)
    return code.value == 259


def tail(path, nbytes=200000):
    try:
        with open(path, 'rb') as f:
            f.seek(0, 2); size = f.tell(); f.seek(max(0, size - nbytes))
            return f.read().decode('utf-8', 'replace').splitlines()
    except OSError:
        return []


def main():
    argv = sys.argv[1:]; cmd = []
    if '--' in argv: i = argv.index('--'); argv, cmd = argv[:i], argv[i + 1:]
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--ad', required=True, help='short job name')
    p.add_argument('--log', action='append', default=[], help='log file to watch (repeatable)')
    p.add_argument('--pid', type=int, help='job is done when this process ends')
    p.add_argument('--done-file', help='job is done when this file exists')
    p.add_argument('--done-regex', help='job is done when a new log line matches')
    p.add_argument('--fail-regex', help='job failed when a new log line matches (wake at once)')
    p.add_argument('--stall-min', type=float, default=15, help='wake if no log grows for this long (0 = off)')
    p.add_argument('--ram-min-gb', type=float, default=1.0, help='wake if free RAM stays below this (0 = off)')
    p.add_argument('--ram-for-min', type=float, default=3)
    p.add_argument('--timeout-min', type=float, default=0, help='wake after this long (0 = off)')
    p.add_argument('--every', type=float, default=15, help='poll seconds')
    p.add_argument('--tail', type=int, default=12, help='log lines in the package')
    a = p.parse_args(argv)
    proc = None; logs = list(a.log)
    if cmd:
        os.makedirs(LOGDIR, exist_ok=True)
        own = os.path.join(LOGDIR, re.sub(r'[^\w.-]', '_', a.ad) + '.log')
        # ders bekci-bash-c-wsl-1113: Windows'ta yalin 'bash' WSL'e gider ve coker -> Git Bash'e cevir
        gb = r'C:\Program Files\Git\bin\bash.exe'
        if os.name == 'nt' and os.path.basename(cmd[0]).lower() in ('bash', 'bash.exe') and os.path.exists(gb):
            cmd = [gb] + cmd[1:]
        proc = subprocess.Popen(cmd, stdout=open(own, 'wb'), stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        logs.append(own)
    elif not (a.pid or a.done_file or a.done_regex):
        print('bekci: give a command after --, or --pid / --done-file / --done-regex'); return 5
    t0 = time.time(); last_grow = t0; low_since = None
    # an already-running job: only lines written from now on count
    pos = {l: (os.path.getsize(l) if os.path.exists(l) and l in a.log else 0) for l in logs}

    def new_lines():
        out = []; grew = False
        for l in logs:
            try: size = os.path.getsize(l)
            except OSError: continue
            if size < pos[l]: pos[l] = 0
            if size > pos[l]:
                grew = True
                with open(l, 'rb') as f:
                    f.seek(pos[l]); out += f.read(2000000).decode('utf-8', 'replace').splitlines(); pos[l] = f.tell()
        return out, grew

    def finish(code, reason):
        mins = (time.time() - t0) / 60
        print(f"BEKCI {a.ad}: {NAMES[code]} - {reason} ({mins:.0f} dk, bos RAM {free_ram_gb():.1f} GB)")
        for l in logs:
            lines = tail(l)
            errs = [x for x in lines if re.search(a.fail_regex or ERR, x)][-6:]
            print(f'-- {l}')
            if errs and code:
                print('hata satirlari:')
                for x in errs: print('  ' + x.strip()[:220])
            print(f'son {a.tail} satir:')
            for x in lines[-a.tail:]: print('  ' + x.rstrip()[:220])
        alive = (proc and proc.poll() is None) or (a.pid and pid_alive(a.pid))
        if code in (1, 2, 3, 4) and alive:
            print(f"is hala calisiyor (pid {proc.pid if proc else a.pid}); sebebi giderince bekciyi --pid/--log ile yeniden baslat")
        return code

    while True:
        time.sleep(a.every)
        lines, grew = new_lines(); now = time.time()
        if grew: last_grow = now
        if a.fail_regex:
            hit = [x for x in lines if re.search(a.fail_regex, x)]
            if hit: return finish(1, 'hata deseni: ' + hit[0].strip()[:120])
        if a.done_regex and any(re.search(a.done_regex, x) for x in lines): return finish(0, 'bitis deseni goruldu')
        if a.done_file and os.path.exists(a.done_file): return finish(0, 'cikti dosyasi olustu')
        if proc and proc.poll() is not None:
            return finish(0 if proc.returncode == 0 else 1, f'komut cikis kodu {proc.returncode}')
        if a.pid and not pid_alive(a.pid): return finish(0, f'pid {a.pid} sonlandi (cikis kodu bilinmiyor, ciktiyi kontrol et)')
        if a.stall_min and logs and now - last_grow > a.stall_min * 60: return finish(2, f'log {a.stall_min:g} dk sessiz')
        if a.ram_min_gb:
            low_since = (low_since or now) if free_ram_gb() < a.ram_min_gb else None
            if low_since and now - low_since > a.ram_for_min * 60: return finish(3, f'bos RAM {a.ram_for_min:g} dk boyunca {a.ram_min_gb} GB alti')
        if a.timeout_min and now - t0 > a.timeout_min * 60: return finish(4, f'{a.timeout_min:g} dk doldu')


if __name__ == '__main__':
    sys.exit(main())
