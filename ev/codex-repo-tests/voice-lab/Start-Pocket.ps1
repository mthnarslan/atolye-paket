$ErrorActionPreference = "SilentlyContinue"
$Port = 7863
# Listen only, as in Start-Sopro.ps1: TIME_WAIT left by a stopped service is not a service.
$Conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($Conn) {
    Write-Host "Pocket port $Port already listening."
    exit 0
}
# Pocket TTS runs in its own venv (its torch differs from the bridge's) on the CPU.
$Dir = "C:\Users\meteh\codex-repo-tests\voice-lab\pocket-tts"
$Log = "$Dir\pocket_server.log"
Start-Process -FilePath "$Dir\.venv\Scripts\python.exe" `
    -ArgumentList "$Dir\pocket_serve.py" `
    -WorkingDirectory $Dir `
    -RedirectStandardOutput $Log -RedirectStandardError "$Log.err" -WindowStyle Hidden
Write-Host "Pocket started in background on port $Port."
