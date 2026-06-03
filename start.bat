@echo off
echo Starting SynthAnalyst + Lead Triager...


start "Lead Triager" cmd /k "cd /d %~dp0 && python main.py"
start "ngrok" cmd /k "cd /d %~dp0 && ngrok http 5678"

echo All services running.