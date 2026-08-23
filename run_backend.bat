@echo off
cd /d "%~dp0backend"
if exist ".venv\Scripts\uvicorn.exe" (
    echo Starting FastAPI backend using virtual environment...
    ".venv\Scripts\uvicorn.exe" app.main:app --reload --port 8000
) else if exist "%USERPROFILE%\.local\bin\uv.exe" (
    echo Starting FastAPI backend using uv...
    "%USERPROFILE%\.local\bin\uv.exe" run uvicorn app.main:app --reload --port 8000
) else (
    echo Starting FastAPI backend...
    uv run uvicorn app.main:app --reload --port 8000
)
pause
