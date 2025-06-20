@echo off
title Application Launcher


:: 2. 백엔드 파이썬 스크립트 실행
echo RBackend.py를 실행합니다...
python RBackend.py

:: 백엔드가 준비될 시간을 주기 위해 잠시 대기합니다. (2초)
timeout /t 2 >nul

:: 3. 웹 UI HTML 파일 실행
echo WebUI.HTML을 기본 웹 브라우저에서 엽니다...
start WebUI.HTML

echo.
echo 모든 구성 요소가 실행되었습니다.