@echo off
setlocal EnableExtensions EnableDelayedExpansion

if #%PYTHONCALL%#==## set PYTHONCALL=call python3
if #%SPHINXBUILD%#==## set SPHINXBUILD=%PYTHONCALL% -m sphinx

set BUILD_DIR=%~dp0_build
::set STATIC_DIR=%~dp0_static
::set TMP_DIR=%~dp0_tmp

set SPHINX_ALLOPTS=-d %BUILD_DIR%/doctrees %SPHINXOPTS% .
set SPHINX_I18NOPTS=%SPHINXOPTS% .
if NOT "%PAPER%" == "" (
    set SPHINX_ALLOPTS=-D latex_paper_size=%PAPER% %SPHINX_ALLOPTS%
    set SPHINX_I18NOPTS=-D latex_paper_size=%PAPER% %SPHINX_I18NOPTS%
)

set INTERACTIVE=0


if "%~1"=="" (
    set INTERACTIVE=1
    goto DO_HTML
)
if "%~1"=="html"  goto DO_HTML
if "%~1"=="clean" goto DO_CLEAN
set INTERACTIVE=1
goto DO_ASK


:DO_PREPARE
if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"
::if not exist "%STATIC_DIR%" mkdir "%STATIC_DIR%"
exit /B 0


:DO_CLEAN
cls
echo Cleaning...
rmdir /S /Q "%BUILD_DIR%"
goto DO_ASK


:DO_HTML
cls
echo Generating HTML...
call :DO_PREPARE
%SPHINXBUILD% -b html %SPHINX_ALLOPTS% %BUILD_DIR%/html
%PYTHONCALL% -c "print('\7')"
goto DO_ASK


:DO_SERVER
start "HTTP Server" /D "%BUILD_DIR%\html" ^
    %PYTHONCALL% -m http.server 8000 --bind 127.0.0.1
start "" "%ProgramFiles(x86)%\\Google\\Chrome\\Application\\chrome.exe" ^
    --incognito --new-window "http://127.0.0.1:8000"
goto DO_ASK


:DO_ASK
if "%INTERACTIVE%"=="0" goto END
echo.
set /P INPUT="Html/Server/Clean/Quit? [H] "
set ANS=%INPUT%
set INPUT=
if /I "%ANS%"==""  goto DO_HTML
if /I "%ANS%"=="H" goto DO_HTML
if /I "%ANS%"=="S" goto DO_SERVER
if /I "%ANS%"=="C" goto DO_CLEAN
if /I "%ANS%"=="Q" goto END
cls
echo.
echo Unknown answer: "%ANS%"
goto DO_ASK


:END
