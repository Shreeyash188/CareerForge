# ============================================================
# CareerForge — One-Click Startup Script (PowerShell)
# Launches backend (FastAPI) and frontend (Next.js) together
# Usage: .\start.ps1  or double-click start.bat
# ============================================================

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║         🔥 CareerForge Launcher 🔥           ║" -ForegroundColor Cyan
Write-Host "  ║   AI-Powered Job Application Assistant       ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Definition

# ── Start Backend ────────────────────────────────────────────
Write-Host "[1/2] Starting Backend (FastAPI) on http://localhost:8000 ..." -ForegroundColor Yellow

$backendJob = Start-Job -ScriptBlock {
    param($root)
    Set-Location "$root\backend"
    
    # Try venv in backend, then root
    if (Test-Path "$root\backend\venv\Scripts\Activate.ps1") {
        & "$root\backend\venv\Scripts\Activate.ps1"
    } elseif (Test-Path "$root\venv\Scripts\Activate.ps1") {
        & "$root\venv\Scripts\Activate.ps1"
    }
    
    # Set PYTHONPATH so backend can import from root
    $env:PYTHONPATH = $root
    
    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload 2>&1
} -ArgumentList $ROOT

# ── Start Frontend ───────────────────────────────────────────
Write-Host "[2/2] Starting Frontend (Next.js) on http://localhost:3000 ..." -ForegroundColor Yellow

$frontendJob = Start-Job -ScriptBlock {
    param($root)
    Set-Location "$root\frontend"
    npm run dev 2>&1
} -ArgumentList $ROOT

# ── Wait for servers to boot ─────────────────────────────────
Write-Host ""
Write-Host "Waiting for servers to start..." -ForegroundColor Gray
Start-Sleep -Seconds 4

# ── Open browser ─────────────────────────────────────────────
Write-Host ""
Write-Host "  ✅ Backend:  http://localhost:8000/docs" -ForegroundColor Green
Write-Host "  ✅ Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "Opening browser..." -ForegroundColor Gray
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "Press Ctrl+C to stop both servers." -ForegroundColor DarkGray
Write-Host "─────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

# ── Stream logs until user hits Ctrl+C ───────────────────────
try {
    while ($true) {
        # Print backend logs
        $backendOutput = Receive-Job -Job $backendJob -ErrorAction SilentlyContinue
        if ($backendOutput) {
            foreach ($line in $backendOutput) {
                Write-Host "[BACKEND] $line" -ForegroundColor DarkCyan
            }
        }

        # Print frontend logs
        $frontendOutput = Receive-Job -Job $frontendJob -ErrorAction SilentlyContinue
        if ($frontendOutput) {
            foreach ($line in $frontendOutput) {
                Write-Host "[FRONTEND] $line" -ForegroundColor DarkMagenta
            }
        }

        Start-Sleep -Milliseconds 500
    }
}
finally {
    Write-Host ""
    Write-Host "Shutting down..." -ForegroundColor Yellow
    Stop-Job -Job $backendJob -ErrorAction SilentlyContinue
    Stop-Job -Job $frontendJob -ErrorAction SilentlyContinue
    Remove-Job -Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job -Job $frontendJob -ErrorAction SilentlyContinue
    Write-Host "✅ All servers stopped." -ForegroundColor Green
}
