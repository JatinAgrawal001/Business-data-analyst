@echo off
title InsightFlow AI - Frontend Server
cd /d "%~dp0Business-data-analyst"
if not exist "node_modules" (
    echo Installing frontend dependencies, please wait...
    npm install
)
echo.
echo ===================================================
echo   Starting InsightFlow AI Frontend on Port 5173
echo   Opening Chrome / Browser: http://localhost:5173
echo ===================================================
echo.
npm run dev
pause
