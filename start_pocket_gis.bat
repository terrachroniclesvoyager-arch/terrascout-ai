@echo off
title Pocket GIS Launcher
cls
echo ========================================================
echo          POCKET GIS - AI Satellite Analysis
echo ========================================================
echo.

:START
echo [INFO] Starting Application...
echo.

rem Check if python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.10+
    pause
    exit /b
)

rem Install/Update dependencies if needed (first run specific)
if not exist "installed.flag" (
    echo [INIT] First run detected. Checking dependencies...
    pip install -r requirements.txt
    echo done > installed.flag
)


rem Set PROJ_LIB to avoid version mismatches
for /f "delims=" %%i in ('python -c "import pyproj; import os; print(os.path.join(os.path.dirname(pyproj.__file__), 'proj_dir', 'share', 'proj'))"') do set PROJ_LIB=%%i
echo [INFO] PROJ_LIB set to: %PROJ_LIB%

rem Run Streamlit
streamlit run app.py --server.port 8501 --browser.serverAddress localhost

if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Application crashed or stopped.
    echo [ACTION] Restarting in 5 seconds...
    timeout /t 5
    goto START
)

echo [INFO] Application closed normally.
pause
