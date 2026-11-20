#!/bin/bash
# run_when_free2.sh <film folder> <start stage>: same arguments as run_when_free.sh, but admits one film at a time.
# - in-flight films = unique film folders on drive.py command lines (Git Bash fork stubs repeat a command line)
# - admit only while that count is below MAX_FILMS (4) and free RAM >= 4.0 GB
# - admission lock dir .admit_lock (PID + epoch), held HOLD_S (90) s after the film starts so its RAM shows
# - a lock is stale when its PID is dead or it is older than STALE_S (900) s
# - poll interval is random between POLL_MIN and POLL_MAX (45-75) s
# Test hooks (env): ADMIT_LOCK, DRIVE_PY, DRIVE_MATCH, FAKE_FREE_GB (number or file holding it), BATCH_LOG, QUEUE_DIR,
# MAX_FILMS, HOLD_S, STALE_S, POLL_MIN, POLL_MAX, MIN_FREE_GB.
F="$1"; S="$2"; N=$(basename "$F")
TOOLS=/c/Users/meteh/Kanallar/Engineered/tools
LOCK="${ADMIT_LOCK:-$TOOLS/.admit_lock}"
DRIVE_PY="${DRIVE_PY:-$TOOLS/drive.py}"
DRIVE_MATCH="${DRIVE_MATCH:-drive.py}"
BATCH_LOG="${BATCH_LOG:-/c/Users/meteh/Belgesel_Teslim/batch.log}"
QUEUE_DIR="${QUEUE_DIR:-/c/Users/meteh/Belgesel_Teslim/queue}"
MAX_FILMS="${MAX_FILMS:-4}"; HOLD_S="${HOLD_S:-90}"; STALE_S="${STALE_S:-900}"
POLL_MIN="${POLL_MIN:-45}"; POLL_MAX="${POLL_MAX:-75}"; MIN_FREE_GB="${MIN_FREE_GB:-4.0}"
mkdir -p "$QUEUE_DIR"
HELD=0
release() { [ "$HELD" = 1 ] && [ "$(cut -d' ' -f1 "$LOCK/info" 2>/dev/null)" = "$$" ] && rm -rf "$LOCK"; HELD=0; }
trap release EXIT

inflight() {  # number of unique film folders among running drive.py command lines
  local lines
  if [ -n "$PROC_LIST_FILE" ]; then lines=$(cat "$PROC_LIST_FILE")
  else lines=$(powershell -NoProfile -c "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | % CommandLine"); fi
  echo "$lines" | tr -d '\r' | grep -E "$DRIVE_MATCH" \
    | sed -E "s/^.*($DRIVE_MATCH)\"? +//; s/^\"([^\"]*)\".*/\1/; s/^([^ ]*).*/\1/; s#[\\/]+\$##; s#^.*[\\/]##" | sort -u | grep -c .
}
free_gb() {  # free physical RAM in GB, one decimal
  if [ -n "$FAKE_FREE_GB" ]; then [ -f "$FAKE_FREE_GB" ] && cat "$FAKE_FREE_GB" || echo "$FAKE_FREE_GB"; return; fi
  powershell -NoProfile -c "[math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB,1)" | tr -d '\r' | tr ',' '.'
}
lock_stale() {  # 0 = stale; prints the info it judged
  local info pid ts now
  now=$(date +%s)
  info=$(cat "$LOCK/info" 2>/dev/null)
  if [ -z "$info" ]; then  # holder has not written yet: give it 30 s
    local m; m=$(stat -c %Y "$LOCK" 2>/dev/null || echo "$now"); [ $((now - m)) -gt 30 ]; return
  fi
  read -r pid ts _ <<< "$info"
  [ $((now - ts)) -gt "$STALE_S" ] && return 0
  kill -0 "$pid" 2>/dev/null && return 1
  return 0
}
take_lock() {
  if mkdir "$LOCK" 2>/dev/null; then :; else
    lock_stale || return 1
    local before; before=$(cat "$LOCK/info" 2>/dev/null)
    local dead="$LOCK.dead.$$"
    mv "$LOCK" "$dead" 2>/dev/null || return 1   # atomic: one breaker wins
    if [ "$(cat "$dead/info" 2>/dev/null)" != "$before" ]; then mv "$dead" "$LOCK" 2>/dev/null; return 1; fi
    rm -rf "$dead"
    mkdir "$LOCK" 2>/dev/null || return 1
  fi
  echo "$$ $(date +%s) $N" > "$LOCK/info"; HELD=1
}

while true; do
  if take_lock; then
    n=$(inflight); free=$(free_gb)
    if [ "${n:-9}" -lt "$MAX_FILMS" ] && awk "BEGIN{exit !(${free:-0} >= $MIN_FREE_GB)}"; then break; fi
    release
  fi
  sleep $((POLL_MIN + RANDOM % (POLL_MAX - POLL_MIN + 1)))
done

echo "$(date '+%Y-%m-%d %H:%M:%S') $N manual run from stage $S (admitted, $n in flight, free $free GB)" >> "$BATCH_LOG"
cd "$(dirname "$DRIVE_PY")" && PYTHONIOENCODING=utf-8 python "$DRIVE_PY" "$F" "$S" 4 >> "$QUEUE_DIR/$N.log" 2>&1 &
dpid=$!
sleep "$HOLD_S"; release
wait "$dpid"; rc=$?
echo "$(date '+%Y-%m-%d %H:%M:%S') $N manual run exit $rc" >> "$BATCH_LOG"
