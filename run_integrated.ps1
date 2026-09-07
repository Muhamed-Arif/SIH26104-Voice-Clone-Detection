param([switch]$NoBrowser)
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $MyInvocation.MyCommand.Path -Parent
$Python = Join-Path $RepoRoot ".venv-m2/Scripts/python.exe"
if (-not (Test-Path $Python)) {
    throw "Run .\m2\setup_windows.ps1 first."
}

$env:MODEL_PATH = (Resolve-Path (Join-Path $RepoRoot "models/voice_authenticity_balanced.joblib")).Path
$env:MODEL_THRESHOLD = "0.45"
$env:DATABASE_URL = "sqlite+aiosqlite:///./voice_shield.db"
$env:ML_SERVICE_URL = "http://127.0.0.1:8001/predict"
$env:MOCK_ML_SERVICE = "False"

$ml = Start-Process -FilePath $Python -ArgumentList "-m","uvicorn","app:app","--host","127.0.0.1","--port","8001" -WorkingDirectory (Join-Path $RepoRoot "ml-service") -PassThru
Start-Sleep -Seconds 2
$backend = Start-Process -FilePath $Python -ArgumentList "-m","uvicorn","main:app","--host","127.0.0.1","--port","8000" -WorkingDirectory (Join-Path $RepoRoot "backend") -PassThru
Start-Sleep -Seconds 2

Write-Host "M1:       http://127.0.0.1:8001/health"
Write-Host "Backend:  http://127.0.0.1:8000/integration-health"
Write-Host "Frontend: http://127.0.0.1:8000/"
Write-Host "M2 live:  .\.venv-m2\Scripts\python.exe -m m2.stream_to_backend"
Write-Host "Press Ctrl+C here to stop the local services."

if (-not $NoBrowser) { Start-Process "http://127.0.0.1:8000/" }
try {
    Wait-Process -Id $backend.Id
} finally {
    foreach ($p in @($backend, $ml)) {
        if ($p -and -not $p.HasExited) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
    }
}
