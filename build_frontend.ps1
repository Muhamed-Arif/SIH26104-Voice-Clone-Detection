param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $MyInvocation.MyCommand.Path -Parent
$Frontend = Join-Path $RepoRoot "frontend"
$Dist = Join-Path $Frontend "dist"
$Target = Join-Path $RepoRoot "backend\app\static\aethervoice"

if (-not (Test-Path (Join-Path $Frontend "package.json"))) {
    throw "frontend/package.json not found."
}

$npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $npm) { $npm = Get-Command npm -ErrorAction SilentlyContinue }
if (-not $npm) {
    throw "Node.js/npm is not installed or is not available in PATH."
}

Push-Location $Frontend
try {
    if (-not $SkipInstall -or -not (Test-Path (Join-Path $Frontend "node_modules"))) {
        Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
        & $npm.Source ci
        if ($LASTEXITCODE -ne 0) { throw "npm ci failed with exit code $LASTEXITCODE" }
    }

    Write-Host "Building AetherVoice frontend..." -ForegroundColor Cyan
    & $npm.Source run build
    if ($LASTEXITCODE -ne 0) { throw "npm run build failed with exit code $LASTEXITCODE" }
} finally {
    Pop-Location
}

if (-not (Test-Path (Join-Path $Dist "index.html"))) {
    throw "Vite build did not produce frontend/dist/index.html"
}

if (Test-Path $Target) {
    Remove-Item $Target -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $Target | Out-Null
Copy-Item (Join-Path $Dist "*") $Target -Recurse -Force

Write-Host "" 
Write-Host "AetherVoice production frontend is ready." -ForegroundColor Green
Write-Host "Target: $Target"
Write-Host "Restart the integrated prototype with:"
Write-Host "powershell -ExecutionPolicy Bypass -File .\run_integrated.ps1"
