#!/bin/bash
# waits for the running EP08 drive.py to end, then requeues EP08 from stage 3 (its manifest query now matches the current topic)
F='C:\Users\meteh\Downloads\Compressed\drive-download-20261030T074711Z-1-001\EP08_Peraliya_Tsunami_Train_2004'
while [ "$(powershell -NoProfile -c "@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | ? { \$_.CommandLine -match 'drive.py' -and \$_.CommandLine -match 'EP08' }).Count")" != "0" ]; do sleep 30; done
[ -f /c/Users/meteh/CodexOutputs/EP08_Peraliya_Tsunami_Train_2004/03_materials/planning/material_plan.json ] && exit 0
exec bash run_when_free.sh "$F" 3
