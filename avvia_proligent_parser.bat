@echo off
setlocal

cd /d "%~dp0"

set LOG_DIR=%~dp0logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Unique log per launch so a previous instance cannot lock the file.
set LOG_STAMP=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%_%RANDOM%
set LOG_STAMP=%LOG_STAMP: =0%
set LOG_FILE=%LOG_DIR%\launcher_%LOG_STAMP%.log

call :log Launcher avviato

REM =========================
REM Python detection robusta
REM =========================

if exist "%~dp0.venv\Scripts\python.exe" (
    call :log Usando: %~dp0.venv\Scripts\python.exe
    "%~dp0.venv\Scripts\python.exe" gui.py >> "%LOG_FILE%" 2>&1
    set EXIT_CODE=%errorlevel%
    call :log Exit code: %EXIT_CODE%
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

call :log Python NON trovato
exit /b 1

:run
call :log Usando: %PYTHON_CMD%

%PYTHON_CMD% gui.py >> "%LOG_FILE%" 2>&1

set EXIT_CODE=%errorlevel%

call :log Exit code: %EXIT_CODE%

exit /b %EXIT_CODE%

:log
echo [%date% %time%] %* >> "%LOG_FILE%" 2>nul
echo [%date% %time%] %*
goto :eof
