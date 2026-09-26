@echo off
REM ==============================================================================
REM Stop Telegram Bot Supervisor & Process
REM ==============================================================================
echo Stopping Telegram Bot processes...
powershell -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*run_bot.py*' -or $_.CommandLine -like '*main.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
echo Bot processes stopped.
pause
