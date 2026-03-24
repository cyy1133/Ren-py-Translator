@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Ren'Py Translation Workbench Launcher

for %%I in ("%~dp0.") do set "APP_ROOT=%%~fI"
cd /d "%APP_ROOT%"

set "BACKEND_URL=http://127.0.0.1:5000/health"
set "WEB_URL=http://127.0.0.1:8765/WebUI.HTML"
set "VENV_DIR=%APP_ROOT%\.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "VENV_PYW=%VENV_DIR%\Scripts\pythonw.exe"
set "LAUNCH_PY=%VENV_PY%"
set "BOOTSTRAP_PYTHON="
set "RENTRY_RENPY_LATEST_PAGE=https://www.renpy.org/latest.html"
set "RENTRY_RENPY_SDK_FALLBACK_URL=https://www.renpy.org/dl/8.5.2/renpy-8.5.2-sdk.zip"
set "RENTRY_RENPY_SDK_ZIP=%APP_ROOT%\renpy_sdk.zip"
set "RENTRY_RENPY_SDK_DIR=%APP_ROOT%\renpy_sdk"

echo [1/7] Checking Python runtime...
call :resolve_python
if errorlevel 1 goto :fail

echo [2/7] Preparing virtual environment...
if not exist "%VENV_PY%" (
    call %BOOTSTRAP_PYTHON% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Failed to create the virtual environment.
        goto :fail
    )
)
if exist "%VENV_PYW%" set "LAUNCH_PY=%VENV_PYW%"

echo [3/7] Installing Python packages...
"%VENV_PY%" -m pip install --disable-pip-version-check --upgrade pip >nul
if errorlevel 1 (
    echo Failed to upgrade pip.
    goto :fail
)
"%VENV_PY%" -m pip install --disable-pip-version-check -r "%APP_ROOT%\requirements.txt"
if errorlevel 1 (
    echo Failed to install required Python packages.
    goto :fail
)

echo [4/7] Checking optional Node.js runtime for Codex CLI...
call :ensure_node_runtime

echo [5/7] Preparing bundled Ren'Py SDK...
call :ensure_renpy_sdk
if errorlevel 1 goto :fail

echo [6/7] Starting backend and local web server...
call :ensure_backend
if errorlevel 1 goto :fail
call :ensure_web_server
if errorlevel 1 goto :fail

echo [7/7] Opening the workbench...
start "" "%WEB_URL%"

echo.
echo Workbench is ready.
echo Browser: %WEB_URL%
echo Backend: %BACKEND_URL%
echo.
echo You only need to enter your API key in the UI.
exit /b 0

:resolve_python
where python >nul 2>nul
if not errorlevel 1 (
    set "BOOTSTRAP_PYTHON=python"
    exit /b 0
)

where py >nul 2>nul
if not errorlevel 1 (
    set "BOOTSTRAP_PYTHON=py -3.12"
    exit /b 0
)

echo Python was not found. Attempting to install Python 3.12 with winget...
where winget >nul 2>nul
if errorlevel 1 (
    echo winget is not available. Install Python 3.12 manually and run Start.bat again.
    exit /b 1
)

winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements --disable-interactivity >nul

if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    set "BOOTSTRAP_PYTHON=\"%LocalAppData%\Programs\Python\Python312\python.exe\""
    exit /b 0
)

where python >nul 2>nul
if not errorlevel 1 (
    set "BOOTSTRAP_PYTHON=python"
    exit /b 0
)

where py >nul 2>nul
if not errorlevel 1 (
    set "BOOTSTRAP_PYTHON=py -3.12"
    exit /b 0
)

echo Python installation did not complete successfully.
exit /b 1

:ensure_node_runtime
where node >nul 2>nul
if not errorlevel 1 goto :node_done
where npm >nul 2>nul
if not errorlevel 1 goto :node_done

where winget >nul 2>nul
if errorlevel 1 (
    echo Node.js was not found and winget is unavailable. OpenAI OAuth will stay unavailable until Node.js is installed.
    goto :node_done
)

echo Installing Node.js LTS for Codex CLI support...
winget install -e --id OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements --disable-interactivity >nul

:node_done
exit /b 0

:ensure_renpy_sdk
if exist "%RENTRY_RENPY_SDK_DIR%" exit /b 0

if not exist "%RENTRY_RENPY_SDK_ZIP%" (
    echo Ren'Py SDK archive not found. Downloading the official SDK...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "$latestPage = $env:RENTRY_RENPY_LATEST_PAGE;" ^
        "$fallbackUrl = $env:RENTRY_RENPY_SDK_FALLBACK_URL;" ^
        "$targetZip = $env:RENTRY_RENPY_SDK_ZIP;" ^
        "$downloadUrl = $env:RENTRY_RENPY_SDK_URL;" ^
        "if (-not $downloadUrl) {" ^
        "  try {" ^
        "    $page = Invoke-WebRequest -Uri $latestPage -UseBasicParsing -TimeoutSec 30;" ^
        "    $patterns = @(" ^
        "      'https://www\.renpy\.org/dl/[0-9.]+/renpy-[0-9.]+-sdk\.zip'," ^
        "      'href=\"(/dl/[0-9.]+/renpy-[0-9.]+-sdk\.zip)\"'" ^
        "    );" ^
        "    foreach ($pattern in $patterns) {" ^
        "      $match = [regex]::Match($page.Content, $pattern);" ^
        "      if ($match.Success) {" ^
        "        $downloadUrl = $match.Value;" ^
        "        if ($match.Groups.Count -gt 1 -and $match.Groups[1].Value) { $downloadUrl = 'https://www.renpy.org' + $match.Groups[1].Value }" ^
        "        break;" ^
        "      }" ^
        "    }" ^
        "  } catch { }" ^
        "}" ^
        "if (-not $downloadUrl) { $downloadUrl = $fallbackUrl }" ^
        "Invoke-WebRequest -Uri $downloadUrl -OutFile $targetZip -UseBasicParsing -TimeoutSec 120"
    if errorlevel 1 (
        echo Failed to download the Ren'Py SDK.
        exit /b 1
    )
)

if not exist "%RENTRY_RENPY_SDK_ZIP%" (
    echo Ren'Py SDK archive could not be found or downloaded.
    exit /b 1
)

echo Extracting Ren'Py SDK...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%RENTRY_RENPY_SDK_ZIP%' -DestinationPath '%RENTRY_RENPY_SDK_DIR%' -Force" >nul
if errorlevel 1 (
    echo Failed to extract the Ren'Py SDK archive.
    exit /b 1
)

if not exist "%RENTRY_RENPY_SDK_DIR%" (
    echo Ren'Py SDK directory was not created successfully.
    exit /b 1
)

exit /b 0

:ensure_backend
call :wait_url "%BACKEND_URL%" 1
if not errorlevel 1 exit /b 0

start "RenPy Workbench Backend" /min "%LAUNCH_PY%" "%APP_ROOT%\RBackend.py"
call :wait_url "%BACKEND_URL%" 45
if errorlevel 1 (
    echo Failed to start RenPy Workbench Backend.
    exit /b 1
)
exit /b 0

:ensure_web_server
call :wait_url "%WEB_URL%" 1
if not errorlevel 1 exit /b 0

start "RenPy Workbench Web" /min "%VENV_PY%" -m http.server 8765 --bind 127.0.0.1 --directory "%APP_ROOT%"
call :wait_url "%WEB_URL%" 45
if errorlevel 1 (
    echo Failed to start RenPy Workbench Web.
    exit /b 1
)
exit /b 0

:wait_url
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$uri = '%~1'; $deadline = (Get-Date).AddSeconds(%~2); while ((Get-Date) -lt $deadline) { try { $response = Invoke-WebRequest -UseBasicParsing -Uri $uri -TimeoutSec 2; if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) { exit 0 } } catch { } Start-Sleep -Milliseconds 500 }; exit 1" >nul
exit /b %errorlevel%

:fail
echo.
echo Launcher failed. Review the messages above and retry.
pause
exit /b 1
