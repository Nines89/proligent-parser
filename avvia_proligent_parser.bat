@echo off
setlocal

cd /d "%~dp0"

set LOG_DIR=%~dp0logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

set LOG_FILE=%LOG_DIR%\launcher_%date:~-4%%date:~3,2%%date:~0,2%.log

echo [%date% %time%] Launcher avviato >> "%LOG_FILE%"

REM =========================
REM Python detection robusta
REM =========================

if exist "%~dp0.venv\Scripts\python.exe" (
    echo [%date% %time%] Usando: %~dp0.venv\Scripts\python.exe >> "%LOG_FILE%"
    "%~dp0.venv\Scripts\python.exe" gui.py >> "%LOG_FILE%" 2>&1
    set EXIT_CODE=%errorlevel%
    echo [%date% %time%] Exit code: %EXIT_CODE% >> "%LOG_FILE%"
    exit /b %EXIT_CODE%
)

set PYTHON_CMD=

where py >nul 2>nul
if %errorlevel%==0 (
    set PYTHON_CMD=py -3
    goto :run
)

where python >nul 2>nul
if %errorlevel%==0 (
    set PYTHON_CMD=python
    goto :run
)

where pythonw >nul 2>nul
if %errorlevel%==0 (
    set PYTHON_CMD=pythonw
    goto :run
)

echo [%date% %time%] Python NON trovato >> "%LOG_FILE%"
exit /b 1

:run
echo [%date% %time%] Usando: %PYTHON_CMD% >> "%LOG_FILE%"

%PYTHON_CMD% gui.py >> "%LOG_FILE%" 2>&1

set EXIT_CODE=%errorlevel%

echo [%date% %time%] Exit code: %EXIT_CODE% >> "%LOG_FILE%"

exit /b %EXIT_CODE%
