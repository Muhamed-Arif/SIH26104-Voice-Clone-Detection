$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent
Push-Location $RepoRoot
try {
    py -3.12 -m venv .venv-m2
    if ($LASTEXITCODE -ne 0) { throw "Install Python 3.12, then retry." }
    $Python = Join-Path $RepoRoot ".venv-m2/Scripts/python.exe"
    & $Python -m pip install --upgrade pip
    & $Python -m pip install `
        -r m2/requirements.txt `
        -r ml-service/requirements.txt `
        -r backend/requirements.txt `
        -c m2/constraints.txt
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
    Write-Host "Integrated M1 + M2 + backend environment is ready."
} finally {
    Pop-Location
}
