# Run from the repository root: .\scripts\start-backend.ps1
# The virtual environment keeps project packages separate from Windows Python.

Set-Location "$PSScriptRoot\..\backend"

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    py -m venv .venv
}

.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
