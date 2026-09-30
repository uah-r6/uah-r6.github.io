$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..'))
& .\.venv\Scripts\python.exe -m r6stats admin
