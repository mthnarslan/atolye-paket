#!/bin/bash
# run_when_free.sh <film folder> <start stage>: waits until at most 4 drive.py run and 4 GB RAM is free, then runs the film.
F="$1"; S="$2"; N=$(basename "$F")
while true; do
  n=$(powershell -NoProfile -c "@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | ? { \$_.CommandLine -match 'drive.py' }).Count")
  free=$(powershell -NoProfile -c "[int]((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB*10)")
  [ "${n//[^0-9]/}" -le 4 ] && [ "${free//[^0-9]/}" -ge 40 ] && break
  sleep 60
done
echo "$(date '+%Y-%m-%d %H:%M:%S') $N manual run from stage $S" >> /c/Users/meteh/Belgesel_Teslim/batch.log
cd /c/Users/meteh/Kanallar/Engineered/tools && PYTHONIOENCODING=utf-8 python drive.py "$F" "$S" 4 >> "/c/Users/meteh/Belgesel_Teslim/queue/$N.log" 2>&1; rc=$?
echo "$(date '+%Y-%m-%d %H:%M:%S') $N manual run exit $rc" >> /c/Users/meteh/Belgesel_Teslim/batch.log
