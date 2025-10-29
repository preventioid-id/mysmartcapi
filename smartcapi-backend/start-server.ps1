# ============================================
# SmartCAPI Backend - PowerShell Launcher
# ============================================

$PORT = 8001
$HOST = "0.0.0.0"

Write-Host ""
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     SmartCAPI Backend Launcher           ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "[ERROR] Virtual environment tidak ditemukan!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Jalankan setup dulu:" -ForegroundColor Yellow
    Write-Host "  python -m venv venv" -ForegroundColor Yellow
    Write-Host "  venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "  pip install -r requirements.txt" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Kill existing processes on port
Write-Host "[INFO] Checking port $PORT..." -ForegroundColor Yellow

$connections = Get-NetTCPConnection -LocalPort $PORT -ErrorAction SilentlyContinue
if ($connections) {
    foreach ($conn in $connections) {
        $processId = $conn.OwningProcess
        Write-Host "[INFO] Stopping process on port $PORT (PID: $processId)..." -ForegroundColor Yellow
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
}

# Activate virtual environment
Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Green
& "venv\Scripts\Activate.ps1"

# Check if FastAPI is installed
try {
    python -c "import fastapi" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "FastAPI not installed"
    }
} catch {
    Write-Host "[ERROR] FastAPI tidak terinstall!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install dependencies dulu:" -ForegroundColor Yellow
    Write-Host "  pip install -r requirements.txt" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Display server info
Write-Host "[INFO] Starting server on port $PORT..." -ForegroundColor Green
Write-Host ""
Write-Host "┌──────────────────────────────────────────┐" -ForegroundColor Cyan
Write-Host "│ Server tersedia di:                      │" -ForegroundColor Cyan
Write-Host "│ http://127.0.0.1:$PORT                    │" -ForegroundColor White
Write-Host "│ http://127.0.0.1:$PORT/docs (Swagger)    │" -ForegroundColor White  
Write-Host "│ http://127.0.0.1:$PORT/redoc (ReDoc)     │" -ForegroundColor White
Write-Host "└──────────────────────────────────────────┘" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press CTRL+C to stop server" -ForegroundColor Yellow
Write-Host ""

# Start server
python app.py

# If server stopped
Write-Host ""
Write-Host "[INFO] Server stopped." -ForegroundColor Yellow
Read-Host "Press Enter to exit"