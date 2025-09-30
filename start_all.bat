@echo off
REM Skript pro spuštění celé aplikace na Windows s virtuálním prostředím

echo ======================================
echo Volby PS CR 2025 - Starting All Services
echo ======================================

REM Kontrola Python instalace
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

echo Python version:
python --version

REM Přechod do adresáře skriptu
cd /d %~dp0

REM Vytvoření virtuálního prostředí pokud neexistuje
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo Error: Failed to create virtual environment
        echo Make sure you have python venv module installed
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
) else (
    echo Virtual environment already exists
)

REM Aktivace virtuálního prostředí
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Kontrola aktivace
if "%VIRTUAL_ENV%"=="" (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

echo Virtual environment activated: %VIRTUAL_ENV%

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip -q

REM Kontrola a instalace závislostí
echo Checking Python dependencies...
pip show flask >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Python dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
    echo Dependencies installed successfully
) else (
    echo Verifying all dependencies are up to date...
    pip install -q -r requirements.txt --upgrade
)

REM Vytvoření složky pro logy
if not exist logs mkdir logs

REM Vytvoření databázové složky
if not exist database mkdir database

echo.
echo Starting services...
echo.

REM Spuštění data collectoru v novém okně
echo Starting Data Collector...
start "Data Collector - Volby 2025" cmd /k "venv\Scripts\activate && python start_collector.py"

REM Počkat 3 sekundy
timeout /t 3 /nobreak >nul

REM Spuštění webové aplikace v novém okně
echo Starting Web Application...
start "Web Application - Volby 2025" cmd /k "venv\Scripts\activate && python start_webapp.py"

REM Počkat na start aplikací
timeout /t 3 /nobreak >nul

echo.
echo ======================================
echo All services are running!
echo ======================================
echo.
echo Web application: http://localhost:8080
echo.
echo Services running in separate windows:
echo   - Data Collector
echo   - Web Application
echo.
echo To stop services: Close the command windows
echo.
echo Logs are saved in:
echo   - logs\collector.log
echo   - logs\webapp.log
echo.

REM Otevřít prohlížeč
echo Opening web browser...
timeout /t 2 /nobreak >nul
start http://localhost:8080

pause