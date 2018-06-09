@echo off
setlocal

set PYTHON_CMD=

if not "%FITDECODE_PYTHON%"=="" (
    %FITDECODE_PYTHON% --version >nul 2>&1
    if not ERRORLEVEL 1 set PYTHON_CMD=%FITDECODE_PYTHON%
)

if "%PYTHON_CMD%"=="" (
    if not "%PYTHON%"=="" (
        %PYTHON% --version >nul 2>&1
        if not ERRORLEVEL 1 set PYTHON_CMD=%PYTHON%
    )
)

if "%PYTHON_CMD%"=="" (
    call python3 --version >nul 2>&1
    if not ERRORLEVEL 1 set PYTHON_CMD=call python3
)

if "%PYTHON_CMD%"=="" (
    call python --version >nul 2>&1
    if not ERRORLEVEL 1 set PYTHON_CMD=call python
)

if "%PYTHON_CMD%"=="" (
    call wpy --version >nul 2>&1
    if not ERRORLEVEL 1 set PYTHON_CMD=call wpy
)

if "%PYTHON_CMD%"=="" (
    echo ERROR: failed to find Python
    exit /b 1
)

%PYTHON_CMD% -B %*
