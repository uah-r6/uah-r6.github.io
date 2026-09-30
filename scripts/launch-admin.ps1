$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$adminUrl = 'http://127.0.0.1:8000/admin'
$sessionUrl = 'http://127.0.0.1:8000/api/admin/session'
$runtimeUrl = 'http://127.0.0.1:8000/api/admin/runtime'
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Setup has not been run. Run scripts\setup.ps1 once first.'
}

function Get-AdminSession {
    try { return Invoke-RestMethod -Uri $sessionUrl -TimeoutSec 2 }
    catch { return $null }
}

function Get-AdminRuntime {
    try { return Invoke-RestMethod -Uri $runtimeUrl -TimeoutSec 2 }
    catch { return $null }
}

function Test-CurrentRuntime($runtime) {
    if ($null -eq $runtime -or $runtime.project_root -ine $projectRoot -or
        $runtime.r6stats_file -ine (Join-Path $projectRoot 'r6stats\__init__.py') -or
        $runtime.siege_dissect_file -ine (Join-Path $projectRoot 'r6stats\parser\siege_dissect.py') -or
        $runtime.server_file -ine (Join-Path $projectRoot 'r6stats\admin\server.py')) {
        return $false
    }
    $files = @(Get-ChildItem -LiteralPath (Join-Path $projectRoot 'r6stats') -Recurse -File -Filter '*.py')
    if (@($runtime.source_hashes.PSObject.Properties).Count -ne $files.Count) { return $false }
    foreach ($file in $files) {
        $relative = $file.FullName.Substring($projectRoot.Length + 1).Replace('\', '/')
        $loadedHash = $runtime.source_hashes.PSObject.Properties[$relative].Value
        if (-not $loadedHash -or $loadedHash -ine (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash) {
            return $false
        }
    }
    return $true
}

function Get-Listener {
    return Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
}

function Test-LegacyProjectListener($listener) {
    if ($null -eq $listener) { return $false }
    $serverProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
    if ($null -eq $serverProcess -or $serverProcess.CommandLine -notmatch '\-m\s+r6stats\s+admin') {
        return $false
    }
    $parent = Get-CimInstance Win32_Process -Filter "ProcessId=$($serverProcess.ParentProcessId)"
    return $null -ne $parent -and $parent.ExecutablePath -ieq $pythonPath -and
        $parent.CommandLine -match '\-m\s+r6stats\s+admin'
}

$session = Get-AdminSession
if ($null -ne $session) {
    $runtime = Get-AdminRuntime
    if (-not (Test-CurrentRuntime $runtime)) {
        $listener = Get-Listener
        $belongsToProject = ($null -ne $runtime -and $runtime.project_root -ieq $projectRoot) -or
                            (Test-LegacyProjectListener $listener)
        if (-not $belongsToProject -or $null -eq $listener) {
            throw 'Port 8000 has an admin server that cannot be verified as this project. Stop it before launching NECC Admin.'
        }
        Write-Host "Restarting outdated NECC admin process $($listener.OwningProcess)..."
        Stop-Process -Id $listener.OwningProcess -Force
        for ($attempt = 0; $attempt -lt 30 -and $null -ne (Get-Listener); $attempt++) {
            Start-Sleep -Milliseconds 200
        }
        if ($null -ne (Get-Listener)) { throw 'Old admin process did not release port 8000.' }
        $session = $null
    }
}

if ($null -eq $session) {
    if ($null -ne (Get-Listener)) { throw 'Port 8000 is occupied by another process.' }
    Start-Process -FilePath $pythonPath -ArgumentList '-m', 'r6stats', 'admin' -WorkingDirectory $projectRoot -WindowStyle Hidden | Out-Null
    $ready = $false
    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        Start-Sleep -Milliseconds 500
        if ($null -ne (Get-AdminSession) -and (Test-CurrentRuntime (Get-AdminRuntime))) {
            $ready = $true
            break
        }
    }
    if (-not $ready) {
        throw 'Local admin did not start from current source. Run scripts\start-admin.ps1 to see the server error.'
    }
}

$runtime = Get-AdminRuntime
Write-Host "Admin PID: $($runtime.pid)"
Write-Host "Python: $($runtime.sys_executable)"
Write-Host "Working directory: $($runtime.cwd)"
Write-Host "r6stats: $($runtime.r6stats_file)"
Write-Host "parser: $($runtime.siege_dissect_file)"
Write-Host "server: $($runtime.server_file)"
$browserLaunch = Start-Process -FilePath $adminUrl -PassThru
Write-Host "Browser launch requested: $adminUrl"
$browserName = if ($null -ne $browserLaunch) { $browserLaunch.ProcessName } else { 'default URL handler' }
$browserPid = if ($null -ne $browserLaunch) { $browserLaunch.Id } else { '' }
if ($null -ne $browserLaunch) { Write-Host "Browser handler: $browserName (PID $browserPid)" }
$logDirectory = Join-Path $projectRoot 'data\logs'
New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
$launchLog = Join-Path $logDirectory 'admin-launch.log'
$entry = if ($env:NECC_LAUNCHER_ENTRY) { $env:NECC_LAUNCHER_ENTRY } else { 'PowerShell' }
Add-Content -LiteralPath $launchLog -Value "$(Get-Date -Format o) | entry=$entry | python=$($runtime.sys_executable) | server_pid=$($runtime.pid) | browser=$browserName | browser_pid=$browserPid | url=$adminUrl"
