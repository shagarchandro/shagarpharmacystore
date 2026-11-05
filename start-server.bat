@echo off
rem Starts the real server (real accounts, passwords and two-step login). Needs Python 3.
cd /d "%~dp0"
echo Starting the shop server. Keep this window open. Close it to stop the server.
start "" /b cmd /c "timeout /t 3 >nul & start http://localhost:8000/admin/login.html"
where python >nul 2>nul && (python server\server.py %*) || (py -3 server\server.py %*)
pause
