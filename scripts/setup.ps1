$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..'))
if (-not (Test-Path '.venv')) { py -3.12 -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
Push-Location web
try {
    npm.cmd ci
    if ($LASTEXITCODE -ne 0) { throw 'Node dependency installation failed.' }
    npm.cmd run build:admin
    if ($LASTEXITCODE -ne 0) { throw 'Admin web build failed.' }
} finally { Pop-Location }
& .\.venv\Scripts\python.exe -m r6stats init
if ($LASTEXITCODE -ne 0) { throw 'Database initialization failed.' }
& (Join-Path $PSScriptRoot 'install-parser.ps1')
Write-Host 'Next: double-click Start NECC Admin.cmd to open the browser admin.'
