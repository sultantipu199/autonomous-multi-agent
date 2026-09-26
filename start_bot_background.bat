@echo off
REM ==============================================================================
REM Start Telegram Bot in Background (Windows Detached Process)
REM ==============================================================================
cd /d "%~dp0"
echo Starting Autonomous Multi-Agent Telegram Bot in background...

powershell -Command "Start-Process python -ArgumentList 'run_bot.py' -WindowStyle Hidden"

timeout /t 2 /nobreak >nul
echo Telegram Bot launched in background!
echo Check data\bot.log for live logs.
pause
