param(
    [string]$ModelPath = "",
    [double]$Threshold = 0.45,
    [int]$Port = 8001
)
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent
$Python = Join-Path $RepoRoot ".venv-m2/Scripts/python.exe"

if (-not (Test-Path $Python)) {
    throw "Python environment not found. Run: powershell -ExecutionPolicy Bypass -File .\m2\setup_windows.ps1"
}

if (-not $ModelPath) {
    $ModelPath = Join-Path $RepoRoot "models/voice_authenticity_balanced.joblib"
}

$env:MODEL_PATH = (Resolve-Path $ModelPath).Path
$env:MODEL_THRESHOLD = [string]$Threshold

Write-Host "Starting M1 ML service"
Write-Host "Model: $env:MODEL_PATH"
Write-Host "Threshold: $env:MODEL_THRESHOLD"
Write-Host "URL: http://127.0.0.1:$Port"

Push-Location (Join-Path $RepoRoot "ml-service")
try {
    & $Python -m uvicorn app:app --host 127.0.0.1 --port $Port
} finally {
    Pop-Location
}
