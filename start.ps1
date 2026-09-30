$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path $PSScriptRoot).Path
Set-Location $projectRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$settingsPath = Join-Path $projectRoot 'config\settings.json'
$adminPage = Join-Path $projectRoot 'web\admin-dist\admin.html'
$nodeModules = Join-Path $projectRoot 'web\node_modules'
$localParser = Join-Path $projectRoot '.local-tools\bin\siege-dissect.exe'

if (-not (Test-Path -LiteralPath $pythonPath) -or
    -not (Test-Path -LiteralPath $settingsPath) -or
    -not (Test-Path -LiteralPath $adminPage) -or
    -not (Test-Path -LiteralPath $nodeModules) -or
    (-not (Test-Path -LiteralPath $localParser) -and -not (Get-Command siege-dissect -ErrorAction SilentlyContinue))) {
    Write-Host 'Completing first-time setup...'
    & (Join-Path $projectRoot 'scripts\setup.ps1')
}

# Activate the project environment for this launcher process. The background
# server itself is started with its absolute .venv Python path.
& (Join-Path $projectRoot '.venv\Scripts\Activate.ps1')
& (Join-Path $projectRoot 'scripts\launch-admin.ps1')
