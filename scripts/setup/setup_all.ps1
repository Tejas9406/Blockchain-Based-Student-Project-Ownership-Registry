# ==============================================================================
# Master Setup Script for Windows PowerShell
# Installs dependencies for Frontend, Backend, and Blockchain modules
# ==============================================================================

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Student Project Ownership Registry - Master Setup" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

$RootPath = (Get-Item -Path $PSScriptRoot).Parent.Parent.FullName
Set-Location $RootPath

# 1. Environment Files Initialization
Write-Host "`n[1/4] Initializing Environment Variables (.env)..." -ForegroundColor Yellow
if (-not (Test-Path "$RootPath\.env")) {
    Copy-Item "$RootPath\.env.example" "$RootPath\.env"
    Write-Host " -> Created root .env" -ForegroundColor Green
}
if (-not (Test-Path "$RootPath\frontend\.env")) {
    Copy-Item "$RootPath\frontend\.env.example" "$RootPath\frontend\.env"
    Write-Host " -> Created frontend\.env" -ForegroundColor Green
}
if (-not (Test-Path "$RootPath\backend\.env")) {
    Copy-Item "$RootPath\backend\.env.example" "$RootPath\backend\.env"
    Write-Host " -> Created backend\.env" -ForegroundColor Green
}
if (-not (Test-Path "$RootPath\blockchain\.env")) {
    Copy-Item "$RootPath\blockchain\.env.example" "$RootPath\blockchain\.env"
    Write-Host " -> Created blockchain\.env" -ForegroundColor Green
}

# 2. Frontend Setup
Write-Host "`n[2/4] Installing Frontend Dependencies (npm)..." -ForegroundColor Yellow
Set-Location "$RootPath\frontend"
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "Frontend npm install failed." -ForegroundColor Red
} else {
    Write-Host "Frontend dependencies installed successfully." -ForegroundColor Green
}

# 3. Backend Setup
Write-Host "`n[3/4] Setting up Backend Python Virtual Environment..." -ForegroundColor Yellow
Set-Location "$RootPath\backend"
if (-not (Test-Path "$RootPath\backend\.venv")) {
    python -m venv .venv
}
& "$RootPath\backend\.venv\Scripts\pip.exe" install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Backend pip install failed." -ForegroundColor Red
} else {
    Write-Host "Backend dependencies installed successfully." -ForegroundColor Green
}

# 4. Blockchain Setup
Write-Host "`n[4/4] Installing Blockchain Dependencies (Hardhat)..." -ForegroundColor Yellow
Set-Location "$RootPath\blockchain"
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "Blockchain npm install failed." -ForegroundColor Red
} else {
    Write-Host "Blockchain dependencies installed successfully." -ForegroundColor Green
}

Set-Location $RootPath
Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "Setup Completed! You can now run tests or start services." -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
