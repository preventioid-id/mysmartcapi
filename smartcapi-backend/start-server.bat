@echo off
REM ============================================
REM SmartCAPI Backend - Auto Start Script
REM ============================================

echo.
echo ╔══════════════════════════════════════════╗
echo ║     SmartCAPI Backend Launcher           ║
echo ╚══════════════════════════════════════════╝
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [ERROR] Virtual environment tidak ditemukan!
    echo.
    echo Jalankan setup dulu:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Kill any existing processes on port 8001
echo [INFO] Checking port 8001...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do (
    echo [INFO] Stopping existing server on port 8001 (PID: %%a)...
    taskkill /F /PID %%a >nul 2>&1
)

REM Kill any Python processes that might interfere
echo [INFO] Cleaning up old Python processes...
taskkill /IM python.exe /F >nul 2>&1

timeout /t 2 /nobreak >nul

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if FastAPI is installed
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] FastAPI tidak terinstall!
    echo.
    echo Install dependencies dulu:
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo [INFO] Starting server on port 8001...
echo.
echo ┌──────────────────────────────────────────┐
echo │ Server akan tersedia di:                 │
echo │ http://127.0.0.1:8001                    │
echo │ http://127.0.0.1:8001/docs (API Docs)   │
echo └──────────────────────────────────────────┘
echo.
echo Press CTRL+C to stop server
echo.

REM Start server
python app.py

REM If server stopped unexpectedly
echo.
echo [INFO] Server stopped.
pause