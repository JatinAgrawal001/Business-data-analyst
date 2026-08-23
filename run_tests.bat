@echo off
cd /d "%~dp0backend"
if exist "%USERPROFILE%\.local\bin\uv.exe" (
    "%USERPROFILE%\.local\bin\uv.exe" run pytest -v
) else (
    uv run pytest -v
)
pause
