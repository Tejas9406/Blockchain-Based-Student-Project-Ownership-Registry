# ==============================================================================
# Master Test Runner Script for Windows PowerShell
# Executes test suites across Frontend, Backend, and Blockchain modules
# ==============================================================================

$RootPath = (Get-Item -Path $PSScriptRoot).Parent.Parent.FullName
$FailedModules = @()

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Student Project Ownership Registry - Monorepo Test Runner" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

# 1. Frontend Tests
Write-Host "`n[1/3] Running Frontend Tests (Vitest)..." -ForegroundColor Yellow
Set-Location "$RootPath\frontend"
npm test
if ($LASTEXITCODE -ne 0) {
    $FailedModules += "Frontend"
    Write-Host "[FAIL] Frontend Tests Failed!" -ForegroundColor Red
} else {
    Write-Host "[PASS] Frontend Tests Passed." -ForegroundColor Green
}

# 2. Backend Tests
Write-Host "`n[2/3] Running Backend Tests (pytest)..." -ForegroundColor Yellow
Set-Location "$RootPath\backend"
& "$RootPath\backend\.venv\Scripts\pytest.exe"
if ($LASTEXITCODE -ne 0) {
    $FailedModules += "Backend"
    Write-Host "[FAIL] Backend Tests Failed!" -ForegroundColor Red
} else {
    Write-Host "[PASS] Backend Tests Passed." -ForegroundColor Green
}

# 3. Blockchain Tests
Write-Host "`n[3/3] Running Blockchain Smart Contract Tests (Hardhat)..." -ForegroundColor Yellow
Set-Location "$RootPath\blockchain"
npx hardhat test
if ($LASTEXITCODE -ne 0) {
    $FailedModules += "Blockchain"
    Write-Host "[FAIL] Blockchain Tests Failed!" -ForegroundColor Red
} else {
    Write-Host "[PASS] Blockchain Tests Passed." -ForegroundColor Green
}

Set-Location $RootPath
Write-Host "`n================================================================" -ForegroundColor Cyan
if ($FailedModules.Count -eq 0) {
    Write-Host "[SUCCESS] ALL TESTS PASSED! (Frontend, Backend, Blockchain)" -ForegroundColor Green
    exit 0
} else {
    $FailList = $FailedModules -join ", "
    Write-Host "[ERROR] Test failures detected in: $FailList" -ForegroundColor Red
    exit 1
}
