# Start Hardhat Local Blockchain Node
$RootPath = (Get-Item -Path $PSScriptRoot).Parent.Parent.FullName
Set-Location "$RootPath\blockchain"

Write-Host "Starting Local Hardhat EVM Node on http://127.0.0.1:8545..." -ForegroundColor Cyan
npx hardhat node
