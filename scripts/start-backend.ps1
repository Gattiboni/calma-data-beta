# Start FastAPI backend (Windows PowerShell)
# Usage: 1) Open PowerShell at repo root  2) Set-ExecutionPolicy -Scope Process Bypass -Force  3) .\scripts\start-backend.ps1

$ErrorActionPreference = "Stop"

# Go to backend folder
Set-Location (Join-Path $PSScriptRoot "..\backend")

# Pick Python launcher
$python = $null
if (Get-Command py -ErrorAction SilentlyContinue) { $python = "py" }
elseif (Get-Command python -ErrorAction SilentlyContinue) { $python = "python" }
else { Write-Error "Python não encontrado. Instale Python 3.10+ e reexecute." }

# Create venv if not exists
if (-not (Test-Path ".venv")) {
  & $python -m venv .venv
}

# Install deps
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt

Write-Host "\n[Backend] Servindo em http://localhost:8001 (Ctrl+C para parar)" -ForegroundColor Green
# Run uvicorn (reload)
& ".\.venv\Scripts\python.exe" -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload