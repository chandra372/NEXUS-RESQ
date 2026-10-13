@echo off
echo ========================================================
echo           Starting NEXUS RESQ Systems
echo ========================================================
echo.
echo [1/2] Launching Backend on http://127.0.0.1:8000 ...
start "NEXUS RESQ - Backend" cmd /k "cd /d "%~dp0nexus-resq\backend" && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Launching Frontend on http://localhost:5173 ...
start "NEXUS RESQ - Frontend" cmd /k "cd /d "%~dp0nexus-resq\frontend" && npm run dev"

echo.
echo Both services are starting in separate windows!
echo - Frontend: http://localhost:5173
echo - Backend:  http://127.0.0.1:8000/docs
echo ========================================================
