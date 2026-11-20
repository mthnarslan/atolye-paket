#!/bin/bash
# Restart the documentary bridge (:8099) if /health fails twice in a row. Logs to Belgesel_Teslim\batch.log.
fails=0
while true; do
  if curl -s -m 10 http://127.0.0.1:8099/health | grep -q PASS; then fails=0; else fails=$((fails+1)); fi
  if [ $fails -ge 2 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') bridge DOWN -> restart" >> /c/Users/meteh/Belgesel_Teslim/batch.log
    powershell -NoProfile -c "\$env:PYTHONIOENCODING='utf-8'; Start-Process python -WorkingDirectory C:\Users\meteh\.gemini\scripts -WindowStyle Hidden -ArgumentList 'documentary_native_bridge.py' -RedirectStandardOutput C:\Users\meteh\.gemini\scripts\bridge_\$(Get-Date -f HHmm).log -RedirectStandardError C:\Users\meteh\.gemini\scripts\bridge_\$(Get-Date -f HHmm).err.log"
    sleep 30; fails=0
  fi
  sleep 30
done
