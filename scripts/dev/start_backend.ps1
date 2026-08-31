# Start FastAPI Backend Locally
$RootPath = (Get-Item -Path $PSScriptRoot).Parent.Parent.FullName
Set-Location "$RootPath\backend"

Write-Host "Starting FastAPI Backend server on http://localhost:8000..." -ForegroundColor Cyan
& "$RootPath\backend\.venv\Scripts\uvicorn.exe" app.main:app --reload --host 0.0.0.0 --port 8000
