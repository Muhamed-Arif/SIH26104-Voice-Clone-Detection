param(
    [ValidateSet("candidate", "baseline")][string]$Model = "candidate",
    [string]$ModelPath = "",
    [int]$Port = 8001,
    [switch]$EnableShadow
)
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent

if (-not $ModelPath) {
    if ($Model -eq "candidate") {
        $ModelPath = Join-Path $RepoRoot "ml-service/model_artifacts/candidate-gradient-boosting-v1.joblib"
    } else {
        $ModelPath = Join-Path $RepoRoot "ml-service/model_artifacts/baseline-v2.joblib"
    }
}

$resolved = (Resolve-Path $ModelPath).Path
$env:MODEL_ARTIFACT_PATH = $resolved
$env:ALLOW_MOCK_PREDICTOR = "0"
if ($EnableShadow) {
    $env:ENABLE_SHADOW_PREDICTOR = "1"
} else {
    $env:ENABLE_SHADOW_PREDICTOR = "0"
}

Write-Host "Starting M1 model: $resolved"
Write-Host "Shadow predictor: $env:ENABLE_SHADOW_PREDICTOR"
Push-Location (Join-Path $RepoRoot "ml-service")
try {
    & (Join-Path $RepoRoot ".venv-m2/Scripts/python.exe") -m uvicorn ml_service.api:app --host 127.0.0.1 --port $Port
} finally {
    Pop-Location
}
