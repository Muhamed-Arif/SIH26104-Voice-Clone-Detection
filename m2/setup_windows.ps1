$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent
Push-Location $RepoRoot
try {
    py -3.12 -m venv .venv-m2
    if ($LASTEXITCODE -ne 0) { throw "Install Python 3.12, then retry." }
    & ./.venv-m2/Scripts/python.exe -m pip install -r m2/requirements.txt -r ml-service/requirements-ml.txt -c m2/constraints.txt
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
} finally { Pop-Location }
