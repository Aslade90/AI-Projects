@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_EXE=C:\Users\sladeand\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "REPORT_URL=http://127.0.0.1:8765/report/manufacturing_report.html"

powershell -NoProfile -ExecutionPolicy Bypass -Command "if (-not (Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' })) { Start-Process -FilePath '%PYTHON_EXE%' -ArgumentList 'tools\serve_report.py' -WorkingDirectory '%~dp0' -WindowStyle Hidden; Start-Sleep -Seconds 1 }"

start "" "%REPORT_URL%"
endlocal
