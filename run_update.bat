@echo off
<<<<<<< HEAD
setlocal

set "PROJ=C:\!Workspace\Project\Project_industry_analyzer\industry-dashboard"
cd /d "%PROJ%"
set "VENV_PY=%PROJ%\.venv\Scripts\python.exe"
=======
cd /d "C:\!Workspace\Project\Project_industry_analyzer\industry-dashboard"
>>>>>>> ee484fafef39d9e18ac7963d5eb924d4c25e1fc4

echo.
echo ========================================
echo   Industry Dashboard - Data Update
echo ========================================
echo.

<<<<<<< HEAD
:: ---- .venv 확인: 있으면 그걸 쓰고, 없으면 새로 생성 ----
if exist "%VENV_PY%" goto :have_venv

echo [SETUP] .venv 가 없어 새로 만듭니다 ...
set "BOOT_PY="
where py      >nul 2>&1 && set "BOOT_PY=py"
if not defined BOOT_PY (
    where python3 >nul 2>&1 && set "BOOT_PY=python3"
)
if not defined BOOT_PY (
    where python  >nul 2>&1 && set "BOOT_PY=python"
)
if not defined BOOT_PY (
    echo [ERROR] Python not found. Please install Python from https://python.org
    echo         Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
echo [SETUP] bootstrap Python: %BOOT_PY%
"%BOOT_PY%" -m venv ".venv"
if not exist "%VENV_PY%" (
    echo [ERROR] .venv 생성 실패.
    pause
    exit /b 1
)

:have_venv
echo [OK] venv Python: %VENV_PY%
"%VENV_PY%" --version
echo.

echo [1/3] Installing requirements (requirements.txt) ...
"%VENV_PY%" -m pip install -r requirements.txt --quiet
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] 패키지 설치 실패. 위 오류를 확인하세요.
    pause
    exit /b 1
)
echo [OK] dependencies ready.
echo.

echo [2/3] Running collect_data.py ...
"%VENV_PY%" collect_data.py --sector all
=======
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

>>>>>>> ee484fafef39d9e18ac7963d5eb924d4c25e1fc4
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
<<<<<<< HEAD
exit /b 0
=======
>>>>>>> ee484fafef39d9e18ac7963d5eb924d4c25e1fc4
