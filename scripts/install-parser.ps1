$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$toolRoot = Join-Path $projectRoot '.local-tools'
$parserPath = Join-Path $toolRoot 'bin\siege-dissect.exe'
if ((Get-Command siege-dissect -ErrorAction SilentlyContinue) -or (Test-Path -LiteralPath $parserPath)) {
    Write-Host 'siege-dissect is available.'
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

$env:GOBIN = Join-Path $toolRoot 'bin'
New-Item -ItemType Directory -Force -Path $env:GOBIN | Out-Null
Write-Host 'Building lumina-r6/siege-dissect from pinned source...'
& $goExe install 'github.com/lumina-r6/siege-dissect@ea662d31f4dc2a66576088c49ab8d3174b0b3989'
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $parserPath)) {
    throw 'The siege-dissect build failed. Check the Go output above.'
}
Write-Host "Parser ready: $parserPath"
