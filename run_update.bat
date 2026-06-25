@echo off
cd /d "C:\!Workspace\Project\Project_industry_analyzer\industry-dashboard"

echo.
echo ========================================
echo   Industry Dashboard - Data Update
echo ========================================
echo.

echo [CHECK] Python path: C:\!Workspace\Project\Project_industry_analyzer\industry-dashboard
echo.

:: py 먼저 시도, 없으면 python3, 없으면 python
set PYTHON_CMD=

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=py
    goto :found
)

where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python3
    goto :found
)

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
    goto :found
)

echo [ERROR] Python not found. Please install Python from https://python.org
echo         Make sure to check "Add Python to PATH" during installation.
pause
exit /b 1

:found
echo [OK] Python found: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

echo [1/3] Installing requirements ...
%PYTHON_CMD% -m pip install requests --quiet
echo [OK] requests ready.
echo.

echo [2/3] Running collect_data.py ...
%PYTHON_CMD% collect_data.py --sector all

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] collect_data.py failed. Check error above.
    pause
    exit /b 1
)

echo.
echo [3/3] Done! All sector data updated.
echo       Open index.html to view dashboards.
echo.
pause
