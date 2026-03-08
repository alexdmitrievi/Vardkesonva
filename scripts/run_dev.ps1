$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$BackendEnv = Join-Path $RootDir "backend\.env"

if (-not (Test-Path $BackendEnv)) {
  Copy-Item (Join-Path $RootDir "backend\.env.example") $BackendEnv
  Write-Host "Created backend\.env from .env.example"
}

python -m pip install -r (Join-Path $RootDir "backend\requirements.txt")

Write-Host "Starting backend on http://localhost:8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$RootDir\backend'; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

Write-Host "Starting static frontend on http://localhost:8080/legal_portal.html"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$RootDir\frontend'; python -m http.server 8080"
