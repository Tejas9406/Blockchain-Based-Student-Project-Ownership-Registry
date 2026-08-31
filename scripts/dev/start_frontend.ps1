# Start React Vite Frontend Locally
$RootPath = (Get-Item -Path $PSScriptRoot).Parent.Parent.FullName
Set-Location "$RootPath\frontend"

Write-Host "Starting React Frontend dev server on http://localhost:5173..." -ForegroundColor Cyan
npm run dev
