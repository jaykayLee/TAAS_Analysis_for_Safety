@echo off
chcp 65001 >nul
cd /d %~dp0
python build.py %*
if errorlevel 1 (echo. & echo 빌드 실패: pip install -r requirements.txt 를 먼저 실행했는지 확인하세요.)
pause
