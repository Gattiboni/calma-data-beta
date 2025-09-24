# Start React + Vite frontend (Windows PowerShell)
# Usage: 1) Open PowerShell at repo root  2) Set-ExecutionPolicy -Scope Process Bypass -Force  3) .\scripts\start-frontend.ps1

$ErrorActionPreference = "Stop"

# Go to frontend folder
Set-Location (Join-Path $PSScriptRoot "..\frontend")

# Ensure Node is available
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
  Write-Error "Node.js não encontrado. Instale Node 18~20 antes de continuar."
}

# Ensure Yarn via Corepack
& corepack enable | Out-Null
& corepack prepare yarn@stable --activate | Out-Null

# Ensure Yarn classic node_modules (Windows-friendly)
$yrc = ".yarnrc.yml"
if (-not (Test-Path $yrc)) {
  @"
nodeLinker: node-modules
enableGlobalCache: true
"@ | Out-File -Encoding utf8 $yrc
}

# Install deps and start dev server
& yarn install
Write-Host "\n[Frontend] Servindo em http://localhost:3000 (Ctrl+C para parar)" -ForegroundColor Green
& yarn start