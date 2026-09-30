$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$toolRoot = Join-Path $projectRoot '.local-tools'
$parserPath = Join-Path $toolRoot 'bin\siege-dissect.exe'
$sourceRoot = Join-Path $projectRoot 'third_party\siege-dissect'
$manifestPath = Join-Path $toolRoot 'bin\parser-source.txt'
$sources = @(Get-ChildItem -LiteralPath $sourceRoot -Recurse -File |
    Where-Object { $_.Extension -eq '.go' -or $_.Name -in @('go.mod', 'go.sum') } |
    Sort-Object FullName)
$manifest = ($sources | ForEach-Object {
    $relative = $_.FullName.Substring($sourceRoot.Length + 1)
    "$relative $((Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash)"
}) -join "`n"
if ((Test-Path -LiteralPath $parserPath) -and
    (Test-Path -LiteralPath $manifestPath) -and
    (Get-Content -LiteralPath $manifestPath -Raw).TrimEnd() -eq $manifest) {
    Write-Host 'Local siege-dissect build matches repository source.'
    exit 0
}

$goCommand = Get-Command go -ErrorAction SilentlyContinue
if ($goCommand) {
    $goExe = $goCommand.Source
} else {
    $goExe = Join-Path $toolRoot 'go\bin\go.exe'
    if (-not (Test-Path -LiteralPath $goExe)) {
        $goZip = Join-Path $toolRoot 'go1.23.12.windows-amd64.zip'
        New-Item -ItemType Directory -Force -Path $toolRoot | Out-Null
        Write-Host 'Downloading a local Go toolchain to build siege-dissect...'
        Invoke-WebRequest -Uri 'https://go.dev/dl/go1.23.12.windows-amd64.zip' -OutFile $goZip
        $actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $goZip).Hash.ToLowerInvariant()
        if ($actualHash -ne '07c35866cdd864b81bb6f1cfbf25ac7f87ddc3a976ede1bf5112acbb12dfe6dc') {
            throw 'The downloaded Go archive failed its official SHA-256 check.'
        }
        Expand-Archive -LiteralPath $goZip -DestinationPath $toolRoot -Force
        Remove-Item -LiteralPath $goZip
    }
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $parserPath) | Out-Null
$buildPath = Join-Path $toolRoot 'bin\siege-dissect-building.exe'
Write-Host 'Building the repository siege-dissect source...'
Push-Location $sourceRoot
try {
    & $goExe build -o $buildPath .
} finally { Pop-Location }
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $buildPath)) {
    throw 'The siege-dissect build failed. Check the Go output above.'
}
Move-Item -LiteralPath $buildPath -Destination $parserPath -Force
[IO.File]::WriteAllText($manifestPath, $manifest + "`n")
Write-Host "Parser ready: $parserPath"
